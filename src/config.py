"""
Konfigurationsdatei für Canys CRM Angebotstool
Enthält API-Keys und zentrale Einstellungen
"""

import os

# Groq API Configuration
# API-Key aus Umgebungsvariable (muss vor Start gesetzt werden)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.1-8b-instant"  # Schnelles Modell für Pferderasse-Abfragen

# App Configuration
APP_NAME = "Allianz Angebotstool"
APP_VERSION = "1.0.0"
