"""
Test-Skript um zu sehen wie der Text aus PDFs extrahiert wird
Und ob Euro-Beträge gefunden werden können
"""
import sys
import fitz  # PyMuPDF


def test_template(pdf_path):
    """Teste ob die Euro-Beträge im Template gefunden werden"""
    print(f"\n=== Teste Template: {pdf_path} ===\n")

    doc = fitz.open(pdf_path)

    # Die Beträge die wir suchen
    search_terms = [
        "243,81€", "243,81 €", "243,81",
        "295,81€", "295,81 €", "295,81",
        "385,62€", "385,62 €", "385,62",
    ]

    for i, page in enumerate(doc):
        print(f"--- Seite {i+1} ---")

        # Extrahiere Text
        text = page.get_text()

        # Suche nach Euro-Zeichen und Beträgen
        for line in text.split('\n'):
            if '€' in line or 'EUR' in line or '243' in line or '295' in line or '385' in line:
                print(f"  Zeile: {repr(line)}")

        print()

        # Teste search_for Funktion
        print("  Suche mit search_for():")
        for term in search_terms:
            results = page.search_for(term)
            if results:
                print(f"    ✅ '{term}' gefunden: {len(results)} Treffer")
                for rect in results:
                    print(f"       Position: x={rect.x0:.1f}, y={rect.y0:.1f}")
            else:
                # Versuche ohne €
                pass

        print()

    doc.close()


def test_amis(pdf_path):
    """Teste AMIS PDF Extraktion"""
    print(f"\n=== Teste AMIS: {pdf_path} ===\n")

    import pdfplumber

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            print(f"--- Seite {i+1} (erste 1500 Zeichen) ---")
            print(text[:1500] if text else "Kein Text")
            print("\n")

            # Suche nach EUR Beträgen
            if text:
                import re
                matches = re.findall(r'(\d{1,3}(?:\.\d{3})*,\d{2})\s*EUR', text, re.IGNORECASE)
                if matches:
                    print(f"  EUR-Beträge gefunden: {matches}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Verwendung:")
        print("  python test_extract.py template <pfad_zum_template.pdf>")
        print("  python test_extract.py amis <pfad_zum_amis.pdf>")
        print()
        print("Beispiele:")
        print("  python test_extract.py template templates\\samet_uz\\teil1.pdf")
        print("  python test_extract.py amis C:\\Users\\Beyar\\Desktop\\angebot.pdf")
        sys.exit(1)

    mode = sys.argv[1].lower()
    pdf_path = sys.argv[2]

    if mode == "template":
        test_template(pdf_path)
    elif mode == "amis":
        test_amis(pdf_path)
    else:
        print(f"Unbekannter Modus: {mode}")
        print("Verwende 'template' oder 'amis'")
