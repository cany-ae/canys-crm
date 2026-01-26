"""
Admin-Fenster für Vertriebler-Verwaltung
Vertriebler anlegen, bearbeiten, löschen
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTableWidget, QTableWidgetItem,
    QMessageBox, QDialog, QLineEdit, QFileDialog, QCheckBox,
    QHeaderView, QTabWidget, QFrame
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
        font-size: 20px;
        font-weight: bold;
        color: {COLORS['primary_blue']};
        padding: 10px;
    }}

    QTableWidget {{
        background-color: {COLORS['white']};
        border: 1px solid {COLORS['border_gray']};
        border-radius: 8px;
        gridline-color: {COLORS['border_gray']};
        font-size: 13px;
    }}

    QTableWidget::item {{
        padding: 8px;
    }}

    QTableWidget::item:selected {{
        background-color: {COLORS['accent_blue']};
        color: {COLORS['white']};
    }}

    QHeaderView::section {{
        background-color: {COLORS['primary_blue']};
        color: {COLORS['white']};
        padding: 10px;
        border: none;
        font-weight: bold;
        font-size: 13px;
    }}

    QLineEdit {{
        padding: 10px 15px;
        border: 2px solid {COLORS['border_gray']};
        border-radius: 8px;
        background-color: {COLORS['white']};
        font-size: 13px;
        color: {COLORS['text_dark']};
    }}

    QLineEdit:hover {{
        border-color: {COLORS['light_blue']};
    }}

    QLineEdit:focus {{
        border-color: {COLORS['primary_blue']};
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
    }}

    QPushButton#primaryBtn:hover {{
        background-color: {COLORS['light_blue']};
    }}

    QPushButton#secondaryBtn {{
        background-color: {COLORS['white']};
        color: {COLORS['primary_blue']};
        border: 2px solid {COLORS['primary_blue']};
    }}

    QPushButton#secondaryBtn:hover {{
        background-color: {COLORS['bg_light']};
    }}

    QPushButton#dangerBtn {{
        background-color: {COLORS['error_red']};
        color: {COLORS['white']};
    }}

    QPushButton#dangerBtn:hover {{
        background-color: #c82333;
    }}

    QDialog {{
        background-color: {COLORS['white']};
    }}

    QCheckBox {{
        font-size: 13px;
        color: {COLORS['text_dark']};
    }}
"""


class UserDialog(QDialog):
    """Dialog für Vertriebler anlegen/bearbeiten"""

    def __init__(self, parent=None, user=None):
        super().__init__(parent)
        self.user = user
        self.template_path = None
        self.init_ui()

    def init_ui(self):
        """Initialisiere UI"""
        is_edit = self.user is not None
        title = "Vertriebler bearbeiten" if is_edit else "Neuen Vertriebler anlegen"
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setStyleSheet(STYLESHEET)

        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        self.setLayout(layout)

        # Vorname
        vorname_label = QLabel("Vorname:")
        vorname_label.setStyleSheet(f"color: {COLORS['text_dark']}; font-weight: bold;")
        layout.addWidget(vorname_label)

        self.vorname_input = QLineEdit()
        self.vorname_input.setPlaceholderText("z.B. Samet")
        if is_edit:
            self.vorname_input.setText(self.user.get("vorname", ""))
        layout.addWidget(self.vorname_input)

        # Nachname
        nachname_label = QLabel("Nachname:")
        nachname_label.setStyleSheet(f"color: {COLORS['text_dark']}; font-weight: bold;")
        layout.addWidget(nachname_label)

        self.nachname_input = QLineEdit()
        self.nachname_input.setPlaceholderText("z.B. Uz")
        if is_edit:
            self.nachname_input.setText(self.user.get("nachname", ""))
        layout.addWidget(self.nachname_input)

        # Login (nur Anzeige)
        login_label = QLabel("Login wird automatisch generiert:")
        login_label.setStyleSheet(f"color: {COLORS['text_gray']}; font-size: 12px; font-style: italic;")
        layout.addWidget(login_label)

        # Template
        template_label = QLabel("Vorlage (PDF):")
        template_label.setStyleSheet(f"color: {COLORS['text_dark']}; font-weight: bold;")
        layout.addWidget(template_label)

        template_layout = QHBoxLayout()

        self.template_path_label = QLabel("Keine Datei ausgewählt")
        if is_edit and self.user.get("template"):
            self.template_path_label.setText(Path(self.user.get("template")).name)
        self.template_path_label.setStyleSheet(f"color: {COLORS['text_gray']}; font-style: italic;")
        template_layout.addWidget(self.template_path_label, 1)

        template_btn = QPushButton("Datei auswählen")
        template_btn.setObjectName("secondaryBtn")
        template_btn.clicked.connect(self.select_template)
        template_layout.addWidget(template_btn)

        layout.addLayout(template_layout)

        # Aktiv
        if is_edit:
            self.active_checkbox = QCheckBox("Aktiv")
            self.active_checkbox.setChecked(self.user.get("active", True))
            layout.addWidget(self.active_checkbox)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.setObjectName("secondaryBtn")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Speichern")
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self.accept)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def select_template(self):
        """Template-Datei auswählen"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Vorlage auswählen",
            "",
            "PDF Dateien (*.pdf)"
        )

        if file_path:
            self.template_path = file_path
            self.template_path_label.setText(Path(file_path).name)
            self.template_path_label.setStyleSheet(f"color: {COLORS['success_green']}; font-weight: bold;")

    def get_data(self):
        """Hole eingegebene Daten"""
        data = {
            "vorname": self.vorname_input.text().strip(),
            "nachname": self.nachname_input.text().strip(),
            "template_path": self.template_path
        }

        if hasattr(self, 'active_checkbox'):
            data["active"] = self.active_checkbox.isChecked()

        return data


class AdminWindow(QMainWindow):
    """Admin-Fenster für Vertriebler-Verwaltung"""

    # Signals
    logout_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.user_manager = UserManager()
        self.all_users = []  # Alle User für Suche
        self.init_ui()
        self.load_users()

    def init_ui(self):
        """Initialisiere die Benutzeroberfläche"""
        self.setWindowTitle("Allianz Angebotstool - Admin")
        self.setMinimumSize(1200, 700)
        self.setStyleSheet(STYLESHEET)

        # Zentrales Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Hauptlayout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        central_widget.setLayout(main_layout)

        # Titel
        title_label = QLabel("Vertriebler-Verwaltung")
        title_label.setObjectName("titleLabel")
        main_layout.addWidget(title_label)

        # Tab Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 2px solid {COLORS['border_gray']};
                border-radius: 8px;
                background-color: {COLORS['white']};
                padding: 10px;
            }}
            QTabBar::tab {{
                background-color: {COLORS['bg_light']};
                color: {COLORS['text_dark']};
                padding: 12px 30px;
                margin-right: 5px;
                border: 2px solid {COLORS['border_gray']};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }}
            QTabBar::tab:selected {{
                background-color: {COLORS['white']};
                color: {COLORS['primary_blue']};
                border-bottom: 2px solid {COLORS['white']};
            }}
            QTabBar::tab:hover {{
                background-color: {COLORS['accent_blue']};
                color: {COLORS['white']};
            }}
        """)

        # Tab 1: Dashboard
        dashboard_tab = self._create_dashboard_tab()
        self.tab_widget.addTab(dashboard_tab, "📊 Dashboard")

        # Tab 2: Vertriebler-Tabelle
        users_tab = self._create_users_tab()
        self.tab_widget.addTab(users_tab, "👥 Vertriebler")

        main_layout.addWidget(self.tab_widget)

        # Buttons unten (global)
        button_layout = QHBoxLayout()

        # Abmelden-Button (links)
        logout_btn = QPushButton("Abmelden")
        logout_btn.setObjectName("secondaryBtn")
        logout_btn.clicked.connect(self.logout)
        button_layout.addWidget(logout_btn)

        button_layout.addStretch()

        main_layout.addLayout(button_layout)

    def _create_dashboard_tab(self):
        """Erstelle Dashboard Tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(30)
        layout.setContentsMargins(20, 20, 20, 20)
        tab.setLayout(layout)

        # Statistiken
        self.dashboard_stats = self._create_dashboard_header()
        layout.addWidget(self.dashboard_stats)

        # Weitere Dashboard-Elemente hier...
        info_label = QLabel("Übersicht über alle Vertriebler im System")
        info_label.setStyleSheet(f"color: {COLORS['text_gray']}; font-size: 14px; padding: 20px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)

        layout.addStretch()

        return tab

    def _create_users_tab(self):
        """Erstelle Vertriebler-Tabellen Tab"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        tab.setLayout(layout)

        # Suchfeld und Neuer-Button
        top_layout = QHBoxLayout()

        search_label = QLabel("🔍 Suche:")
        search_label.setStyleSheet(f"color: {COLORS['text_dark']}; font-weight: bold;")
        top_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Suche nach Name oder Login...")
        self.search_input.setMinimumWidth(300)
        self.search_input.textChanged.connect(self._filter_users)
        top_layout.addWidget(self.search_input)

        top_layout.addStretch()

        new_btn = QPushButton("➕ Neuer Vertriebler")
        new_btn.setObjectName("primaryBtn")
        new_btn.clicked.connect(self.create_user)
        top_layout.addWidget(new_btn)

        layout.addLayout(top_layout)

        # Tabelle
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Vorname", "Nachname", "Login", "Template", "Status", "Aktionen"])

        # Spaltenbreiten
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        # Zeilenhöhe für bessere Button-Darstellung
        self.table.verticalHeader().setDefaultSectionSize(50)

        # Tabellen-Styling (Zebrastreifen, Hover)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(self.table.styleSheet() + f"""
            QTableWidget::item:alternate {{
                background-color: {COLORS['bg_light']};
            }}
            QTableWidget::item:hover {{
                background-color: {COLORS['accent_blue']};
                color: {COLORS['white']};
            }}
        """)

        layout.addWidget(self.table)

        return tab

    def _create_dashboard_header(self):
        """Erstelle Dashboard-Header mit Statistiken"""
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setSpacing(15)
        widget.setLayout(layout)

        # Gesamtanzahl
        total_users = len(self.user_manager.get_all_users())
        total_card = self._create_stat_card("👥 Gesamt", str(total_users), COLORS['primary_blue'])
        layout.addWidget(total_card)

        # Aktive Vertriebler (letzter Login < 30 Tage)
        active_count = self.user_manager.get_active_user_count()
        active_card = self._create_stat_card("✓ Aktiv", str(active_count), COLORS['success_green'])
        layout.addWidget(active_card)

        # Inaktive Vertriebler
        inactive_count = self.user_manager.get_inactive_user_count()
        inactive_card = self._create_stat_card("✗ Inaktiv", str(inactive_count), COLORS['text_gray'])
        layout.addWidget(inactive_card)

        layout.addStretch()

        return widget

    def _create_stat_card(self, title: str, value: str, color: str):
        """Erstelle Statistik-Card"""
        card = QWidget()
        card.setMinimumWidth(150)
        card.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['white']};
                border: 2px solid {color};
                border-radius: 10px;
                padding: 20px;
            }}
        """)

        layout = QVBoxLayout()
        layout.setSpacing(8)
        card.setLayout(layout)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: bold;")
        layout.addWidget(value_label)

        return card

    def load_users(self, users=None):
        """Lade Vertriebler in Tabelle"""
        if users is None:
            users = self.user_manager.get_all_users()
            self.all_users = users  # Speichere für Suche

        self.table.setRowCount(len(users))

        for row, user in enumerate(users):
            # ID
            id_item = QTableWidgetItem(str(user["id"]))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, id_item)

            # Vorname
            vorname_item = QTableWidgetItem(user["vorname"])
            self.table.setItem(row, 1, vorname_item)

            # Nachname
            nachname_item = QTableWidgetItem(user["nachname"])
            self.table.setItem(row, 2, nachname_item)

            # Login
            login_item = QTableWidgetItem(user["login"])
            self.table.setItem(row, 3, login_item)

            # Template
            template = user.get("template", "")
            template_name = Path(template).name if template else "Keine"
            template_item = QTableWidgetItem(template_name)
            self.table.setItem(row, 4, template_item)

            # Status (basierend auf last_login) als Tag
            is_active = self.user_manager.is_user_active(user)
            status_widget = QWidget()
            status_layout = QHBoxLayout()
            status_layout.setContentsMargins(8, 4, 8, 4)
            status_widget.setLayout(status_layout)

            # Status-Tag
            status_tag = QLabel("Aktiv" if is_active else "Inaktiv")
            status_color = COLORS['success_green'] if is_active else COLORS['text_gray']
            status_bg = '#e8f5e9' if is_active else '#f5f5f5'
            status_tag.setStyleSheet(f"""
                QLabel {{
                    background-color: {status_bg};
                    color: {status_color};
                    border: 1px solid {status_color};
                    border-radius: 12px;
                    padding: 4px 12px;
                    font-size: 11px;
                    font-weight: bold;
                }}
            """)
            status_tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
            status_layout.addWidget(status_tag)
            status_layout.addStretch()

            self.table.setCellWidget(row, 5, status_widget)

            # Aktionen (Bearbeiten & Löschen Icon-Buttons ohne Hintergrund)
            action_widget = QWidget()
            action_layout = QHBoxLayout()
            action_layout.setContentsMargins(8, 4, 8, 4)
            action_layout.setSpacing(8)
            action_widget.setLayout(action_layout)

            # Bearbeiten-Button (Blauer Stift)
            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(35, 35)
            edit_btn.setToolTip("Vertriebler bearbeiten")
            edit_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    font-size: 20px;
                }}
                QPushButton:hover {{
                    background-color: #e3f2fd;
                    border-radius: 6px;
                }}
            """)
            edit_btn.clicked.connect(lambda checked, u=user: self.edit_user_direct(u))
            action_layout.addWidget(edit_btn)

            # Löschen-Button (Rote Mülltonne)
            delete_btn = QPushButton("🗑️")
            delete_btn.setFixedSize(35, 35)
            delete_btn.setToolTip("Vertriebler löschen")
            delete_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    font-size: 20px;
                }}
                QPushButton:hover {{
                    background-color: #ffebee;
                    border-radius: 6px;
                }}
            """)
            delete_btn.clicked.connect(lambda checked, u=user: self.delete_user_direct(u))
            action_layout.addWidget(delete_btn)

            action_layout.addStretch()

            self.table.setCellWidget(row, 6, action_widget)

        # Aktualisiere Dashboard
        self._update_dashboard()

    def create_user(self):
        """Neuen Vertriebler anlegen"""
        dialog = UserDialog(self)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()

            # Validierung
            if not data["vorname"] or not data["nachname"]:
                QMessageBox.warning(
                    self,
                    "Fehler",
                    "Bitte geben Sie Vor- und Nachname ein."
                )
                return

            try:
                self.user_manager.create_user(
                    data["vorname"],
                    data["nachname"],
                    data["template_path"]
                )

                QMessageBox.information(
                    self,
                    "Erfolg",
                    f"Vertriebler {data['vorname']} {data['nachname']} wurde angelegt."
                )

                self.load_users()

            except ValueError as e:
                QMessageBox.critical(
                    self,
                    "Fehler",
                    str(e)
                )

    def edit_user_direct(self, user: dict):
        """Vertriebler direkt bearbeiten (von Action-Button)"""
        dialog = UserDialog(self, user)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()

            # Validierung
            if not data["vorname"] or not data["nachname"]:
                QMessageBox.warning(
                    self,
                    "Fehler",
                    "Bitte geben Sie Vor- und Nachname ein."
                )
                return

            try:
                self.user_manager.update_user(
                    user["id"],
                    data["vorname"],
                    data["nachname"],
                    data["template_path"],
                    data.get("active", True)
                )

                QMessageBox.information(
                    self,
                    "Erfolg",
                    f"Vertriebler wurde aktualisiert."
                )

                self.load_users()

            except ValueError as e:
                QMessageBox.critical(
                    self,
                    "Fehler",
                    str(e)
                )

    def delete_user_direct(self, user: dict):
        """Vertriebler direkt löschen (von Action-Button)"""
        reply = QMessageBox.question(
            self,
            "Vertriebler löschen",
            f"Möchten Sie {user['vorname']} {user['nachname']} wirklich löschen?\n\nDieser Vorgang kann nicht rückgängig gemacht werden.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.user_manager.delete_user(user["id"])

                QMessageBox.information(
                    self,
                    "Erfolg",
                    f"Vertriebler wurde gelöscht."
                )

                self.load_users()

            except ValueError as e:
                QMessageBox.critical(
                    self,
                    "Fehler",
                    str(e)
                )

    def _filter_users(self):
        """Filtere Vertriebler basierend auf Suchbegriff"""
        search_text = self.search_input.text().lower()

        if not search_text:
            # Zeige alle User
            self.load_users(self.all_users)
            return

        # Filtere nach Vorname, Nachname oder Login
        filtered_users = [
            user for user in self.all_users
            if search_text in user["vorname"].lower()
            or search_text in user["nachname"].lower()
            or search_text in user["login"].lower()
        ]

        self.load_users(filtered_users)

    def _update_dashboard(self):
        """Aktualisiere Dashboard-Statistiken"""
        # Entferne altes Dashboard
        if hasattr(self, 'dashboard_stats'):
            old_layout = self.dashboard_stats.layout()
            if old_layout:
                while old_layout.count():
                    item = old_layout.takeAt(0)
                    if item.widget():
                        item.widget().deleteLater()

            # Erstelle neues Dashboard
            layout = self.dashboard_stats.layout()

            # Gesamtanzahl
            total_users = len(self.user_manager.get_all_users())
            total_card = self._create_stat_card("👥 Gesamt", str(total_users), COLORS['primary_blue'])
            layout.addWidget(total_card)

            # Aktive Vertriebler
            active_count = self.user_manager.get_active_user_count()
            active_card = self._create_stat_card("✓ Aktiv", str(active_count), COLORS['success_green'])
            layout.addWidget(active_card)

            # Inaktive Vertriebler
            inactive_count = self.user_manager.get_inactive_user_count()
            inactive_card = self._create_stat_card("✗ Inaktiv", str(inactive_count), COLORS['text_gray'])
            layout.addWidget(inactive_card)

            layout.addStretch()

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
