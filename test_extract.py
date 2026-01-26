"""
Test-Skript um zu sehen wie der Text aus dem AMIS-PDF extrahiert wird
"""
import sys
import pdfplumber

def test_extract(pdf_path):
    print(f"\n=== Teste PDF: {pdf_path} ===\n")

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            print(f"--- Seite {i+1} ---")
            print(text[:2000] if text else "Kein Text")
            print("\n")

            # Suche speziell nach "Beitrag"
            if text and "Beitrag" in text:
                print("=== BEITRAG GEFUNDEN ===")
                # Zeige 200 Zeichen um "Beitrag" herum
                idx = text.find("Beitrag")
                start = max(0, idx - 50)
                end = min(len(text), idx + 200)
                print(f"Kontext um 'Beitrag':")
                print(repr(text[start:end]))  # repr() zeigt \n und andere Zeichen
                print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Verwendung: python test_extract.py <pfad_zur_amis_pdf>")
        print("Beispiel: python test_extract.py C:\\Users\\Beyar\\Desktop\\amis_angebot.pdf")
        sys.exit(1)

    test_extract(sys.argv[1])
