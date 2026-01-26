"""
PDF-Merger für Angebotserstellung
Fügt PDFs zusammen: Teil1 (2 Seiten) + AMIS Angebot + Teil2 (4 Seiten)
"""

from pathlib import Path
from typing import Optional
from PyPDF2 import PdfReader, PdfWriter


class PDFMerger:
    """Fügt Vertriebler-Template mit AMIS-Angebot zusammen"""

    TEMPLATES_DIR = Path(__file__).parent.parent.parent / "templates"

    # Verfügbare Vertriebler und ihre Template-Ordner
    VERTRIEBLER = {
        "Samet Uz": "samet_uz",
        "Vertriebler 2": "vertriebler_2",
        "Vertriebler 3": "vertriebler_3",
        "Vertriebler 4": "vertriebler_4",
        "Vertriebler 5": "vertriebler_5",
        "Vertriebler 6": "vertriebler_6",
        "Vertriebler 7": "vertriebler_7",
    }

    def __init__(self, vertriebler_name: str):
        """
        Initialisiere Merger

        Args:
            vertriebler_name: Name des Vertrieblers
        """
        self.vertriebler_name = vertriebler_name
        self.template_folder = self._get_template_folder(vertriebler_name)

    def _get_template_folder(self, vertriebler_name: str) -> Path:
        """
        Hole Template-Ordner für Vertriebler

        Args:
            vertriebler_name: Name des Vertrieblers

        Returns:
            Pfad zum Template-Ordner
        """
        folder_name = self.VERTRIEBLER.get(vertriebler_name, "samet_uz")
        return self.TEMPLATES_DIR / folder_name

    def merge(self, amis_pdf_path: str, output_path: str) -> str:
        """
        Füge PDFs zusammen: Teil1 + AMIS + Teil2

        Args:
            amis_pdf_path: Pfad zum AMIS-Angebot PDF
            output_path: Ausgabepfad für fertiges PDF

        Returns:
            Pfad zur erstellten PDF-Datei
        """
        # Template-Dateien
        teil1_path = self.template_folder / "teil1.pdf"
        teil2_path = self.template_folder / "teil2.pdf"

        # Prüfe ob Templates existieren
        if not teil1_path.exists():
            raise FileNotFoundError(f"Template Teil 1 nicht gefunden: {teil1_path}")
        if not teil2_path.exists():
            raise FileNotFoundError(f"Template Teil 2 nicht gefunden: {teil2_path}")
        if not Path(amis_pdf_path).exists():
            raise FileNotFoundError(f"AMIS PDF nicht gefunden: {amis_pdf_path}")

        # PDF Writer erstellen
        writer = PdfWriter()

        # Teil 1 hinzufügen (erste 2 Seiten)
        teil1_reader = PdfReader(str(teil1_path))
        for page in teil1_reader.pages:
            writer.add_page(page)

        # AMIS Angebot hinzufügen (alle Seiten)
        amis_reader = PdfReader(amis_pdf_path)
        for page in amis_reader.pages:
            writer.add_page(page)

        # Teil 2 hinzufügen (letzte 4 Seiten)
        teil2_reader = PdfReader(str(teil2_path))
        for page in teil2_reader.pages:
            writer.add_page(page)

        # Output-Verzeichnis erstellen
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # PDF speichern
        with open(output_path, "wb") as output_file:
            writer.write(output_file)

        return str(output_path)

    def get_page_info(self, amis_pdf_path: str) -> dict:
        """
        Hole Seiten-Info für Vorschau

        Args:
            amis_pdf_path: Pfad zum AMIS-Angebot PDF

        Returns:
            Dictionary mit Seiten-Infos
        """
        teil1_path = self.template_folder / "teil1.pdf"
        teil2_path = self.template_folder / "teil2.pdf"

        info = {
            "teil1_seiten": 0,
            "amis_seiten": 0,
            "teil2_seiten": 0,
            "gesamt_seiten": 0
        }

        if teil1_path.exists():
            info["teil1_seiten"] = len(PdfReader(str(teil1_path)).pages)

        if Path(amis_pdf_path).exists():
            info["amis_seiten"] = len(PdfReader(amis_pdf_path).pages)

        if teil2_path.exists():
            info["teil2_seiten"] = len(PdfReader(str(teil2_path)).pages)

        info["gesamt_seiten"] = (
            info["teil1_seiten"] +
            info["amis_seiten"] +
            info["teil2_seiten"]
        )

        return info

    @classmethod
    def get_available_vertriebler(cls) -> list:
        """
        Hole Liste der verfügbaren Vertriebler (mit Templates)

        Returns:
            Liste der Vertriebler-Namen
        """
        available = []
        for name, folder in cls.VERTRIEBLER.items():
            template_path = cls.TEMPLATES_DIR / folder
            teil1 = template_path / "teil1.pdf"
            teil2 = template_path / "teil2.pdf"
            if teil1.exists() and teil2.exists():
                available.append(name)
        return available if available else list(cls.VERTRIEBLER.keys())
