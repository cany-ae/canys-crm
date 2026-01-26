"""
Hauptfenster der Angebotstool-Anwendung
PDF-Zusammenführung: Teil1 + AMIS Angebot + Teil2
Farben: Blau-Weiß Theme (Allianz Corporate Design)
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QFileDialog,
    QGroupBox, QMessageBox, QProgressBar, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from pathlib import Path
import os
import subprocess
import sys

from pdf_merger.merger import PDFMerger


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

    QPushButton {{
        padding: 12px 25px;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: bold;
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

    QLabel#previewLabel {{
        background-color: {COLORS['white']};
        border: 2px solid {COLORS['border_gray']};
        border-radius: 8px;
        padding: 15px;
        font-size: 13px;
        font-family: 'Consolas', 'Courier New', monospace;
    }}
"""


class MergeThread(QThread):
    """Thread für die PDF-Zusammenführung"""
    finished = pyqtSignal(bool, str)
    progress = pyqtSignal(int, str)

    def __init__(self, vertriebler_name, amis_pdf_path, output_path):
        super().__init__()
        self.vertriebler_name = vertriebler_name
        self.amis_pdf_path = amis_pdf_path
        self.output_path = output_path

    def run(self):
        try:
            self.progress.emit(30, "Lade Templates...")
            merger = PDFMerger(self.vertriebler_name)

            self.progress.emit(60, "Füge PDFs zusammen...")
            output_path = merger.merge(self.amis_pdf_path, self.output_path)

            self.progress.emit(100, "Fertig!")
            self.finished.emit(True, output_path)

        except Exception as e:
            self.finished.emit(False, str(e))


class MainWindow(QMainWindow):
    """Hauptfenster - PDF Zusammenführung"""

    def __init__(self):
        super().__init__()
        self.amis_pdf_path = None
        self.merge_thread = None
        self.init_ui()

    def init_ui(self):
        """Initialisiere die Benutzeroberfläche"""
        self.setWindowTitle("Allianz Angebotstool - AMIS Pferde-Versicherung")
        self.setMinimumSize(900, 750)
        self.setStyleSheet(STYLESHEET)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

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

        # AMIS PDF Upload
        pdf_group = self._create_pdf_group()
        layout.addWidget(pdf_group)

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

    def _create_vertriebler_group(self):
        """Erstelle Vertriebler-Auswahl"""
        group = QGroupBox("Schritt 1: Vertriebler auswählen")
        layout = QVBoxLayout()
        layout.setSpacing(10)

        description = QLabel("Wählen Sie den Vertriebler für die Vorlage:")
        description.setStyleSheet(f"color: {COLORS['text_gray']}; font-weight: normal;")
        layout.addWidget(description)

        self.vertriebler_combo = QComboBox()
        vertriebler_list = PDFMerger.get_available_vertriebler()
        if not vertriebler_list:
            vertriebler_list = ["Samet Uz"]
        self.vertriebler_combo.addItems(vertriebler_list)
        self.vertriebler_combo.currentTextChanged.connect(self._update_preview)
        layout.addWidget(self.vertriebler_combo)

        group.setLayout(layout)
        return group

    def _create_pdf_group(self):
        """Erstelle AMIS PDF Upload"""
        group = QGroupBox("Schritt 2: AMIS Angebot hochladen")
        layout = QHBoxLayout()
        layout.setSpacing(15)

        pdf_info_layout = QVBoxLayout()

        self.pdf_label = QLabel("Keine Datei ausgewählt")
        self.pdf_label.setStyleSheet(f"color: {COLORS['text_gray']}; font-style: italic;")
        pdf_info_layout.addWidget(self.pdf_label)

        pdf_hint = QLabel("Wählen Sie das AMIS Pferde-Angebot (PDF)")
        pdf_hint.setStyleSheet(f"color: {COLORS['text_gray']}; font-size: 11px;")
        pdf_info_layout.addWidget(pdf_hint)

        layout.addLayout(pdf_info_layout, 1)

        upload_btn = QPushButton("PDF auswählen")
        upload_btn.setObjectName("secondaryBtn")
        upload_btn.clicked.connect(self.select_pdf)
        layout.addWidget(upload_btn)

        group.setLayout(layout)
        return group

    def _create_preview_group(self):
        """Erstelle Vorschau"""
        group = QGroupBox("Schritt 3: Vorschau")
        layout = QVBoxLayout()
        layout.setSpacing(10)

        self.preview_label = QLabel(self._get_preview_text())
        self.preview_label.setObjectName("previewLabel")
        self.preview_label.setWordWrap(True)
        layout.addWidget(self.preview_label)

        group.setLayout(layout)
        return group

    def _get_preview_text(self) -> str:
        """Erstelle Vorschau-Text"""
        vertriebler = self.vertriebler_combo.currentText() if hasattr(self, 'vertriebler_combo') else "Samet Uz"

        if self.amis_pdf_path:
            try:
                merger = PDFMerger(vertriebler)
                info = merger.get_page_info(self.amis_pdf_path)

                return f"""Zusammenführung:

  Teil 1 (Anfang):     {info['teil1_seiten']} Seiten
  AMIS Angebot:        {info['amis_seiten']} Seiten
  Teil 2 (Ende):       {info['teil2_seiten']} Seiten
  ─────────────────────────────
  GESAMT:              {info['gesamt_seiten']} Seiten

  Vertriebler: {vertriebler}
  AMIS-Datei:  {Path(self.amis_pdf_path).name}"""

            except Exception as e:
                return f"Fehler: {str(e)}"
        else:
            return """So funktioniert es:

  1. Wählen Sie Ihren Vertriebler-Namen
  2. Laden Sie das AMIS Angebot (PDF) hoch
  3. Klicken Sie auf "PDF erstellen"

  Das fertige PDF wird auf Ihrem Desktop gespeichert:
  Desktop/Angebote/Angebot_[Dateiname].pdf"""

    def _update_preview(self):
        """Aktualisiere Vorschau"""
        self.preview_label.setText(self._get_preview_text())
        self._check_ready()

    def select_pdf(self):
        """AMIS PDF auswählen"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "AMIS Angebot auswählen",
            "",
            "PDF Dateien (*.pdf)"
        )

        if file_path:
            self.amis_pdf_path = file_path
            self.pdf_label.setText(f"✓ {Path(file_path).name}")
            self.pdf_label.setStyleSheet(
                f"color: {COLORS['success_green']}; font-weight: bold; font-style: normal;"
            )
            self._update_preview()
            self._check_ready()

    def _check_ready(self):
        """Prüfe ob bereit"""
        ready = (
            self.amis_pdf_path is not None and
            self.vertriebler_combo.currentText() != ""
        )
        self.generate_btn.setEnabled(ready)

    def merge_pdfs(self):
        """Starte PDF-Zusammenführung"""
        output_dir = Path.home() / "Desktop" / "Angebote"
        output_dir.mkdir(parents=True, exist_ok=True)

        pdf_name = Path(self.amis_pdf_path).stem
        output_path = output_dir / f"Angebot_{pdf_name}.pdf"

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setVisible(True)
        self.status_label.setText("Starte Zusammenführung...")
        self.generate_btn.setEnabled(False)

        self.merge_thread = MergeThread(
            self.vertriebler_combo.currentText(),
            self.amis_pdf_path,
            str(output_path)
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
