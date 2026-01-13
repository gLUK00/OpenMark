#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script pour créer un nouvel utilisateur dans la base de données d'authentification."""

import argparse
import os
import sys
import getpass

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.user_manager import UserManager


def create_user(config_path: str, username: str, password: str, 
                role: str = "user", email: str = None) -> bool:
    """Crée un nouvel utilisateur.
    
    Args:
        config_path: Chemin vers le fichier de configuration
        username: Nom d'utilisateur
        password: Mot de passe en clair
        role: Rôle de l'utilisateur (admin ou user)
        email: Email optionnel
        
    Returns:
        True si l'utilisateur a été créé, False sinon
    """
    try:
        manager = UserManager(config_path)
        backend_type = manager.get_backend_type()
        
        # Vérifier si l'utilisateur existe déjà
        if manager.user_exists(username):
            print(f"❌ Erreur: L'utilisateur '{username}' existe déjà.")
            manager.close()
            return False
        
        # Valider le rôle
        valid_roles = ['admin', 'user']
        if role not in valid_roles:
            print(f"❌ Erreur: Rôle invalide '{role}'. Rôles valides: {', '.join(valid_roles)}")
            manager.close()
            return False
        
        # Créer le nouvel utilisateur
        success = manager.create_user(username, password, role, email)
        manager.close()
        
        if success:
            print(f"✅ Utilisateur '{username}' créé avec succès (rôle: {role}) dans {backend_type}.")
            return True
        else:
            print(f"❌ Erreur lors de la création de l'utilisateur '{username}'.")
            return False
            
    except FileNotFoundError as e:
        print(f"❌ Erreur: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur de connexion au backend: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Créer un nouvel utilisateur dans la base de données d'authentification.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  %(prog)s -u john -p secret123
  %(prog)s -u admin2 -p adminpass -r admin
  %(prog)s -u john -e john@example.com  # Demande le mot de passe interactivement
  %(prog)s -u john  # Demande le mot de passe de manière interactive

Le script utilise automatiquement le backend configuré dans config.json
(local, mongodb, ou postgresql).
        """
    )
    
    parser.add_argument(
        '-u', '--username',
        required=True,
        help="Nom d'utilisateur à créer"
    )
    parser.add_argument(
        '-p', '--password',
        help="Mot de passe de l'utilisateur (si non fourni, sera demandé de manière interactive)"
    )
    parser.add_argument(
        '-r', '--role',
        choices=['admin', 'user'],
        default='user',
        help="Rôle de l'utilisateur (par défaut: user)"
    )
    parser.add_argument(
        '-e', '--email',
        help="Email de l'utilisateur (optionnel)"
    )
    parser.add_argument(
        '-c', '--config',
        default='config.json',
        help="Chemin vers le fichier de configuration (par défaut: config.json)"
    )
    
    args = parser.parse_args()
    
    # Demander le mot de passe de manière interactive si non fourni
    password = args.password
    if not password:
        password = getpass.getpass("Mot de passe: ")
        password_confirm = getpass.getpass("Confirmer le mot de passe: ")
        if password != password_confirm:
            print("❌ Erreur: Les mots de passe ne correspondent pas.")
            sys.exit(1)
    
    if not password:
        print("❌ Erreur: Le mot de passe ne peut pas être vide.")
        sys.exit(1)
    
    success = create_user(args.config, args.username, password, args.role, args.email)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
