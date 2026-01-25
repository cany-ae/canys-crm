"""
PDF-Datenextraktion für AMIS Pferde-Angebote
Extrahiert: Pferdename, Kundenname, Erstelldatum
"""

import re
from datetime import datetime
from pathlib import Path
import pdfplumber
from typing import Dict, Optional


class PDFExtractor:
    """Extrahiert Daten aus AMIS PDF-Angeboten"""

    def __init__(self, pdf_path: str):
        """
        Initialisiere Extractor

        Args:
            pdf_path: Pfad zur PDF-Datei
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF nicht gefunden: {pdf_path}")

    def extract(self) -> Dict[str, str]:
        """
        Extrahiere alle relevanten Daten aus PDF

        Returns:
            Dictionary mit: horse_name, customer_name, created_date
        """
        with pdfplumber.open(self.pdf_path) as pdf:
            # Gesamten Text aus allen Seiten extrahieren
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"

            # Daten extrahieren
            data = {
                "horse_name": self._extract_horse_name(full_text),
                "customer_name": self._extract_customer_name(full_text),
                "created_date": self._extract_date(full_text)
            }

            return data

    def _extract_horse_name(self, text: str) -> str:
        """
        Extrahiere Pferdename

        Sucht nach Mustern wie:
        - "Pferdename: XXX"
        - "Name des Pferdes: XXX"
        - "Pferd: XXX"
        """
        patterns = [
            r"Pferdename:\s*(.+?)(?:\n|$)",
            r"Name des Pferdes:\s*(.+?)(?:\n|$)",
            r"Pferd:\s*(.+?)(?:\n|$)",
            r"Tier:\s*(.+?)(?:\n|$)",
            r"Versichertes Pferd:\s*(.+?)(?:\n|$)"
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                name = match.group(1).strip()
                # Bereinige Name (entferne Sonderzeichen am Ende)
                name = re.sub(r'[,;:.]$', '', name).strip()
                if name:
                    return name

        return "Nicht gefunden"

    def _extract_customer_name(self, text: str) -> str:
        """
        Extrahiere Kundenname

        Sucht nach Mustern wie:
        - "Versicherungsnehmer: XXX"
        - "Kunde: XXX"
        - "Antragsteller: XXX"
        """
        patterns = [
            r"Versicherungsnehmer:\s*(.+?)(?:\n|$)",
            r"Kunde:\s*(.+?)(?:\n|$)",
            r"Antragsteller:\s*(.+?)(?:\n|$)",
            r"Name:\s*(.+?)(?:\n|$)",
            r"Halter:\s*(.+?)(?:\n|$)"
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                name = match.group(1).strip()
                # Bereinige Name
                name = re.sub(r'[,;:.]$', '', name).strip()
                if name and len(name) > 2:  # Mindestens 3 Zeichen
                    return name

        return "Nicht gefunden"

    def _extract_date(self, text: str) -> str:
        """
        Extrahiere Erstelldatum

        Sucht nach Mustern wie:
        - "Datum: DD.MM.YYYY"
        - "Erstellt am: DD.MM.YYYY"
        - DD.MM.YYYY Format
        """
        patterns = [
            r"Datum:\s*(\d{1,2}\.\d{1,2}\.\d{4})",
            r"Erstellt am:\s*(\d{1,2}\.\d{1,2}\.\d{4})",
            r"Angebotsdatum:\s*(\d{1,2}\.\d{1,2}\.\d{4})",
            r"vom\s+(\d{1,2}\.\d{1,2}\.\d{4})",
            r"(\d{1,2}\.\d{1,2}\.\d{4})"  # Fallback: Jedes Datum
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                date_str = match.group(1).strip()
                # Validiere Datum
                if self._validate_date(date_str):
                    return date_str

        # Fallback: Heutiges Datum
        return datetime.now().strftime("%d.%m.%Y")

    def _validate_date(self, date_str: str) -> bool:
        """
        Validiere Datum im Format DD.MM.YYYY

        Args:
            date_str: Datum als String

        Returns:
            True wenn gültig
        """
        try:
            datetime.strptime(date_str, "%d.%m.%Y")
            return True
        except ValueError:
            return False

    def get_text_preview(self, max_chars: int = 500) -> str:
        """
        Hole Text-Vorschau aus PDF (für Debugging)

        Args:
            max_chars: Maximale Anzahl Zeichen

        Returns:
            Text-Vorschau
        """
        with pdfplumber.open(self.pdf_path) as pdf:
            if pdf.pages:
                text = pdf.pages[0].extract_text()
                return text[:max_chars] if text else "Kein Text gefunden"
        return "Keine Seiten gefunden"
