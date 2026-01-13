#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'exportation des annotations (notes et surlignages) vers un fichier JSON.

Ce script permet d'exporter des annotations depuis OpenMark vers un fichier JSON.
Il utilise automatiquement le backend d'annotations configuré dans l'application
(local JSON, MongoDB, ou PostgreSQL).

Usage:
    # Exporter les annotations d'un utilisateur/document
    python3 scripts/annotations_export.py -u admin -d rapport2026 -o export.json

    # Exporter toutes les annotations d'un utilisateur
    python3 scripts/annotations_export.py -u admin --all -o user_export.json

    # Exporter vers stdout (pour piping)
    python3 scripts/annotations_export.py -u admin -d rapport2026

    # Format compact (une ligne)
    python3 scripts/annotations_export.py -u admin -d doc1 --compact
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class AnnotationsManager:
    """Gestionnaire d'annotations utilisant la configuration de l'application."""
    
    def __init__(self, config_path: str = None, verbose: bool = False):
        """Initialise le gestionnaire avec la configuration de l'application."""
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.verbose = verbose
        
        if config_path is None:
            config_path = os.path.join(self.project_root, 'config.json')
        elif not os.path.isabs(config_path):
            config_path = os.path.join(self.project_root, config_path)
        
        self.config = self._load_config(config_path)
        self.ann_type = self.config.get('plugins', {}).get('annotations', {}).get('type', 'local')
        self.ann_config = self.config.get('plugins', {}).get('annotations', {}).get('config', {})
        
        self._plugin = self._init_plugin()
    
    def _load_config(self, config_path: str) -> dict:
        """Charge la configuration depuis le fichier JSON."""
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        raise FileNotFoundError(f"Fichier de configuration non trouvé: {config_path}")
    
    def _init_plugin(self):
        """Initialise le plugin d'annotations approprié."""
        if self.ann_type == 'local':
            from app.plugins.annotations.local_annotations import LocalAnnotationsPlugin
            return LocalAnnotationsPlugin(self.ann_config)
        elif self.ann_type == 'mongodb':
            from app.plugins.annotations.mongodb_annotations import MongoDBAnnotationsPlugin
            return MongoDBAnnotationsPlugin(self.ann_config)
        elif self.ann_type == 'postgresql':
            from app.plugins.annotations.postgresql_annotations import PostgreSQLAnnotationsPlugin
            return PostgreSQLAnnotationsPlugin(self.ann_config)
        else:
            raise ValueError(f"Type d'annotations non supporté: {self.ann_type}")
    
    def get_annotations(self, user_id: str, document_id: str) -> dict:
        """Récupère les annotations existantes."""
        return self._plugin.get_annotations(user_id, document_id)
    
    def list_all_keys(self) -> List[tuple]:
        """Liste toutes les clés user:document disponibles."""
        if self.ann_type == 'local':
            # Pour le backend local, lire directement le fichier
            storage_path = self.ann_config.get('storage_path', './data/annotations.json')
            if not os.path.isabs(storage_path):
                storage_path = os.path.join(self.project_root, storage_path)
            
            if os.path.exists(storage_path):
                with open(storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return [tuple(key.split(':', 1)) for key in data.keys() if ':' in key]
            return []
        
        elif self.ann_type == 'mongodb':
            # Pour MongoDB, utiliser une requête distinct
            if hasattr(self._plugin, '_collection') and self._plugin._collection:
                docs = self._plugin._collection.find({}, {'user_id': 1, 'document_id': 1})
                return [(doc['user_id'], doc['document_id']) for doc in docs]
            return []
        
        elif self.ann_type == 'postgresql':
            # Pour PostgreSQL, faire une requête
            if hasattr(self._plugin, '_pool') and self._plugin._pool:
                conn = self._plugin._get_connection()
                try:
                    with conn.cursor() as cur:
                        cur.execute(f"SELECT user_id, document_id FROM {self._plugin.table}")
                        return [(row[0], row[1]) for row in cur.fetchall()]
                finally:
                    self._plugin._put_connection(conn)
            return []
        
        return []
    
    def list_user_documents(self, user_id: str) -> List[str]:
        """Liste tous les documents d'un utilisateur."""
        all_keys = self.list_all_keys()
        return [doc_id for uid, doc_id in all_keys if uid == user_id]
    
    def get_backend_type(self) -> str:
        """Retourne le type de backend utilisé."""
        return self.ann_type


def export_annotations(
    manager: AnnotationsManager,
    user_id: str,
    document_id: str = None,
    export_all: bool = False,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Exporte les annotations.
    
    Args:
        manager: Gestionnaire d'annotations
        user_id: Utilisateur source
        document_id: Document spécifique (None si --all)
        export_all: Exporter tous les documents de l'utilisateur
        verbose: Afficher les détails
    
    Returns:
        Données d'export au format standard
    """
    export_data = {
        'version': '1.0',
        'exported_at': datetime.utcnow().isoformat() + 'Z',
        'source': f'openmark-{manager.get_backend_type()}',
        'data': []
    }
    
    if export_all:
        # Exporter tous les documents de l'utilisateur
        documents = manager.list_user_documents(user_id)
        if verbose:
            print(f"📋 Documents trouvés pour {user_id}: {len(documents)}", file=sys.stderr)
        
        for doc_id in documents:
            annotations = manager.get_annotations(user_id, doc_id)
            if annotations.get('notes') or annotations.get('highlights'):
                export_data['data'].append({
                    'user_id': user_id,
                    'document_id': doc_id,
                    'annotations': annotations
                })
                if verbose:
                    notes_count = len(annotations.get('notes', []))
                    hl_count = len(annotations.get('highlights', []))
                    print(f"   📄 {doc_id}: {notes_count} notes, {hl_count} highlights", file=sys.stderr)
    else:
        # Exporter un document spécifique
        annotations = manager.get_annotations(user_id, document_id)
        export_data['data'].append({
            'user_id': user_id,
            'document_id': document_id,
            'annotations': annotations
        })
        if verbose:
            notes_count = len(annotations.get('notes', []))
            hl_count = len(annotations.get('highlights', []))
            print(f"📄 {user_id}:{document_id}: {notes_count} notes, {hl_count} highlights", file=sys.stderr)
    
    return export_data


def main():
    parser = argparse.ArgumentParser(
        description="Export des annotations OpenMark vers un fichier JSON",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Exporter un document spécifique
  python3 scripts/annotations_export.py -u admin -d rapport2026 -o export.json

  # Exporter tous les documents d'un utilisateur
  python3 scripts/annotations_export.py -u admin --all -o user_backup.json

  # Afficher sur stdout (pour piping)
  python3 scripts/annotations_export.py -u admin -d doc1 | jq .

  # Format compact
  python3 scripts/annotations_export.py -u admin -d doc1 --compact -o export.json

Le fichier exporté est compatible avec annotations_import.py.
"""
    )
    
    parser.add_argument('-u', '--user', required=True,
                        help="Utilisateur source")
    parser.add_argument('-d', '--document',
                        help="Document spécifique à exporter")
    parser.add_argument('--all', action='store_true', dest='export_all',
                        help="Exporter tous les documents de l'utilisateur")
    parser.add_argument('-o', '--output',
                        help="Fichier de sortie (stdout si non spécifié)")
    parser.add_argument('--compact', action='store_true',
                        help="Format JSON compact (une ligne)")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Afficher les détails")
    parser.add_argument('-c', '--config',
                        help="Chemin vers le fichier de configuration")
    
    args = parser.parse_args()
    
    # Vérifier les arguments
    if not args.document and not args.export_all:
        print("❌ Spécifiez --document ou --all", file=sys.stderr)
        sys.exit(1)
    
    if args.document and args.export_all:
        print("❌ --document et --all sont mutuellement exclusifs", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Initialiser le gestionnaire
        manager = AnnotationsManager(config_path=args.config, verbose=args.verbose)
        
        if args.verbose:
            print(f"🔌 Backend: {manager.get_backend_type()}", file=sys.stderr)
        
        # Exporter
        export_data = export_annotations(
            manager=manager,
            user_id=args.user,
            document_id=args.document,
            export_all=args.export_all,
            verbose=args.verbose
        )
        
        # Formater le JSON
        if args.compact:
            json_output = json.dumps(export_data, ensure_ascii=False)
        else:
            json_output = json.dumps(export_data, indent=2, ensure_ascii=False)
        
        # Écrire la sortie
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(json_output)
            
            total_notes = sum(len(d['annotations'].get('notes', [])) for d in export_data['data'])
            total_hl = sum(len(d['annotations'].get('highlights', [])) for d in export_data['data'])
            
            print(f"✅ Export réussi vers {args.output}", file=sys.stderr)
            print(f"   📝 Notes: {total_notes}", file=sys.stderr)
            print(f"   🖍️  Highlights: {total_hl}", file=sys.stderr)
            print(f"   📄 Documents: {len(export_data['data'])}", file=sys.stderr)
        else:
            # Sortie stdout
            print(json_output)
        
    except FileNotFoundError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
