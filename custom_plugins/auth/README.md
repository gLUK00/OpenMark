# Custom Authentication Plugins

Place your custom authentication plugin files here.

## Example

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

Then configure in config.json:
```json
{
  "plugins": {
    "authentication": {
      "type": "myldap",
      "config": {
        "ldap_url": "ldap://your-ldap-server:389",
        "base_dn": "dc=yourcompany,dc=com"
      }
    }
  }
}
```

The plugin name is derived from the class name: `MyLDAPAuthPlugin` → `myldap`
