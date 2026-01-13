#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module de gestion des utilisateurs utilisant la configuration de l'application.
Ce module charge dynamiquement le backend de gestion utilisateurs en fonction du plugin
d'authentification configuré. Il supporte les plugins intégrés et les plugins personnalisés
ajoutés par l'utilisateur.

Architecture:
- UserManagementBackend: Classe de base abstraite pour les backends de gestion utilisateurs
- UserBackendRegistry: Registre singleton pour la découverte dynamique des backends
- UserManager: Interface unifiée pour la gestion des utilisateurs
"""

import os
import sys
import json
import hashlib
import importlib
import importlib.util
import inspect
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Type

# Ajouter le répertoire parent au path pour pouvoir importer les modules de l'application
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# Classe de base abstraite pour les backends de gestion utilisateurs
# =============================================================================

class UserManagementBackend(ABC):
    """Classe de base abstraite pour les backends de gestion des utilisateurs.
    
    Tous les backends (intégrés ou personnalisés) doivent hériter de cette classe
    et implémenter les méthodes abstraites.
    
    Pour créer un nouveau backend personnalisé:
    1. Créer un fichier dans custom_plugins/auth/ (ex: mybackend_users.py)
    2. Créer une classe qui hérite de UserManagementBackend
    3. Implémenter toutes les méthodes abstraites
    4. La classe sera automatiquement découverte et utilisable
    
    Le nom du backend est extrait du nom de la classe:
    - MyCustomUserBackend -> 'mycustom'
    - LDAPUserBackend -> 'ldap'
    """
    
    def __init__(self, config: dict, project_root: str = None):
        """Initialise le backend avec sa configuration.
        
        Args:
            config: Configuration du plugin d'authentification
            project_root: Chemin racine du projet (optionnel)
        """
        self.config = config
        self.project_root = project_root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    @abstractmethod
    def list_users(self) -> List[Dict[str, Any]]:
        """Liste tous les utilisateurs."""
        pass
    
    @abstractmethod
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Récupère les informations d'un utilisateur."""
        pass
    
    @abstractmethod
    def create_user(self, username: str, password: str, role: str = 'user',
                    email: str = None) -> bool:
        """Crée un nouvel utilisateur."""
        pass
    
    @abstractmethod
    def update_user(self, username: str, new_password: str = None,
                    new_role: str = None, new_username: str = None,
                    new_email: str = None) -> bool:
        """Modifie un utilisateur existant."""
        pass
    
    @abstractmethod
    def delete_user(self, username: str) -> bool:
        """Supprime un utilisateur."""
        pass
    
    @abstractmethod
    def user_exists(self, username: str) -> bool:
        """Vérifie si un utilisateur existe."""
        pass
    
    @abstractmethod
    def count_admins(self) -> int:
        """Compte le nombre d'administrateurs."""
        pass
    
    def close(self):
        """Ferme les connexions (à surcharger si nécessaire)."""
        pass
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash un mot de passe avec SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()


# =============================================================================
# Registre de découverte dynamique des backends
# =============================================================================

class UserBackendRegistry:
    """Registre singleton pour la découverte et l'enregistrement des backends.
    
    Ce registre scanne automatiquement:
    - Les backends intégrés dans scripts/backends/
    - Les backends personnalisés dans custom_plugins/auth/
    
    Les backends sont identifiés par convention de nommage:
    - Fichiers: *_users.py ou *_user_backend.py
    - Classes: héritant de UserManagementBackend
    """
    
    _instance: Optional['UserBackendRegistry'] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not UserBackendRegistry._initialized:
            self._backends: Dict[str, Type[UserManagementBackend]] = {}
            self._project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            UserBackendRegistry._initialized = True
    
    @property
    def backends(self) -> Dict[str, Type[UserManagementBackend]]:
        """Retourne le dictionnaire des backends enregistrés."""
        return self._backends
    
    def register(self, name: str, backend_class: Type[UserManagementBackend]):
        """Enregistre un backend.
        
        Args:
            name: Nom du backend (ex: 'local', 'mongodb', 'ldap')
            backend_class: Classe du backend
        """
        self._backends[name.lower()] = backend_class
    
    def get(self, name: str) -> Optional[Type[UserManagementBackend]]:
        """Récupère une classe de backend par son nom.
        
        Args:
            name: Nom du backend
            
        Returns:
            Classe du backend ou None si non trouvé
        """
        return self._backends.get(name.lower())
    
    def list_backends(self) -> List[str]:
        """Liste les noms de tous les backends disponibles."""
        return list(self._backends.keys())
    
    def discover(self, verbose: bool = False):
        """Découvre et enregistre tous les backends disponibles.
        
        Scanne:
        1. Les backends intégrés (dans ce fichier)
        2. Les backends dans scripts/backends/
        3. Les plugins personnalisés dans custom_plugins/auth/
        
        Args:
            verbose: Affiche les backends découverts
        """
        if verbose:
            print("🔍 Découverte des backends de gestion utilisateurs...")
        
        # 1. Enregistrer les backends intégrés définis dans ce fichier
        self._register_builtin_backends(verbose)
        
        # 2. Scanner le répertoire scripts/backends/ pour des backends additionnels
        backends_dir = os.path.join(os.path.dirname(__file__), 'backends')
        if os.path.isdir(backends_dir):
            self._scan_directory(backends_dir, verbose)
        
        # 3. Scanner custom_plugins/auth/ pour les plugins personnalisés
        custom_dir = os.path.join(self._project_root, 'custom_plugins', 'auth')
        if os.path.isdir(custom_dir):
            self._scan_directory(custom_dir, verbose, prefix='custom_')
        
        if verbose:
            print(f"✅ {len(self._backends)} backend(s) disponible(s): {', '.join(self._backends.keys())}")
    
    def _register_builtin_backends(self, verbose: bool = False):
        """Enregistre les backends intégrés définis dans ce module."""
        # Récupérer toutes les classes définies dans ce module qui héritent de UserManagementBackend
        current_module = sys.modules[__name__]
        
        for name, obj in inspect.getmembers(current_module, inspect.isclass):
            if (issubclass(obj, UserManagementBackend) and 
                obj is not UserManagementBackend and
                not inspect.isabstract(obj)):
                backend_name = self._extract_backend_name(obj)
                self._backends[backend_name] = obj
                if verbose:
                    print(f"  ✓ Backend intégré: {backend_name}")
    
    def _scan_directory(self, directory: str, verbose: bool = False, prefix: str = ''):
        """Scanne un répertoire pour trouver des backends.
        
        Args:
            directory: Chemin du répertoire à scanner
            verbose: Affiche les découvertes
            prefix: Préfixe pour les noms de modules (évite les collisions)
        """
        directory = Path(directory)
        
        for file_path in directory.glob('*.py'):
            if file_path.name.startswith('_'):
                continue
            
            # Charger le module dynamiquement
            module_name = f"user_backend_{prefix}{file_path.stem}"
            module = self._load_module(file_path, module_name)
            
            if module is None:
                continue
            
            # Chercher les classes de backend dans le module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, UserManagementBackend) and 
                    obj is not UserManagementBackend and
                    not inspect.isabstract(obj)):
                    backend_name = self._extract_backend_name(obj)
                    self._backends[backend_name] = obj
                    if verbose:
                        source = "personnalisé" if prefix else "additionnel"
                        print(f"  ✓ Backend {source}: {backend_name} ({file_path.name})")
    
    def _load_module(self, file_path: Path, module_name: str):
        """Charge dynamiquement un module Python.
        
        Args:
            file_path: Chemin du fichier Python
            module_name: Nom à donner au module
            
        Returns:
            Module chargé ou None en cas d'erreur
        """
        try:
            spec = importlib.util.spec_from_file_location(module_name, file_path)
            if spec is None or spec.loader is None:
                return None
            
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            return module
        except Exception:
            return None
    
    def _extract_backend_name(self, cls: type) -> str:
        """Extrait le nom du backend depuis le nom de la classe.
        
        Conventions:
        - LocalUserBackend -> 'local'
        - MongoDBUserBackend -> 'mongodb'
        - MyCustomUserBackend -> 'mycustom'
        
        Args:
            cls: Classe du backend
            
        Returns:
            Nom du backend en minuscules
        """
        name = cls.__name__
        
        # Supprimer les suffixes communs
        suffixes = ['UserBackend', 'UsersBackend', 'Backend']
        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)]
                break
        
        # Convertir en minuscules (gérer les acronymes comme MongoDB, PostgreSQL)
        return name.lower()


def get_backend_registry(discover: bool = True, verbose: bool = False) -> UserBackendRegistry:
    """Récupère le registre des backends (singleton).
    
    Args:
        discover: Lance la découverte automatique si True
        verbose: Affiche les backends découverts
        
    Returns:
        Instance du registre
    """
    registry = UserBackendRegistry()
    if discover and not registry.backends:
        registry.discover(verbose=verbose)
    return registry


# =============================================================================
# Gestionnaire d'utilisateurs principal
# =============================================================================

class UserManager:
    """Gestionnaire d'utilisateurs unifié avec découverte dynamique des backends.
    
    Cette classe charge automatiquement le backend approprié en fonction de la
    configuration du plugin d'authentification. Elle supporte:
    - Les backends intégrés (local, mongodb, postgresql)
    - Les backends personnalisés (ajoutés dans custom_plugins/auth/)
    
    Usage:
        manager = UserManager()  # Utilise config.json par défaut
        manager = UserManager('/path/to/config.json')
        
        users = manager.list_users()
        manager.create_user('john', 'password123', role='user')
    """
    
    def __init__(self, config_path: str = None, verbose: bool = False):
        """Initialise le gestionnaire avec la configuration de l'application.
        
        Args:
            config_path: Chemin vers le fichier de configuration (par défaut: config.json)
            verbose: Affiche des informations de debug
        """
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.verbose = verbose
        
        if config_path is None:
            config_path = os.path.join(self.project_root, 'config.json')
        elif not os.path.isabs(config_path):
            config_path = os.path.join(self.project_root, config_path)
        
        self.config = self._load_config(config_path)
        self.auth_type = self.config.get('plugins', {}).get('authentication', {}).get('type', 'local')
        self.auth_config = self.config.get('plugins', {}).get('authentication', {}).get('config', {})
        
        # Initialiser le backend via le registre dynamique
        self._backend = self._init_backend()
    
    def _load_config(self, config_path: str) -> dict:
        """Charge la configuration depuis le fichier JSON."""
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        raise FileNotFoundError(f"Fichier de configuration non trouvé: {config_path}")
    
    def _init_backend(self) -> UserManagementBackend:
        """Initialise le backend d'authentification via découverte dynamique.
        
        Returns:
            Instance du backend configuré
            
        Raises:
            ValueError: Si le type de backend n'est pas trouvé
        """
        # Obtenir le registre et découvrir les backends
        registry = get_backend_registry(discover=True, verbose=self.verbose)
        
        # Chercher le backend correspondant au type configuré
        backend_class = registry.get(self.auth_type)
        
        if backend_class is None:
            available = ', '.join(registry.list_backends())
            raise ValueError(
                f"Type d'authentification non supporté: '{self.auth_type}'. "
                f"Backends disponibles: {available}. "
                f"Pour ajouter un nouveau backend, créez une classe héritant de "
                f"UserManagementBackend dans custom_plugins/auth/"
            )
        
        # Instancier le backend
        return backend_class(self.auth_config, self.project_root)
    
    def list_users(self, role_filter: str = None) -> List[Dict[str, Any]]:
        """Liste tous les utilisateurs.
        
        Args:
            role_filter: Filtrer par rôle (admin ou user)
            
        Returns:
            Liste des utilisateurs
        """
        users = self._backend.list_users()
        if role_filter:
            users = [u for u in users if u.get('role', 'user') == role_filter]
        return users
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Récupère les informations d'un utilisateur.
        
        Args:
            username: Nom d'utilisateur
            
        Returns:
            Informations de l'utilisateur ou None
        """
        return self._backend.get_user(username)
    
    def create_user(self, username: str, password: str, role: str = 'user', 
                    email: str = None) -> bool:
        """Crée un nouvel utilisateur.
        
        Args:
            username: Nom d'utilisateur
            password: Mot de passe
            role: Rôle (admin ou user)
            email: Email optionnel
            
        Returns:
            True si succès, False sinon
        """
        return self._backend.create_user(username, password, role, email)
    
    def update_user(self, username: str, new_password: str = None, 
                    new_role: str = None, new_username: str = None,
                    new_email: str = None) -> bool:
        """Modifie un utilisateur existant.
        
        Args:
            username: Nom d'utilisateur actuel
            new_password: Nouveau mot de passe (optionnel)
            new_role: Nouveau rôle (optionnel)
            new_username: Nouveau nom d'utilisateur (optionnel)
            new_email: Nouvel email (optionnel)
            
        Returns:
            True si succès, False sinon
        """
        return self._backend.update_user(username, new_password, new_role, new_username, new_email)
    
    def delete_user(self, username: str) -> bool:
        """Supprime un utilisateur.
        
        Args:
            username: Nom d'utilisateur à supprimer
            
        Returns:
            True si succès, False sinon
        """
        return self._backend.delete_user(username)
    
    def user_exists(self, username: str) -> bool:
        """Vérifie si un utilisateur existe.
        
        Args:
            username: Nom d'utilisateur
            
        Returns:
            True si l'utilisateur existe
        """
        return self._backend.user_exists(username)
    
    def count_admins(self) -> int:
        """Compte le nombre d'administrateurs.
        
        Returns:
            Nombre d'administrateurs
        """
        return self._backend.count_admins()
    
    def get_backend_type(self) -> str:
        """Retourne le type de backend utilisé.
        
        Returns:
            Type de backend (local, mongodb, postgresql, ou personnalisé)
        """
        return self.auth_type
    
    def get_available_backends(self) -> List[str]:
        """Retourne la liste des backends disponibles.
        
        Returns:
            Liste des noms de backends
        """
        registry = get_backend_registry(discover=True)
        return registry.list_backends()
    
    def close(self):
        """Ferme les connexions du backend."""
        if hasattr(self._backend, 'close'):
            self._backend.close()


# =============================================================================
# Backends intégrés
# =============================================================================

class LocalUserBackend(UserManagementBackend):
    """Backend pour l'authentification locale (fichier JSON).
    
    Ce backend stocke les utilisateurs dans un fichier JSON local.
    Idéal pour le développement et les petites installations.
    """
    
    def __init__(self, config: dict, project_root: str = None):
        super().__init__(config, project_root)
        self.users_file = config.get('users_file', './data/users.json')
        if not os.path.isabs(self.users_file):
            self.users_file = os.path.join(self.project_root, self.users_file)
    
    def _load_data(self) -> dict:
        """Charge les données depuis le fichier JSON."""
        if os.path.exists(self.users_file):
            with open(self.users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"users": []}
    
    def _save_data(self, data: dict):
        """Sauvegarde les données dans le fichier JSON."""
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def list_users(self) -> List[Dict[str, Any]]:
        data = self._load_data()
        return [{'username': u['username'], 'role': u.get('role', 'user')} 
                for u in data.get('users', [])]
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        data = self._load_data()
        for user in data.get('users', []):
            if user['username'] == username:
                return {'username': user['username'], 'role': user.get('role', 'user')}
        return None
    
    def create_user(self, username: str, password: str, role: str = 'user', 
                    email: str = None) -> bool:
        data = self._load_data()
        if any(u['username'] == username for u in data.get('users', [])):
            return False
        
        new_user = {
            'username': username,
            'password_hash': self.hash_password(password),
            'role': role
        }
        data['users'].append(new_user)
        self._save_data(data)
        return True
    
    def update_user(self, username: str, new_password: str = None,
                    new_role: str = None, new_username: str = None,
                    new_email: str = None) -> bool:
        data = self._load_data()
        user_index = None
        
        for i, user in enumerate(data.get('users', [])):
            if user['username'] == username:
                user_index = i
                break
        
        if user_index is None:
            return False
        
        # Vérifier unicité du nouveau nom
        if new_username:
            if any(u['username'] == new_username for u in data.get('users', []) 
                   if u['username'] != username):
                return False
            data['users'][user_index]['username'] = new_username
        
        if new_password:
            data['users'][user_index]['password_hash'] = self.hash_password(new_password)
        
        if new_role:
            data['users'][user_index]['role'] = new_role
        
        self._save_data(data)
        return True
    
    def delete_user(self, username: str) -> bool:
        data = self._load_data()
        initial_len = len(data.get('users', []))
        data['users'] = [u for u in data.get('users', []) if u['username'] != username]
        
        if len(data['users']) == initial_len:
            return False
        
        self._save_data(data)
        return True
    
    def user_exists(self, username: str) -> bool:
        data = self._load_data()
        return any(u['username'] == username for u in data.get('users', []))
    
    def count_admins(self) -> int:
        data = self._load_data()
        return sum(1 for u in data.get('users', []) if u.get('role') == 'admin')


class MongoDBUserBackend(UserManagementBackend):
    """Backend pour l'authentification MongoDB.
    
    Ce backend stocke les utilisateurs dans une collection MongoDB.
    Recommandé pour les installations avec plusieurs serveurs ou volumes importants.
    """
    
    def __init__(self, config: dict, project_root: str = None):
        super().__init__(config, project_root)
        try:
            from pymongo import MongoClient
            from pymongo.errors import ConnectionFailure
        except ImportError:
            raise ImportError(
                "Le backend MongoDB nécessite pymongo. "
                "Installez-le avec: pip install pymongo"
            )
        
        self.connection_string = config.get('connection_string', 'mongodb://localhost:27017')
        self.database_name = config.get('database', 'openmark')
        self.users_collection_name = config.get('users_collection', 'users')
        
        self._client = MongoClient(self.connection_string, serverSelectionTimeoutMS=5000)
        self._client.admin.command('ping')  # Vérifier la connexion
        self._db = self._client[self.database_name]
        self._users = self._db[self.users_collection_name]
    
    def list_users(self) -> List[Dict[str, Any]]:
        users = list(self._users.find({}, {'password_hash': 0}))
        for user in users:
            user['_id'] = str(user['_id'])
        return users
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        user = self._users.find_one({'username': username}, {'password_hash': 0})
        if user:
            user['_id'] = str(user['_id'])
        return user
    
    def create_user(self, username: str, password: str, role: str = 'user',
                    email: str = None) -> bool:
        if self._users.find_one({'username': username}):
            return False
        
        try:
            self._users.insert_one({
                'username': username,
                'password_hash': self.hash_password(password),
                'role': role,
                'email': email,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow(),
                'active': True
            })
            return True
        except Exception:
            return False
    
    def update_user(self, username: str, new_password: str = None,
                    new_role: str = None, new_username: str = None,
                    new_email: str = None) -> bool:
        if not self._users.find_one({'username': username}):
            return False
        
        # Vérifier unicité du nouveau nom
        if new_username and self._users.find_one({'username': new_username}):
            return False
        
        update_fields = {'updated_at': datetime.utcnow()}
        
        if new_password:
            update_fields['password_hash'] = self.hash_password(new_password)
        if new_role:
            update_fields['role'] = new_role
        if new_username:
            update_fields['username'] = new_username
        if new_email:
            update_fields['email'] = new_email
        
        try:
            result = self._users.update_one(
                {'username': username},
                {'$set': update_fields}
            )
            return result.modified_count > 0
        except Exception:
            return False
    
    def delete_user(self, username: str) -> bool:
        try:
            result = self._users.delete_one({'username': username})
            return result.deleted_count > 0
        except Exception:
            return False
    
    def user_exists(self, username: str) -> bool:
        return self._users.find_one({'username': username}) is not None
    
    def count_admins(self) -> int:
        return self._users.count_documents({'role': 'admin', 'active': True})
    
    def close(self):
        if self._client:
            self._client.close()


class PostgreSQLUserBackend(UserManagementBackend):
    """Backend pour l'authentification PostgreSQL.
    
    Ce backend stocke les utilisateurs dans une base PostgreSQL.
    Recommandé pour les environnements nécessitant des transactions ACID.
    """
    
    def __init__(self, config: dict, project_root: str = None):
        super().__init__(config, project_root)
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
        except ImportError:
            raise ImportError(
                "Le backend PostgreSQL nécessite psycopg2. "
                "Installez-le avec: pip install psycopg2-binary"
            )
        
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 5432)
        self.database = config.get('database', 'openmark')
        self.user = config.get('user', 'openmark')
        self.password = config.get('password')
        self.users_table = config.get('users_table', 'auth_users')
        self.connection_string = config.get('connection_string')
        
        if self.connection_string:
            self._conn = psycopg2.connect(self.connection_string)
        else:
            self._conn = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
    
    def list_users(self) -> List[Dict[str, Any]]:
        import psycopg2.extras
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(f"""
                SELECT id, username, role, email, created_at, updated_at, active
                FROM {self.users_table}
                ORDER BY id
            """)
            return [dict(row) for row in cur.fetchall()]
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        import psycopg2.extras
        with self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(f"""
                SELECT id, username, role, email, created_at, updated_at, active
                FROM {self.users_table}
                WHERE username = %s
            """, (username,))
            row = cur.fetchone()
            return dict(row) if row else None
    
    def create_user(self, username: str, password: str, role: str = 'user',
                    email: str = None) -> bool:
        try:
            with self._conn.cursor() as cur:
                cur.execute(f"""
                    INSERT INTO {self.users_table} (username, password_hash, role, email)
                    VALUES (%s, %s, %s, %s)
                """, (username, self.hash_password(password), role, email))
            self._conn.commit()
            return True
        except Exception:
            self._conn.rollback()
            return False
    
    def update_user(self, username: str, new_password: str = None,
                    new_role: str = None, new_username: str = None,
                    new_email: str = None) -> bool:
        # Construire la requête dynamiquement
        updates = []
        params = []
        
        if new_password:
            updates.append("password_hash = %s")
            params.append(self.hash_password(new_password))
        if new_role:
            updates.append("role = %s")
            params.append(new_role)
        if new_username:
            updates.append("username = %s")
            params.append(new_username)
        if new_email:
            updates.append("email = %s")
            params.append(new_email)
        
        if not updates:
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(username)
        
        try:
            with self._conn.cursor() as cur:
                cur.execute(f"""
                    UPDATE {self.users_table}
                    SET {', '.join(updates)}
                    WHERE username = %s
                """, params)
                updated = cur.rowcount > 0
            self._conn.commit()
            return updated
        except Exception:
            self._conn.rollback()
            return False
    
    def delete_user(self, username: str) -> bool:
        try:
            with self._conn.cursor() as cur:
                cur.execute(f"""
                    DELETE FROM {self.users_table}
                    WHERE username = %s
                """, (username,))
                deleted = cur.rowcount > 0
            self._conn.commit()
            return deleted
        except Exception:
            self._conn.rollback()
            return False
    
    def user_exists(self, username: str) -> bool:
        with self._conn.cursor() as cur:
            cur.execute(f"""
                SELECT 1 FROM {self.users_table}
                WHERE username = %s
            """, (username,))
            return cur.fetchone() is not None
    
    def count_admins(self) -> int:
        with self._conn.cursor() as cur:
            cur.execute(f"""
                SELECT COUNT(*) FROM {self.users_table}
                WHERE role = 'admin' AND active = TRUE
            """)
            return cur.fetchone()[0]
    
    def close(self):
        if self._conn:
            self._conn.close()
