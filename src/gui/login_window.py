"""
Login-Fenster für Allianz Angebotstool
Einfacher Login mit Benutzername
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from pathlib import Path

from auth.user_manager import UserManager


# Allianz Blau-Weiß Farbschema
COLORS = {
    'primary_blue': '#003781',
    'light_blue': '#0066cc',
    'accent_blue': '#4da6ff',
    'white': '#ffffff',
    'bg_light': '#f8f9fa',
    'text_dark': '#2c3e50',
    'text_gray': '#6c757d',
    'border_gray': '#dee2e6',
    'success_green': '#28a745',
    'error_red': '#dc3545'
}

STYLESHEET = f"""
    QMainWindow {{
        background-color: {COLORS['bg_light']};
    }}

    QLabel#titleLabel {{
        font-size: 24px;
        font-weight: bold;
        color: {COLORS['primary_blue']};
        padding: 20px;
    }}

    QLabel#subtitleLabel {{
        font-size: 14px;
        color: {COLORS['text_gray']};
        padding: 10px;
    }}

    QLineEdit {{
        padding: 15px;
        border: 2px solid {COLORS['border_gray']};
        border-radius: 8px;
        background-color: {COLORS['white']};
        font-size: 14px;
        color: {COLORS['text_dark']};
        min-width: 300px;
    }}

    QLineEdit:hover {{
        border-color: {COLORS['light_blue']};
    }}

    QLineEdit:focus {{
        border-color: {COLORS['primary_blue']};
        border-width: 2px;
    }}

    QPushButton {{
        padding: 15px 30px;
        border: none;
        border-radius: 8px;
        font-size: 14px;
        font-weight: bold;
        min-width: 200px;
    }}

    QPushButton#primaryBtn {{
        background-color: {COLORS['primary_blue']};
        color: {COLORS['white']};
    }}

    QPushButton#primaryBtn:hover {{
        background-color: {COLORS['light_blue']};
    }}

    QPushButton#primaryBtn:pressed {{
        background-color: {COLORS['primary_blue']};
    }}

    QPushButton#primaryBtn:disabled {{
        background-color: {COLORS['border_gray']};
        color: {COLORS['text_gray']};
    }}
"""


class LoginWindow(QMainWindow):
    """Login-Fenster"""

    # Signals
    login_successful = pyqtSignal(dict)  # Emitted mit User-Daten

    def __init__(self):
        super().__init__()
        self.user_manager = UserManager()
        self.init_ui()

    def init_ui(self):
        """Initialisiere die Benutzeroberfläche"""
        self.setWindowTitle("Allianz Angebotstool - Login")
        self.setFixedSize(500, 400)
        self.setStyleSheet(STYLESHEET)

        # Zentrales Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Hauptlayout
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        central_widget.setLayout(layout)

        # Vertikaler Spacer oben
        layout.addStretch()

        # Logo/Titel
        title_label = QLabel("Allianz Angebotstool")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Untertitel
        subtitle_label = QLabel("AMIS Pferde-Versicherung")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        # Abstand
        layout.addSpacing(20)

        # Anmeldung Label
        login_label = QLabel("Bitte melden Sie sich an:")
        login_label.setStyleSheet(f"color: {COLORS['text_dark']}; font-size: 13px; font-weight: bold;")
        login_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(login_label)

        # Benutzername Eingabe
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Benutzername (z.B. Sametuz oder Admin)")
        self.username_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.username_input.returnPressed.connect(self.login)
        layout.addWidget(self.username_input, alignment=Qt.AlignmentFlag.AlignCenter)

        # Login Button
        login_btn = QPushButton("Anmelden")
        login_btn.setObjectName("primaryBtn")
        login_btn.clicked.connect(self.login)
        layout.addWidget(login_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Hinweis
        hint_label = QLabel("Hinweis: Admin-Zugang mit 'Admin'")
        hint_label.setStyleSheet(f"color: {COLORS['text_gray']}; font-size: 11px; font-style: italic;")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint_label)

        # Vertikaler Spacer unten
        layout.addStretch()

        # Fokus auf Eingabefeld
        self.username_input.setFocus()

    def login(self):
        """Login durchführen"""
        username = self.username_input.text().strip()

        if not username:
            QMessageBox.warning(
                self,
                "Fehler",
                "Bitte geben Sie einen Benutzernamen ein."
            )
            return

        # Authentifizierung
        user = self.user_manager.authenticate(username)

        if user:
            # Login erfolgreich
            self.login_successful.emit(user)
            self.close()
        else:
            # Login fehlgeschlagen
            QMessageBox.critical(
                self,
                "Anmeldung fehlgeschlagen",
                f"Benutzer '{username}' nicht gefunden.\n\nBitte überprüfen Sie den Benutzernamen."
            )
            self.username_input.clear()
            self.username_input.setFocus()
