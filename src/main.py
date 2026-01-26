#!/usr/bin/env python3
"""
Angebotstool für Allianz - Haupteinstiegspunkt
Desktop-Anwendung für PDF-Upload und Angebotserstellung
"""

import sys
from PyQt6.QtWidgets import QApplication
from gui.login_window import LoginWindow
from gui.admin_window import AdminWindow
from gui.main_window import MainWindow


class Application:
    """Hauptanwendung mit Login-Flow"""

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Allianz Angebotstool")
        self.app.setOrganizationName("Canys CRM")

        self.login_window = None
        self.main_window = None
        self.admin_window = None

    def run(self):
        """Starte die Anwendung"""
        # Zeige Login-Fenster
        self.show_login()
        return self.app.exec()

    def show_login(self):
        """Zeige Login-Fenster"""
        self.login_window = LoginWindow()
        self.login_window.login_successful.connect(self.on_login_success)
        self.login_window.show()

    def on_login_success(self, user: dict):
        """
        Callback nach erfolgreichem Login

        Args:
            user: User-Daten mit 'role' Feld
        """
        role = user.get('role', 'user')

        if role == 'admin':
            # Admin-View öffnen
            self.admin_window = AdminWindow()
            self.admin_window.logout_requested.connect(self.on_logout)
            self.admin_window.show()
        else:
            # Benutzer-GUI öffnen
            self.main_window = MainWindow(user)
            self.main_window.logout_requested.connect(self.on_logout)
            self.main_window.show()

    def on_logout(self):
        """Callback nach Logout - zeige Login-Fenster wieder"""
        # Schließe aktuelle Fenster
        if self.admin_window:
            self.admin_window.close()
            self.admin_window = None
        if self.main_window:
            self.main_window.close()
            self.main_window = None

        # Zeige Login-Fenster
        self.show_login()


def main():
    """Starte die Anwendung"""
    app = Application()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
