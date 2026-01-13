#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Script pour modifier un utilisateur dans la base de données d'authentification."""

import argparse
import os
import sys
import getpass

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.user_manager import UserManager


def modify_user(config_path: str, username: str, new_password: str = None, 
                new_role: str = None, new_username: str = None,
                new_email: str = None) -> bool:
    """Modifie un utilisateur existant.
    
    Args:
        config_path: Chemin vers le fichier de configuration
        username: Nom d'utilisateur actuel
        new_password: Nouveau mot de passe (optionnel)
        new_role: Nouveau rôle (optionnel)
        new_username: Nouveau nom d'utilisateur (optionnel)
        new_email: Nouvel email (optionnel)
        
    Returns:
        True si l'utilisateur a été modifié, False sinon
    """
    try:
        manager = UserManager(config_path)
        backend_type = manager.get_backend_type()
        
        # Vérifier que l'utilisateur existe
        if not manager.user_exists(username):
            print(f"❌ Erreur: L'utilisateur '{username}' n'existe pas.")
            manager.close()
            return False
        
        # Vérifier si le nouveau nom d'utilisateur est disponible
        if new_username and manager.user_exists(new_username):
            print(f"❌ Erreur: Le nom d'utilisateur '{new_username}' est déjà utilisé.")
            manager.close()
            return False
        
        # Valider le rôle si fourni
        if new_role:
            valid_roles = ['admin', 'user']
            if new_role not in valid_roles:
                print(f"❌ Erreur: Rôle invalide '{new_role}'. Rôles valides: {', '.join(valid_roles)}")
                manager.close()
                return False
        
        # Appliquer les modifications
        success = manager.update_user(username, new_password, new_role, new_username, new_email)
        manager.close()
        
        if success:
            modifications = []
            if new_username:
                modifications.append(f"nom d'utilisateur: {username} → {new_username}")
            if new_password:
                modifications.append("mot de passe modifié")
            if new_role:
                modifications.append(f"rôle modifié → {new_role}")
            if new_email:
                modifications.append(f"email modifié → {new_email}")
            
            print(f"✅ Utilisateur '{username}' modifié avec succès dans {backend_type}:")
            for mod in modifications:
                print(f"   • {mod}")
            return True
        else:
            print(f"❌ Erreur lors de la modification de l'utilisateur '{username}'.")
            return False
            
    except FileNotFoundError as e:
        print(f"❌ Erreur: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur de connexion au backend: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Modifier un utilisateur dans la base de données d'authentification.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  %(prog)s -u john -p newpassword123
  %(prog)s -u john -r admin
  %(prog)s -u john --new-username johnny
  %(prog)s -u john -e john@newdomain.com
  %(prog)s -u john -p newpass -r admin --new-username johnny
  %(prog)s -u john --password  # Demande le nouveau mot de passe interactivement

Le script utilise automatiquement le backend configuré dans config.json
(local, mongodb, ou postgresql).
        """
    )
    
    parser.add_argument(
        '-u', '--username',
        required=True,
        help="Nom d'utilisateur à modifier"
    )
    parser.add_argument(
        '-p', '--password',
        nargs='?',
        const='INTERACTIVE',
        default=None,
        help="Nouveau mot de passe (si flag sans valeur, sera demandé de manière interactive)"
    )
    parser.add_argument(
        '-r', '--role',
        choices=['admin', 'user'],
        help="Nouveau rôle de l'utilisateur"
    )
    parser.add_argument(
        '--new-username',
        help="Nouveau nom d'utilisateur"
    )
    parser.add_argument(
        '-e', '--email',
        help="Nouvel email"
    )
    parser.add_argument(
        '-c', '--config',
        default='config.json',
        help="Chemin vers le fichier de configuration (par défaut: config.json)"
    )
    
    args = parser.parse_args()
    
    # Gérer le mot de passe interactif
    new_password = None
    if args.password == 'INTERACTIVE':
        new_password = getpass.getpass("Nouveau mot de passe: ")
        password_confirm = getpass.getpass("Confirmer le nouveau mot de passe: ")
        if new_password != password_confirm:
            print("❌ Erreur: Les mots de passe ne correspondent pas.")
            sys.exit(1)
        if not new_password:
            print("❌ Erreur: Le mot de passe ne peut pas être vide.")
            sys.exit(1)
    elif args.password:
        new_password = args.password
    
    # Vérifier qu'au moins une modification est demandée
    if not new_password and not args.role and not args.new_username and not args.email:
        print("❌ Erreur: Au moins une modification doit être spécifiée (-p, -r, -e, ou --new-username).")
        parser.print_help()
        sys.exit(1)
    
    success = modify_user(args.config, args.username, new_password, args.role, 
                          args.new_username, args.email)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
