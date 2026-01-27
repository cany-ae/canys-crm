"""
Konfigurationsdatei für Canys CRM Angebotstool
Enthält API-Keys und zentrale Einstellungen
"""

import os
import json
from pathlib import Path


def _load_api_key():
    """Lade API Key aus config.json oder Umgebungsvariable"""
    # 1. Prüfe Umgebungsvariable
    key = os.environ.get("GROQ_API_KEY", "")
    if key:
        return key

    # 2. Lade aus config.json (neben der .exe oder im Projektordner)
    config_paths = [
        Path(__file__).parent.parent / "config.json",  # Projektordner
        Path.cwd() / "config.json",  # Aktuelles Verzeichnis
        Path(__file__).parent / "config.json",  # src Ordner
    ]

    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    return config.get("GROQ_API_KEY", "")
            except:
                pass

    return ""


# Groq API Configuration
GROQ_API_KEY = _load_api_key()
GROQ_MODEL = "llama-3.1-8b-instant"  # Schnelles Modell für Pferderasse-Abfragen

# App Configuration
APP_NAME = "Allianz Angebotstool"
APP_VERSION = "1.0.0"
