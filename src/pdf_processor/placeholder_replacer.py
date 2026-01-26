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

        # Euro-Beträge für Selbstbeteiligung (auf Seite 1)
        # Formatiere Beträge: Entferne € falls vorhanden, füge es dann hinzu
        def format_beitrag(value):
            if not value:
                return ""
            # Entferne € und Leerzeichen
            clean = value.replace("€", "").replace(" ", "").strip()
            return f"{clean}€"  # Format: "243,81€" (ohne Leerzeichen vor €)

        beitrag_20 = data.get("beitrag_20", "")
        beitrag_10 = data.get("beitrag_10", "")
        beitrag_0 = data.get("beitrag_0", "")

        # Beitrags-Ersetzungen (Original -> Neu)
        # Verschiedene Formate für Euro-Beträge (mit/ohne Leerzeichen, Non-Breaking Space)
        beitrag_replacements = {}
        if beitrag_20:
            new_val = format_beitrag(beitrag_20)
            # Alle möglichen Formate für 243,81
            beitrag_replacements["243,81€"] = new_val
            beitrag_replacements["243,81 €"] = new_val
            beitrag_replacements["243,81\xa0€"] = new_val  # Non-breaking space
            beitrag_replacements["243,81"] = new_val  # Ohne €
        if beitrag_10:
            new_val = format_beitrag(beitrag_10)
            # Alle möglichen Formate für 295,81
            beitrag_replacements["295,81€"] = new_val
            beitrag_replacements["295,81 €"] = new_val
            beitrag_replacements["295,81\xa0€"] = new_val  # Non-breaking space
            beitrag_replacements["295,81"] = new_val  # Ohne €
        if beitrag_0:
            new_val = format_beitrag(beitrag_0)
            # Alle möglichen Formate für 385,62
            beitrag_replacements["385,62€"] = new_val
            beitrag_replacements["385,62 €"] = new_val
            beitrag_replacements["385,62\xa0€"] = new_val  # Non-breaking space
            beitrag_replacements["385,62"] = new_val  # Ohne €

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

        # Ersetze Euro-Beträge (Selbstbeteiligung) auf allen Seiten
        # (Die Beträge können auf verschiedenen Seiten sein, z.B. Seite 3 bei Samet)
        if beitrag_replacements and len(doc) > 0:
            print(f"[DEBUG] Suche Beträge auf allen {len(doc)} Seiten...")

            # Farben für Beitrags-Ersetzung (dunkles Türkis auf hellem Hintergrund)
            beitrag_bg_color = (0.855, 0.937, 0.980)  # Hellblau #DAEFFA
            beitrag_text_color = (0.0, 0.325, 0.6)  # Dunkelblau #005399

            found_any = False

            # Durchsuche ALLE Seiten nach Beträgen
            for page_idx, page in enumerate(doc):
                for old_beitrag, new_beitrag in beitrag_replacements.items():
                    if not new_beitrag:
                        continue

                    # Suche nach altem Betrag
                    text_instances = page.search_for(old_beitrag)
                    if text_instances:
                        print(f"[DEBUG] ✅ Seite {page_idx + 1}: '{old_beitrag}' gefunden: {len(text_instances)} Treffer")
                        found_any = True

                    for inst in text_instances:
                        # Überschreibe mit Hintergrundfarbe
                        page.draw_rect(inst, color=beitrag_bg_color, fill=beitrag_bg_color)

                        # Berechne Schriftgröße
                        base_font_size = inst.height * 0.75
                        rect_width = inst.x1 - inst.x0

                        fontname = "helv"
                        font_size = base_font_size

                        # Optimale Schriftgröße finden
                        while font_size > 10:
                            text_width = fitz.get_text_length(new_beitrag, fontname=fontname, fontsize=font_size)
                            if text_width <= rect_width * 0.95:
                                break
                            font_size -= 0.5

                        font_size = max(font_size, 10)

                        # Zentriere Text vertikal und horizontal
                        text_width = fitz.get_text_length(new_beitrag, fontname=fontname, fontsize=font_size)
                        x_offset = (rect_width - text_width) / 2
                        y_offset = -2

                        page.insert_text(
                            (inst.x0 + x_offset, inst.y1 + y_offset),
                            new_beitrag,
                            fontname=fontname,
                            fontsize=font_size,
                            color=beitrag_text_color
                        )

            # Debug: Wenn nichts gefunden wurde
            if not found_any:
                print(f"[DEBUG] ❌ Keine Beträge gefunden auf allen Seiten!")

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
