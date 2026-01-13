"""Global pytest fixtures for OpenMark tests."""

import os
import sys
import json
import pytest
import tempfile
import shutil
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.config import Config


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def fixtures_dir():
    """Return the fixtures directory."""
    return PROJECT_ROOT / "tests" / "fixtures"


@pytest.fixture(scope="session")
def sample_pdf(fixtures_dir):
    """Return path to sample PDF file."""
    return fixtures_dir / "sample.pdf"


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def test_users_file(temp_dir):
    """Create a temporary users file for testing."""
    import hashlib

    users_data = {
        "users": [
            {
                "username": "admin",
                "password_hash": hashlib.sha256("adminpassword".encode()).hexdigest(),
                "role": "admin",
                "email": "admin@test.local",
            },
            {
                "username": "testuser",
                "password_hash": hashlib.sha256("testpassword".encode()).hexdigest(),
                "role": "user",
                "email": "testuser@test.local",
            },
        ]
    }

    users_file = temp_dir / "users.json"
    users_file.write_text(json.dumps(users_data, indent=2))
    return str(users_file)


@pytest.fixture
def test_annotations_file(temp_dir):
    """Create a temporary annotations file for testing."""
    annotations_file = temp_dir / "annotations.json"
    annotations_file.write_text("{}")
    return str(annotations_file)


@pytest.fixture
def test_config(temp_dir, test_users_file, test_annotations_file, fixtures_dir):
    """Create a test configuration file."""
    config_data = {
        "server": {
            "host": "0.0.0.0",
            "port": 8080,
            "debug": False,
            "secret_key": "test-secret-key-for-testing-only",
        },
        "cache": {"directory": str(temp_dir / "cache"), "duration_seconds": 3600},
        "plugins": {
            "authentication": {
                "type": "local",
                "config": {"users_file": test_users_file, "token_expiry_hours": 24},
            },
            "pdf_source": {
                "type": "local",
                "config": {"base_path": str(fixtures_dir / "pdfs")},
            },
            "annotations": {
                "type": "local",
                "config": {"storage_file": test_annotations_file},
            },
        },
    }

    config_file = temp_dir / "config_test.json"
    config_file.write_text(json.dumps(config_data, indent=2))

    # Create cache directory
    (temp_dir / "cache").mkdir(exist_ok=True)

    return str(config_file)


@pytest.fixture
def app(test_config):
    """Create application for testing."""
    application = create_app(test_config)
    application.config["TESTING"] = True
    application.config["WTF_CSRF_ENABLED"] = False
    return application


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def app_context(app):
    """Create application context."""
    with app.app_context() as ctx:
        yield ctx


@pytest.fixture
def auth_headers(client):
    """Get authentication headers with valid token."""
    response = client.post(
        "/api/authenticate", json={"username": "testuser", "password": "testpassword"}
    )
    assert response.status_code == 200
    token = response.json["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(client):
    """Get authentication headers with admin token."""
    response = client.post(
        "/api/authenticate", json={"username": "admin", "password": "adminpassword"}
    )
    assert response.status_code == 200
    token = response.json["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_annotations():
    """Return sample annotations data."""
    return {
        "notes": [
            {
                "id": "note-test-1",
                "page": 1,
                "x": 100,
                "y": 200,
                "width": 150,
                "height": 100,
                "content": "Test note content",
                "color": "#ffff00",
                "created_at": "2026-01-13T10:00:00Z",
                "updated_at": "2026-01-13T10:00:00Z",
            },
            {
                "id": "note-test-2",
                "page": 2,
                "x": 50,
                "y": 300,
                "width": 200,
                "height": 150,
                "content": "Another test note",
                "color": "#ff9900",
                "created_at": "2026-01-13T11:00:00Z",
                "updated_at": "2026-01-13T11:00:00Z",
            },
        ],
        "highlights": [
            {
                "id": "hl-test-1",
                "page": 1,
                "rects": [{"x": 50, "y": 100, "width": 300, "height": 20}],
                "color": "#00ff00",
                "created_at": "2026-01-13T10:30:00Z",
            }
        ],
    }


# Markers for test categories
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests (no external dependencies)")
    config.addinivalue_line(
        "markers", "integration: Integration tests (requires database)"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests (requires full environment)"
    )
    config.addinivalue_line("markers", "slow: Slow tests")
    config.addinivalue_line("markers", "docker: Tests requiring Docker")
