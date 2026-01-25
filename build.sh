#!/bin/bash

# Build-Script für Angebotstool EXE

echo "======================================"
echo "  Allianz Angebotstool - EXE Build"
echo "======================================"
echo ""

# 1. Virtuelle Umgebung erstellen (falls nicht vorhanden)
if [ ! -d "venv" ]; then
    echo "Erstelle virtuelle Umgebung..."
    python3 -m venv venv
fi

# 2. Virtuelle Umgebung aktivieren
echo "Aktiviere virtuelle Umgebung..."
source venv/bin/activate

# 3. Dependencies installieren
echo "Installiere Dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Templates erstellen
echo "Erstelle Vertriebler-Templates..."
python3 src/utils/template_creator.py

# 5. EXE bauen
echo ""
echo "Baue EXE-Datei..."
pyinstaller build_exe.spec --clean

# 6. Fertig
echo ""
echo "======================================"
echo "  Build abgeschlossen!"
echo "======================================"
echo ""
echo "EXE-Datei: dist/Allianz_Angebotstool"
echo ""
