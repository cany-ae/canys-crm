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
                "created_date": self._extract_date(full_text),
                "beitrag": self._extract_beitrag(full_text)  # 10% Selbstbeteiligung aus AMIS
            }

            return data

    def _extract_horse_name(self, text: str) -> str:
        """
        Extrahiere Pferdename

        Sucht nach Mustern wie:
        - "Pferdename: XXX"
        - "Name des Pferdes: XXX"
        - "Pferd, Rasse: XXX" (AMIS-spezifisch)
        """
        # AMIS-spezifisches Muster: "Pferd, Rasse: Name"
        amis_pattern = r"Pferd[,\s]*Rasse:\s*([^,\n]+)"
        match = re.search(amis_pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            name = match.group(1).strip()
            # Bereinige Name
            name = re.sub(r'[,;:.]$', '', name).strip()
            # Entferne "Geburtsdatum:" falls vorhanden
            name = re.split(r',\s*Geburtsdatum', name)[0].strip()
            if name:
                return name

        # Standard-Patterns
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
        - "Für\nHerr\nName" (AMIS-spezifisch)
        """
        # AMIS-spezifisches Muster: Zeile nach "Herr" oder "Frau"
        # WICHTIG: Nur den ERSTEN Treffer nach "Für" verwenden (= Kunde)
        # um Vertriebler/Vermittler zu ignorieren
        lines = text.split('\n')

        # Suche nach "Für" und dann nach erstem "Herr" oder "Frau"
        found_fuer = False
        for i, line in enumerate(lines):
            # Markiere dass wir im Kundenbereich sind
            if re.search(r'\bFür\b', line, re.IGNORECASE):
                found_fuer = True
                continue

            # Nur nach "Für" suchen wir nach Herr/Frau
            if found_fuer and re.search(r'\b(Herr|Frau)\b', line, re.IGNORECASE):
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()

                    # Verbesserter Regex - GENAU 2 Wörter (Vorname + Nachname)
                    # Erlaubt: Buchstaben, Umlaute, Bindestriche, Apostrophe
                    # Verhindert dass "Samet Uz Im Bühl" vollständig gematcht wird
                    name_match = re.match(
                        r'^([A-ZÄÖÜ][a-zäöüß\-\']+)\s+([A-ZÄÖÜ][a-zäöüß\-\']+)(?:\s|$)',
                        next_line
                    )

                    if name_match:
                        # Kombiniere Vorname (Gruppe 1) + Nachname (Gruppe 2)
                        vorname = name_match.group(1).strip()
                        nachname = name_match.group(2).strip()
                        name = f"{vorname} {nachname}"

                        if name and len(name) > 2:
                            return name

                    # Fallback: Wenn der Regex nicht passt, versuche einfachere Extraktion
                    # Nehme NUR die ersten 2 Wörter die mit Großbuchstaben beginnen
                    # (= Vorname + Nachname, verhindert dass Adresse mitgenommen wird)
                    words = next_line.split()
                    name_words = []
                    for word in words:
                        # Stoppe bei Adresse (Zahlen, "Straße", etc.)
                        if re.match(r'^\d', word) or word.lower() in ['straße', 'str.', 'platz', 'weg', 'im', 'am', 'an', 'der', 'die', 'das']:
                            break
                        # Sammle Wörter die mit Großbuchstaben beginnen
                        if re.match(r'^[A-ZÄÖÜ]', word):
                            name_words.append(word)
                            # Maximal 2 Wörter (Vorname + Nachname)
                            if len(name_words) >= 2:
                                break

                    if len(name_words) == 2:  # Genau 2 Wörter = Vorname + Nachname
                        name = ' '.join(name_words)
                        # Normalisiere Leerzeichen
                        name = re.sub(r'\s+', ' ', name).strip()
                        if len(name) > 2:
                            return name

                    # Stoppe nach erstem Herr/Frau Treffer (auch wenn kein Name gefunden)
                    break

        # Standard-Patterns
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
                # Normalisiere Leerzeichen
                name = re.sub(r'\s+', ' ', name)
                if name and len(name) > 2:  # Mindestens 3 Zeichen
                    return name

        return "Nicht gefunden"

    def _extract_date(self, text: str) -> str:
        """
        Extrahiere Erstelldatum

        Sucht nach Mustern wie:
        - "Datum: DD.MM.YYYY"
        - "vom DD.MM.YYYY"
        - DD.MM.YYYY Format
        """
        patterns = [
            r"vom\s+(\d{1,2}\.\d{1,2}\.\d{4})",  # AMIS: "vom 25.01.2026"
            r"Versicherungsvorschlag vom\s+(\d{1,2}\.\d{1,2}\.\d{4})",
            r"Datum:\s*(\d{1,2}\.\d{1,2}\.\d{4})",
            r"Erstellt am:\s*(\d{1,2}\.\d{1,2}\.\d{4})",
            r"Angebotsdatum:\s*(\d{1,2}\.\d{1,2}\.\d{4})",
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

    def _extract_beitrag(self, text: str) -> str:
        """
        Extrahiere Beitrag (10% Selbstbeteiligung) aus AMIS-PDF

        Sucht nach dem Bereich "Beitrag" und extrahiert den ersten Betrag darunter.
        Format im AMIS-PDF:
        - "Beitrag" als Überschrift
        - "240,20 EUR" als Betrag darunter
        """
        # Zuerst: Suche nach "Beitrag" gefolgt von Betrag mit EUR (AMIS-Format)
        # Das Format ist: "Beitrag\n240,20 EUR" oder "Beitrag\n240,20 EUR\nmonatlich"
        amis_patterns = [
            # "Beitrag" gefolgt von Zeilenumbruch und Betrag mit EUR
            r"Beitrag\s*\n\s*(\d{1,3}(?:\.\d{3})*,\d{2})\s*EUR",
            # "Beitrag" mit optionalem Doppelpunkt und Betrag mit EUR auf gleicher/nächster Zeile
            r"Beitrag[:\s]*(\d{1,3}(?:\.\d{3})*,\d{2})\s*EUR",
        ]

        for pattern in amis_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                beitrag = match.group(1).strip()
                return f"{beitrag} €"

        # Fallback: Alte Patterns mit € Symbol
        fallback_patterns = [
            r"Beitrag[:\s]*(\d{1,3}(?:\.\d{3})*,\d{2})\s*€",
            r"Beitrag[:\s]*(\d{1,3}(?:\.\d{3})*,\d{2})",
            r"Jahresbeitrag[:\s]*(\d{1,3}(?:\.\d{3})*,\d{2})\s*€",
            r"Gesamtbeitrag[:\s]*(\d{1,3}(?:\.\d{3})*,\d{2})\s*€",
        ]

        for pattern in fallback_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                beitrag = match.group(1).strip()
                return f"{beitrag} €"

        return ""

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
