# Bedienungsanleitung - Allianz Angebotstool

## Übersicht

Das Angebotstool automatisiert die Erstellung von Pferde-Versicherungsangeboten aus AMIS PDF-Dateien.

## Workflow

### Schritt 1: Anwendung starten

```bash
python3 src/main.py
```

Oder die EXE-Datei doppelklicken (nach Build).

### Schritt 2: Vertriebler auswählen

Im oberen Bereich der Anwendung:
- Dropdown-Menü öffnen
- Einen der 7 Vertriebler auswählen
- Das entsprechende PowerPoint-Template wird automatisch geladen

### Schritt 3: PDF hochladen

1. Button "📁 PDF auswählen" klicken
2. AMIS Pferde-Angebots-PDF auswählen
3. Die Anwendung extrahiert automatisch:
   - **Pferdename**
   - **Kundenname**
   - **Erstelldatum**

### Schritt 4: Extrahierte Daten prüfen

Die automatisch extrahierten Daten werden in den Feldern angezeigt:
- Pferdename: z.B. "Donnerwetter"
- Kunde: z.B. "Max Mustermann"
- Erstelldatum: z.B. "15.01.2026"

**Hinweis:** Felder sind schreibgeschützt, da sie automatisch befüllt werden.

### Schritt 5: Angebot generieren

1. Button "📄 Angebot generieren" klicken
2. Fortschrittsanzeige erscheint
3. Prozess läuft in 3 Phasen:
   - **Phase 1 (20%):** PDF-Daten werden extrahiert
   - **Phase 2 (60%):** PowerPoint wird generiert
   - **Phase 3 (100%):** Fertig!

### Schritt 6: Ergebnis

- PowerPoint-Datei wird automatisch erstellt
- Speicherort: `~/Desktop/Angebote/`
- Dateiname: `Angebot_[PDF-Name].pptx`
- Erfolgsmeldung mit Pfad wird angezeigt

## PowerPoint-Angebot

Das generierte PowerPoint enthält:

### Automatisch befüllte Felder
- ✅ Pferdename
- ✅ Kundenname
- ✅ Erstelldatum
- ✅ Vertriebler-Name

### Manuell auszufüllende Felder
- 🟨 Preis 1 (Basis-Schutz)
- 🟨 Preis 2 (Premium-Schutz)
- 🟨 Preis 3 (Komplett-Schutz)

Die 3 Preisfelder sind **gelb markiert** und müssen manuell ausgefüllt werden.

## Vertriebler-Templates

Es gibt 7 verschiedene Templates:
1. Vertriebler 1
2. Vertriebler 2
3. Vertriebler 3
4. Vertriebler 4
5. Vertriebler 5
6. Vertriebler 6
7. Vertriebler 7

Jedes Template kann individuell angepasst werden:
- Logo
- Farben
- Layout
- Kontaktdaten

Templates befinden sich in: `templates/template_vertriebler_[1-7].pptx`

## Tipps & Tricks

### PDF-Qualität

Für beste Ergebnisse:
- ✅ PDF sollte Text enthalten (kein gescanntes Bild)
- ✅ AMIS-Standard-Format verwenden
- ✅ Alle relevanten Felder sollten befüllt sein

### Template anpassen

1. Öffne `templates/template_vertriebler_X.pptx`
2. Bearbeite Design, Logo, Farben
3. Platzhalter **NICHT** entfernen:
   - `{{PFERDENAME}}`
   - `{{KUNDE}}`
   - `{{DATUM}}`
   - `{{VERTRIEBLER}}`
4. Speichere Template

### Fehlerbehandlung

**Problem:** "Keine Daten gefunden"
- **Lösung:** Prüfe ob PDF Text-basiert ist

**Problem:** "Template nicht gefunden"
- **Lösung:** Führe `python3 src/utils/template_creator.py` aus

**Problem:** "Anwendung startet nicht"
- **Lösung:** Prüfe Python-Version (`python3 --version`)
- **Lösung:** Installiere Dependencies neu (`pip install -r requirements.txt`)

## Batch-Verarbeitung

Für mehrere PDFs:
1. Ersten Fall komplett durchführen
2. Für nächsten Fall: Neues PDF auswählen
3. Angebot generieren
4. Wiederholen

**Tipp:** Anwendung bleibt geöffnet für schnelle Mehrfach-Verarbeitung.

## Ausgabe-Verzeichnis

Alle generierten Angebote werden gespeichert in:
- **Linux/Mac:** `~/Desktop/Angebote/`
- **Windows:** `C:\Users\[Username]\Desktop\Angebote\`

Das Verzeichnis wird automatisch erstellt, falls nicht vorhanden.

## Tastenkürzel

- **Strg+O:** PDF-Datei öffnen
- **Strg+G:** Angebot generieren (wenn bereit)
- **Strg+Q:** Anwendung beenden

## Support

Bei Problemen:
1. Prüfe `docs/INSTALLATION.md`
2. Prüfe `docs/TROUBLESHOOTING.md`
3. Erstelle Issue auf GitHub
