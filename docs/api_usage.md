# OpenMark API Reference

This document provides a complete reference for the OpenMark REST API.

## Authentication

All API endpoints (except `/api/authenticate` and `/api/quickView`) require authentication via a Bearer token in the `Authorization` header:

```
Authorization: Bearer <token>
```

## Endpoints

### Authentication

#### POST `/api/authenticate`

Authenticate a user and receive an access token.

**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": "2026-01-07T12:00:00Z"
}
```

**Response (401 Unauthorized):**
```json
{
  "success": false,
  "error": "Invalid credentials"
}
```

---

#### POST `/api/quickView`

**One-step authentication and document request.** This API combines authentication, document request, and URL generation into a single call. Ideal for external server integration where you need to generate a viewer URL to send to client applications.

**Request:**
```json
{
  "username": "string",
  "password": "string",
  "documentId": "string",
  "hideAnnotationsTools": false,
  "hideAnnotations": false,
  "hideLogo": false
}
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `username` | string | Yes | - | User's username |
| `password` | string | Yes | - | User's password |
| `documentId` | string | Yes | - | ID of the PDF document to view |
| `hideAnnotationsTools` | boolean | No | `false` | Hide annotation tools in the viewer |
| `hideAnnotations` | boolean | No | `false` | Hide existing annotations |
| `hideLogo` | boolean | No | `false` | Hide the OpenMark logo |

**Response (200 OK):**
```json
{
  "success": true,
  "viewUrl": "/api/viewDocument?dat=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "dat": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "validFor": "2 hours",
  "expires_at": "2026-01-07T15:00:00Z"
}
```

> **Note:** The response includes a **Document Access Token (DAT)** - a self-contained JWT that includes the user, document ID, view options, and expiration. This token allows secure document access without requiring the original auth token.
>
> **Benefits of DAT:**
> - ✅ Page refresh (F5) works without losing access
> - ✅ Valid for 2 hours (longer than cache duration)
> - ✅ Single token contains all necessary permissions
> - ✅ Can be stored and reused within validity period

**Response (401 Unauthorized):**
```json
{
  "success": false,
  "error": "Invalid credentials"
}
```

**Response (404 Not Found):**
```json
{
  "success": false,
  "error": "Document not found"
}
```

---

#### POST `/api/logout`

Invalidate the current authentication token.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "success": true
}
```

---

### Document Management

#### POST `/api/requestDocument`

Request a PDF document to be prepared for viewing.

**Headers:**
```
Authorization: Bearer <token>
```

**Request:**
```json
{
  "documentId": "string",
  "hideAnnotationsTools": false,
  "hideAnnotations": false,
  "hideLogo": false
}
```

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `documentId` | string | Yes | - | ID of the PDF document to view |
| `hideAnnotationsTools` | boolean | No | `false` | Hide annotation tools in the viewer |
| `hideAnnotations` | boolean | No | `false` | Hide existing annotations |
| `hideLogo` | boolean | No | `false` | Hide the OpenMark logo |

**Response (200 OK):**
```json
{
  "success": true,
  "dat": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "viewUrl": "/api/viewDocument?dat=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "validFor": "2 hours",
  "expires_at": "2026-01-06T15:00:00Z"
}
```

**Response (404 Not Found):**
```json
{
  "success": false,
  "error": "Document not found"
}
```

---

#### GET `/api/viewDocument`

View a PDF document with annotation capabilities.

**Authentication:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `dat` | string | Yes | Document Access Token (JWT containing all permissions) |

> **Note:** View options (hideAnnotationsTools, hideAnnotations, hideLogo) are embedded in the DAT token. No need to add them as query parameters.

**View Modes (configured when requesting document):**

- **Default mode**: Full annotation capabilities with toolbar and sidebar
- **Read-only mode** (`hideAnnotationsTools=true`): View annotations but cannot create/edit/delete them
- **Clean view mode** (`hideAnnotations=true`): View PDF without any annotations visible (also hides tools)
- **No branding mode** (`hideLogo=true`): Hide the OpenMark logo for embedded or white-label usage

**Example URL:**

```
/api/viewDocument?dat=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response:**
Returns an HTML page with the PDF viewer interface.

---

### Annotations

#### POST `/api/saveAnnotations`

Save annotations (notes and highlights) for a document.

**Headers:**
```
Authorization: Bearer <token>
```

**Request:**
```json
{
  "documentId": "string",
  "annotations": {
    "notes": [
      {
        "id": "note_001",
        "page": 1,
        "x": 100,
        "y": 200,
        "width": 200,
        "height": 150,
        "content": "This is a note",
        "color": "#ffeb3b",
        "created_at": "2026-01-06T12:00:00Z",
        "updated_at": "2026-01-06T12:00:00Z"
      }
    ],
    "highlights": [
      {
        "id": "highlight_001",
        "page": 1,
        "rects": [
          {"x": 50, "y": 100, "width": 200, "height": 20}
        ],
        "color": "#ffff00",
        "created_at": "2026-01-06T12:00:00Z"
      }
    ]
  }
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Annotations saved successfully"
}
```

---

#### GET `/api/getAnnotations`

Retrieve annotations for a document.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `documentId` | string | Yes | Document identifier |

**Response (200 OK):**
```json
{
  "success": true,
  "annotations": {
    "notes": [],
    "highlights": []
  }
}
```

---

### Statistics & History

#### GET `/api/statistics`

Get usage statistics for the authenticated user.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200 OK):**
```json
{
  "success": true,
  "statistics": {
    "documents_viewed": 42,
    "notes_created": 156,
    "highlights_created": 89,
    "last_activity": "2026-01-06T11:30:00Z"
  }
}
```

---

#### GET `/api/history`

Get document consultation history.

**Headers:**
```
Authorization: Bearer <token>
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | integer | No | Maximum number of entries (default: 50) |
| `offset` | integer | No | Pagination offset (default: 0) |

**Response (200 OK):**
```json
{
  "success": true,
  "history": [
    {
      "document_id": "doc123",
      "document_name": "Report Q4 2025",
      "timestamp": "2026-01-06T10:30:00Z",
      "ip_address": "192.168.1.100",
      "duration_seconds": 1800
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0
}
```

---

## Usage Examples

### Python Client Example

```python
import requests

BASE_URL = "http://localhost:5000"

# Authenticate
response = requests.post(f"{BASE_URL}/api/authenticate", json={
    "username": "user1",
    "password": "password123"
})
token = response.json()["token"]

headers = {"Authorization": f"Bearer {token}"}

# Request a document
response = requests.post(f"{BASE_URL}/api/requestDocument", 
    headers=headers,
    json={"documentId": "report-2025-q4"}
)
dat = response.json()["dat"]
view_url = response.json()["viewUrl"]

# View document (open in browser)
full_view_url = f"{BASE_URL}{view_url}"
print(f"Open in browser: {full_view_url}")

# Get annotations
response = requests.get(f"{BASE_URL}/api/getAnnotations",
    headers=headers,
    params={"documentId": "report-2025-q4"}
)
annotations = response.json()["annotations"]

# Save annotations
response = requests.post(f"{BASE_URL}/api/saveAnnotations",
    headers=headers,
    json={
        "documentId": "report-2025-q4",
        "annotations": {
            "notes": [{
                "id": "note_001",
                "page": 1,
                "x": 100,
                "y": 200,
                "width": 200,
                "height": 150,
                "content": "Important section",
                "color": "#ffeb3b"
            }],
            "highlights": []
        }
    }
)
```

### External Server Integration

```python
import requests

OPENMARK_SERVER = 'https://openmark.example.com'

# Your external server calls OpenMark API
response = requests.post(f'{OPENMARK_SERVER}/api/quickView', json={
    'username': 'viewer_user',
    'password': 'secure_password',
    'documentId': 'invoice_2026_001',
    'hideAnnotationsTools': True,
    'hideLogo': True
})

data = response.json()
if data['success']:
    # Build full URL with the Document Access Token (DAT)
    viewer_url = OPENMARK_SERVER + data['viewUrl']
    # The DAT is valid for 2 hours - can safely store and reuse
    dat = data['dat']
    # Send this URL to your client application
```

### JavaScript (Client-side)

```javascript
// Embed in iframe - DAT-based URL survives page refreshes
const OPENMARK_SERVER = 'https://openmark.example.com';
const iframe = document.createElement('iframe');
iframe.src = OPENMARK_SERVER + viewUrl;  // Contains ?dat=<token>
iframe.width = '100%';
iframe.height = '800px';
document.body.appendChild(iframe);
```

### cURL Examples

```bash
# Authenticate
curl -X POST http://localhost:5000/api/authenticate \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "password": "password123"}'

# Quick view (one-step authentication + document)
curl -X POST http://localhost:5000/api/quickView \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "password": "password123", "documentId": "report-2025-q4"}'

# Request document
curl -X POST http://localhost:5000/api/requestDocument \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"documentId": "report-2025-q4"}'

# Get annotations
curl -X GET "http://localhost:5000/api/getAnnotations?documentId=report-2025-q4" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get statistics
curl -X GET http://localhost:5000/api/statistics \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get history
curl -X GET "http://localhost:5000/api/history?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Logout
curl -X POST http://localhost:5000/api/logout \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Error Handling

All API endpoints return errors in a consistent format:

```json
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid or expired token |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error |

## Rate Limiting

The API does not currently implement rate limiting. For production deployments, consider implementing rate limiting at the reverse proxy level (nginx, HAProxy, etc.).
