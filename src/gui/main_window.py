"""
Hauptfenster der Angebotstool-Anwendung
Farben: Blau-Weiß Theme (Allianz Corporate Design)
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QFileDialog,
    QTextEdit, QGroupBox, QLineEdit, QMessageBox,
    QProgressBar, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor
from pathlib import Path
import os

from pdf_parser.extractor import PDFExtractor
from pptx_manager.generator import PPTXGenerator


# Allianz Blau-Weiß Farbschema
COLORS = {
    'primary_blue': '#003781',      # Allianz Dunkelblau
    'light_blue': '#0066cc',        # Helleres Blau
    'accent_blue': '#4da6ff',       # Akzent Blau
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
        border: 2px solid {COLORS['border_gray']};
        border-radius: 10px;
        margin-top: 15px;
        padding: 15px;
        font-size: 14px;
        font-weight: bold;
        color: {COLORS['primary_blue']};
    }}

    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 5px 15px;
        background-color: {COLORS['primary_blue']};
        color: {COLORS['white']};
        border-radius: 5px;
        margin-left: 10px;
    }}

    QLineEdit {{
        padding: 10px 15px;
        border: 2px solid {COLORS['border_gray']};
        border-radius: 8px;
        background-color: {COLORS['white']};
        font-size: 13px;
        color: {COLORS['text_dark']};
    }}

    QLineEdit:focus {{
        border-color: {COLORS['light_blue']};
    }}

    QLineEdit:read-only {{
        background-color: {COLORS['light_gray']};
        color: {COLORS['text_gray']};
    }}

    QComboBox {{
        padding: 10px 15px;
        border: 2px solid {COLORS['border_gray']};
        border-radius: 8px;
        background-color: {COLORS['white']};
        font-size: 13px;
        color: {COLORS['text_dark']};
        min-width: 200px;
    }}

    QComboBox:hover {{
        border-color: {COLORS['light_blue']};
    }}

    QComboBox::drop-down {{
        border: none;
        padding-right: 15px;
    }}

    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 8px solid {COLORS['primary_blue']};
        margin-right: 10px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {COLORS['white']};
        border: 2px solid {COLORS['border_gray']};
        border-radius: 8px;
        selection-background-color: {COLORS['light_blue']};
        selection-color: {COLORS['white']};
    }}

    QPushButton {{
        padding: 12px 25px;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: bold;
        cursor: pointer;
    }}

    QPushButton#primaryBtn {{
        background-color: {COLORS['primary_blue']};
        color: {COLORS['white']};
        min-width: 200px;
        min-height: 50px;
        font-size: 16px;
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
        border: 2px solid {COLORS['primary_blue']};
    }}

    QPushButton#secondaryBtn:hover {{
        background-color: {COLORS['primary_blue']};
        color: {COLORS['white']};
    }}

    QProgressBar {{
        border: none;
        border-radius: 10px;
        background-color: {COLORS['border_gray']};
        height: 20px;
        text-align: center;
    }}

    QProgressBar::chunk {{
        background-color: {COLORS['light_blue']};
        border-radius: 10px;
    }}

    QLabel {{
        color: {COLORS['text_dark']};
        font-size: 13px;
    }}

    QLabel#titleLabel {{
        font-size: 28px;
        font-weight: bold;
        color: {COLORS['primary_blue']};
        padding: 20px;
    }}

    QLabel#subtitleLabel {{
        font-size: 14px;
        color: {COLORS['text_gray']};
        padding-bottom: 20px;
    }}

    QLabel#statusLabel {{
        font-size: 13px;
        color: {COLORS['light_blue']};
        font-weight: bold;
    }}
"""


class ProcessingThread(QThread):
    """Thread für die Verarbeitung ohne UI-Blockierung"""
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(int, str)

    def __init__(self, pdf_path, template_name, output_path):
        super().__init__()
        self.pdf_path = pdf_path
        self.template_name = template_name
        self.output_path = output_path

    def run(self):
        try:
            self.progress.emit(20, "Extrahiere Daten aus PDF...")
            extractor = PDFExtractor(self.pdf_path)
            data = extractor.extract()

            self.progress.emit(60, "Generiere PowerPoint...")
            generator = PPTXGenerator(self.template_name)
            pptx_path = generator.generate(data, self.output_path)

            self.progress.emit(100, "Fertig!")
            self.finished.emit(True, f"Angebot erstellt:\n{pptx_path}")

        except Exception as e:
            self.finished.emit(False, f"Fehler: {str(e)}")


class MainWindow(QMainWindow):
    """Hauptfenster der Anwendung - Blau-Weiß Design"""

    VERTRIEBLER = [
        "Vertriebler 1",
        "Vertriebler 2",
        "Vertriebler 3",
        "Vertriebler 4",
        "Vertriebler 5",
        "Vertriebler 6",
        "Vertriebler 7"
    ]

    def __init__(self):
        super().__init__()
        self.pdf_path = None
        self.processing_thread = None
        self.init_ui()

    def init_ui(self):
        """Initialisiere die Benutzeroberfläche"""
        self.setWindowTitle("Allianz Angebotstool - AMIS Pferde-Versicherung")
        self.setMinimumSize(900, 700)
        self.setStyleSheet(STYLESHEET)

        # Zentrales Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Hauptlayout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Header
        header_widget = self._create_header()
        layout.addWidget(header_widget)

        # Trennlinie
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {COLORS['border_gray']}; max-height: 2px;")
        layout.addWidget(line)

        # Vertriebler-Auswahl
        vertriebler_group = self._create_vertriebler_group()
        layout.addWidget(vertriebler_group)

        # PDF-Upload
        pdf_group = self._create_pdf_group()
        layout.addWidget(pdf_group)

        # Extrahierte Daten
        data_group = self._create_data_group()
        layout.addWidget(data_group)

        # Fortschrittsanzeige
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        # Aktionsbuttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.generate_btn = QPushButton("Angebot generieren")
        self.generate_btn.setObjectName("primaryBtn")
        self.generate_btn.setEnabled(False)
        self.generate_btn.clicked.connect(self.generate_offer)
        button_layout.addWidget(self.generate_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        layout.addStretch()

        # Footer
        footer = QLabel("© 2026 Allianz Angebotstool | Entwickelt für AMIS Pferde-Versicherung")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet(f"color: {COLORS['text_gray']}; font-size: 11px; padding: 10px;")
        layout.addWidget(footer)

    def _create_header(self):
        """Erstelle Header mit Titel"""
        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(5)

        # Titel
        title = QLabel("AMIS Pferde-Angebotsgenerator")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(title)

        # Untertitel
        subtitle = QLabel("Erstellen Sie professionelle Versicherungsangebote in Sekunden")
        subtitle.setObjectName("subtitleLabel")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(subtitle)

        return header

    def _create_vertriebler_group(self):
        """Erstelle Vertriebler-Auswahlbereich"""
        group = QGroupBox("Schritt 1: Vertriebler auswählen")
        layout = QVBoxLayout()
        layout.setSpacing(10)

        description = QLabel("Wählen Sie Ihren Namen aus der Liste:")
        description.setStyleSheet(f"color: {COLORS['text_gray']}; font-weight: normal;")
        layout.addWidget(description)

        self.vertriebler_combo = QComboBox()
        self.vertriebler_combo.addItems(self.VERTRIEBLER)
        self.vertriebler_combo.currentTextChanged.connect(self._check_ready)
        layout.addWidget(self.vertriebler_combo)

        group.setLayout(layout)
        return group

    def _create_pdf_group(self):
        """Erstelle PDF-Upload Bereich"""
        group = QGroupBox("Schritt 2: AMIS PDF hochladen")
        layout = QHBoxLayout()
        layout.setSpacing(15)

        # PDF Info
        pdf_info_layout = QVBoxLayout()

        self.pdf_label = QLabel("Keine Datei ausgewählt")
        self.pdf_label.setStyleSheet(f"color: {COLORS['text_gray']}; font-style: italic;")
        pdf_info_layout.addWidget(self.pdf_label)

        pdf_hint = QLabel("Unterstützt: PDF-Dateien aus dem AMIS-System")
        pdf_hint.setStyleSheet(f"color: {COLORS['text_gray']}; font-size: 11px;")
        pdf_info_layout.addWidget(pdf_hint)

        layout.addLayout(pdf_info_layout, 1)

        # Upload Button
        upload_btn = QPushButton("PDF auswählen")
        upload_btn.setObjectName("secondaryBtn")
        upload_btn.clicked.connect(self.select_pdf)
        layout.addWidget(upload_btn)

        group.setLayout(layout)
        return group

    def _create_data_group(self):
        """Erstelle Bereich für extrahierte Daten"""
        group = QGroupBox("Schritt 3: Extrahierte Daten prüfen")
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Pferdename
        horse_layout = QHBoxLayout()
        horse_label = QLabel("Pferdename:")
        horse_label.setMinimumWidth(120)
        horse_label.setStyleSheet("font-weight: bold;")
        horse_layout.addWidget(horse_label)
        self.horse_input = QLineEdit()
        self.horse_input.setPlaceholderText("Wird automatisch aus PDF extrahiert...")
        self.horse_input.setReadOnly(True)
        horse_layout.addWidget(self.horse_input)
        layout.addLayout(horse_layout)

        # Kundenname
        customer_layout = QHBoxLayout()
        customer_label = QLabel("Kunde:")
        customer_label.setMinimumWidth(120)
        customer_label.setStyleSheet("font-weight: bold;")
        customer_layout.addWidget(customer_label)
        self.customer_input = QLineEdit()
        self.customer_input.setPlaceholderText("Wird automatisch aus PDF extrahiert...")
        self.customer_input.setReadOnly(True)
        customer_layout.addWidget(self.customer_input)
        layout.addLayout(customer_layout)

        # Erstelldatum
        date_layout = QHBoxLayout()
        date_label = QLabel("Erstelldatum:")
        date_label.setMinimumWidth(120)
        date_label.setStyleSheet("font-weight: bold;")
        date_layout.addWidget(date_label)
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("Wird automatisch aus PDF extrahiert...")
        self.date_input.setReadOnly(True)
        date_layout.addWidget(self.date_input)
        layout.addLayout(date_layout)

        group.setLayout(layout)
        return group

    def select_pdf(self):
        """PDF-Datei auswählen"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "AMIS PDF auswählen",
            "",
            "PDF Dateien (*.pdf)"
        )

        if file_path:
            self.pdf_path = file_path
            self.pdf_label.setText(f"✓ {Path(file_path).name}")
            self.pdf_label.setStyleSheet(f"color: {COLORS['success_green']}; font-weight: bold; font-style: normal;")
            self._extract_pdf_data()
            self._check_ready()

    def _extract_pdf_data(self):
        """Extrahiere Daten aus PDF"""
        try:
            extractor = PDFExtractor(self.pdf_path)
            data = extractor.extract()

            self.horse_input.setText(data.get("horse_name", ""))
            self.customer_input.setText(data.get("customer_name", ""))
            self.date_input.setText(data.get("created_date", ""))

        except Exception as e:
            QMessageBox.warning(
                self,
                "Fehler beim Lesen",
                f"Die PDF-Datei konnte nicht vollständig gelesen werden:\n\n{str(e)}"
            )

    def _check_ready(self):
        """Prüfe ob alle Daten vorhanden sind"""
        ready = (
            self.pdf_path is not None and
            self.vertriebler_combo.currentText() != ""
        )
        self.generate_btn.setEnabled(ready)

    def generate_offer(self):
        """Generiere Angebot"""
        output_dir = Path.home() / "Desktop" / "Angebote"
        output_dir.mkdir(parents=True, exist_ok=True)

        pdf_name = Path(self.pdf_path).stem
        output_path = output_dir / f"Angebot_{pdf_name}.pptx"

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setVisible(True)
        self.status_label.setText("Starte Verarbeitung...")
        self.generate_btn.setEnabled(False)

        template_name = self.vertriebler_combo.currentText()

        self.processing_thread = ProcessingThread(
            self.pdf_path,
            template_name,
            str(output_path)
        )
        self.processing_thread.progress.connect(self._update_progress)
        self.processing_thread.finished.connect(self._processing_finished)
        self.processing_thread.start()

    def _update_progress(self, value, message):
        """Update Fortschrittsanzeige"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)

    def _processing_finished(self, success, message):
        """Verarbeitung abgeschlossen"""
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)
        self.generate_btn.setEnabled(True)

        if success:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setWindowTitle("Erfolg!")
            msg.setText("Angebot wurde erfolgreich erstellt!")
            msg.setInformativeText(message)
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
                }}
            """)
            msg.exec()
        else:
            QMessageBox.critical(
                self,
                "Fehler",
                message
            )
