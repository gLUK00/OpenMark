# Custom Authentication Plugins

Place your custom authentication plugin files here.

## Authentication Plugin Example

```python
# my_ldap_auth.py

from app.plugins.base import AuthenticationPlugin
from typing import Optional
import ldap  # pip install python-ldap

class MyLDAPAuthPlugin(AuthenticationPlugin):
    """Custom LDAP authentication plugin."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.ldap_url = config.get('ldap_url', 'ldap://localhost:389')
        self.base_dn = config.get('base_dn', 'dc=example,dc=com')
    
    def authenticate(self, username: str, password: str) -> Optional[dict]:
        # Your LDAP authentication logic here
        pass
    
    def validate_token(self, token: str) -> Optional[dict]:
        # Your token validation logic here
        pass
    
    def invalidate_token(self, token: str) -> bool:
        # Your token invalidation logic here
        pass
```

---

## User Management Backend Example

Pour que les scripts d'administration (`scripts/user_*.py`) fonctionnent avec votre 
plugin d'authentification personnalisé, vous devez également créer un backend de 
gestion des utilisateurs.

```python
# my_ldap_users.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scripts.user_manager import UserManagementBackend
from typing import Optional, List, Dict, Any

class MyLDAPUserBackend(UserManagementBackend):
    """Backend de gestion des utilisateurs pour LDAP.
    
    Le nom du backend est extrait automatiquement du nom de la classe:
    MyLDAPUserBackend -> 'myldap'
    """
    
    def __init__(self, config: dict, project_root: str = None):
        super().__init__(config, project_root)
        # Initialiser la connexion LDAP
        self.ldap_url = config.get('ldap_url', 'ldap://localhost:389')
        self.base_dn = config.get('base_dn', 'dc=example,dc=com')
        self.admin_dn = config.get('admin_dn')
        self.admin_password = config.get('admin_password')
        # ... connexion LDAP
    
    def list_users(self) -> List[Dict[str, Any]]:
        """Liste les utilisateurs LDAP."""
        # Recherche LDAP pour lister les utilisateurs
        # return [{'username': 'user1', 'role': 'user'}, ...]
        pass
    
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Récupère un utilisateur LDAP."""
        pass
    
    def create_user(self, username: str, password: str, role: str = 'user',
                    email: str = None) -> bool:
        """Crée un utilisateur dans LDAP."""
        # Note: utiliser self.hash_password(password) pour le stockage
        pass
    
    def update_user(self, username: str, new_password: str = None,
                    new_role: str = None, new_username: str = None,
                    new_email: str = None) -> bool:
        """Modifie un utilisateur LDAP."""
        pass
    
    def delete_user(self, username: str) -> bool:
        """Supprime un utilisateur LDAP."""
        pass
    
    def user_exists(self, username: str) -> bool:
        """Vérifie si un utilisateur existe dans LDAP."""
        pass
    
    def count_admins(self) -> int:
        """Compte les administrateurs dans LDAP."""
        pass
    
    def close(self):
        """Ferme la connexion LDAP."""
        pass
```

---

## Configuration

Configurez dans config.json:

```json
{
  "plugins": {
    "authentication": {
      "type": "myldap",
      "config": {
        "ldap_url": "ldap://your-ldap-server:389",
        "base_dn": "dc=yourcompany,dc=com",
        "admin_dn": "cn=admin,dc=yourcompany,dc=com",
        "admin_password": "your-admin-password"
      }
    }
  }
}
```

Le nom du plugin/backend est dérivé du nom de la classe:
- `MyLDAPAuthPlugin` → `myldap` (pour l'authentification)
- `MyLDAPUserBackend` → `myldap` (pour la gestion des utilisateurs)

Les deux doivent avoir le même nom pour fonctionner ensemble.
