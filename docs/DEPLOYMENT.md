# Deployment und GitHub Setup

## GitHub Repository erstellen

Das Projekt ist bereit für GitHub. Führe folgende Schritte aus:

### Option 1: Mit gh CLI (empfohlen)

```bash
# gh CLI installieren (falls nicht vorhanden)
# Siehe: https://cli.github.com/

# Repository erstellen und pushen
cd ~/claude-projects/canys-crm
gh repo create canys-crm --private --source=. --remote=origin --push
```

### Option 2: Manuell über GitHub Web

1. Gehe zu https://github.com/new
2. Repository-Name: `canys-crm`
3. Visibility: **Private**
4. KEINE README, .gitignore oder LICENSE hinzufügen (bereits vorhanden)
5. Klicke "Create repository"

Dann im Terminal:

```bash
cd ~/claude-projects/canys-crm

# Remote hinzufügen (falls noch nicht geschehen)
git remote add origin https://github.com/cany-ae/canys-crm.git

# Pushen
git push -u origin master
```

### Option 3: Mit Personal Access Token

Falls Push fehlschlägt (Authentifizierung):

```bash
# 1. Token erstellen auf GitHub
# https://github.com/settings/tokens
# Scopes: repo, workflow

# 2. Token als Umgebungsvariable setzen
export GITHUB_TOKEN="ghp_xxx..."

# 3. Remote mit Token
git remote set-url origin https://${GITHUB_TOKEN}@github.com/cany-ae/canys-crm.git

# 4. Pushen
git push -u origin master
```

## Weitere Commits

Nach Änderungen am Code:

```bash
cd ~/claude-projects/canys-crm

# Änderungen stagen
git add .

# Commit erstellen
git commit -m "feat: Beschreibung der Änderung"

# Pushen
git push
```

## Release erstellen

Für eine neue Version:

```bash
# Tag erstellen
git tag -a v1.0.0 -m "Version 1.0.0 - Initiale Release"

# Tag pushen
git push origin v1.0.0
```

Dann auf GitHub:
1. Gehe zu Releases
2. "Create a new release"
3. Wähle Tag v1.0.0
4. Lade die EXE-Datei hoch (aus `dist/`)
5. Publish release

## Continuous Integration (Optional)

Für automatische Builds bei jedem Push:

Erstelle `.github/workflows/build.yml`:

```yaml
name: Build EXE

on:
  push:
    branches: [ master ]
  pull_request:
    branches: [ master ]

jobs:
  build:
    runs-on: windows-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Create templates
      run: python src/utils/template_creator.py

    - name: Build EXE
      run: pyinstaller build_exe.spec --clean

    - name: Upload artifact
      uses: actions/upload-artifact@v3
      with:
        name: Allianz_Angebotstool
        path: dist/Allianz_Angebotstool.exe
```

## Branching-Strategie

Empfohlene Branches:
- `master` - Produktions-Code
- `develop` - Entwicklungs-Code
- `feature/*` - Neue Features
- `bugfix/*` - Bugfixes

Workflow:
```bash
# Feature-Branch erstellen
git checkout -b feature/neue-funktion

# Arbeiten...
git add .
git commit -m "feat: Neue Funktion"

# Pushen
git push -u origin feature/neue-funktion

# Auf GitHub Pull Request erstellen
# Nach Review: Merge in develop/master
```

## Sicherheit

**WICHTIG:** Niemals committen:
- Passwörter
- API-Keys
- Zugangsdaten
- `.env` Dateien mit Secrets

Falls versehentlich committed:
```bash
# Entferne aus Git-Historie
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch pfad/zur/datei" \
  --prune-empty --tag-name-filter cat -- --all

# Force-Push (VORSICHT!)
git push origin --force --all
```

## Backup

Regelmäßige Backups:
```bash
# Lokales Backup
cd ~
tar -czf canys-crm-backup-$(date +%Y%m%d).tar.gz claude-projects/canys-crm/

# Auf externen Server
scp canys-crm-backup-*.tar.gz backup-server:/backups/
```
