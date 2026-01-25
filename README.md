# 🐴 Allianz Angebotstool - AMIS Pferde-Versicherung

Desktop-Anwendung für die automatische Erstellung von Versicherungsangeboten aus AMIS PDF-Dateien.

## ✨ Features

- **PDF-Upload**: Import von AMIS Pferde-Angebots-PDFs
- **Automatische Datenextraktion**: Pferdename, Kundenname, Erstelldatum
- **Multi-Vertriebler-System**: 7 verschiedene PowerPoint-Templates
- **PowerPoint-Integration**: Automatische Befüllung von Angebotsvorlagen
- **Preisfelder-Platzhalter**: 3 gelb markierte Felder für manuelle Preiseingabe
- **EXE-Datei**: Standalone-Anwendung ohne Python-Installation

## 🚀 Installation

### Entwicklungsumgebung

```bash
# Repository klonen
git clone https://github.com/cany-ae/canys-crm.git
cd canys-crm

# Virtuelle Umgebung erstellen
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate  # Windows

# Dependencies installieren
pip install -r requirements.txt

# Templates erstellen
python3 src/utils/template_creator.py
```

### EXE-Build (Windows)

```bash
# Automatischer Build
chmod +x build.sh
./build.sh

# Oder manuell
pyinstaller build_exe.spec --clean
```

Die fertige EXE-Datei befindet sich in: `dist/Allianz_Angebotstool.exe`

## 📖 Verwendung

### Desktop-App starten

```bash
# Entwicklungsmodus
python3 src/main.py

# Oder direkt die EXE-Datei ausführen (nach Build)
./dist/Allianz_Angebotstool
```

### Workflow

1. **Vertriebler auswählen** - Wähle einen der 7 Vertriebler aus dem Dropdown
2. **PDF hochladen** - Lade das AMIS Pferde-Angebots-PDF hoch
3. **Daten prüfen** - Automatisch extrahierte Daten werden angezeigt
4. **Angebot generieren** - PowerPoint wird erstellt mit:
   - Automatisch eingefügten Daten (Pferdename, Kunde, Datum)
   - 3 gelb markierten Preisfeldern zum manuellen Ausfüllen
5. **Ergebnis** - Fertiges Angebot wird auf dem Desktop gespeichert

## 📁 Projektstruktur

```
canys-crm/
├── src/
│   ├── main.py                    # Haupteinstiegspunkt
│   ├── gui/
│   │   ├── __init__.py
│   │   └── main_window.py         # Hauptfenster (PyQt6)
│   ├── pdf_parser/
│   │   ├── __init__.py
│   │   └── extractor.py           # PDF-Datenextraktion
│   ├── pptx_manager/
│   │   ├── __init__.py
│   │   └── generator.py           # PowerPoint-Generator
│   └── utils/
│       ├── __init__.py
│       └── template_creator.py    # Template-Ersteller
├── templates/                      # PowerPoint-Templates (7 Stück)
│   ├── template_vertriebler_1.pptx
│   ├── template_vertriebler_2.pptx
│   └── ...
├── tests/                          # Tests
├── docs/                           # Dokumentation
├── requirements.txt                # Python-Dependencies
├── build_exe.spec                  # PyInstaller-Konfiguration
├── build.sh                        # Build-Script
├── .gitignore
├── CLAUDE.md                       # Projekt-Konfiguration
└── README.md
```

## 🔧 Technologie-Stack

- **GUI**: PyQt6
- **PDF-Verarbeitung**: pdfplumber, PyPDF2
- **PowerPoint**: python-pptx
- **Build**: PyInstaller
- **Testing**: pytest

## 📋 Anforderungen

- Python 3.8+
- Windows/Linux/Mac
- Mindestens 100 MB freier Speicherplatz

## 🐛 Troubleshooting

### "Keine Daten gefunden" bei PDF-Upload

- Prüfe ob das PDF Text enthält (nicht nur Bilder)
- Stelle sicher dass es ein AMIS-Angebots-PDF ist

### EXE funktioniert nicht

- Prüfe ob alle Templates vorhanden sind im `templates/` Ordner
- Stelle sicher dass das Build-Script vollständig durchgelaufen ist

### Templates fehlen

```bash
# Templates neu erstellen
python3 src/utils/template_creator.py
```

## 📝 Lizenz

Private Repository - Nur für internen Gebrauch

## 👥 Kontakt

Projekt-Maintainer: cany-ae
Repository: https://github.com/cany-ae/canys-crm
