# Testing Guide - Allianz Angebotstool

## ✅ Code-Status

**Syntax-Check:** ✓ Alle Python-Dateien sind korrekt
**Module:** 10 Python-Dateien, 781 Zeilen Code
**GitHub:** https://github.com/cany-ae/canys-crm

## ⚠️ GUI-Test auf diesem Server

Die Desktop-App (PyQt6) **kann auf diesem Server nicht gestartet werden**, weil:
- Kein Display/X11 Server vorhanden
- Kein GUI-Framework installiert
- Server ist headless (nur Terminal)

## 🚀 Test-Optionen

### Option 1: Auf Build-Server testen (ssh-eco-crm)

```bash
# Zum Build-Server wechseln (via SSH-MCP)
# Server aus ~/.claude.json: ssh-eco-crm

# Code übertragen
scp -r ~/claude-projects/canys-crm frappe@[IP-VON-ECO-CRM]:/tmp/

# SSH zum Build-Server
ssh frappe@[IP-VON-ECO-CRM]

# Auf dem Build-Server:
cd /tmp/canys-crm
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 src/utils/template_creator.py  # Templates erstellen
python3 src/main.py                     # App starten
```

**Hinweis:** Auch der Build-Server braucht X11/Display für die GUI!

### Option 2: Lokal auf Windows/Mac testen (EMPFOHLEN)

**Schritt 1:** Projekt herunterladen
```bash
git clone https://github.com/cany-ae/canys-crm.git
cd canys-crm
```

**Schritt 2:** Dependencies installieren
```bash
# Windows
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Schritt 3:** Templates erstellen
```bash
python src/utils/template_creator.py
```

**Schritt 4:** App starten
```bash
python src/main.py
```

Die GUI öffnet sich mit:
- Vertriebler-Dropdown (1-7)
- PDF-Upload Button
- Automatische Datenextraktion
- Angebot-Generierung

### Option 3: EXE bauen (nur Windows)

Auf einer **Windows-Maschine**:

```bash
cd canys-crm
pip install -r requirements.txt
python src/utils/template_creator.py

# EXE bauen
pyinstaller build_exe.spec --clean

# Ausgabe: dist/Allianz_Angebotstool.exe
```

Die EXE kann dann **ohne Python-Installation** auf jedem Windows-PC gestartet werden.

### Option 4: Headless-Test (nur Kern-Funktionen)

Ohne GUI, nur Core-Funktionalität testen:

```bash
cd ~/claude-projects/canys-crm

# Dependencies installieren (braucht pip)
pip3 install reportlab pdfplumber python-pptx

# Headless-Test ausführen
python3 test_headless.py
```

Dies testet:
- ✓ PDF-Generierung (Sample-Daten)
- ✓ PDF-Datenextraktion
- ✓ PowerPoint-Template-Erstellung
- ✓ PowerPoint-Generierung

**OHNE** die GUI zu starten.

## 📊 Was funktioniert bereits

### Syntax & Code-Qualität ✅

```bash
cd ~/claude-projects/canys-crm
python3 -m py_compile src/**/*.py  # Alle Dateien OK
```

### Module & Struktur ✅

- `src/main.py` - Haupteinstiegspunkt
- `src/gui/main_window.py` - PyQt6 GUI (290 Zeilen)
- `src/pdf_parser/extractor.py` - PDF-Parser (180 Zeilen)
- `src/pptx_manager/generator.py` - PowerPoint-Generator (280 Zeilen)
- `src/utils/template_creator.py` - Template-Ersteller

### Tests & Dokumentation ✅

- `tests/sample_data.py` - Sample-PDF Generator
- `docs/INSTALLATION.md` - Installation-Anleitung
- `docs/USAGE.md` - Benutzer-Handbuch
- `docs/DEPLOYMENT.md` - Deployment-Guide
- `README.md` - Projekt-Übersicht

## 🎯 Empfohlener Test-Workflow

**Für schnellen Test:**
1. Klone Repo auf Windows/Mac
2. Installiere Dependencies (`pip install -r requirements.txt`)
3. Starte App (`python src/main.py`)
4. Teste mit Sample-PDF

**Für Production:**
1. Baue EXE auf Windows (`pyinstaller build_exe.spec`)
2. Verteile `dist/Allianz_Angebotstool.exe`
3. Keine Python-Installation beim Endnutzer nötig

## 🔍 Verifizierung ohne GUI

Falls du nur prüfen willst ob der Code funktioniert:

```bash
cd ~/claude-projects/canys-crm

# Syntax-Check
python3 -m py_compile src/**/*.py

# Import-Test (zeigt ob Struktur korrekt ist)
python3 -c "import sys; sys.path.insert(0, 'src'); import main"

# Zeige Code-Statistik
find src -name "*.py" -exec wc -l {} + | tail -1
```

## 📝 Nächste Schritte

1. **Lokal testen** - Klone Repo auf Windows/Mac Maschine
2. **EXE bauen** - Auf Windows: `pyinstaller build_exe.spec`
3. **An Nutzer verteilen** - EXE-Datei ist standalone
4. **Feedback sammeln** - Features erweitern basierend auf Nutzung

## 🆘 Support

Bei Problemen:
- Prüfe `docs/INSTALLATION.md`
- GitHub Issues: https://github.com/cany-ae/canys-crm/issues
- Logs prüfen in: `~/.claude/logs/`
