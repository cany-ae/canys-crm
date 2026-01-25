#!/usr/bin/env python3
"""
Angebotstool für Allianz - Haupteinstiegspunkt
Desktop-Anwendung für PDF-Upload und PowerPoint-Angebotserstellung
"""

import sys
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow


def main():
    """Starte die Anwendung"""
    app = QApplication(sys.argv)
    app.setApplicationName("Allianz Angebotstool")
    app.setOrganizationName("Canys CRM")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
