"""
PowerPoint-Generator für Angebote
Nutzt Templates für 7 verschiedene Vertriebler
"""

from pathlib import Path
from typing import Dict
from pptx import Presentation
from pptx.util import Pt, Cm
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
import os


class PPTXGenerator:
    """Generiert PowerPoint-Angebote aus Templates"""

    # Template-Pfade für 7 Vertriebler
    TEMPLATE_DIR = Path(__file__).parent.parent.parent / "templates"

    def __init__(self, vertriebler_name: str):
        """
        Initialisiere Generator

        Args:
            vertriebler_name: Name des Vertrieblers (1-7)
        """
        self.vertriebler_name = vertriebler_name
        self.template_path = self._get_template_path(vertriebler_name)

    def _get_template_path(self, vertriebler_name: str) -> Path:
        """
        Hole Template-Pfad für Vertriebler

        Args:
            vertriebler_name: Name des Vertrieblers

        Returns:
            Pfad zum Template
        """
        # Extrahiere Nummer aus Namen (z.B. "Vertriebler 3" -> "3")
        import re
        match = re.search(r'\d+', vertriebler_name)
        if match:
            number = match.group()
            template_file = self.TEMPLATE_DIR / f"template_vertriebler_{number}.pptx"
        else:
            template_file = self.TEMPLATE_DIR / "template_default.pptx"

        return template_file

    def generate(self, data: Dict[str, str], output_path: str) -> str:
        """
        Generiere PowerPoint-Angebot

        Args:
            data: Dictionary mit horse_name, customer_name, created_date
            output_path: Ausgabepfad für PPTX

        Returns:
            Pfad zur erstellten PPTX-Datei
        """
        # Template laden oder neue Präsentation erstellen
        if self.template_path.exists():
            prs = Presentation(str(self.template_path))
        else:
            prs = Presentation()
            # Erstelle Standard-Folie
            self._create_default_slide(prs, data)

        # Ersetze Platzhalter in allen Folien
        self._replace_placeholders(prs, data)

        # Speichere Präsentation
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        prs.save(str(output_path))

        return str(output_path)

    def _create_default_slide(self, prs: Presentation, data: Dict[str, str]):
        """
        Erstelle Standard-Folie wenn kein Template vorhanden

        Args:
            prs: Presentation-Objekt
            data: Daten Dictionary
        """
        # Layout auswählen (Titel-Slide)
        blank_slide_layout = prs.slide_layouts[6]  # Leeres Layout
        slide = prs.slides.add_slide(blank_slide_layout)

        # Titel
        left = top = Cm(2)
        width = Cm(20)
        height = Cm(2)
        title_box = slide.shapes.add_textbox(left, top, width, height)
        title_frame = title_box.text_frame
        title_frame.text = "🐴 AMIS Pferde-Versicherung"

        p = title_frame.paragraphs[0]
        p.font.size = Pt(32)
        p.font.bold = True
        p.font.color.rgb = RGBColor(0, 102, 204)  # Blau
        p.alignment = PP_ALIGN.CENTER

        # Daten
        data_top = Cm(6)
        data_left = Cm(4)
        data_width = Cm(16)
        data_height = Cm(8)

        data_box = slide.shapes.add_textbox(data_left, data_top, data_width, data_height)
        data_frame = data_box.text_frame

        # Füge Daten hinzu
        lines = [
            f"Pferdename: {data.get('horse_name', 'N/A')}",
            "",
            f"Kunde: {data.get('customer_name', 'N/A')}",
            "",
            f"Erstelldatum: {data.get('created_date', 'N/A')}",
            "",
            "",
            "Preisfelder (manuell ausfüllen):",
            "",
            "□ Preis 1: _________________€",
            "",
            "□ Preis 2: _________________€",
            "",
            "□ Preis 3: _________________€"
        ]

        for i, line in enumerate(lines):
            if i > 0:
                data_frame.add_paragraph()
            p = data_frame.paragraphs[i]
            p.text = line
            p.font.size = Pt(16)

            # Gelbe Markierung für Preisfelder
            if "Preis" in line and "□" in line:
                run = p.runs[0]
                run.font.bold = True
                # Hinweis: Gelbe Hintergrundfarbe muss manuell im Template gesetzt werden

    def _replace_placeholders(self, prs: Presentation, data: Dict[str, str]):
        """
        Ersetze Platzhalter in allen Folien und Shapes

        Args:
            prs: Presentation-Objekt
            data: Daten Dictionary
        """
        # Platzhalter-Mapping
        replacements = {
            "{{PFERDENAME}}": data.get("horse_name", ""),
            "{{KUNDE}}": data.get("customer_name", ""),
            "{{DATUM}}": data.get("created_date", ""),
            "{{VERTRIEBLER}}": self.vertriebler_name,

            # Alternative Schreibweisen
            "{{HORSE_NAME}}": data.get("horse_name", ""),
            "{{CUSTOMER_NAME}}": data.get("customer_name", ""),
            "{{DATE}}": data.get("created_date", "")
        }

        # Durchlaufe alle Folien
        for slide in prs.slides:
            # Durchlaufe alle Shapes
            for shape in slide.shapes:
                if hasattr(shape, "text_frame"):
                    self._replace_in_textframe(shape.text_frame, replacements)

                # Tabellen durchsuchen
                if hasattr(shape, "table"):
                    table = shape.table
                    for row in table.rows:
                        for cell in row.cells:
                            self._replace_in_textframe(cell.text_frame, replacements)

    def _replace_in_textframe(self, text_frame, replacements: Dict[str, str]):
        """
        Ersetze Platzhalter in einem TextFrame

        Args:
            text_frame: TextFrame-Objekt
            replacements: Dictionary mit Ersetzungen
        """
        for paragraph in text_frame.paragraphs:
            for run in paragraph.runs:
                for placeholder, value in replacements.items():
                    if placeholder in run.text:
                        run.text = run.text.replace(placeholder, value)

    def create_template(self, vertriebler_name: str, output_path: str = None) -> str:
        """
        Erstelle ein Basis-Template für einen Vertriebler

        Args:
            vertriebler_name: Name des Vertrieblers
            output_path: Optionaler Ausgabepfad

        Returns:
            Pfad zum erstellten Template
        """
        if output_path is None:
            # Extrahiere Nummer
            import re
            match = re.search(r'\d+', vertriebler_name)
            number = match.group() if match else "default"
            output_path = self.TEMPLATE_DIR / f"template_vertriebler_{number}.pptx"

        # Neue Präsentation
        prs = Presentation()

        # Erstelle Beispiel-Folie mit Platzhaltern
        blank_layout = prs.slide_layouts[6]
        slide = prs.slides.add_slide(blank_layout)

        # Titel
        title_box = slide.shapes.add_textbox(Cm(2), Cm(1), Cm(20), Cm(2))
        title_frame = title_box.text_frame
        title_frame.text = f"Angebot - {vertriebler_name}"
        p = title_frame.paragraphs[0]
        p.font.size = Pt(32)
        p.font.bold = True
        p.font.color.rgb = RGBColor(0, 102, 204)
        p.alignment = PP_ALIGN.CENTER

        # Inhalts-Box mit Platzhaltern
        content_box = slide.shapes.add_textbox(Cm(3), Cm(4), Cm(18), Cm(12))
        content_frame = content_box.text_frame

        lines = [
            "AMIS Pferde-Versicherung",
            "",
            "Pferdename: {{PFERDENAME}}",
            "Kunde: {{KUNDE}}",
            "Datum: {{DATUM}}",
            "",
            "Vertriebler: {{VERTRIEBLER}}",
            "",
            "─────────────────────────",
            "",
            "PREISFELDER (gelb markiert):",
            "",
            "Basis-Schutz:     ____________€",
            "Premium-Schutz:   ____________€",
            "Komplett-Schutz:  ____________€"
        ]

        for i, line in enumerate(lines):
            if i > 0:
                content_frame.add_paragraph()
            p = content_frame.paragraphs[i]
            p.text = line
            p.font.size = Pt(14)

        # Speichere Template
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        prs.save(str(output_path))

        return str(output_path)
