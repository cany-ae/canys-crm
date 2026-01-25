# PyInstaller Specification File für Angebotstool
# Build-Befehl: pyinstaller build_exe.spec

# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

# Projektpfad
project_dir = Path('.').absolute()
src_dir = project_dir / 'src'
templates_dir = project_dir / 'templates'

a = Analysis(
    [str(src_dir / 'main.py')],
    pathex=[str(project_dir), str(src_dir)],
    binaries=[],
    datas=[
        (str(templates_dir), 'templates'),  # Templates mitpacken
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'pdfplumber',
        'pptx',
        'PIL',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Allianz_Angebotstool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Kein Konsolenfenster
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Optional: Icon-Pfad angeben
)
