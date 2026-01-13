# Annotations Import/Export

This document describes how to import and export annotations (notes and highlights) in OpenMark using the command-line scripts.

## Overview

OpenMark provides two scripts for managing annotations:

| Script | Description |
|--------|-------------|
| `annotations_import.py` | Import annotations from a JSON file |
| `annotations_export.py` | Export annotations to a JSON file |

Both scripts automatically use the configured annotations backend (local JSON, MongoDB, or PostgreSQL).

## JSON Format

### Standard Format (Recommended)

The recommended format for import/export operations:

```json
{
  "version": "1.0",
  "exported_at": "2026-01-13T10:00:00Z",
  "source": "openmark-local",
  "data": [
    {
      "user_id": "admin",
      "document_id": "report-2026",
      "annotations": {
        "notes": [
          {
            "id": "note_1234567890",
            "page": 1,
            "x": 100.5,
            "y": 200.0,
            "width": 200,
            "height": 150,
            "content": "This is a note",
            "color": "#ffff00",
            "created_at": "2026-01-13T10:00:00Z",
            "updated_at": "2026-01-13T10:00:00Z"
          }
        ],
        "highlights": [
          {
            "id": "highlight_1234567890",
            "page": 1,
            "rects": [
              {"x": 50, "y": 100, "width": 300, "height": 20}
            ],
            "color": "#00ff00",
            "created_at": "2026-01-13T10:00:00Z"
          }
        ]
      }
    }
  ]
}
```

### Simple Format

For importing annotations to a single user/document:

```json
{
  "annotations": {
    "notes": [...],
    "highlights": [...]
  }
}
```

### Minimal Format

The simplest format (requires `--user` and `--document` options):

```json
{
  "notes": [...],
  "highlights": [...]
}
```

## Field Reference

### Notes

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | string | No | auto-generated | Unique identifier |
| `page` | integer | **Yes** | - | Page number (1-indexed) |
| `x` | number | **Yes** | - | X position on page |
| `y` | number | **Yes** | - | Y position on page |
| `content` | string | **Yes** | - | Note text content |
| `width` | number | No | 200 | Note width in pixels |
| `height` | number | No | 150 | Note height in pixels |
| `color` | string | No | "#ffff00" | Background color (hex) |
| `created_at` | string | No | current time | ISO 8601 timestamp |
| `updated_at` | string | No | current time | ISO 8601 timestamp |

### Highlights

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | string | No | auto-generated | Unique identifier |
| `page` | integer | **Yes** | - | Page number (1-indexed) |
| `rects` | array | **Yes** | - | Array of rectangles |
| `color` | string | No | "#ffff00" | Highlight color (hex) |
| `created_at` | string | No | current time | ISO 8601 timestamp |

### Rectangle Object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `x` | number | **Yes** | X position |
| `y` | number | **Yes** | Y position |
| `width` | number | **Yes** | Rectangle width |
| `height` | number | **Yes** | Rectangle height |

---

## Export Script

### Usage

```bash
python3 scripts/annotations_export.py -u <user> -d <document> [options]
```

### Options

| Option | Description |
|--------|-------------|
| `-u, --user` | User ID (required) |
| `-d, --document` | Document ID to export |
| `--all` | Export all documents for the user |
| `-o, --output` | Output file (stdout if not specified) |
| `--compact` | Compact JSON format (single line) |
| `-v, --verbose` | Show detailed output |
| `-c, --config` | Path to config file |

### Examples

**Export a specific document:**
```bash
python3 scripts/annotations_export.py -u admin -d report-2026 -o export.json
```

**Export all user documents:**
```bash
python3 scripts/annotations_export.py -u admin --all -o user_backup.json
```

**Export to stdout (for piping):**
```bash
python3 scripts/annotations_export.py -u admin -d doc1 | jq '.data[0].annotations'
```

**Compact format:**
```bash
python3 scripts/annotations_export.py -u admin -d doc1 --compact -o export.json
```

---

## Import Script

### Usage

```bash
python3 scripts/annotations_import.py -f <file> [options]
```

### Options

| Option | Description |
|--------|-------------|
| `-f, --file` | JSON file to import (required) |
| `-u, --user` | Target user (required for simple/minimal format) |
| `-d, --document` | Target document (required for simple/minimal format) |
| `--mode` | Import mode: `merge` (default) or `replace` |
| `--dry-run` | Validate without importing |
| `-v, --verbose` | Show detailed output |
| `-c, --config` | Path to config file |

### Import Modes

| Mode | Description |
|------|-------------|
| `merge` | Add new annotations to existing ones (default) |
| `replace` | Replace all existing annotations |

### Examples

**Import multi-user file:**
```bash
python3 scripts/annotations_import.py -f export.json
```

**Import to specific user/document:**
```bash
python3 scripts/annotations_import.py -f notes.json -u admin -d report-2026
```

**Replace existing annotations:**
```bash
python3 scripts/annotations_import.py -f export.json --mode replace
```

**Validate without importing:**
```bash
python3 scripts/annotations_import.py -f export.json --dry-run -v
```

**Use custom config:**
```bash
python3 scripts/annotations_import.py -f export.json -c config-mongodb.json
```

---

## Use Cases

### Backup and Restore

```bash
# Backup
python3 scripts/annotations_export.py -u admin --all -o backup_$(date +%Y%m%d).json

# Restore
python3 scripts/annotations_import.py -f backup_20260113.json
```

### Migrate Between Backends

```bash
# Export from local
python3 scripts/annotations_export.py -u admin --all -o migration.json -c config.json

# Import to MongoDB
python3 scripts/annotations_import.py -f migration.json -c config-mongodb.json
```

### Copy Annotations Between Users

```bash
# Export from source user
python3 scripts/annotations_export.py -u user1 -d document1 -o temp.json

# Import to target user (edit temp.json to change user_id, or use -u)
python3 scripts/annotations_import.py -f temp.json -u user2 -d document1
```

### Batch Import from External System

Create a file `external_annotations.json`:

```json
{
  "version": "1.0",
  "data": [
    {
      "user_id": "john",
      "document_id": "contract-2026",
      "annotations": {
        "notes": [
          {"page": 1, "x": 100, "y": 200, "content": "Review this section"}
        ],
        "highlights": [
          {"page": 1, "rects": [{"x": 50, "y": 300, "width": 400, "height": 15}], "color": "#ff0000"}
        ]
      }
    },
    {
      "user_id": "jane",
      "document_id": "contract-2026",
      "annotations": {
        "notes": [
          {"page": 2, "x": 150, "y": 100, "content": "Approved"}
        ],
        "highlights": []
      }
    }
  ]
}
```

Then import:

```bash
python3 scripts/annotations_import.py -f external_annotations.json -v
```

---

## Validation Rules

The import script validates:

1. **Required fields** are present
2. **Page numbers** are positive integers
3. **Coordinates** (x, y, width, height) are valid numbers
4. **Rects array** is not empty for highlights
5. **Color format** is valid hex color (optional)

Use `--dry-run` to validate without modifying data:

```bash
python3 scripts/annotations_import.py -f data.json --dry-run -v
```

---

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Fichier non trouvé" | Input file doesn't exist | Check file path |
| "Format non reconnu" | Invalid JSON structure | Use one of the supported formats |
| "champ obligatoire manquant" | Missing required field | Add the missing field |
| "Backend non supporté" | Unknown annotations backend | Check config.json |

### Verbose Mode

Use `-v` or `--verbose` to get detailed error messages:

```bash
python3 scripts/annotations_import.py -f data.json --dry-run -v
```

---

## Integration with API

In addition to CLI scripts, OpenMark provides an API endpoint for importing annotations programmatically. See [API Usage](api_usage.md) for details on:

- `POST /api/saveAnnotations` - Save annotations for a document
- `GET /api/getAnnotations` - Retrieve annotations for a document

The CLI scripts are ideal for:
- Batch operations
- Backup/restore workflows
- Migration between backends
- CI/CD pipelines

---

## See Also

- [Scripts Administration](scripts_administration.md) - Complete CLI scripts documentation
- [Configuration](configuration.md) - General OpenMark configuration
- [Architecture](architecture.md) - Plugin system architecture
