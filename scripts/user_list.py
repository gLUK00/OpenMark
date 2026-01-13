#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script pour lister les utilisateurs de la base de données d'authentification."""

import argparse
import json
import os
import sys

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.user_manager import UserManager


def list_users(config_path: str, role_filter: str = None, output_format: str = 'table') -> bool:
    """Liste les utilisateurs.
    
    Args:
        config_path: Chemin vers le fichier de configuration
        role_filter: Filtrer par rôle (admin ou user)
        output_format: Format de sortie (table, json, csv)
        
    Returns:
        True si la liste a été affichée, False sinon
    """
    try:
        manager = UserManager(config_path)
        backend_type = manager.get_backend_type()
        users = manager.list_users(role_filter)
        
        if not users:
            if role_filter:
                print(f"ℹ️  Aucun utilisateur trouvé avec le rôle '{role_filter}'.")
            else:
                print("ℹ️  Aucun utilisateur trouvé.")
            return True
        
        # Afficher selon le format demandé
        if output_format == 'json':
            output = {
                "backend": backend_type,
                "users": [{"username": u['username'], "role": u.get('role', 'user')} for u in users]
            }
            print(json.dumps(output, indent=2, ensure_ascii=False, default=str))
        
        elif output_format == 'csv':
            print("username,role")
            for user in users:
                print(f"{user['username']},{user.get('role', 'user')}")
        
        else:  # table
            # Calculer la largeur des colonnes
            max_username = max(len(str(u['username'])) for u in users)
            header_username = "Nom d'utilisateur"
            max_username = max(max_username, len(header_username))
            
            # En-tête
            print()
            print(f"🔌 Backend: {backend_type}")
            print(f"📋 Liste des utilisateurs ({len(users)} trouvé(s)):")
            print()
            print(f"  {header_username:<{max_username}}  │  Rôle")
            separator = "─" * max_username
            print(f"  {separator}──┼──{'─' * 10}")
            
            # Données
            for user in users:
                username = user['username']
                role = user.get('role', 'user')
                role_icon = "👑" if role == 'admin' else "👤"
                active = user.get('active', True)
                status = "" if active else " (inactif)"
                print(f"  {username:<{max_username}}  │  {role_icon} {role}{status}")
            
            print()
        
        manager.close()
        return True
        
    except FileNotFoundError as e:
        print(f"❌ Erreur: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur de connexion au backend: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Lister les utilisateurs de la base de données d'authentification.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  %(prog)s
  %(prog)s --role admin
  %(prog)s --format json
  %(prog)s --format csv > users.csv
  %(prog)s -c ./config.json

Le script utilise automatiquement le backend configuré dans config.json
(local, mongodb, ou postgresql).
        """
    )
    
    parser.add_argument(
        '-r', '--role',
        choices=['admin', 'user'],
        help="Filtrer par rôle"
    )
    parser.add_argument(
        '--format',
        choices=['table', 'json', 'csv'],
        default='table',
        help="Format de sortie (par défaut: table)"
    )
    parser.add_argument(
        '-c', '--config',
        default='config.json',
        help="Chemin vers le fichier de configuration (par défaut: config.json)"
    )
    
    args = parser.parse_args()
    
    success = list_users(args.config, args.role, args.format)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
