# Guide des Tests Automatisés

Ce document décrit la stratégie de tests automatisés mise en place pour OpenMark, incluant les tests unitaires, d'intégration, end-to-end (E2E) et les tests des scripts d'administration.

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Structure des tests](#structure-des-tests)
3. [Installation](#installation)
4. [Exécution des tests](#exécution-des-tests)
5. [Tests avec Docker](#tests-avec-docker)
6. [Couverture de code](#couverture-de-code)
7. [Tests dans VS Code](#tests-dans-vs-code)
8. [Écrire de nouveaux tests](#écrire-de-nouveaux-tests)
9. [Intégration CI/CD](#intégration-cicd)

---

## Vue d'ensemble

OpenMark utilise **pytest** comme framework de tests principal. La suite de tests couvre :

| Type de test    | Description                                                   | Marqueur                   |
| --------------- | ------------------------------------------------------------- | -------------------------- |
| **Unitaires**   | Tests isolés des composants individuels                       | `@pytest.mark.unit`        |
| **Intégration** | Tests des API et interactions entre composants                | `@pytest.mark.integration` |
| **E2E**         | Workflows complets de bout en bout                            | `@pytest.mark.e2e`         |
| **Scripts**     | Tests des scripts d'administration CLI                        | `@pytest.mark.scripts`     |
| **Docker**      | Tests nécessitant des services externes (MongoDB, PostgreSQL) | `@pytest.mark.docker`      |

---

## Structure des tests

```
tests/
├── __init__.py
├── conftest.py              # Fixtures globales partagées
├── pytest.ini               # Configuration pytest
├── requirements-test.txt    # Dépendances de test
│
├── fixtures/                # Données de test
│   ├── users.json           # Utilisateurs de test
│   ├── annotations.json     # Annotations de test
│   ├── config_test.json     # Configuration de test
│   └── pdfs/
│       └── sample.pdf       # PDF de test
│
├── unit/                    # Tests unitaires
│   ├── __init__.py
│   ├── test_jwt_handler.py  # Tests JWT
│   ├── test_config.py       # Tests configuration
│   └── plugins/
│       ├── __init__.py
│       ├── test_local_auth.py
│       ├── test_local_annotations.py
│       └── test_local_source.py
│
├── integration/             # Tests d'intégration
│   ├── __init__.py
│   ├── api/                 # Tests des endpoints API
│   │   ├── __init__.py
│   │   ├── test_auth_api.py
│   │   ├── test_document_api.py
│   │   ├── test_annotations_api.py
│   │   └── test_statistics_api.py
│   └── plugins/             # Tests plugins avec bases de données
│       ├── __init__.py
│       ├── test_mongodb_auth.py
│       ├── test_mongodb_annotations.py
│       ├── test_postgresql_auth.py
│       └── test_postgresql_annotations.py
│
├── scripts/                 # Tests des scripts d'administration
│   ├── __init__.py
│   ├── test_user_scripts.py
│   └── test_annotations_scripts.py
│
├── e2e/                     # Tests end-to-end
│   ├── __init__.py
│   └── test_workflows.py
│
└── docker/                  # Configuration Docker pour les tests
    ├── docker-compose.test.yml
    └── Dockerfile.test
```

---

## Installation

### Prérequis

- Python 3.8+
- pip
- Docker et Docker Compose (optionnel, pour les tests avec bases de données)

### Installation des dépendances de test

```bash
# Installation des dépendances de test uniquement
pip install -r tests/requirements-test.txt

# Ou installation complète (application + tests)
pip install -r requirements.txt
pip install -r tests/requirements-test.txt
```

### Dépendances de test

Les principales dépendances de test sont :

| Package      | Version | Description            |
| ------------ | ------- | ---------------------- |
| pytest       | ≥8.0.0  | Framework de test      |
| pytest-cov   | ≥4.1.0  | Couverture de code     |
| pytest-flask | ≥1.3.0  | Support Flask          |
| pytest-xdist | ≥3.5.0  | Exécution parallèle    |
| pytest-mock  | ≥3.12.0 | Mocking avancé         |
| responses    | ≥0.24.0 | Mock des requêtes HTTP |
| freezegun    | ≥1.2.0  | Mock du temps          |
| factory-boy  | ≥3.3.0  | Génération de données  |

---

## Exécution des tests

### Avec Make (recommandé)

```bash
# Tous les tests
make test

# Tests unitaires uniquement
make test-unit

# Tests d'intégration uniquement
make test-integration

# Tests E2E uniquement
make test-e2e

# Tests des scripts uniquement
make test-scripts

# Tests avec Docker (MongoDB, PostgreSQL)
make test-docker

# Couverture de code
make coverage

# Nettoyage des fichiers de test
make clean
```

### Avec le script run_tests.sh

```bash
# Tous les tests
./scripts/run_tests.sh all

# Tests unitaires
./scripts/run_tests.sh unit

# Tests d'intégration
./scripts/run_tests.sh integration

# Tests E2E
./scripts/run_tests.sh e2e

# Tests avec Docker
./scripts/run_tests.sh docker

# Options disponibles
./scripts/run_tests.sh unit --coverage   # Avec couverture
./scripts/run_tests.sh unit --verbose    # Mode verbeux
./scripts/run_tests.sh unit --fast       # Exécution parallèle
```

### Avec pytest directement

```bash
# Tous les tests
pytest tests/ -v

# Tests par marqueur
pytest tests/ -m unit -v          # Tests unitaires
pytest tests/ -m integration -v    # Tests d'intégration
pytest tests/ -m e2e -v           # Tests E2E
pytest tests/ -m scripts -v       # Tests des scripts
pytest tests/ -m docker -v        # Tests Docker

# Exclure les tests Docker (pour CI sans Docker)
pytest tests/ -m "not docker" -v

# Fichier ou dossier spécifique
pytest tests/unit/test_jwt_handler.py -v
pytest tests/integration/api/ -v

# Test spécifique
pytest tests/unit/test_jwt_handler.py::TestJWTHandler::test_create_token -v

# Avec couverture
pytest tests/ --cov=app --cov-report=html --cov-report=term

# Exécution parallèle (4 workers)
pytest tests/ -n 4

# Mode verbeux avec traceback complet
pytest tests/ -v --tb=long

# Arrêter au premier échec
pytest tests/ -x

# Derniers tests échoués uniquement
pytest tests/ --lf
```

---

## Tests avec Docker

Les tests nécessitant des bases de données externes (MongoDB, PostgreSQL) utilisent Docker Compose.

### Démarrer l'environnement de test

```bash
# Démarrer les services
docker-compose -f tests/docker/docker-compose.test.yml up -d

# Vérifier que les services sont prêts
docker-compose -f tests/docker/docker-compose.test.yml ps

# Exécuter les tests Docker
pytest tests/ -m docker -v

# Arrêter les services
docker-compose -f tests/docker/docker-compose.test.yml down -v
```

### Exécuter tous les tests dans Docker

```bash
# Build et exécution de la suite complète dans Docker
docker-compose -f tests/docker/docker-compose.test.yml run --rm test-runner

# Avec couverture
docker-compose -f tests/docker/docker-compose.test.yml run --rm test-runner \
    pytest tests/ --cov=app --cov-report=html
```

### Configuration Docker

Le fichier `tests/docker/docker-compose.test.yml` définit :

- **openmark-test** : Instance de l'application pour les tests
- **mongodb-test** : MongoDB pour les tests de plugins
- **postgres-test** : PostgreSQL pour les tests de plugins
- **test-runner** : Container dédié à l'exécution des tests

Les bases de données utilisent `tmpfs` pour des performances optimales :

```yaml
mongodb-test:
  tmpfs:
    - /data/db:size=512m

postgres-test:
  tmpfs:
    - /var/lib/postgresql/data:size=512m
```

---

## Couverture de code

### Générer un rapport de couverture

```bash
# Rapport terminal + HTML
pytest tests/ --cov=app --cov-report=term --cov-report=html

# Le rapport HTML est généré dans htmlcov/
open htmlcov/index.html
```

### Avec Make

```bash
make coverage
# Génère le rapport dans htmlcov/
```

### Objectifs de couverture

| Module               | Objectif minimum |
| -------------------- | ---------------- |
| `app/jwt_handler.py` | 90%              |
| `app/config.py`      | 85%              |
| `app/plugins/`       | 80%              |
| `app/routes/api.py`  | 85%              |
| **Global**           | **80%**          |

### Configuration de la couverture

La configuration se trouve dans `tests/pytest.ini` :

```ini
[pytest]
addopts = --cov=app --cov-report=term-missing
testpaths = tests
```

---

## Tests dans VS Code

### Configuration

Le workspace est configuré pour pytest via `.vscode/settings.json` :

```json
{
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests", "-v", "--tb=short"]
}
```

### Configurations de lancement (launch.json)

Plusieurs configurations de débogage sont disponibles :

| Configuration                | Description                    |
| ---------------------------- | ------------------------------ |
| **Tests: All Tests**         | Exécuter tous les tests        |
| **Tests: Unit Tests**        | Tests unitaires uniquement     |
| **Tests: Integration Tests** | Tests d'intégration uniquement |
| **Tests: E2E Tests**         | Tests end-to-end uniquement    |
| **Tests: Script Tests**      | Tests des scripts uniquement   |
| **Tests: Current File**      | Tests du fichier courant       |
| **Tests: With Coverage**     | Tous les tests avec couverture |

### Utilisation

1. **Explorer les tests** : Ouvrir le panneau "Testing" (icône bécher)
2. **Exécuter un test** : Cliquer sur le bouton play à côté du test
3. **Déboguer un test** : Cliquer droit → "Debug Test"
4. **Lancer une configuration** : `F5` ou menu "Run and Debug"

### Raccourcis clavier utiles

| Action                           | Raccourci       |
| -------------------------------- | --------------- |
| Exécuter tous les tests          | `Ctrl+; A`      |
| Exécuter le test sous le curseur | `Ctrl+; C`      |
| Déboguer le test sous le curseur | `Ctrl+; Ctrl+C` |
| Afficher la sortie des tests     | `Ctrl+; Ctrl+O` |

---

## Écrire de nouveaux tests

### Structure d'un test

```python
import pytest

@pytest.mark.unit  # Marqueur de catégorie
class TestMyFeature:
    """Tests pour MyFeature."""

    def test_basic_functionality(self, client):
        """Test de la fonctionnalité de base."""
        # Arrange (Préparation)
        data = {"key": "value"}

        # Act (Action)
        result = my_function(data)

        # Assert (Vérification)
        assert result is not None
        assert result["status"] == "success"

    def test_error_handling(self, client):
        """Test de la gestion des erreurs."""
        with pytest.raises(ValueError) as exc_info:
            my_function(None)

        assert "Invalid input" in str(exc_info.value)
```

### Utiliser les fixtures

Les fixtures globales sont définies dans `tests/conftest.py` :

```python
def test_with_fixtures(self, client, auth_headers, sample_annotations):
    """Exemple d'utilisation des fixtures."""
    # client : Client Flask de test
    # auth_headers : Headers avec token JWT valide
    # sample_annotations : Annotations de test

    response = client.get(
        '/api/getAnnotations',
        headers=auth_headers,
        query_string={'documentId': 'test.pdf'}
    )

    assert response.status_code == 200
```

### Fixtures disponibles

| Fixture                 | Description                       |
| ----------------------- | --------------------------------- |
| `app`                   | Instance Flask de l'application   |
| `client`                | Client de test Flask              |
| `auth_headers`          | Headers avec token utilisateur    |
| `admin_auth_headers`    | Headers avec token admin          |
| `sample_annotations`    | Liste d'annotations de test       |
| `test_users_file`       | Fichier temporaire d'utilisateurs |
| `test_annotations_file` | Fichier temporaire d'annotations  |
| `test_config`           | Configuration de test             |
| `temp_pdf`              | PDF temporaire de test            |

### Marqueurs personnalisés

```python
@pytest.mark.unit          # Test unitaire
@pytest.mark.integration   # Test d'intégration
@pytest.mark.e2e           # Test end-to-end
@pytest.mark.scripts       # Test de script
@pytest.mark.docker        # Nécessite Docker
@pytest.mark.slow          # Test lent
@pytest.mark.skip          # Ignorer le test
```

### Bonnes pratiques

1. **Un test = une assertion logique** : Gardez les tests focalisés
2. **Noms descriptifs** : `test_authenticate_with_valid_credentials_returns_token`
3. **Isolation** : Chaque test doit être indépendant
4. **AAA Pattern** : Arrange, Act, Assert
5. **Fixtures partagées** : Utilisez conftest.py pour les fixtures communes
6. **Marqueurs** : Catégorisez vos tests avec les marqueurs appropriés

---

## Intégration CI/CD

### GitHub Actions

Exemple de workflow `.github/workflows/tests.yml` :

```yaml
name: Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      mongodb:
        image: mongo:7.0
        ports:
          - 27017:27017

      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
          POSTGRES_DB: openmark_test
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements-test.txt

      - name: Run tests
        run: pytest tests/ -v --cov=app --cov-report=xml
        env:
          MONGODB_URI: mongodb://localhost:27017/openmark_test
          POSTGRESQL_URI: postgresql://test:test@localhost:5432/openmark_test

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: coverage.xml
```

### GitLab CI

Exemple de configuration `.gitlab-ci.yml` :

```yaml
stages:
  - test

test:
  stage: test
  image: python:3.11
  services:
    - mongo:7.0
    - postgres:16
  variables:
    MONGODB_URI: mongodb://mongo:27017/openmark_test
    POSTGRES_USER: test
    POSTGRES_PASSWORD: test
    POSTGRES_DB: openmark_test
    POSTGRESQL_URI: postgresql://test:test@postgres:5432/openmark_test
  before_script:
    - pip install -r requirements.txt
    - pip install -r tests/requirements-test.txt
  script:
    - pytest tests/ -v --cov=app --cov-report=xml
  coverage: '/TOTAL.*\s+(\d+%)/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

---

## Dépannage

### Problèmes courants

#### Les tests Docker échouent

```bash
# Vérifier que Docker est en cours d'exécution
docker info

# Vérifier les services
docker-compose -f tests/docker/docker-compose.test.yml ps

# Voir les logs
docker-compose -f tests/docker/docker-compose.test.yml logs
```

#### Import errors

```bash
# S'assurer que le projet est dans le PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Ou installer en mode développement
pip install -e .
```

#### Tests lents

```bash
# Exécution parallèle
pytest tests/ -n auto

# Exclure les tests lents
pytest tests/ -m "not slow"
```

#### Problèmes de fixtures

```bash
# Voir les fixtures disponibles
pytest --fixtures tests/

# Voir les fixtures utilisées par un test
pytest tests/unit/test_jwt_handler.py -v --setup-show
```

---

## Ressources

- [Documentation pytest](https://docs.pytest.org/)
- [pytest-flask](https://pytest-flask.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [Configuration OpenMark](configuration.md)
- [Architecture OpenMark](architecture.md)
- [Administration des scripts](scripts_administration.md)

---

## Changelog

| Version | Date | Description                            |
| ------- | ---- | -------------------------------------- |
| 1.0.0   | 2024 | Création initiale de la suite de tests |
