# Custom Plugins Directory

This directory is used to add custom plugins to OpenMark without modifying the core application.

## Directory Structure

```
custom_plugins/
├── auth/               # Custom authentication plugins
│   └── my_auth.py
├── pdf_source/         # Custom PDF source plugins
│   └── my_source.py
└── annotations/        # Custom annotations plugins
    └── my_annotations.py
```

## How to Add a Custom Plugin

1. Create a Python file in the appropriate subdirectory
2. Implement a class that inherits from the corresponding base class
3. Configure the plugin in `config.json`
4. Restart OpenMark

See the main README.md for detailed examples.
