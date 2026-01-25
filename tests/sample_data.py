"""
Sample-Daten Generator für Testing
Erstellt ein Test-PDF mit typischen AMIS-Daten
"""

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from pathlib import Path


def create_sample_pdf():
    """Erstelle Sample-PDF mit typischen AMIS-Daten"""

    output_dir = Path(__file__).parent
    output_path = output_dir / "sample_amis_angebot.pdf"

    # PDF erstellen
    c = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4

    # Titel
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, "AMIS Pferde-Versicherung")

    # Angebotsdaten
    c.setFont("Helvetica", 12)
    y_position = height - 100

    lines = [
        "",
        "Angebotsdatum: 15.01.2026",
        "",
        "═══════════════════════════════════════",
        "",
        "VERSICHERTES PFERD",
        "",
        "Pferdename: Donnerwetter",
        "Rasse: Holsteiner",
        "Alter: 8 Jahre",
        "",
        "═══════════════════════════════════════",
        "",
        "VERSICHERUNGSNEHMER",
        "",
        "Kunde: Max Mustermann",
        "Adresse: Musterstraße 123",
        "PLZ/Ort: 12345 Musterstadt",
        "Telefon: +49 123 456789",
        "Email: max.mustermann@example.com",
        "",
        "═══════════════════════════════════════",
        "",
        "VERSICHERUNGSDETAILS",
        "",
        "Versicherungsart: Pferde-Lebensversicherung",
        "Versicherungssumme: 15.000,00 EUR",
        "Laufzeit: 12 Monate",
        "Zahlweise: Jährlich",
        "",
        "Selbstbeteiligung: 250,00 EUR",
        "Deckungssumme OP: 5.000,00 EUR",
        "",
        "═══════════════════════════════════════",
        "",
        "LEISTUNGSUMFANG",
        "",
        "✓ Tierarztkosten",
        "✓ Operationskosten",
        "✓ Krankenhausaufenthalt",
        "✓ Transportkosten",
        "✓ Freie Tierarztwahl",
        "",
        "═══════════════════════════════════════",
        "",
        "Erstellt am: 15.01.2026",
        "Angebotsnummer: AMIS-2026-0001",
        "Gültig bis: 15.02.2026"
    ]

    for line in lines:
        c.drawString(50, y_position, line)
        y_position -= 20

    # PDF speichern
    c.save()

    print(f"✓ Sample-PDF erstellt: {output_path}")
    return str(output_path)


if __name__ == "__main__":
    create_sample_pdf()
