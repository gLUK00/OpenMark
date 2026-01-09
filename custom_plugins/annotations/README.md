# Custom Annotations Plugins

Place your custom annotations plugin files here.

## Example

```python
# redis_annotations.py

from app.plugins.base import AnnotationsPlugin
from typing import Optional
import redis  # pip install redis

class RedisAnnotationsPlugin(AnnotationsPlugin):
    """Redis-based annotations storage plugin."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.redis_url = config.get('redis_url', 'redis://localhost:6379')
        self.client = redis.from_url(self.redis_url)
    
    def save_annotations(self, user_id: str, document_id: str, 
                         annotations: dict) -> bool:
        # Save annotations to Redis
        pass
    
    def get_annotations(self, user_id: str, document_id: str) -> dict:
        # Retrieve annotations from Redis
        pass
```

Then configure in config.json:
```json
{
  "plugins": {
    "annotations": {
      "type": "redis",
      "config": {
        "redis_url": "redis://localhost:6379/0"
      }
    }
  }
}
```

The plugin name is derived from the class name: `RedisAnnotationsPlugin` → `redis`
