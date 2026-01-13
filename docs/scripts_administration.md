# Scripts d'administration OpenMark

Ce document décrit les scripts d'automatisation pour la gestion des utilisateurs et des annotations dans OpenMark.

## Fonctionnement

Les scripts utilisent **automatiquement le backend configuré** dans le fichier `config.json` de l'application. Le système de découverte dynamique charge automatiquement :

- **Backends intégrés** : `local`, `mongodb`, `postgresql`
- **Backends personnalisés** : Tout backend placé dans `custom_plugins/auth/`

Cela permet d'ajouter de nouveaux backends (LDAP, Active Directory, etc.) sans modifier le code existant.

## Architecture

```
scripts/
├── user_manager.py         # Module de gestion des utilisateurs
├── user_list.py            # Script: lister les utilisateurs
├── user_create.py          # Script: créer un utilisateur
├── user_modify.py          # Script: modifier un utilisateur
├── user_delete.py          # Script: supprimer un utilisateur
├── annotations_import.py   # Script: importer des annotations
├── annotations_export.py   # Script: exporter des annotations
└── backends/               # (optionnel) Backends additionnels
```

## Prérequis

- Python 3.7+
- Dépendances selon le backend utilisé :
  - **local** : Aucune dépendance externe
  - **mongodb** : `pip install pymongo`
  - **postgresql** : `pip install psycopg2-binary`

---

## Scripts de gestion des utilisateurs

### `user_list.py` - Lister les utilisateurs

Liste tous les utilisateurs de la base de données d'authentification configurée.

```bash
# Afficher tous les utilisateurs (format tableau)
python3 scripts/user_list.py

# Filtrer par rôle
python3 scripts/user_list.py --role admin
python3 scripts/user_list.py --role user

# Exporter en JSON
python3 scripts/user_list.py --format json

# Exporter en CSV
python3 scripts/user_list.py --format csv > users.csv

# Utiliser un fichier de configuration personnalisé
python3 scripts/user_list.py -c ./config-production.json
```

### `user_create.py` - Créer un utilisateur

Crée un nouvel utilisateur dans la base de données d'authentification configurée.

```bash
# Créer un utilisateur standard
python3 scripts/user_create.py -u john -p secret123

# Créer un administrateur
python3 scripts/user_create.py -u admin2 -p adminpass -r admin

# Avec email (pour MongoDB/PostgreSQL)
python3 scripts/user_create.py -u john -p secret123 -e john@example.com

# Saisie interactive du mot de passe (recommandé pour la sécurité)
python3 scripts/user_create.py -u john
# Le script demandera le mot de passe de manière sécurisée
```

**Options:**
- `-u, --username` : Nom d'utilisateur (obligatoire)
- `-p, --password` : Mot de passe (optionnel, demandé interactivement si non fourni)
- `-r, --role` : Rôle de l'utilisateur (`admin` ou `user`, par défaut: `user`)
- `-e, --email` : Email de l'utilisateur (optionnel, supporté par MongoDB/PostgreSQL)
- `-c, --config` : Chemin vers le fichier de configuration

### `user_modify.py` - Modifier un utilisateur

Modifie un utilisateur existant (mot de passe, rôle, nom d'utilisateur, email).

```bash
# Changer le mot de passe
python3 scripts/user_modify.py -u john -p newpassword123

# Changer le rôle
python3 scripts/user_modify.py -u john -r admin

# Changer le nom d'utilisateur
python3 scripts/user_modify.py -u john --new-username johnny

# Changer l'email
python3 scripts/user_modify.py -u john -e john@newdomain.com

# Modifier plusieurs attributs à la fois
python3 scripts/user_modify.py -u john -p newpass -r admin --new-username johnny

# Saisie interactive du nouveau mot de passe
python3 scripts/user_modify.py -u john -p
# Le script demandera le nouveau mot de passe de manière sécurisée
```

**Options:**
- `-u, --username` : Nom d'utilisateur à modifier (obligatoire)
- `-p, --password` : Nouveau mot de passe (optionnel)
- `-r, --role` : Nouveau rôle (`admin` ou `user`)
- `--new-username` : Nouveau nom d'utilisateur
- `-e, --email` : Nouvel email
- `-c, --config` : Chemin vers le fichier de configuration

### `user_delete.py` - Supprimer un utilisateur

Supprime un utilisateur de la base de données d'authentification configurée.

```bash
# Supprimer un utilisateur (avec confirmation)
python3 scripts/user_delete.py -u john

# Supprimer sans confirmation
python3 scripts/user_delete.py -u john --force
python3 scripts/user_delete.py -u john -y
```

**Options:**
- `-u, --username` : Nom d'utilisateur à supprimer (obligatoire)
- `--force, -y` : Supprimer sans demander confirmation
- `-c, --config` : Chemin vers le fichier de configuration

> **Note:** Le script empêche la suppression du dernier administrateur.

---

## Scripts de gestion des annotations

### `annotations_export.py` - Exporter des annotations

Exporte les annotations (notes et surlignages) vers un fichier JSON.

```bash
# Exporter un document spécifique
python3 scripts/annotations_export.py -u admin -d rapport2026 -o export.json

# Exporter tous les documents d'un utilisateur
python3 scripts/annotations_export.py -u admin --all -o backup.json

# Sortie vers stdout (pour piping)
python3 scripts/annotations_export.py -u admin -d doc1 | jq .

# Format compact
python3 scripts/annotations_export.py -u admin -d doc1 --compact
```

**Options:**
- `-u, --user` : Utilisateur source (obligatoire)
- `-d, --document` : Document spécifique à exporter
- `--all` : Exporter tous les documents de l'utilisateur
- `-o, --output` : Fichier de sortie (stdout si non spécifié)
- `--compact` : Format JSON compact
- `-v, --verbose` : Afficher les détails
- `-c, --config` : Chemin vers le fichier de configuration

### `annotations_import.py` - Importer des annotations

Importe des annotations depuis un fichier JSON.

```bash
# Importer un fichier multi-utilisateur
python3 scripts/annotations_import.py -f export.json

# Importer pour un utilisateur/document spécifique
python3 scripts/annotations_import.py -f notes.json -u admin -d rapport2026

# Mode remplacement (écrase les annotations existantes)
python3 scripts/annotations_import.py -f export.json --mode replace

# Validation sans import (dry-run)
python3 scripts/annotations_import.py -f export.json --dry-run -v
```

**Options:**
- `-f, --file` : Fichier JSON à importer (obligatoire)
- `-u, --user` : Utilisateur cible (obligatoire pour format simple)
- `-d, --document` : Document cible (obligatoire pour format simple)
- `--mode` : Mode d'import: `merge` (défaut) ou `replace`
- `--dry-run` : Valider sans importer
- `-v, --verbose` : Afficher les détails
- `-c, --config` : Chemin vers le fichier de configuration

### Format JSON pour les annotations

```json
{
  "version": "1.0",
  "data": [
    {
      "user_id": "admin",
      "document_id": "rapport2026",
      "annotations": {
        "notes": [
          {
            "page": 1,
            "x": 100,
            "y": 200,
            "content": "Ma note",
            "color": "#ffff00"
          }
        ],
        "highlights": [
          {
            "page": 1,
            "rects": [{"x": 50, "y": 100, "width": 300, "height": 20}],
            "color": "#00ff00"
          }
        ]
      }
    }
  ]
}
```

> **Documentation détaillée:** Voir [Annotations Import/Export](annotations_import.md) pour les formats complets et exemples avancés.

---

## Configuration par backend

### Backend Local (fichier JSON)

```json
{
  "plugins": {
    "authentication": {
      "type": "local",
      "config": {
        "users_file": "./data/users.json"
      }
    }
  }
}
```

### Backend MongoDB

```json
{
  "plugins": {
    "authentication": {
      "type": "mongodb",
      "config": {
        "connection_string": "mongodb://admin:adminpassword@localhost:27017/",
        "database": "openmark",
        "users_collection": "users"
      }
    }
  }
}
```

### Backend PostgreSQL

```json
{
  "plugins": {
    "authentication": {
      "type": "postgresql",
      "config": {
        "host": "localhost",
        "port": 5432,
        "database": "openmark",
        "user": "openmark",
        "password": "openmarkpassword",
        "users_table": "auth_users"
      }
    }
  }
}
```

---

## Exemples de flux de travail

### Initialiser un nouveau déploiement

```bash
# 1. Lister les utilisateurs par défaut
python3 scripts/user_list.py

# 2. Créer un nouvel administrateur
python3 scripts/user_create.py -u superadmin -r admin -e admin@company.com
# Entrer le mot de passe de manière interactive

# 3. Supprimer l'utilisateur admin par défaut
python3 scripts/user_delete.py -u admin --force

# 4. Créer les utilisateurs nécessaires
python3 scripts/user_create.py -u user1 -e user1@company.com
python3 scripts/user_create.py -u user2 -e user2@company.com

# 5. Vérifier la liste finale
python3 scripts/user_list.py
```

### Utilisation avec Docker Compose

```bash
# Démarrer les services (depuis le répertoire dev/)
cd dev
docker-compose up -d
cd ..

# Utiliser les scripts avec la configuration MongoDB
python3 scripts/user_list.py -c config-mongodb.json

# Utiliser les scripts avec la configuration PostgreSQL
python3 scripts/user_list.py -c config-postgresql.json
```

### Export et sauvegarde

```bash
# Exporter la liste des utilisateurs en JSON
python3 scripts/user_list.py --format json > backup_users.json

# Exporter la liste des utilisateurs en CSV
python3 scripts/user_list.py --format csv > users_export.csv

# Exporter les annotations
python3 scripts/annotations_export.py -u admin --all -o annotations_backup.json
```

---

## Sécurité

- Les mots de passe sont hashés en SHA-256 avant d'être stockés
- Utilisez la saisie interactive du mot de passe (`-p` sans valeur) pour éviter que le mot de passe n'apparaisse dans l'historique du shell
- Ne partagez jamais les fichiers contenant des hash de mots de passe
- Assurez-vous que les fichiers de configuration avec les mots de passe de base de données ont des permissions restrictives

```bash
chmod 600 config.json
chmod 600 data/users.json
```

---

## Backends personnalisés

Le système supporte l'ajout de backends personnalisés sans modifier le code source.

### Créer un backend personnalisé

1. Créez un fichier Python dans `custom_plugins/auth/` (ex: `ldap_users.py`)
2. Créez une classe héritant de `UserManagementBackend`
3. Implémentez toutes les méthodes abstraites

```python
# custom_plugins/auth/ldap_users.py

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.user_manager import UserManagementBackend
from typing import Optional, List, Dict, Any

class LDAPUserBackend(UserManagementBackend):
    """Backend LDAP pour la gestion des utilisateurs."""
    
    def __init__(self, config: dict, project_root: str = None):
        super().__init__(config, project_root)
        # Initialisation spécifique LDAP...
    
    def list_users(self) -> List[Dict[str, Any]]:
        # Implémentation...
        pass
    
    # ... autres méthodes requises
```

Le nom du backend est automatiquement extrait du nom de la classe :
- `LDAPUserBackend` → `ldap`
- `ActiveDirectoryUserBackend` → `activedirectory`
- `MyCustomUserBackend` → `mycustom`

### Configuration

```json
{
  "plugins": {
    "authentication": {
      "type": "ldap",
      "config": {
        "ldap_url": "ldap://ldap.example.com:389",
        "base_dn": "dc=example,dc=com"
      }
    }
  }
}
```

### Vérifier les backends disponibles

```python
from scripts.user_manager import get_backend_registry

registry = get_backend_registry(discover=True, verbose=True)
print(registry.list_backends())  # ['local', 'mongodb', 'postgresql', 'ldap', ...]
```

---

## Module user_manager.py

Le module `user_manager.py` fournit :

- **`UserManagementBackend`** : Classe de base abstraite pour les backends
- **`UserBackendRegistry`** : Registre singleton avec découverte automatique
- **`UserManager`** : Interface unifiée pour les scripts
- **Backends intégrés** : `LocalUserBackend`, `MongoDBUserBackend`, `PostgreSQLUserBackend`

### Utilisation programmatique

```python
from scripts.user_manager import UserManager

# Utilise la config par défaut (config.json)
manager = UserManager()

# Ou avec une config personnalisée
manager = UserManager('/path/to/config.json', verbose=True)

# Opérations
users = manager.list_users()
manager.create_user('alice', 'password123', role='user')
manager.update_user('alice', new_role='admin')
manager.delete_user('bob')

# Info
print(manager.get_backend_type())       # 'local'
print(manager.get_available_backends()) # ['local', 'mongodb', 'postgresql']

# Fermer les connexions
manager.close()
```
