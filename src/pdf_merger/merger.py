"""
PDF-Merger für Angebotserstellung
Fügt PDFs zusammen: Vorlage (2 Seiten) + AMIS Angebot + Endseiten (4 Seiten)
Ersetzt Platzhalter in Vorlage mit Daten aus AMIS-PDF
"""

from pathlib import Path
from typing import Optional
from PyPDF2 import PdfReader, PdfWriter
import tempfile
import shutil

from pdf_parser.extractor import PDFExtractor
from pdf_processor.placeholder_replacer import PlaceholderReplacer


class PDFMerger:
    """Fügt Vertriebler-Template mit AMIS-Angebot zusammen"""

    def __init__(self, template_path: str):
        """
        Initialisiere Merger

        Args:
            template_path: Pfad zur Vertriebler-Vorlage (PDF)
        """
        self.template_path = Path(template_path)
        if not self.template_path.exists():
            raise FileNotFoundError(f"Vorlage nicht gefunden: {template_path}")

    def merge(self, amis_pdf_path: str, output_path: str, replace_placeholders: bool = True, pferdename: str = None, beitraege: dict = None) -> str:
        """
        Füge PDFs zusammen: Vorlage + AMIS
        Optional: Ersetze Platzhalter in Vorlage mit Daten aus AMIS-PDF

        Args:
            amis_pdf_path: Pfad zum AMIS-Angebot PDF
            output_path: Ausgabepfad für fertiges PDF
            replace_placeholders: Ob Platzhalter ersetzt werden sollen (Standard: True)
            pferdename: Optional: Pferdename für Platzhalter
            beitraege: Optional: Dict mit beitrag_20, beitrag_10, beitrag_0

        Returns:
            Pfad zur erstellten PDF-Datei
        """
        # Prüfe ob AMIS PDF existiert
        if not Path(amis_pdf_path).exists():
            raise FileNotFoundError(f"AMIS PDF nicht gefunden: {amis_pdf_path}")

        # Platzhalter ersetzen falls gewünscht
        vorlage_to_use = self.template_path
        temp_dir = None

        if replace_placeholders:
            try:
                # Extrahiere Daten aus AMIS-PDF
                extractor = PDFExtractor(amis_pdf_path)
                extracted_data = extractor.extract()

                # Bereite Daten für Platzhalter vor
                placeholder_data = PlaceholderReplacer.prepare_data_from_extraction(extracted_data)

                # Füge Pferdename hinzu falls vorhanden
                if pferdename:
                    placeholder_data['pferdename'] = pferdename

                # Füge Beiträge und KI-Rasseinfo hinzu falls vorhanden
                if beitraege:
                    placeholder_data['beitrag_20'] = beitraege.get('beitrag_20', '')
                    placeholder_data['beitrag_10'] = beitraege.get('beitrag_10', '')
                    placeholder_data['beitrag_0'] = beitraege.get('beitrag_0', '')
                    placeholder_data['breed_info'] = beitraege.get('breed_info', '')

                # Erstelle temporäre Kopie von Vorlage mit ersetzten Platzhaltern
                temp_dir = tempfile.mkdtemp()
                temp_vorlage = Path(temp_dir) / "vorlage_filled.pdf"

                replacer = PlaceholderReplacer(str(self.template_path))
                replacer.replace_placeholders(str(temp_vorlage), placeholder_data)

                vorlage_to_use = temp_vorlage

            except Exception as e:
                # Falls Platzhalter-Ersetzung fehlschlägt, nutze Original
                print(f"Warnung: Platzhalter-Ersetzung fehlgeschlagen: {e}")
                vorlage_to_use = self.template_path

        # PDF Writer erstellen
        writer = PdfWriter()

        # Vorlage lesen
        vorlage_reader = PdfReader(str(vorlage_to_use))
        total_vorlage_pages = len(vorlage_reader.pages)

        # Erste 2 Seiten der Vorlage hinzufügen
        for i in range(min(2, total_vorlage_pages)):
            writer.add_page(vorlage_reader.pages[i])

        # AMIS Angebot hinzufügen (alle Seiten)
        amis_reader = PdfReader(amis_pdf_path)
        for page in amis_reader.pages:
            writer.add_page(page)

        # Restliche Seiten der Vorlage hinzufügen (ab Seite 3)
        if total_vorlage_pages > 2:
            for i in range(2, total_vorlage_pages):
                writer.add_page(vorlage_reader.pages[i])

        # Output-Verzeichnis erstellen
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # PDF speichern
        with open(output_path, "wb") as output_file:
            writer.write(output_file)

        # Temporäres Verzeichnis aufräumen
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass

        return str(output_path)

    def get_page_info(self, amis_pdf_path: str) -> dict:
        """
        Hole Seiten-Info für Vorschau

        Args:
            amis_pdf_path: Pfad zum AMIS-Angebot PDF

        Returns:
            Dictionary mit Seiten-Infos
        """
        info = {
            "vorlage_seiten_teil1": 0,  # Erste 2 Seiten vor AMIS
            "amis_seiten": 0,
            "vorlage_seiten_teil2": 0,  # Restliche Seiten nach AMIS
            "gesamt_seiten": 0
        }

        if self.template_path.exists():
            total_vorlage_pages = len(PdfReader(str(self.template_path)).pages)
            # Erste 2 Seiten
            info["vorlage_seiten_teil1"] = min(2, total_vorlage_pages)
            # Restliche Seiten (ab Seite 3)
            info["vorlage_seiten_teil2"] = max(0, total_vorlage_pages - 2)

        if Path(amis_pdf_path).exists():
            info["amis_seiten"] = len(PdfReader(amis_pdf_path).pages)

        info["gesamt_seiten"] = (
            info["vorlage_seiten_teil1"] +
            info["amis_seiten"] +
            info["vorlage_seiten_teil2"]
        )

        return info
