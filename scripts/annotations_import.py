#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'importation des annotations (notes et surlignages) depuis un fichier JSON.

Ce script permet d'importer des annotations dans OpenMark depuis un fichier JSON externe.
Il utilise automatiquement le backend d'annotations configuré dans l'application
(local JSON, MongoDB, ou PostgreSQL).

Usage:
    # Importer toutes les annotations d'un fichier
    python3 scripts/annotations_import.py -f export.json

    # Importer pour un utilisateur/document spécifique
    python3 scripts/annotations_import.py -f notes.json -u admin -d rapport2026

    # Mode remplacement (écrase les annotations existantes)
    python3 scripts/annotations_import.py -f export.json --mode replace

    # Validation sans import (dry-run)
    python3 scripts/annotations_import.py -f export.json --dry-run

    # Afficher les détails
    python3 scripts/annotations_import.py -f export.json --verbose
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class AnnotationsManager:
    """Gestionnaire d'annotations utilisant la configuration de l'application."""

    def __init__(self, config_path: str = None, verbose: bool = False):
        """Initialise le gestionnaire avec la configuration de l'application."""
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.verbose = verbose

        if config_path is None:
            config_path = os.path.join(self.project_root, "config.json")
        elif not os.path.isabs(config_path):
            config_path = os.path.join(self.project_root, config_path)

        self.config = self._load_config(config_path)
        self.ann_type = (
            self.config.get("plugins", {}).get("annotations", {}).get("type", "local")
        )
        self.ann_config = (
            self.config.get("plugins", {}).get("annotations", {}).get("config", {})
        )

        self._plugin = self._init_plugin()

    def _load_config(self, config_path: str) -> dict:
        """Charge la configuration depuis le fichier JSON."""
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        raise FileNotFoundError(f"Fichier de configuration non trouvé: {config_path}")

    def _init_plugin(self):
        """Initialise le plugin d'annotations approprié."""
        if self.ann_type == "local":
            from app.plugins.annotations.local_annotations import LocalAnnotationsPlugin

            return LocalAnnotationsPlugin(self.ann_config)
        elif self.ann_type == "mongodb":
            from app.plugins.annotations.mongodb_annotations import (
                MongoDBAnnotationsPlugin,
            )

            return MongoDBAnnotationsPlugin(self.ann_config)
        elif self.ann_type == "postgresql":
            from app.plugins.annotations.postgresql_annotations import (
                PostgreSQLAnnotationsPlugin,
            )

            return PostgreSQLAnnotationsPlugin(self.ann_config)
        else:
            raise ValueError(f"Type d'annotations non supporté: {self.ann_type}")

    def get_annotations(self, user_id: str, document_id: str) -> dict:
        """Récupère les annotations existantes."""
        return self._plugin.get_annotations(user_id, document_id)

    def save_annotations(
        self, user_id: str, document_id: str, annotations: dict
    ) -> bool:
        """Sauvegarde les annotations."""
        return self._plugin.save_annotations(user_id, document_id, annotations)

    def get_backend_type(self) -> str:
        """Retourne le type de backend utilisé."""
        return self.ann_type


def generate_id(prefix: str) -> str:
    """Génère un ID unique pour une annotation."""
    timestamp = int(datetime.utcnow().timestamp() * 1000)
    return f"{prefix}_{timestamp}"


def validate_note(note: dict, index: int) -> Tuple[bool, List[str]]:
    """Valide une note et retourne les erreurs éventuelles."""
    errors = []
    required_fields = ["page", "x", "y", "content"]

    for field in required_fields:
        if field not in note:
            errors.append(f"Note #{index}: champ obligatoire manquant '{field}'")

    if "page" in note and not isinstance(note["page"], int):
        errors.append(f"Note #{index}: 'page' doit être un entier")

    if "page" in note and note["page"] < 1:
        errors.append(f"Note #{index}: 'page' doit être >= 1")

    return len(errors) == 0, errors


def validate_highlight(highlight: dict, index: int) -> Tuple[bool, List[str]]:
    """Valide un surlignage et retourne les erreurs éventuelles."""
    errors = []
    required_fields = ["page", "rects"]

    for field in required_fields:
        if field not in highlight:
            errors.append(f"Highlight #{index}: champ obligatoire manquant '{field}'")

    if "page" in highlight and not isinstance(highlight["page"], int):
        errors.append(f"Highlight #{index}: 'page' doit être un entier")

    if "rects" in highlight:
        if not isinstance(highlight["rects"], list):
            errors.append(f"Highlight #{index}: 'rects' doit être une liste")
        elif len(highlight["rects"]) == 0:
            errors.append(f"Highlight #{index}: 'rects' ne peut pas être vide")
        else:
            for i, rect in enumerate(highlight["rects"]):
                for field in ["x", "y", "width", "height"]:
                    if field not in rect:
                        errors.append(
                            f"Highlight #{index}, rect #{i}: champ manquant '{field}'"
                        )

    return len(errors) == 0, errors


def normalize_note(note: dict) -> dict:
    """Normalise une note en ajoutant les champs manquants."""
    now = datetime.utcnow().isoformat() + "Z"

    return {
        "id": note.get("id") or generate_id("note"),
        "page": note["page"],
        "x": float(note["x"]),
        "y": float(note["y"]),
        "width": float(note.get("width", 200)),
        "height": float(note.get("height", 150)),
        "content": note["content"],
        "color": note.get("color", "#ffff00"),
        "created_at": note.get("created_at", now),
        "updated_at": note.get("updated_at", now),
    }


def normalize_highlight(highlight: dict) -> dict:
    """Normalise un surlignage en ajoutant les champs manquants."""
    now = datetime.utcnow().isoformat() + "Z"

    return {
        "id": highlight.get("id") or generate_id("highlight"),
        "page": highlight["page"],
        "rects": [
            {
                "x": float(r["x"]),
                "y": float(r["y"]),
                "width": float(r["width"]),
                "height": float(r["height"]),
            }
            for r in highlight["rects"]
        ],
        "color": highlight.get("color", "#ffff00"),
        "created_at": highlight.get("created_at", now),
    }


def load_import_file(file_path: str) -> dict:
    """Charge et parse le fichier d'import JSON."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Vérifier si le fichier est vide
        if not content.strip():
            raise ValueError("Le fichier est vide")

        # Vérifier si le fichier utilise des guillemets simples (erreur Python courante)
        if content.strip().startswith("{'") or "': '" in content:
            raise ValueError(
                "Le fichier semble utiliser des guillemets simples (format Python dict). "
                "JSON requiert des guillemets doubles. "
                "Remplacez les ' par des \" dans le fichier."
            )

        data = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Erreur de syntaxe JSON à la ligne {e.lineno}, colonne {e.colno}: {e.msg}"
        )

    # Détecter le format du fichier
    if "data" in data and isinstance(data["data"], list):
        # Format multi-utilisateur/document
        return {"format": "multi", "data": data}
    elif "annotations" in data:
        # Format simple avec annotations directes
        return {"format": "simple", "data": data}
    elif "notes" in data or "highlights" in data:
        # Format minimal (juste les annotations)
        return {"format": "minimal", "data": {"annotations": data}}
    else:
        raise ValueError(
            "Format de fichier non reconnu. Le fichier doit contenir 'data', 'annotations', 'notes' ou 'highlights'."
        )


def validate_import_data(import_data: dict) -> Tuple[bool, List[str]]:
    """Valide les données d'import et retourne les erreurs."""
    errors = []
    format_type = import_data["format"]
    data = import_data["data"]

    if format_type == "multi":
        for i, entry in enumerate(data.get("data", [])):
            if "user_id" not in entry:
                errors.append(f"Entrée #{i}: 'user_id' manquant")
            if "document_id" not in entry:
                errors.append(f"Entrée #{i}: 'document_id' manquant")
            if "annotations" not in entry:
                errors.append(f"Entrée #{i}: 'annotations' manquant")
            else:
                ann = entry["annotations"]
                for j, note in enumerate(ann.get("notes", [])):
                    valid, note_errors = validate_note(note, j)
                    errors.extend([f"Entrée #{i}, {e}" for e in note_errors])
                for j, hl in enumerate(ann.get("highlights", [])):
                    valid, hl_errors = validate_highlight(hl, j)
                    errors.extend([f"Entrée #{i}, {e}" for e in hl_errors])
    else:
        ann = data.get("annotations", {})
        for j, note in enumerate(ann.get("notes", [])):
            valid, note_errors = validate_note(note, j)
            errors.extend(note_errors)
        for j, hl in enumerate(ann.get("highlights", [])):
            valid, hl_errors = validate_highlight(hl, j)
            errors.extend(hl_errors)

    return len(errors) == 0, errors


def import_annotations(
    manager: AnnotationsManager,
    import_data: dict,
    target_user: str = None,
    target_document: str = None,
    mode: str = "merge",
    dry_run: bool = False,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Importe les annotations.

    Args:
        manager: Gestionnaire d'annotations
        import_data: Données d'import parsées
        target_user: Utilisateur cible (override)
        target_document: Document cible (override)
        mode: 'merge' ou 'replace'
        dry_run: Si True, simule l'import sans écrire
        verbose: Affiche les détails

    Returns:
        Résultat de l'import avec statistiques
    """
    format_type = import_data["format"]
    data = import_data["data"]

    results = {
        "success": True,
        "imports": [],
        "total_notes": 0,
        "total_highlights": 0,
        "errors": [],
    }

    # Préparer les entrées à importer
    entries = []

    if format_type == "multi":
        for entry in data.get("data", []):
            user_id = target_user or entry["user_id"]
            document_id = target_document or entry["document_id"]
            annotations = entry["annotations"]
            entries.append((user_id, document_id, annotations))
    else:
        if not target_user or not target_document:
            results["success"] = False
            results["errors"].append(
                "Format simple: --user et --document sont obligatoires"
            )
            return results
        entries.append((target_user, target_document, data.get("annotations", {})))

    # Traiter chaque entrée
    for user_id, document_id, annotations in entries:
        notes_to_import = [normalize_note(n) for n in annotations.get("notes", [])]
        highlights_to_import = [
            normalize_highlight(h) for h in annotations.get("highlights", [])
        ]

        if verbose:
            print(f"  📄 {user_id}:{document_id}")
            print(
                f"     Notes: {len(notes_to_import)}, Highlights: {len(highlights_to_import)}"
            )

        if mode == "merge":
            # Récupérer les annotations existantes
            existing = manager.get_annotations(user_id, document_id)
            existing_notes = existing.get("notes", [])
            existing_highlights = existing.get("highlights", [])

            # Fusionner (ajouter les nouvelles)
            final_notes = existing_notes + notes_to_import
            final_highlights = existing_highlights + highlights_to_import
        else:
            # Mode replace: remplacer tout
            final_notes = notes_to_import
            final_highlights = highlights_to_import

        final_annotations = {"notes": final_notes, "highlights": final_highlights}

        if not dry_run:
            success = manager.save_annotations(user_id, document_id, final_annotations)
            if not success:
                results["errors"].append(f"Échec sauvegarde {user_id}:{document_id}")
                results["success"] = False
        else:
            success = True

        results["imports"].append(
            {
                "user_id": user_id,
                "document_id": document_id,
                "notes_imported": len(notes_to_import),
                "highlights_imported": len(highlights_to_import),
                "total_notes": len(final_notes),
                "total_highlights": len(final_highlights),
                "success": success,
            }
        )

        results["total_notes"] += len(notes_to_import)
        results["total_highlights"] += len(highlights_to_import)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Import des annotations OpenMark depuis un fichier JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Importer un fichier multi-utilisateur
  python3 scripts/annotations_import.py -f export.json

  # Importer pour un utilisateur/document spécifique
  python3 scripts/annotations_import.py -f notes.json -u admin -d rapport2026

  # Mode remplacement
  python3 scripts/annotations_import.py -f export.json --mode replace

  # Validation sans import
  python3 scripts/annotations_import.py -f export.json --dry-run

Formats de fichier supportés:
  1. Format multi (recommandé pour migrations):
     {
       "version": "1.0",
       "data": [
         {"user_id": "user1", "document_id": "doc1", "annotations": {...}}
       ]
     }

  2. Format simple:
     {
       "annotations": {"notes": [...], "highlights": [...]}
     }

  3. Format minimal:
     {"notes": [...], "highlights": [...]}
""",
    )

    parser.add_argument("-f", "--file", required=True, help="Fichier JSON à importer")
    parser.add_argument(
        "-u", "--user", help="Utilisateur cible (obligatoire pour format simple)"
    )
    parser.add_argument(
        "-d", "--document", help="Document cible (obligatoire pour format simple)"
    )
    parser.add_argument(
        "--mode",
        choices=["merge", "replace"],
        default="merge",
        help="Mode d'import: merge (défaut) ou replace",
    )
    parser.add_argument("--dry-run", action="store_true", help="Valider sans importer")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Afficher les détails"
    )
    parser.add_argument(
        "-c", "--config", help="Chemin vers le fichier de configuration"
    )

    args = parser.parse_args()

    # Vérifier que le fichier existe
    if not os.path.exists(args.file):
        print(f"❌ Fichier non trouvé: {args.file}")
        sys.exit(1)

    try:
        # Initialiser le gestionnaire
        manager = AnnotationsManager(config_path=args.config, verbose=args.verbose)
        print(f"🔌 Backend: {manager.get_backend_type()}")

        # Charger le fichier
        print(f"📂 Chargement de {args.file}...")
        import_data = load_import_file(args.file)
        print(f"   Format détecté: {import_data['format']}")

        # Valider les données
        print("🔍 Validation des données...")
        valid, errors = validate_import_data(import_data)

        if not valid:
            print("❌ Erreurs de validation:")
            for error in errors[:10]:  # Limiter l'affichage
                print(f"   • {error}")
            if len(errors) > 10:
                print(f"   ... et {len(errors) - 10} autres erreurs")
            sys.exit(1)

        print("✅ Validation réussie")

        # Importer
        if args.dry_run:
            print("\n🔬 Mode dry-run (simulation)...")
        else:
            print(f"\n📥 Import en mode '{args.mode}'...")

        results = import_annotations(
            manager=manager,
            import_data=import_data,
            target_user=args.user,
            target_document=args.document,
            mode=args.mode,
            dry_run=args.dry_run,
            verbose=args.verbose,
        )

        # Afficher les résultats
        if results["success"]:
            action = "simulé" if args.dry_run else "importé"
            print(f"\n✅ Import {action} avec succès!")
            print(f"   📝 Notes: {results['total_notes']}")
            print(f"   🖍️  Highlights: {results['total_highlights']}")
            print(f"   📄 Documents: {len(results['imports'])}")

            if args.verbose:
                print("\n📋 Détails:")
                for imp in results["imports"]:
                    status = "✅" if imp["success"] else "❌"
                    print(f"   {status} {imp['user_id']}:{imp['document_id']}")
                    print(
                        f"      Notes: +{imp['notes_imported']} (total: {imp['total_notes']})"
                    )
                    print(
                        f"      Highlights: +{imp['highlights_imported']} (total: {imp['total_highlights']})"
                    )
        else:
            print("\n❌ Import échoué:")
            for error in results["errors"]:
                print(f"   • {error}")
            sys.exit(1)

    except FileNotFoundError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Erreur de parsing JSON: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
