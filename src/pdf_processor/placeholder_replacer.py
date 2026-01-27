"""
PDF-Platzhalter-Ersetzung
Ersetzt Platzhalter in der Vorlage-PDF mit echten Daten
Kombinierte Version: Beiträge + KI-Rasseinfo
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
                  Erwartet: vorname, nachname, pferdename, datum, breed_info (optional),
                           beitrag_20, beitrag_10, beitrag_0 (optional)

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
            "{{RASSEINFO}}": data.get("breed_info", "").strip(),  # KI-generierte Rasseinfo
        }

        # Euro-Beträge für Selbstbeteiligung
        # Formatiere Beträge: Entferne € falls vorhanden, füge EUR hinzu
        def format_beitrag(value):
            if not value:
                return ""
            # Entferne € und EUR und Leerzeichen
            clean = value.replace("€", "").replace("EUR", "").replace(" ", "").strip()
            return f"{clean} EUR"  # Format: "243,81 EUR" (EUR statt € wegen Schriftart)

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
        breed_info_inserted = False
        for page_num, page in enumerate(doc):
            for placeholder, value in replacements.items():
                # Suche nach Platzhalter
                text_instances = page.search_for(placeholder)

                for inst in text_instances:
                    # Spezielle Behandlung für mehrzeiligen Rasseinfo-Text
                    if placeholder == "{{RASSEINFO}}" and value:
                        # Mehrzeiligen Text einfügen
                        self._insert_multiline_text(
                            page, inst, value,
                            fontname="helv",
                            font_size=11,
                            line_height=1.4,
                            text_color=(0.2, 0.2, 0.2),  # Dunkelgrau für bessere Lesbarkeit
                            background_color=None  # Kein Hintergrund für Fließtext
                        )
                        breed_info_inserted = True
                        continue

                    # Standard Platzhalter-Ersetzung für kurze Texte
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

            # Farben für Beitrags-Ersetzung
            # Hintergrund: #ddeb3a (221, 235, 58) -> RGB(0.867, 0.922, 0.227)
            beitrag_bg_color = (0.867, 0.922, 0.227)  # Gelb #ddeb3a
            beitrag_text_color = (0.0, 0.0, 0.0)  # Schwarz

            found_any = False

            # Durchsuche ALLE Seiten nach Beträgen
            for page_idx, page in enumerate(doc):
                for old_beitrag, new_beitrag in beitrag_replacements.items():
                    if not new_beitrag:
                        continue

                    # Suche nach altem Betrag
                    text_instances = page.search_for(old_beitrag)
                    if text_instances:
                        print(f"[DEBUG] Seite {page_idx + 1}: '{old_beitrag}' gefunden: {len(text_instances)} Treffer")
                        found_any = True

                    for inst in text_instances:
                        # Berechne Schriftgröße
                        base_font_size = inst.height * 0.65
                        old_rect_width = inst.x1 - inst.x0

                        # Helvetica unterstützt Euro-Zeichen korrekt
                        fontname = "helv"
                        font_size = base_font_size

                        # Optimale Schriftgröße finden
                        while font_size > 9:
                            text_width = fitz.get_text_length(new_beitrag, fontname=fontname, fontsize=font_size)
                            if text_width <= old_rect_width * 0.9:
                                break
                            font_size -= 0.5

                        font_size = max(font_size, 9)

                        # Berechne finale Textbreite
                        text_width = fitz.get_text_length(new_beitrag, fontname=fontname, fontsize=font_size)

                        # Rechteck: Etwas breiter um alten Text zu überdecken
                        right_edge = max(inst.x1 + 10, inst.x0 + text_width + 6)

                        # Rechteck etwas höher um schwarze Striche zu überdecken
                        rect_height = inst.height * 0.9  # 90% der Original-Höhe
                        y_center = (inst.y0 + inst.y1) / 2

                        # Koordinaten für das Rechteck
                        x0 = inst.x0 - 1
                        y0 = y_center - rect_height / 2
                        x1 = right_edge + 2
                        y1 = y_center + rect_height / 2

                        # Radius für runde Ecken (beide Seiten)
                        radius = min(rect_height / 2, 8)  # Max 8px oder halbe Höhe

                        # Zeichne Rechteck mit runden Ecken auf BEIDEN Seiten
                        shape = page.new_shape()

                        # Magic number für perfekte Kreisbogen mit kubischer Bézier
                        k = 0.5522847498 * radius

                        # Pfad: Beide Seiten perfekt abgerundet
                        # Oben (von links nach rechts)
                        shape.draw_line(fitz.Point(x0 + radius, y0), fitz.Point(x1 - radius, y0))
                        # Bogen oben rechts
                        shape.draw_bezier(
                            fitz.Point(x1 - radius, y0),
                            fitz.Point(x1 - radius + k, y0),
                            fitz.Point(x1, y0 + radius - k),
                            fitz.Point(x1, y0 + radius)
                        )
                        # Rechts (von oben nach unten)
                        shape.draw_line(fitz.Point(x1, y0 + radius), fitz.Point(x1, y1 - radius))
                        # Bogen unten rechts
                        shape.draw_bezier(
                            fitz.Point(x1, y1 - radius),
                            fitz.Point(x1, y1 - radius + k),
                            fitz.Point(x1 - radius + k, y1),
                            fitz.Point(x1 - radius, y1)
                        )
                        # Unten (von rechts nach links)
                        shape.draw_line(fitz.Point(x1 - radius, y1), fitz.Point(x0 + radius, y1))
                        # Bogen unten links
                        shape.draw_bezier(
                            fitz.Point(x0 + radius, y1),
                            fitz.Point(x0 + radius - k, y1),
                            fitz.Point(x0, y1 - radius + k),
                            fitz.Point(x0, y1 - radius)
                        )
                        # Links (von unten nach oben)
                        shape.draw_line(fitz.Point(x0, y1 - radius), fitz.Point(x0, y0 + radius))
                        # Bogen oben links
                        shape.draw_bezier(
                            fitz.Point(x0, y0 + radius),
                            fitz.Point(x0, y0 + radius - k),
                            fitz.Point(x0 + radius - k, y0),
                            fitz.Point(x0 + radius, y0)
                        )

                        shape.finish(fill=beitrag_bg_color, color=beitrag_bg_color)
                        shape.commit()

                        # Text zentriert im Rechteck
                        text_y = y_center + font_size * 0.35

                        page.insert_text(
                            (inst.x0 + 2, text_y),
                            new_beitrag,
                            fontname=fontname,
                            fontsize=font_size,
                            color=beitrag_text_color
                        )

            # Debug: Wenn nichts gefunden wurde
            if not found_any:
                print(f"[DEBUG] Keine Beträge gefunden auf allen Seiten!")

        # Falls kein Platzhalter gefunden wurde, aber breed_info vorhanden ist,
        # füge Text als horizontales Banner ein (Premium Side Banner Design)
        breed_info_text = data.get("breed_info", "").strip()
        if not breed_info_inserted and breed_info_text and len(doc) >= 1:
            page = doc[0]  # Seite 1 (0-indexed)
            page_height = page.rect.height
            page_width = page.rect.width

            # MODERNES BANNER-DESIGN: links unten, rund, dynamisch, ohne XP-Kasten

            # DIMENSIONEN (nur linke Seite)
            banner_width = min(330, page_width * 0.42)
            banner_padding_h = 18
            banner_padding_v = 16
            margin_left = 20  # Weiter links positioniert
            margin_bottom = 55

            # LOOK
            corner_radius = 14
            shadow_offset = 6  # etwas mehr Abstand wirkt natürlicher

            # FARBEN
            banner_bg_color = (0.855, 0.937, 0.980)  # #DAEFFA
            title_color = (0.0, 0.325, 0.6)  # #005399 (wie Platzhalter)
            banner_text_color = (0.0, 0.325, 0.6)  # #005399 (wie Platzhalter)

            # TYPO
            title_font = "helv"
            title_size = 8                # 7 ist zu klein/technisch
            text_font = "helv"
            text_size = 10                # wirkt wertiger
            line_height_px = text_size * 1.45

            # Position links unten (y wird NACH Höhe berechnet)
            x_start = margin_left

            # Wrap Text (OHNE hard lines[:3] – sonst nie dynamisch)
            max_text_width = banner_width - (2 * banner_padding_h)
            lines = self._wrap_text(breed_info_text, text_font, text_size, max_text_width)

            # Optional: begrenze nur, damit das Motiv nicht komplett verdeckt wird
            max_lines = 7
            if len(lines) > max_lines:
                lines = lines[:max_lines]
                # Ellipsis auf letzte Zeile
                if len(lines[-1]) > 3:
                    lines[-1] = lines[-1].rstrip(".") + " ..."

            # Dynamische Höhe berechnen
            title_block_h = title_size + 12
            text_block_h = len(lines) * line_height_px
            banner_height = banner_padding_v + title_block_h + text_block_h + banner_padding_v

            y_start = page_height - banner_height - margin_bottom

            banner_rect = fitz.Rect(x_start, y_start, x_start + banner_width, y_start + banner_height)

            # Schatten: nur wenn Opacity unterstützt wird – sonst weglassen (kein XP-Style!)
            shadow_rect = fitz.Rect(
                banner_rect.x0 + shadow_offset,
                banner_rect.y0 + shadow_offset,
                banner_rect.x1 + shadow_offset,
                banner_rect.y1 + shadow_offset
            )

            shadow_drawn = False
            try:
                self._draw_rounded_rect(page, shadow_rect, corner_radius, fill=(0, 0, 0), fill_opacity=0.12)
                shadow_drawn = True
            except (TypeError, AttributeError):
                shadow_drawn = False  # kein Fallback mit grauem Block, sonst wieder XP

            # Card (runde Ecken!)
            try:
                self._draw_rounded_rect(page, banner_rect, corner_radius, fill=banner_bg_color)
            except AttributeError:
                # Fallback: Rechteck ohne runde Ecken
                page.draw_rect(banner_rect, color=banner_bg_color, fill=banner_bg_color)

            # Optional: subtiler Highlight-Layer oben (macht's „modern")
            hl_rect = fitz.Rect(banner_rect.x0 + 12, banner_rect.y0 + 10, banner_rect.x1 - 12, banner_rect.y0 + 34)
            try:
                page.draw_rect(hl_rect, fill=(1, 1, 1), color=(1, 1, 1), fill_opacity=0.18, stroke_opacity=0)
            except TypeError:
                pass

            # Titel: "Über [Pferdename]"
            pferdename = data.get("pferdename", "")
            title_text = f"Über {pferdename}" if pferdename else "Rasseportrait"
            title_x = banner_rect.x0 + banner_padding_h
            title_y = banner_rect.y0 + banner_padding_v + title_size
            page.insert_text((title_x, title_y), title_text, fontname=title_font, fontsize=title_size, color=title_color)

            # Text
            y_pos = title_y + 14
            for line in lines:
                if y_pos > banner_rect.y1 - banner_padding_v:
                    break
                page.insert_text((title_x, y_pos), line, fontname=text_font, fontsize=text_size, color=banner_text_color)
                y_pos += line_height_px

        # Speichere neue PDF
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(output_path))
        doc.close()

        return str(output_path)

    def _insert_multiline_text(self, page, rect, text, fontname="helv", font_size=11,
                               line_height=1.4, text_color=(0, 0, 0), background_color=None):
        """
        Füge mehrzeiligen Text in ein Rechteck ein (bei Platzhalter)

        Args:
            page: PDF-Seite
            rect: Rechteck (fitz.Rect) des Platzhalters
            text: Einzufügender Text
            fontname: Schriftart
            font_size: Schriftgröße
            line_height: Zeilenhöhe (Multiplikator)
            text_color: RGB Tuple (0-1 Bereich)
            background_color: RGB Tuple oder None
        """
        if background_color:
            page.draw_rect(rect, color=background_color, fill=background_color)

        # Berechne maximale Breite
        max_width = rect.x1 - rect.x0 - 10  # 5pt Rand links+rechts

        # Text in Zeilen aufbrechen (word wrap)
        lines = self._wrap_text(text, fontname, font_size, max_width)

        # Füge Zeilen ein
        y_position = rect.y0 + font_size
        for line in lines:
            if y_position > rect.y1:  # Nicht über Rechteck-Grenze hinaus
                break

            page.insert_text(
                (rect.x0 + 5, y_position),
                line,
                fontname=fontname,
                fontsize=font_size,
                color=text_color
            )
            y_position += font_size * line_height

    def _wrap_text(self, text, fontname, font_size, max_width):
        """
        Breche Text in Zeilen um (word wrap)

        Args:
            text: Text zum Umbrechen
            fontname: Schriftart
            font_size: Schriftgröße
            max_width: Maximale Breite in Punkten

        Returns:
            Liste von Textzeilen
        """
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            # Teste ob Wort in aktuelle Zeile passt
            test_line = ' '.join(current_line + [word])
            text_width = fitz.get_text_length(test_line, fontname=fontname, fontsize=font_size)

            if text_width <= max_width:
                current_line.append(word)
            else:
                # Zeile ist voll, starte neue Zeile
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]

        # Letzte Zeile hinzufügen
        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def _draw_rounded_rect(self, page, rect, r, fill, fill_opacity=None):
        """
        Rounded rect simulation for PyMuPDF: 2 rects + 4 circles.
        Supports opacity if available in the local PyMuPDF build.
        """
        r = min(r, rect.width / 2, rect.height / 2)

        kwargs = {}
        if fill_opacity is not None:
            kwargs["fill_opacity"] = fill_opacity
            kwargs["stroke_opacity"] = 0

        x0, y0, x1, y1 = rect.x0, rect.y0, rect.x1, rect.y1

        # Core rectangles
        page.draw_rect(fitz.Rect(x0 + r, y0, x1 - r, y1), fill=fill, color=fill, **kwargs)
        page.draw_rect(fitz.Rect(x0, y0 + r, x1, y1 - r), fill=fill, color=fill, **kwargs)

        # Corner circles
        page.draw_circle((x0 + r, y0 + r), r, fill=fill, color=fill, **kwargs)
        page.draw_circle((x1 - r, y0 + r), r, fill=fill, color=fill, **kwargs)
        page.draw_circle((x0 + r, y1 - r), r, fill=fill, color=fill, **kwargs)
        page.draw_circle((x1 - r, y1 - r), r, fill=fill, color=fill, **kwargs)

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
