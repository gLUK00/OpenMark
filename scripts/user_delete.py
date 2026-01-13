#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script pour supprimer un utilisateur de la base de données d'authentification."""

import argparse
import os
import sys

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.user_manager import UserManager


def delete_user(config_path: str, username: str, force: bool = False) -> bool:
    """Supprime un utilisateur.
    
    Args:
        config_path: Chemin vers le fichier de configuration
        username: Nom d'utilisateur à supprimer
        force: Si True, supprime sans demander confirmation
        
    Returns:
        True si l'utilisateur a été supprimé, False sinon
    """
    try:
        manager = UserManager(config_path)
        backend_type = manager.get_backend_type()
        
        # Vérifier que l'utilisateur existe
        user = manager.get_user(username)
        if not user:
            print(f"❌ Erreur: L'utilisateur '{username}' n'existe pas.")
            manager.close()
            return False
        
        # Vérifier qu'il reste au moins un admin
        if user.get('role') == 'admin' and manager.count_admins() <= 1:
            print(f"❌ Erreur: Impossible de supprimer le dernier administrateur.")
            manager.close()
            return False
        
        # Demander confirmation si pas en mode force
        if not force:
            print(f"\n🔌 Backend: {backend_type}")
            print(f"\n📋 Informations de l'utilisateur à supprimer:")
            print(f"   • Nom d'utilisateur: {user['username']}")
            print(f"   • Rôle: {user.get('role', 'user')}")
            if user.get('email'):
                print(f"   • Email: {user.get('email')}")
            print()
            
            confirmation = input(f"⚠️  Êtes-vous sûr de vouloir supprimer l'utilisateur '{username}'? (oui/non): ")
            if confirmation.lower() not in ['oui', 'o', 'yes', 'y']:
                print("❌ Suppression annulée.")
                manager.close()
                return False
        
        # Supprimer l'utilisateur
        success = manager.delete_user(username)
        manager.close()
        
        if success:
            print(f"✅ Utilisateur '{username}' supprimé avec succès de {backend_type}.")
            return True
        else:
            print(f"❌ Erreur lors de la suppression de l'utilisateur '{username}'.")
            return False
            
    except FileNotFoundError as e:
        print(f"❌ Erreur: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur de connexion au backend: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Supprimer un utilisateur de la base de données d'authentification.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  %(prog)s -u john
  %(prog)s -u john --force
  %(prog)s -u john -c ./config.json

Le script utilise automatiquement le backend configuré dans config.json
(local, mongodb, ou postgresql).

Note: Le dernier administrateur ne peut pas être supprimé.
        """
    )
    
    parser.add_argument(
        '-u', '--username',
        required=True,
        help="Nom d'utilisateur à supprimer"
    )
    parser.add_argument(
        '--force', '-y',
        action='store_true',
        help="Supprimer sans demander confirmation"
    )
    parser.add_argument(
        '-c', '--config',
        default='config.json',
        help="Chemin vers le fichier de configuration (par défaut: config.json)"
    )
    
    args = parser.parse_args()
    
    success = delete_user(args.config, args.username, args.force)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
