# -*- mode: python ; coding: utf-8 -*-
"""Spécification PyInstaller pour Tank War : Arena Duel.

Compile le jeu en un binaire autonome exécutable Windows (.exe)
en incluant automatiquement l'arborescence complète des ressources multimédias (assets/).
"""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# Racine du projet
project_dir = Path(__file__).resolve().parent

# Collecte des données (assets, images, sons, icônes)
datas = [
    (str(project_dir / "assets"), "assets"),
    (str(project_dir / "settings.py"), "."),
]

# Modules cachés potentiellement nécessaires
hiddenimports = [
    "pygame",
    "pygame.font",
    "pygame.mixer",
    "pygame.image",
    "pygame.transform",
    "game.ai_controller",
    "network.discovery",
]

a = Analysis(
    ["main.py"],
    pathex=[str(project_dir)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "unittest", "pydoc"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 1. Mode Répertoire Distribuable (Recommandé pour distribution zip / installateur)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="TankWar",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Mode fenêtré (pas de console noire d'arrière-plan)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_dir / "assets" / "icons" / "menu" / "play.png") if (project_dir / "assets" / "icons" / "menu" / "play.png").exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="TankWar",
)

