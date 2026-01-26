#!/usr/bin/env python3
"""
Headless Test - Testet die Anwendung ohne GUI
Demonstriert PDF-Parser und PowerPoint-Generator
"""

import sys
from pathlib import Path

# Füge src zum Python-Path hinzu
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("=" * 60)
print("  ALLIANZ ANGEBOTSTOOL - HEADLESS TEST")
print("=" * 60)
print()

# Test 1: Sample-PDF erstellen
print("1. Erstelle Sample-PDF...")
try:
    from tests.sample_data import create_sample_pdf
    pdf_path = create_sample_pdf()
    print(f"   ✓ Sample-PDF erstellt: {pdf_path}")
except Exception as e:
    print(f"   ✗ Fehler: {e}")
    pdf_path = None

print()

# Test 2: Templates erstellen
print("2. Erstelle PowerPoint-Templates...")
try:
    from utils.template_creator import create_all_templates
    create_all_templates()
except Exception as e:
    print(f"   ✗ Fehler: {e}")

print()

# Test 3: PDF-Daten extrahieren
if pdf_path:
    print("3. Extrahiere Daten aus PDF...")
    try:
        from pdf_parser.extractor import PDFExtractor

        extractor = PDFExtractor(pdf_path)
        data = extractor.extract()

        print(f"   ✓ Pferdename: {data['horse_name']}")
        print(f"   ✓ Kunde: {data['customer_name']}")
        print(f"   ✓ Datum: {data['created_date']}")
    except Exception as e:
        print(f"   ✗ Fehler: {e}")
        import traceback
        traceback.print_exc()
        data = None

    print()

    # Test 4: PowerPoint generieren
    if data:
        print("4. Generiere PowerPoint-Angebot...")
        try:
            from pptx_manager.generator import PPTXGenerator

            output_dir = Path(__file__).parent / "output"
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / "test_angebot.pptx"

            generator = PPTXGenerator("Vertriebler 1")
            pptx_path = generator.generate(data, str(output_path))

            print(f"   ✓ PowerPoint erstellt: {pptx_path}")
            print(f"   ✓ Dateigröße: {Path(pptx_path).stat().st_size} Bytes")
        except Exception as e:
            print(f"   ✗ Fehler: {e}")
            import traceback
            traceback.print_exc()

print()
print("=" * 60)
print("  TEST ABGESCHLOSSEN")
print("=" * 60)
print()
print("Hinweis: Die Desktop-App (GUI) kann auf diesem Server")
print("ohne Display nicht gestartet werden.")
print()
print("Für die vollständige App mit GUI:")
print("  - Auf Windows/Mac mit Display ausführen")
print("  - Oder EXE unter Windows bauen: ./build.sh")
print()
