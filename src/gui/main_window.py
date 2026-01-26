"""
Hauptfenster der Angebotstool-Anwendung
PDF-Zusammenführung: Teil1 + AMIS Angebot + Teil2
Farben: Blau-Weiß Theme (Allianz Corporate Design)
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QFileDialog,
    QGroupBox, QMessageBox, QProgressBar, QFrame, QLineEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from pathlib import Path
import os
import subprocess
import sys

from pdf_merger.merger import PDFMerger
from pdf_parser.extractor import PDFExtractor
from pdf_processor.placeholder_replacer import PlaceholderReplacer
from auth.user_manager import UserManager


# Allianz Blau-Weiß Farbschema
COLORS = {
    'primary_blue': '#003781',
    'light_blue': '#0066cc',
    'accent_blue': '#4da6ff',
    'white': '#ffffff',
    'light_gray': '#f5f7fa',
    'border_gray': '#e0e5eb',
    'text_dark': '#1a1a2e',
    'text_gray': '#6b7280',
    'success_green': '#10b981',
    'error_red': '#ef4444'
}

STYLESHEET = f"""
    QMainWindow {{
        background-color: {COLORS['light_gray']};
    }}

    QWidget {{
        font-family: 'Segoe UI', Arial, sans-serif;
    }}

    QGroupBox {{
        background-color: {COLORS['white']};
        border: 3px solid {COLORS['primary_blue']};
        border-radius: 12px;
        margin-top: 20px;
        padding: 20px;
        padding-top: 25px;
        font-size: 16px;
        font-weight: bold;
        color: {COLORS['primary_blue']};
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 8px 20px;
        background-color: {COLORS['primary_blue']};
        color: {COLORS['white']};
        border-radius: 8px;
        margin-left: 15px;
        font-size: 15px;
        font-weight: bold;
    }}

    QComboBox {{
        padding: 14px 18px;
        border: 3px solid {COLORS['light_blue']};
        border-radius: 10px;
        background-color: {COLORS['white']};
        font-size: 15px;
        color: {COLORS['text_dark']};
        min-width: 220px;
        min-height: 25px;
    }}

    QComboBox:hover {{
        border-color: {COLORS['primary_blue']};
        background-color: #f0f7ff;
    }}

    QComboBox::drop-down {{
        border: none;
        padding-right: 18px;
    }}

    QComboBox::down-arrow {{
        image: none;
        border-left: 6px solid transparent;
        border-right: 6px solid transparent;
        border-top: 10px solid {COLORS['primary_blue']};
        margin-right: 12px;
    }}

    QLineEdit {{
        padding: 14px 18px;
        border: 3px solid {COLORS['light_blue']};
        border-radius: 10px;
        background-color: {COLORS['white']};
        font-size: 16px;
        font-weight: 500;
        color: {COLORS['text_dark']};
        min-width: 180px;
        min-height: 25px;
    }}

    QLineEdit:hover {{
        border-color: {COLORS['primary_blue']};
        background-color: #f0f7ff;
    }}

    QLineEdit:focus {{
        border-color: {COLORS['primary_blue']};
        border-width: 3px;
        background-color: #e8f4ff;
    }}

    QLineEdit::placeholder {{
        color: {COLORS['text_gray']};
        font-style: italic;
    }}

    QPushButton {{
        padding: 14px 28px;
        border: none;
        border-radius: 10px;
        font-size: 15px;
        font-weight: bold;
    }}

    QPushButton#primaryBtn {{
        background-color: {COLORS['primary_blue']};
        color: {COLORS['white']};
        min-width: 220px;
        min-height: 55px;
        font-size: 18px;
    }}

    QPushButton#primaryBtn:hover {{
        background-color: {COLORS['light_blue']};
    }}

    QPushButton#primaryBtn:disabled {{
        background-color: {COLORS['border_gray']};
        color: {COLORS['text_gray']};
    }}

    QPushButton#secondaryBtn {{
        background-color: {COLORS['white']};
        color: {COLORS['primary_blue']};
        border: 3px solid {COLORS['primary_blue']};
        min-height: 45px;
    }}

    QPushButton#secondaryBtn:hover {{
        background-color: {COLORS['primary_blue']};
        color: {COLORS['white']};
    }}

    QProgressBar {{
        border: none;
        border-radius: 12px;
        background-color: {COLORS['border_gray']};
        height: 24px;
        text-align: center;
    }}

    QProgressBar::chunk {{
        background-color: {COLORS['light_blue']};
        border-radius: 12px;
    }}

    QLabel {{
        color: {COLORS['text_dark']};
        font-size: 14px;
    }}

    QLabel#titleLabel {{
        font-size: 32px;
        font-weight: bold;
        color: {COLORS['primary_blue']};
        padding: 25px;
    }}

    QLabel#subtitleLabel {{
        font-size: 16px;
        color: {COLORS['text_gray']};
        padding-bottom: 25px;
    }}

    QLabel#statusLabel {{
        font-size: 15px;
        color: {COLORS['light_blue']};
        font-weight: bold;
    }}

    QLabel#previewLabel {{
        background-color: {COLORS['white']};
        border: 3px solid {COLORS['border_gray']};
        border-radius: 10px;
        padding: 20px;
        font-size: 14px;
        line-height: 1.8;
        font-family: 'Consolas', 'Courier New', monospace;
    }}

    QLabel#inputLabel {{
        font-size: 15px;
        font-weight: bold;
        color: {COLORS['primary_blue']};
        padding: 5px 0px;
    }}

    QLabel#hintLabel {{
        font-size: 12px;
        color: {COLORS['text_gray']};
        font-style: italic;
        padding: 3px 0px;
    }}
"""


class MergeThread(QThread):
    """Thread für die PDF-Zusammenführung"""
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(int, str)

    def __init__(self, template_path, amis_pdf_path, output_path, pferdename=None, beitraege=None):
        super().__init__()
        self.template_path = template_path
        self.amis_pdf_path = amis_pdf_path
        self.output_path = output_path
        self.pferdename = pferdename
        self.beitraege = beitraege or {}  # Dict mit beitrag_20, beitrag_10, beitrag_0

    def run(self):
        try:
            self.progress.emit(30, "Lade Vorlage...")
            merger = PDFMerger(template_path=self.template_path)

            self.progress.emit(60, "Füge PDFs zusammen...")
            output_path = merger.merge(
                self.amis_pdf_path,
                self.output_path,
                pferdename=self.pferdename,
                beitraege=self.beitraege
            )

            self.progress.emit(100, "Fertig!")
            self.finished.emit(True, output_path)

        except Exception as e:
            self.finished.emit(False, str(e))


class MainWindow(QMainWindow):
    """Hauptfenster - PDF Zusammenführung"""

    # Signals
    logout_requested = pyqtSignal()

    def __init__(self, user: dict):
        super().__init__()
        self.user = user  # Eingeloggter User
        self.user_manager = UserManager()
        self.amis_pdf_path = None
        self.merge_thread = None
        self.extracted_data = None  # Extrahierte Daten aus AMIS-PDF
        self.pferdename_input = None  # Eingabefeld für Pferdename
        self.beitrag_20_input = None  # 20% Selbstbeteiligung (manuell)
        self.beitrag_10_label = None  # 10% Selbstbeteiligung (aus AMIS)
        self.beitrag_0_input = None   # Keine Selbstbeteiligung (manuell)
        self.init_ui()

    def init_ui(self):
        """Initialisiere die Benutzeroberfläche"""
        self.setWindowTitle("Allianz Angebotstool - AMIS Pferde-Versicherung")
        self.setMinimumSize(1000, 850)
        self.setStyleSheet(STYLESHEET)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(35, 30, 35, 30)
        layout.setSpacing(15)

        # Header
        header_widget = self._create_header()
        layout.addWidget(header_widget)

        # Trennlinie
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {COLORS['border_gray']}; max-height: 2px;")
        layout.addWidget(line)

        # User-Info-Anzeige
        user_info_group = self._create_user_info_group()
        layout.addWidget(user_info_group)

        # AMIS PDF Upload
        pdf_group = self._create_pdf_group()
        layout.addWidget(pdf_group)

        # Pferdename Eingabe
        pferdename_group = self._create_pferdename_group()
        layout.addWidget(pferdename_group)

        # Beiträge (Selbstbeteiligung)
        beitraege_group = self._create_beitraege_group()
        layout.addWidget(beitraege_group)

        # Vorschau
        preview_group = self._create_preview_group()
        layout.addWidget(preview_group)

        # Fortschrittsanzeige
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        # Aktionsbutton
        button_layout = QHBoxLayout()

        # Abmelden-Button (links)
        logout_btn = QPushButton("Abmelden")
        logout_btn.setObjectName("secondaryBtn")
        logout_btn.clicked.connect(self.logout)
        button_layout.addWidget(logout_btn)

        button_layout.addStretch()

        self.generate_btn = QPushButton("PDF erstellen")
        self.generate_btn.setObjectName("primaryBtn")
        self.generate_btn.setEnabled(False)
        self.generate_btn.clicked.connect(self.merge_pdfs)
        button_layout.addWidget(self.generate_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        layout.addStretch()

        # Footer
        footer = QLabel("© 2026 Allianz Angebotstool | PDF-Zusammenführung für AMIS Angebote")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet(f"color: {COLORS['text_gray']}; font-size: 11px; padding: 10px;")
        layout.addWidget(footer)

    def _create_header(self):
        """Erstelle Header"""
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)

        title = QLabel("AMIS Angebots-Generator")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)

        subtitle = QLabel("Fügen Sie Ihr AMIS-Angebot mit der Vertriebler-Vorlage zusammen")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle)

        return header

    def _create_user_info_group(self):
        """Erstelle User-Info-Anzeige"""
        group = QGroupBox("Angemeldet als")
        layout = QHBoxLayout()
        layout.setSpacing(18)

        # User-Icon (Emoji)
        icon_label = QLabel("👤")
        icon_label.setStyleSheet("font-size: 38px;")
        layout.addWidget(icon_label)

        # User-Name
        user_name = f"{self.user.get('vorname', '')} {self.user.get('nachname', '')}".strip()
        if not user_name:
            user_name = self.user.get('login', 'Unbekannt')

        name_label = QLabel(user_name)
        name_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLORS['primary_blue']};")
        layout.addWidget(name_label)

        layout.addStretch()

        # Hinweis zur aktuellen Vorlage
        template_hint = QLabel("📋 Vorlage wird automatisch verwendet")
        template_hint.setStyleSheet(f"color: {COLORS['text_gray']}; font-size: 13px; font-style: italic;")
        layout.addWidget(template_hint)

        group.setLayout(layout)
        return group

    def _create_pdf_group(self):
        """Erstelle AMIS PDF Upload"""
        group = QGroupBox("Schritt 1: AMIS Angebot hochladen")
        layout = QHBoxLayout()
        layout.setSpacing(20)

        # Icon
        icon_label = QLabel("📄")
        icon_label.setStyleSheet("font-size: 36px;")
        layout.addWidget(icon_label)

        pdf_info_layout = QVBoxLayout()
        pdf_info_layout.setSpacing(8)

        self.pdf_label = QLabel("Keine Datei ausgewählt")
        self.pdf_label.setStyleSheet(f"color: {COLORS['text_gray']}; font-style: italic; font-size: 15px;")
        pdf_info_layout.addWidget(self.pdf_label)

        pdf_hint = QLabel("Wählen Sie das AMIS Pferde-Angebot (PDF)")
        pdf_hint.setObjectName("hintLabel")
        pdf_info_layout.addWidget(pdf_hint)

        layout.addLayout(pdf_info_layout, 1)

        upload_btn = QPushButton("📁 PDF auswählen")
        upload_btn.setObjectName("secondaryBtn")
        upload_btn.setMinimumWidth(180)
        upload_btn.clicked.connect(self.select_pdf)
        layout.addWidget(upload_btn)

        group.setLayout(layout)
        return group

    def _create_pferdename_group(self):
        """Erstelle Pferdename-Eingabe"""
        group = QGroupBox("Schritt 2: Pferdename eingeben")
        layout = QVBoxLayout()
        layout.setSpacing(12)

        # Label für Eingabefeld
        label = QLabel("Pferdename:")
        label.setObjectName("inputLabel")
        layout.addWidget(label)

        # Eingabefeld mit größerem Styling
        input_layout = QHBoxLayout()
        self.pferdename_input = QLineEdit()
        self.pferdename_input.setPlaceholderText("z.B. Black Beauty")
        self.pferdename_input.setMinimumHeight(50)
        self.pferdename_input.textChanged.connect(self._update_preview)
        input_layout.addWidget(self.pferdename_input)
        layout.addLayout(input_layout)

        hint = QLabel("💡 Dieser Name wird in der Vorlage eingefügt")
        hint.setObjectName("hintLabel")
        layout.addWidget(hint)

        group.setLayout(layout)
        return group

    def _create_beitraege_group(self):
        """Erstelle Beiträge-Eingabe (Selbstbeteiligung)"""
        group = QGroupBox("Schritt 3: Beiträge (Selbstbeteiligung)")
        layout = QVBoxLayout()
        layout.setSpacing(18)

        # Grid für die 3 Beiträge
        beitraege_layout = QHBoxLayout()
        beitraege_layout.setSpacing(25)

        # 20% Selbstbeteiligung (manuell)
        sb20_layout = QVBoxLayout()
        sb20_layout.setSpacing(8)
        sb20_label = QLabel("20% Selbstbeteiligung:")
        sb20_label.setObjectName("inputLabel")
        sb20_layout.addWidget(sb20_label)

        # Input mit € Suffix
        sb20_input_layout = QHBoxLayout()
        sb20_input_layout.setSpacing(8)
        self.beitrag_20_input = QLineEdit()
        self.beitrag_20_input.setPlaceholderText("z.B. 243,81")
        self.beitrag_20_input.setMinimumHeight(50)
        self.beitrag_20_input.textChanged.connect(self._update_preview)
        sb20_input_layout.addWidget(self.beitrag_20_input)
        euro20 = QLabel("€")
        euro20.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLORS['primary_blue']};")
        sb20_input_layout.addWidget(euro20)
        sb20_layout.addLayout(sb20_input_layout)

        hint20 = QLabel("✏️ Manuell eingeben")
        hint20.setObjectName("hintLabel")
        sb20_layout.addWidget(hint20)
        beitraege_layout.addLayout(sb20_layout)

        # 10% Selbstbeteiligung (aus AMIS)
        sb10_layout = QVBoxLayout()
        sb10_layout.setSpacing(8)
        sb10_label = QLabel("10% Selbstbeteiligung:")
        sb10_label.setObjectName("inputLabel")
        sb10_layout.addWidget(sb10_label)

        # Anzeige-Label mit € Suffix (wie die anderen Felder)
        sb10_input_layout = QHBoxLayout()
        sb10_input_layout.setSpacing(8)
        self.beitrag_10_label = QLabel("—")
        self.beitrag_10_label.setStyleSheet(f"""
            padding: 8px 18px;
            border: 3px solid {COLORS['light_blue']};
            border-radius: 10px;
            background-color: {COLORS['white']};
            font-size: 16px;
            font-weight: 500;
            color: {COLORS['text_gray']};
            min-width: 120px;
            max-height: 44px;
        """)
        sb10_input_layout.addWidget(self.beitrag_10_label)
        euro10 = QLabel("€")
        euro10.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLORS['primary_blue']};")
        sb10_input_layout.addWidget(euro10)
        sb10_layout.addLayout(sb10_input_layout)

        hint10 = QLabel("🔄 Automatisch aus AMIS")
        hint10.setObjectName("hintLabel")
        sb10_layout.addWidget(hint10)
        beitraege_layout.addLayout(sb10_layout)

        # Keine Selbstbeteiligung (manuell)
        sb0_layout = QVBoxLayout()
        sb0_layout.setSpacing(8)
        sb0_label = QLabel("Keine Selbstbeteiligung:")
        sb0_label.setObjectName("inputLabel")
        sb0_layout.addWidget(sb0_label)

        # Input mit € Suffix
        sb0_input_layout = QHBoxLayout()
        sb0_input_layout.setSpacing(8)
        self.beitrag_0_input = QLineEdit()
        self.beitrag_0_input.setPlaceholderText("z.B. 385,62")
        self.beitrag_0_input.setMinimumHeight(50)
        self.beitrag_0_input.textChanged.connect(self._update_preview)
        sb0_input_layout.addWidget(self.beitrag_0_input)
        euro0 = QLabel("€")
        euro0.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLORS['primary_blue']};")
        sb0_input_layout.addWidget(euro0)
        sb0_layout.addLayout(sb0_input_layout)

        hint0 = QLabel("✏️ Manuell eingeben")
        hint0.setObjectName("hintLabel")
        sb0_layout.addWidget(hint0)
        beitraege_layout.addLayout(sb0_layout)

        layout.addLayout(beitraege_layout)

        # Hinweis
        hint = QLabel("💡 Diese Beträge werden in der Vorlage (Seite 1) eingetragen")
        hint.setObjectName("hintLabel")
        layout.addWidget(hint)

        group.setLayout(layout)
        return group

    def _create_preview_group(self):
        """Erstelle Vorschau"""
        group = QGroupBox("Schritt 4: Vorschau der Zusammenführung")
        layout = QVBoxLayout()
        layout.setSpacing(12)

        self.preview_label = QLabel(self._get_preview_text())
        self.preview_label.setObjectName("previewLabel")
        self.preview_label.setWordWrap(True)
        self.preview_label.setMinimumHeight(180)
        layout.addWidget(self.preview_label)

        group.setLayout(layout)
        return group

    def _get_preview_text(self) -> str:
        """Erstelle Vorschau-Text"""
        user_name = f"{self.user.get('vorname', '')} {self.user.get('nachname', '')}".strip()

        if self.amis_pdf_path:
            try:
                # Hole Template-Pfad aus User-Daten
                template_path = self.user_manager.get_user_template_path(self.user['id'])

                if not template_path:
                    return "Fehler: Keine Vorlage für diesen Vertriebler gefunden."

                # Hole Seiten-Info vom Merger
                merger = PDFMerger(str(template_path))
                info = merger.get_page_info(self.amis_pdf_path)

                preview = f"""Zusammenführung:

  Vorlage Teil 1:      {info['vorlage_seiten_teil1']} Seiten (vor AMIS)
  AMIS Angebot:        {info['amis_seiten']} Seiten
  Vorlage Teil 2:      {info['vorlage_seiten_teil2']} Seiten (nach AMIS)
  ─────────────────────────────
  GESAMT:              {info['gesamt_seiten']} Seiten

  Vertriebler: {user_name}
  AMIS-Datei:  {Path(self.amis_pdf_path).name}"""

                # Füge extrahierte Daten hinzu
                if self.extracted_data:
                    placeholder_data = PlaceholderReplacer.prepare_data_from_extraction(self.extracted_data)
                    pferdename = self.pferdename_input.text() if self.pferdename_input else ""
                    beitrag_20 = self.beitrag_20_input.text() if self.beitrag_20_input else ""
                    beitrag_10 = self.extracted_data.get('beitrag', '')
                    beitrag_0 = self.beitrag_0_input.text() if self.beitrag_0_input else ""

                    preview += f"""

  ─────────────────────────────
  Extrahierte Daten:

  • Name:        {placeholder_data.get('vorname', 'N/A')} {placeholder_data.get('nachname', 'N/A')}
  • Datum:       {placeholder_data.get('datum', 'N/A')}
  • Pferdename:  {pferdename if pferdename else '(noch nicht eingegeben)'}

  ─────────────────────────────
  Beiträge (Selbstbeteiligung):

  • 20%:         {beitrag_20 if beitrag_20 else '(noch nicht eingegeben)'} €
  • 10%:         {beitrag_10 if beitrag_10 else '(nicht gefunden)'}
  • Keine:       {beitrag_0 if beitrag_0 else '(noch nicht eingegeben)'} €"""

                return preview

            except Exception as e:
                return f"Fehler: {str(e)}"
        else:
            return """So funktioniert es:

  1. Laden Sie das AMIS Angebot (PDF) hoch
  2. Geben Sie den Pferdenamen ein
  3. Klicken Sie auf "PDF erstellen"

  Das fertige PDF wird auf Ihrem Desktop gespeichert:
  Desktop/Angebote/Angebot_[Dateiname].pdf

  Automatisch befüllt werden:
  • Name des Kunden (Vor- und Nachname)
  • Datum des Angebots
  • Pferdename"""

    def _update_preview(self):
        """Aktualisiere Vorschau"""
        self.preview_label.setText(self._get_preview_text())
        self._check_ready()

    def select_pdf(self):
        """AMIS PDF auswählen und Daten extrahieren"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "AMIS Angebot auswählen",
            "",
            "PDF Dateien (*.pdf)"
        )

        if file_path:
            self.amis_pdf_path = file_path
            self.pdf_label.setText(f"✅ {Path(file_path).name}")
            self.pdf_label.setStyleSheet(
                f"color: {COLORS['success_green']}; font-weight: bold; font-style: normal; font-size: 16px;"
            )

            # Extrahiere Daten aus PDF
            try:
                extractor = PDFExtractor(file_path)
                self.extracted_data = extractor.extract()

                # Zeige extrahierten Beitrag (10% Selbstbeteiligung)
                beitrag = self.extracted_data.get('beitrag', '')
                if beitrag and self.beitrag_10_label:
                    # Entferne € falls vorhanden für saubere Anzeige
                    beitrag_clean = beitrag.replace('€', '').replace(' ', '').strip()
                    self.beitrag_10_label.setText(beitrag_clean)
                    self.beitrag_10_label.setStyleSheet(f"""
                        padding: 8px 18px;
                        border: 3px solid {COLORS['success_green']};
                        border-radius: 10px;
                        background-color: {COLORS['white']};
                        font-size: 16px;
                        font-weight: bold;
                        color: {COLORS['text_dark']};
                        min-width: 120px;
                        max-height: 44px;
                    """)
                else:
                    self.beitrag_10_label.setText("—")
                    self.beitrag_10_label.setStyleSheet(f"""
                        padding: 8px 18px;
                        border: 3px solid {COLORS['error_red']};
                        border-radius: 10px;
                        background-color: #fff0f0;
                        font-size: 16px;
                        color: {COLORS['error_red']};
                        min-width: 120px;
                        max-height: 44px;
                    """)
            except Exception as e:
                print(f"Warnung: Datenextraktion fehlgeschlagen: {e}")
                self.extracted_data = None

            self._update_preview()
            self._check_ready()

    def _check_ready(self):
        """Prüfe ob bereit"""
        pferdename = self.pferdename_input.text().strip() if self.pferdename_input else ""
        beitrag_20 = self.beitrag_20_input.text().strip() if self.beitrag_20_input else ""
        beitrag_0 = self.beitrag_0_input.text().strip() if self.beitrag_0_input else ""
        beitrag_10 = self.extracted_data.get('beitrag', '') if self.extracted_data else ""

        ready = (
            self.amis_pdf_path is not None and
            len(pferdename) > 0 and
            len(beitrag_20) > 0 and
            len(beitrag_0) > 0 and
            len(beitrag_10) > 0
        )
        self.generate_btn.setEnabled(ready)

    def merge_pdfs(self):
        """Starte PDF-Zusammenführung"""
        from datetime import datetime

        # Hole Template-Pfad
        template_path = self.user_manager.get_user_template_path(self.user['id'])
        if not template_path:
            QMessageBox.critical(
                self,
                "Fehler",
                "Keine Vorlage für diesen Vertriebler gefunden."
            )
            return

        output_dir = Path.home() / "Desktop" / "Angebote"
        output_dir.mkdir(parents=True, exist_ok=True)

        pdf_name = Path(self.amis_pdf_path).stem
        timestamp = datetime.now().strftime("%H-%M-%S")
        output_path = output_dir / f"Angebot_{pdf_name}_{timestamp}.pdf"

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setVisible(True)
        self.status_label.setText("Starte Zusammenführung...")
        self.generate_btn.setEnabled(False)

        pferdename = self.pferdename_input.text().strip() if self.pferdename_input else None

        # Sammle Beiträge
        beitraege = {
            'beitrag_20': self.beitrag_20_input.text().strip() if self.beitrag_20_input else "",
            'beitrag_10': self.extracted_data.get('beitrag', '') if self.extracted_data else "",
            'beitrag_0': self.beitrag_0_input.text().strip() if self.beitrag_0_input else ""
        }

        self.merge_thread = MergeThread(
            str(template_path),
            self.amis_pdf_path,
            str(output_path),
            pferdename=pferdename,
            beitraege=beitraege
        )
        self.merge_thread.progress.connect(self._update_progress)
        self.merge_thread.finished.connect(self._merge_finished)
        self.merge_thread.start()

    def _update_progress(self, value, message):
        """Update Fortschritt"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)

    def _merge_finished(self, success, result):
        """Zusammenführung abgeschlossen"""
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)
        self.generate_btn.setEnabled(True)

        if success:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Erfolg!")
            msg.setText("PDF wurde erfolgreich erstellt!")
            msg.setInformativeText(f"Gespeichert unter:\n{result}")
            msg.setStyleSheet(f"""
                QMessageBox {{
                    background-color: {COLORS['white']};
                }}
                QMessageBox QLabel {{
                    color: {COLORS['text_dark']};
                    font-size: 14px;
                }}
                QPushButton {{
                    background-color: {COLORS['primary_blue']};
                    color: {COLORS['white']};
                    padding: 8px 20px;
                    border-radius: 5px;
                    font-weight: bold;
                    min-width: 80px;
                }}
            """)

            open_btn = msg.addButton("Öffnen", QMessageBox.ButtonRole.AcceptRole)
            msg.addButton("OK", QMessageBox.ButtonRole.RejectRole)

            msg.exec()

            if msg.clickedButton() == open_btn:
                self._open_file(result)
        else:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler bei der Zusammenführung:\n\n{result}"
            )

    def _open_file(self, file_path):
        """Öffne Datei mit Standard-Programm"""
        try:
            if sys.platform == "win32":
                os.startfile(file_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", file_path])
            else:
                subprocess.run(["xdg-open", file_path])
        except Exception:
            QMessageBox.warning(
                self,
                "Hinweis",
                f"Datei konnte nicht automatisch geöffnet werden.\n\nPfad: {file_path}"
            )

    def logout(self):
        """Abmelden und zurück zum Login"""
        reply = QMessageBox.question(
            self,
            "Abmelden",
            "Möchten Sie sich wirklich abmelden?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.logout_requested.emit()
            self.close()
