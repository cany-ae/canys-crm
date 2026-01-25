# Installation und Setup

## Voraussetzungen

- Python 3.8 oder höher
- pip (Python Package Manager)
- Git

## Setup-Schritte

### 1. Repository klonen

```bash
git clone https://github.com/cany-ae/canys-crm.git
cd canys-crm
```

### 2. Virtuelle Umgebung erstellen

```bash
python3 -m venv venv
```

### 3. Virtuelle Umgebung aktivieren

**Linux/Mac:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 4. Dependencies installieren

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Templates erstellen

```bash
python3 src/utils/template_creator.py
```

Dies erstellt 7 PowerPoint-Templates für die verschiedenen Vertriebler im `templates/` Ordner.

### 6. Anwendung testen

```bash
python3 src/main.py
```

## EXE-Datei erstellen (Windows)

### Automatischer Build

```bash
chmod +x build.sh
./build.sh
```

### Manueller Build

```bash
pyinstaller build_exe.spec --clean
```

Die fertige EXE-Datei befindet sich dann in:
```
dist/Allianz_Angebotstool.exe
```

## Troubleshooting

### Import-Fehler

Falls Module nicht gefunden werden:
```bash
pip install --upgrade -r requirements.txt
```

### Templates fehlen

```bash
python3 src/utils/template_creator.py
```

### PyQt6 Fehler unter Linux

```bash
sudo apt-get install python3-pyqt6
# oder
pip install --upgrade PyQt6
```

## Sample-Daten zum Testen

Sample-PDF erstellen:
```bash
python3 tests/sample_data.py
```

Dies erstellt `tests/sample_amis_angebot.pdf` zum Testen der Anwendung.
