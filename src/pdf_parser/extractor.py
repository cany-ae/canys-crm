"""
PDF-Datenextraktion für AMIS Pferde-Angebote
Extrahiert: Pferdename, Kundenname, Erstelldatum, Pferderasse, Beitrag
Integriert KI-gestützte Rasseninformationen via Groq API
Kombinierte Version: Beitrag + KI-Rasseinfo
"""

import re
from datetime import datetime
from pathlib import Path
import pdfplumber
from typing import Dict, Optional
import sys
import os

# Import AI Module für Rassenabfrage
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
try:
    from ai import query_horse_breed
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("⚠️ Groq AI nicht verfügbar - installiere 'groq' package")


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

    def extract(self, fetch_breed_info: bool = True) -> Dict[str, str]:
        """
        Extrahiere alle relevanten Daten aus PDF

        Args:
            fetch_breed_info: Wenn True, werden automatisch KI-Infos zur Rasse abgerufen

        Returns:
            Dictionary mit: horse_name, customer_name, created_date, horse_breed, breed_info, beitrag
        """
        with pdfplumber.open(self.pdf_path) as pdf:
            # Gesamten Text aus allen Seiten extrahieren
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"

            # Daten extrahieren
            horse_name = self._extract_horse_name(full_text)
            horse_breed = self._extract_horse_breed(full_text)

            data = {
                "horse_name": horse_name,
                "customer_name": self._extract_customer_name(full_text),
                "created_date": self._extract_date(full_text),
                "horse_breed": horse_breed,
                "breed_info": None,
                "beitrag": self._extract_beitrag(full_text)  # 10% Selbstbeteiligung aus AMIS
            }

            # KI-gestützte Rasseninformationen abrufen
            if fetch_breed_info and AI_AVAILABLE and horse_breed != "Nicht gefunden":
                try:
                    print(f"🤖 Frage KI nach Infos zu Rasse: {horse_breed}")
                    breed_data = query_horse_breed(horse_breed, horse_name)
                    data["breed_info"] = breed_data.get("info", "Keine Infos verfügbar")
                except Exception as e:
                    print(f"⚠️ KI-Abfrage fehlgeschlagen: {str(e)}")
                    data["breed_info"] = "Fehler bei Rasseninformationen"

            return data

    def _extract_horse_name(self, text: str) -> str:
        """
        Extrahiere Pferdename

        Sucht nach Mustern wie:
        - "Pferdename: XXX"
        - "Name des Pferdes: XXX"
        """
        patterns = [
            r"Pferdename:\s*(.+?)(?:\n|$)",
            r"Name des Pferdes:\s*(.+?)(?:\n|$)",
            r"Pferd:\s*(.+?)(?:,|Rasse|\n|$)",  # Stoppt vor Komma oder "Rasse"
            r"Tier:\s*([^,\n]+?)(?:,|Rasse|\n|$)",  # Stoppt vor Komma oder "Rasse"
            r"Versichertes Pferd:\s*(.+?)(?:\n|$)"
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                name = match.group(1).strip()
                # Bereinige Name (entferne Sonderzeichen am Ende)
                name = re.sub(r'[,;:.]$', '', name).strip()
                # Entferne "Geburtsdatum:" falls vorhanden
                name = re.split(r',?\s*Geburtsdatum', name)[0].strip()
                # Verhindere dass Rasse extrahiert wird
                if name and len(name) > 1 and not name.lower().startswith('rasse'):
                    return name

        return "Nicht gefunden"

    def _extract_horse_breed(self, text: str) -> str:
        """
        Extrahiere Pferderasse

        Sucht nach Mustern wie:
        - "Rasse: XXX"
        - "Pferd, Rasse: XXX" (AMIS-spezifisch)
        - "Tier: Pferd, Rasse: XXX, Geburtsdatum"
        """
        # AMIS-spezifisches Muster: "Rasse: Achal Tekkiner"
        # Extrahiert Text zwischen "Rasse:" und dem nächsten Komma/Zeilenumbruch
        patterns = [
            r"Rasse:\s*([^,\n]+?)(?:,|\n|Geburtsdatum)",  # Stoppt vor Komma oder "Geburtsdatum"
            r"Rasse:\s*([^,\n]+)",  # Fallback: Bis Komma oder Zeilenumbruch
            r"Pferderasse:\s*([^,\n]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                breed = match.group(1).strip()
                # Bereinige Rasse (entferne trailing Sonderzeichen)
                breed = re.sub(r'[,;:.]$', '', breed).strip()
                # Entferne eventuelle Zusatzinfos in Klammern
                breed = re.split(r'\s*\(', breed)[0].strip()
                if breed and len(breed) > 2:
                    return breed

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

        Das AMIS-PDF hat eine Tabelle mit:
        - Spalte "Beitrag" als Überschrift
        - Wert wie "240,20 EUR" in der Zeile darunter

        Die Textextraktion kann unterschiedlich sein, daher mehrere Patterns.
        """
        # Pattern 1: Suche nach "XXX,XX EUR" direkt nach "Beitrag" (mit beliebigem Text dazwischen)
        # Das erfasst Tabellen-Layouts wo Beitrag als Header steht
        amis_patterns = [
            # "Beitrag" gefolgt von Betrag mit EUR (mit beliebigem Text dazwischen, aber nicht zu viel)
            r"Beitrag\s*\n?\s*(\d{1,3}(?:\.\d{3})*,\d{2})\s*EUR",
            # Tabellen-Format: Nach "Beitrag" kommt irgendwann "XXX,XX EUR"
            r"Beitrag.*?(\d{1,3}(?:\.\d{3})*,\d{2})\s*EUR",
            # Gesamtbeitrag Format
            r"Gesamtbeitrag.*?(\d{1,3}(?:\.\d{3})*,\d{2})\s*EUR",
        ]

        for pattern in amis_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                beitrag = match.group(1).strip()
                return f"{beitrag} €"

        # Pattern 2: Suche einfach nach dem ersten "XXX,XX EUR" im Dokument
        # (AMIS PDFs haben typischerweise den Beitrag als ersten EUR-Betrag)
        eur_pattern = r"(\d{1,3}(?:\.\d{3})*,\d{2})\s*EUR"
        match = re.search(eur_pattern, text, re.IGNORECASE)
        if match:
            beitrag = match.group(1).strip()
            return f"{beitrag} €"

        # Fallback: Patterns mit € Symbol
        fallback_patterns = [
            r"Beitrag[:\s]*(\d{1,3}(?:\.\d{3})*,\d{2})\s*€",
            r"(\d{1,3}(?:\.\d{3})*,\d{2})\s*€",
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
