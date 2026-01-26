"""
PDF-Platzhalter-Ersetzung
Ersetzt Platzhalter in der Vorlage-PDF mit echten Daten
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict


class PlaceholderReplacer:
    """Ersetzt Platzhalter in PDF-Vorlagen"""

    def __init__(self, template_path: str):
        """
        Initialisiere Replacer

        Args:
            template_path: Pfad zur Vorlage-PDF
        """
        self.template_path = Path(template_path)
        if not self.template_path.exists():
            raise FileNotFoundError(f"Vorlage nicht gefunden: {template_path}")

    def replace_placeholders(self, output_path: str, data: Dict[str, str]) -> str:
        """
        Ersetze Platzhalter in der Vorlage

        Args:
            output_path: Pfad für die Ausgabe-PDF
            data: Dictionary mit Daten zum Ersetzen
                  Erwartet: vorname, nachname, pferdename, datum

        Returns:
            Pfad zur erstellten PDF-Datei
        """
        # Öffne Vorlage
        doc = fitz.open(str(self.template_path))

        # Platzhalter-Mapping
        # Kombiniere Vor- und Nachname für den kombinierten Platzhalter
        # Normalisiere Leerzeichen (entferne mehrfache Leerzeichen)
        import re
        vorname = data.get('vorname', '').strip()
        nachname = data.get('nachname', '').strip()
        full_name = f"{vorname} {nachname}".strip()
        # Entferne mehrfache Leerzeichen
        full_name = re.sub(r'\s+', ' ', full_name)

        # Nur die Platzhalter die tatsächlich in der Vorlage stehen
        replacements = {
            "Vorname, Nachname": full_name,  # Kombinierter Platzhalter für Namen
            "Pferdename": data.get("pferdename", "").strip(),  # Manuell eingegeben in GUI
            "tt.mm.jjjj": data.get("datum", "").strip(),  # Datum
        }

        # Farben für Platzhalter-Ersetzung
        # Hintergrund: #DAEFFA (218, 239, 250) -> RGB(0.855, 0.937, 0.980)
        background_color = (0.855, 0.937, 0.980)
        # Schrift: #005399 (0, 83, 153) -> RGB(0.0, 0.325, 0.6)
        text_color = (0.0, 0.325, 0.6)

        # Ersetze auf allen Seiten
        for page in doc:
            for placeholder, value in replacements.items():
                # Suche nach Platzhalter
                text_instances = page.search_for(placeholder)

                for inst in text_instances:
                    # Überschreibe mit hellblauem Rechteck (#DAEFFA)
                    page.draw_rect(inst, color=background_color, fill=background_color)

                    # Schreibe neuen Text in dunkelblau (#005399)
                    # Berechne Textgröße basierend auf Rechteck-Höhe
                    base_font_size = inst.height * 0.8
                    rect_width = inst.x1 - inst.x0

                    # Verwende Helvetica als Standardschrift
                    fontname = "helv"  # Helvetica

                    # Dynamische Schriftgrößenanpassung basierend auf tatsächlicher Textbreite
                    font_size = base_font_size

                    # Iterativ die optimale Schriftgröße finden
                    while font_size > 8:
                        # Berechne tatsächliche Textbreite mit PyMuPDF
                        text_width = fitz.get_text_length(value, fontname=fontname, fontsize=font_size)

                        # Prüfe ob Text in Rechteck passt (mit 5% Puffer)
                        if text_width <= rect_width * 0.95:
                            break

                        # Verkleinere Schrift
                        font_size -= 0.5

                    # Mindestschriftgröße
                    font_size = max(font_size, 8)

                    # Y-Offset anpassen: Datum weiter nach unten verschieben für mehr Abstand
                    y_offset = -2  # Standard
                    if placeholder == "tt.mm.jjjj":
                        y_offset = 5  # Datum nach unten verschieben für mehr Abstand zum Pferdename

                    page.insert_text(
                        (inst.x0 + 2, inst.y1 + y_offset),  # Kleiner Abstand von links, angepasste Y-Position
                        value,
                        fontname=fontname,
                        fontsize=font_size,
                        color=text_color
                    )

        # Speichere neue PDF
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(output_path))
        doc.close()

        return str(output_path)

    def replace_in_place(self, data: Dict[str, str]) -> str:
        """
        Ersetze Platzhalter und überschreibe Original

        Args:
            data: Dictionary mit Daten zum Ersetzen

        Returns:
            Pfad zur modifizierten PDF-Datei
        """
        # Temporäre Datei erstellen
        temp_path = self.template_path.parent / f"{self.template_path.stem}_temp.pdf"

        # Ersetze
        self.replace_placeholders(str(temp_path), data)

        # Ersetze Original
        self.template_path.unlink()
        temp_path.rename(self.template_path)

        return str(self.template_path)

    @staticmethod
    def prepare_data_from_extraction(extracted_data: Dict[str, str]) -> Dict[str, str]:
        """
        Bereite extrahierte Daten für Platzhalter-Ersetzung vor

        Args:
            extracted_data: Daten aus PDFExtractor
                           Erwartet: customer_name, horse_name, created_date

        Returns:
            Dictionary mit: vorname, nachname, pferdename, datum
        """
        # Trenne Vor- und Nachname
        customer_name = extracted_data.get("customer_name", "")
        name_parts = customer_name.split(maxsplit=1)

        vorname = name_parts[0] if len(name_parts) > 0 else ""
        nachname = name_parts[1] if len(name_parts) > 1 else ""

        # Entferne "Herr" oder "Frau" falls vorhanden
        for title in ["Herr", "Frau", "Dr.", "Prof."]:
            if vorname.startswith(title):
                vorname = vorname.replace(title, "").strip()
                # Verschiebe erste Wort nach vorne
                if " " in vorname:
                    parts = vorname.split(maxsplit=1)
                    vorname = parts[0]
                    nachname = parts[1] if len(parts) > 1 else nachname

        return {
            "vorname": vorname,
            "nachname": nachname,
            "pferdename": extracted_data.get("horse_name", ""),
            "datum": extracted_data.get("created_date", "")
        }
