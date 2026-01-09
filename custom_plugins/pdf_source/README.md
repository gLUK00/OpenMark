# Custom PDF Source Plugins

Place your custom PDF source plugin files here.

## Example

```python
# azure_blob_source.py

from app.plugins.base import PDFSourcePlugin
from typing import Optional

class AzureBlobSourcePlugin(PDFSourcePlugin):
    """Azure Blob Storage PDF source plugin."""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.connection_string = config.get('connection_string')
        self.container_name = config.get('container_name', 'pdfs')
        # Initialize Azure Blob client here
    
    def get_document(self, document_id: str) -> Optional[bytes]:
        # Download PDF from Azure Blob Storage
        pass
    
    def document_exists(self, document_id: str) -> bool:
        # Check if document exists in Azure Blob Storage
        pass
```

Then configure in config.json:
```json
{
  "plugins": {
    "pdf_source": {
      "type": "azureblob",
      "config": {
        "connection_string": "DefaultEndpointsProtocol=https;...",
        "container_name": "documents"
      }
    }
  }
}
```

The plugin name is derived from the class name: `AzureBlobSourcePlugin` → `azureblob`
