#!/usr/bin/env python3
"""OpenMark application entry point."""

from app import create_app
from app.config import Config

app = create_app()

if __name__ == '__main__':
    config = Config()
    app.run(
        host=config.server.get('host', '0.0.0.0'),
        port=config.server.get('port', 5000),
        debug=config.server.get('debug', False)
    )
