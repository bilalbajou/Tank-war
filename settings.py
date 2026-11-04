"""Paramètres et configuration centrale du jeu Tank War (Arena Duel).

Centralise les constantes d'affichage, de physique, les chemins d'accès aux assets
et la palette de couleurs cartoon.
"""

import sys
from pathlib import Path

# Chemins d'accès du projet (compatible exécution Python standard et bundle PyInstaller)
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent

ASSETS_DIR = BASE_DIR / "assets"
MAPS_DIR = ASSETS_DIR / "maps"
OBSTACLES_DIR = ASSETS_DIR / "obstacles"
SPRITES_DIR = ASSETS_DIR / "sprites"
SOUNDS_DIR = ASSETS_DIR / "sounds"
FONTS_DIR = ASSETS_DIR / "fonts"
ICONS_DIR = ASSETS_DIR / "icons"
POWERUPS_DIR = ASSETS_DIR / "powerups"

# Paramètres d'affichage
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 900
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)
FPS = 60
WINDOW_TITLE = "Tank War - Arena Duel"

# Arène et bordures
BORDER_THICKNESS = 28
ARENA_RECT = (BORDER_THICKNESS, BORDER_THICKNESS, SCREEN_WIDTH - 2 * BORDER_THICKNESS, SCREEN_HEIGHT - 2 * BORDER_THICKNESS)

# Dimensions des obstacles (en pixels)
CRATE_SIZE = 64
BARRIER_H_WIDTH = 120
BARRIER_H_HEIGHT = 40
BARRIER_V_WIDTH = 40
BARRIER_V_HEIGHT = 120
ROCK_LARGE_SIZE = 80
ROCK_SMALL_SIZE = 48
CACTUS_SIZE = 64
BUSH_SIZE = 54

# Spawns des joueurs (Positions équilibrées pour le duel)
PLAYER_1_SPAWN = (180, 450, 0.0)      # (X, Y, rotation en degrés)
PLAYER_2_SPAWN = (1420, 450, 180.0)

# Paramètres des projectiles
BULLET_SPEED = 650.0

# Palette de couleurs Cartoon Désertique
COLOR_SAND = (235, 209, 153)
COLOR_SAND_DARK = (214, 184, 126)
COLOR_BORDER_WALL = (82, 48, 22)
COLOR_BORDER_INNER = (140, 110, 75)

COLOR_WOOD_CRATE = (184, 125, 75)
COLOR_HAZARD_YELLOW = (255, 204, 0)
COLOR_HAZARD_BLACK = (35, 38, 45)
COLOR_ROCK = (165, 155, 145)
COLOR_CACTUS = (58, 175, 85)

COLOR_SHADOW = (40, 30, 20, 70)
COLOR_UI_TEXT = (250, 250, 250)
COLOR_UI_MUTED = (190, 190, 190)

