# Projekt: Canys CRM - Angebotstool

## PROJEKT-UEBERSICHT
**Beschreibung:** Desktop-Anwendung (EXE) für Allianz-Angebotserstellung mit PDF-Upload und PowerPoint-Integration
**Tech-Stack:** Python (PyQt6/Tkinter), python-pptx, PyPDF2, cx_Freeze/PyInstaller

---

## BUILD-SERVER
- **Server:** `ssh-eco-crm`
- **Pfad:** `/home/frappe/frappe-bench`

**Befehle:** `ssh-eco-crm run "cd /home/frappe/frappe-bench && BEFEHL"`

---

## AUTONOMIE
**Arbeite KOMPLETT AUTONOM bis fertig!**

---

## PRIORITAETEN
1. Python Desktop-App Grundstruktur (GUI)
2. PDF-Upload und -Verarbeitung
3. PowerPoint-Template Management (7 Vertriebler)
4. Datenextraktion (Pferdename, Kunde, Datum)
5. PowerPoint-Manipulation (Platzhalter für Preise)
6. EXE-Build Pipeline
7. Multi-User Template-System

---

## FUNKTIONALE ANFORDERUNGEN
- **PDF Upload:** AMIS-Angebote für Pferde
- **PowerPoint Templates:** 7 verschiedene Vertriebler-Vorlagen
- **Datenfelder:** Pferdename, Erstelldatum, Kundenname
- **Preisfelder:** 3 gelb markierte Felder als Platzhalter
- **Vertriebler-Auswahl:** Dropdown mit 7 Namen
- **Output:** Fertiges Angebot (PDF + PowerPoint kombiniert)

---

## GITHUB
**Repository:** https://github.com/cany-ae/canys-crm
**Visibility:** PRIVATE

---

## BROWSER-TESTING
**URL:** N/A (Desktop-App)
- EXE-Datei testen mit Sample-Daten

---

## OFFENE TODOS
- [ ] GUI Framework Setup
- [ ] PDF-Parser implementieren
- [ ] PowerPoint-Library Integration
- [ ] Template-Management System
- [ ] EXE-Build Konfiguration
- [ ] Sample-Daten für Tests
- [ ] Desktop-App Test
