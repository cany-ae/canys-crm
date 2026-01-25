"""
Hauptfenster der Angebotstool-Anwendung
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QFileDialog,
    QTextEdit, QGroupBox, QLineEdit, QMessageBox,
    QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from pathlib import Path
import os

from pdf_parser.extractor import PDFExtractor
from pptx_manager.generator import PPTXGenerator


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
            # PDF-Daten extrahieren
            self.progress.emit(20, "Extrahiere Daten aus PDF...")
            extractor = PDFExtractor(self.pdf_path)
            data = extractor.extract()

            # PowerPoint generieren
            self.progress.emit(60, "Generiere PowerPoint...")
            generator = PPTXGenerator(self.template_name)
            pptx_path = generator.generate(data, self.output_path)

            self.progress.emit(100, "Fertig!")
            self.finished.emit(True, f"Angebot erstellt: {pptx_path}")

        except Exception as e:
            self.finished.emit(False, f"Fehler: {str(e)}")


class MainWindow(QMainWindow):
    """Hauptfenster der Anwendung"""

    # 7 Vertriebler
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
        self.setWindowTitle("Allianz Angebotstool")
        self.setMinimumSize(800, 600)

        # Zentrales Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Hauptlayout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Titel
        title = QLabel("🐴 AMIS Pferde-Angebotsgenerator")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0066cc;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

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
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        # Aktionsbuttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.generate_btn = QPushButton("📄 Angebot generieren")
        self.generate_btn.setEnabled(False)
        self.generate_btn.setMinimumHeight(45)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #0066cc;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
                padding: 10px 30px;
            }
            QPushButton:hover {
                background-color: #0052a3;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.generate_btn.clicked.connect(self.generate_offer)
        button_layout.addWidget(self.generate_btn)

        button_layout.addStretch()
        layout.addLayout(button_layout)

        layout.addStretch()

    def _create_vertriebler_group(self):
        """Erstelle Vertriebler-Auswahlbereich"""
        group = QGroupBox("1️⃣ Vertriebler auswählen")
        group.setStyleSheet("QGroupBox { font-weight: bold; }")
        layout = QVBoxLayout()

        self.vertriebler_combo = QComboBox()
        self.vertriebler_combo.addItems(self.VERTRIEBLER)
        self.vertriebler_combo.setMinimumHeight(35)
        self.vertriebler_combo.currentTextChanged.connect(self._check_ready)
        layout.addWidget(self.vertriebler_combo)

        group.setLayout(layout)
        return group

    def _create_pdf_group(self):
        """Erstelle PDF-Upload Bereich"""
        group = QGroupBox("2️⃣ AMIS PDF hochladen")
        group.setStyleSheet("QGroupBox { font-weight: bold; }")
        layout = QHBoxLayout()

        self.pdf_label = QLabel("Keine Datei ausgewählt")
        self.pdf_label.setStyleSheet("color: #666666;")
        layout.addWidget(self.pdf_label, 1)

        upload_btn = QPushButton("📁 PDF auswählen")
        upload_btn.setMinimumHeight(35)
        upload_btn.clicked.connect(self.select_pdf)
        layout.addWidget(upload_btn)

        group.setLayout(layout)
        return group

    def _create_data_group(self):
        """Erstelle Bereich für extrahierte Daten"""
        group = QGroupBox("3️⃣ Extrahierte Daten")
        group.setStyleSheet("QGroupBox { font-weight: bold; }")
        layout = QVBoxLayout()

        # Pferdename
        horse_layout = QHBoxLayout()
        horse_layout.addWidget(QLabel("Pferdename:"))
        self.horse_input = QLineEdit()
        self.horse_input.setPlaceholderText("Wird automatisch aus PDF extrahiert")
        self.horse_input.setReadOnly(True)
        horse_layout.addWidget(self.horse_input)
        layout.addLayout(horse_layout)

        # Kundenname
        customer_layout = QHBoxLayout()
        customer_layout.addWidget(QLabel("Kunde:"))
        self.customer_input = QLineEdit()
        self.customer_input.setPlaceholderText("Wird automatisch aus PDF extrahiert")
        self.customer_input.setReadOnly(True)
        customer_layout.addWidget(self.customer_input)
        layout.addLayout(customer_layout)

        # Erstelldatum
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Erstelldatum:"))
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("Wird automatisch aus PDF extrahiert")
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
            self.pdf_label.setText(Path(file_path).name)
            self.pdf_label.setStyleSheet("color: #00aa00; font-weight: bold;")
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
                "Fehler",
                f"Fehler beim Extrahieren der Daten:\n{str(e)}"
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
        # Output-Pfad
        output_dir = Path.home() / "Desktop" / "Angebote"
        output_dir.mkdir(parents=True, exist_ok=True)

        pdf_name = Path(self.pdf_path).stem
        output_path = output_dir / f"Angebot_{pdf_name}.pptx"

        # Verarbeitung im Thread starten
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
            QMessageBox.information(
                self,
                "Erfolg",
                message
            )
        else:
            QMessageBox.critical(
                self,
                "Fehler",
                message
            )
