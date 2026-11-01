"""Générateur de sprites 2D cartoon pour Arena Duel.

Génère des sprites PNG transparents 32-bit de qualité dans assets/maps/ et assets/obstacles/.
Documentés comme sprites originaux procéduraux au style cartoon pour le jeu.
"""

import os
import math
import pygame
from pathlib import Path

# Initialisation de Pygame en mode sans tête
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
MAPS_DIR = ASSETS_DIR / "maps"
OBSTACLES_DIR = ASSETS_DIR / "obstacles"

MAPS_DIR.mkdir(parents=True, exist_ok=True)
OBSTACLES_DIR.mkdir(parents=True, exist_ok=True)

# Palette de couleurs cartoon lumineuse
COLOR_SAND = (235, 209, 153)
COLOR_SAND_DARK = (214, 184, 126)
COLOR_SAND_LIGHT = (248, 226, 178)
COLOR_SAND_DUNE = (196, 164, 105)

COLOR_WOOD_BASE = (184, 125, 75)
COLOR_WOOD_DARK = (138, 88, 48)
COLOR_WOOD_LIGHT = (212, 152, 98)
COLOR_WOOD_BORDER = (82, 48, 22)
COLOR_METAL_CORNER = (170, 175, 185)
COLOR_METAL_DARK = (95, 100, 110)

COLOR_HAZARD_YELLOW = (255, 204, 0)
COLOR_HAZARD_BLACK = (35, 38, 45)
COLOR_BARRIER_FRAME = (120, 125, 135)
COLOR_BARRIER_DARK = (60, 64, 72)

COLOR_ROCK_BASE = (165, 155, 145)
COLOR_ROCK_LIGHT = (198, 188, 178)
COLOR_ROCK_SHADOW = (118, 108, 98)
COLOR_ROCK_OUTLINE = (70, 65, 60)

COLOR_CACTUS_BASE = (58, 175, 85)
COLOR_CACTUS_DARK = (38, 135, 62)
COLOR_CACTUS_LIGHT = (92, 210, 120)
COLOR_CACTUS_OUTLINE = (24, 85, 38)
COLOR_CACTUS_FLOWER = (245, 65, 95)

COLOR_SHADOW = (40, 30, 20, 75)


def generate_desert_background(width=1600, height=900) -> pygame.Surface:
    """Génère la texture complète du sol désertique avec dunes ondulées."""
    surf = pygame.Surface((width, height))
    surf.fill(COLOR_SAND)

    # 1. Bandes ondulées douces (dunes de sable)
    dune_overlay = pygame.Surface((width, height), pygame.SRCALPHA)
    for y_band in range(0, height, 120):
        points = []
        for x in range(0, width + 40, 20):
            # Onde sinusoïdale douce
            wave_y = y_band + math.sin(x * 0.008 + y_band * 0.05) * 22 + math.cos(x * 0.02) * 8
            points.append((x, wave_y))
        points.append((width, height))
        points.append((0, height))
        pygame.draw.polygon(dune_overlay, (214, 184, 126, 45), points)
    surf.blit(dune_overlay, (0, 0))

    # 2. Textures et ondulations de vent (petites rides de sable)
    ripple_surf = pygame.Surface((width, height), pygame.SRCALPHA)
    for y in range(20, height - 20, 35):
        offset = (y * 37) % 80
        for x in range(offset, width, 140):
            w = 55 + (x % 35)
            # Ride claire
            pygame.draw.arc(ripple_surf, (248, 226, 178, 90), (x, y, w, 16), 0.1, math.pi * 0.9, 2)
            # Ombre sous la ride
            pygame.draw.arc(ripple_surf, (185, 155, 95, 70), (x, y + 2, w, 16), 0.1, math.pi * 0.9, 1)

    surf.blit(ripple_surf, (0, 0))

    # 3. Petits cailloux décoratifs sur le sol
    pebbles = [
        (220, 180, 5), (340, 720, 4), (520, 380, 6), (740, 820, 4),
        (920, 120, 5), (1100, 580, 6), (1350, 320, 4), (1480, 780, 5),
        (400, 500, 3), (1240, 210, 4), (680, 260, 5), (980, 710, 5)
    ]
    for px, py, r in pebbles:
        pygame.draw.circle(surf, COLOR_SAND_DUNE, (px + 1, py + 2), r)
        pygame.draw.circle(surf, COLOR_ROCK_BASE, (px, py), r)
        pygame.draw.circle(surf, COLOR_ROCK_LIGHT, (px - 1, py - 1), max(1, r - 2))

    return surf


def generate_crate(size=64, damaged=False) -> pygame.Surface:
    """Génère une caisse en bois cartoon avec renforts et rivets."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Corps en bois
    rect = pygame.Rect(4, 4, size - 8, size - 8)
    pygame.draw.rect(surf, COLOR_WOOD_BASE, rect, border_radius=5)
    
    # Lattes de bois intérieures (horizontales)
    plank_h = rect.height / 3.0
    for i in range(1, 3):
        y = int(rect.top + i * plank_h)
        pygame.draw.line(surf, COLOR_WOOD_DARK, (rect.left + 2, y), (rect.right - 2, y), 2)
        pygame.draw.line(surf, COLOR_WOOD_LIGHT, (rect.left + 2, y + 2), (rect.right - 2, y + 2), 1)

    # Renfort en X (croix diagonale)
    pygame.draw.line(surf, COLOR_WOOD_DARK, (rect.left + 4, rect.top + 4), (rect.right - 4, rect.bottom - 4), 6)
    pygame.draw.line(surf, COLOR_WOOD_LIGHT, (rect.left + 4, rect.top + 5), (rect.right - 4, rect.bottom - 3), 3)

    pygame.draw.line(surf, COLOR_WOOD_DARK, (rect.left + 4, rect.bottom - 4), (rect.right - 4, rect.top + 4), 6)
    pygame.draw.line(surf, COLOR_WOOD_LIGHT, (rect.left + 4, rect.bottom - 3), (rect.right - 4, rect.top + 5), 3)

    # Coins métalliques
    corner_size = 12
    corners = [rect.topleft, (rect.right - corner_size, rect.top),
               (rect.left, rect.bottom - corner_size), (rect.right - corner_size, rect.bottom - corner_size)]
    for cx, cy in corners:
        c_rect = pygame.Rect(cx, cy, corner_size, corner_size)
        pygame.draw.rect(surf, COLOR_METAL_CORNER, c_rect, border_radius=2)
        pygame.draw.rect(surf, COLOR_METAL_DARK, c_rect, width=1, border_radius=2)
        # Rivet
        pygame.draw.circle(surf, (40, 45, 50), (cx + corner_size // 2, cy + corner_size // 2), 2)

    # Contour cartoon foncé
    pygame.draw.rect(surf, COLOR_WOOD_BORDER, rect, width=3, border_radius=5)

    if damaged:
        # Fissures / impacts
        pygame.draw.lines(surf, (40, 20, 10), False, [(22, 14), (28, 28), (22, 38), (32, 50)], 3)
        pygame.draw.lines(surf, (40, 20, 10), False, [(42, 24), (36, 34)], 2)

    return surf


def generate_barrier_horizontal(width=120, height=40) -> pygame.Surface:
    """Génère une barrière de chantier / sécurité avec bandes jaunes et noires."""
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Pieds de support métalliques
    foot_w, foot_h = 14, height
    pygame.draw.rect(surf, COLOR_BARRIER_FRAME, (4, 0, foot_w, foot_h), border_radius=3)
    pygame.draw.rect(surf, COLOR_BARRIER_DARK, (4, 0, foot_w, foot_h), 2, border_radius=3)
    pygame.draw.rect(surf, COLOR_BARRIER_FRAME, (width - foot_w - 4, 0, foot_w, foot_h), border_radius=3)
    pygame.draw.rect(surf, COLOR_BARRIER_DARK, (width - foot_w - 4, 0, foot_w, foot_h), 2, border_radius=3)

    # Panneau principal
    panel_rect = pygame.Rect(8, 8, width - 16, height - 16)
    panel_surf = pygame.Surface((panel_rect.width, panel_rect.height))
    panel_surf.fill(COLOR_HAZARD_YELLOW)

    # Bandes diagonales noires (Hazard Stripes)
    stripe_w = 16
    for x in range(-panel_rect.height, panel_rect.width + panel_rect.height, stripe_w * 2):
        points = [
            (x, 0),
            (x + stripe_w, 0),
            (x + stripe_w + panel_rect.height, panel_rect.height),
            (x + panel_rect.height, panel_rect.height),
        ]
        pygame.draw.polygon(panel_surf, COLOR_HAZARD_BLACK, points)

    # Bordure interne du panneau
    pygame.draw.rect(panel_surf, (20, 20, 20), (0, 0, panel_rect.width, panel_rect.height), 2)
    surf.blit(panel_surf, panel_rect.topleft)

    # Contour et rivets de fixation
    pygame.draw.circle(surf, (220, 220, 220), (12, height // 2), 3)
    pygame.draw.circle(surf, (30, 30, 30), (12, height // 2), 1)
    pygame.draw.circle(surf, (220, 220, 220), (width - 12, height // 2), 3)
    pygame.draw.circle(surf, (30, 30, 30), (width - 12, height // 2), 1)

    return surf


def generate_barrier_vertical(width=40, height=120) -> pygame.Surface:
    """Génère la barrière orientée verticalement."""
    horiz = generate_barrier_horizontal(height, width)
    return pygame.transform.rotate(horiz, 90)


def generate_rock(size=80) -> pygame.Surface:
    """Génère un rocher désertique avec facettes et éclairage contrasté."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size / 2.0, size / 2.0

    # Silhouette polygonale cartoon du rocher
    points = [
        (cx - 30, cy - 10),
        (cx - 18, cy - 32),
        (cx + 10, cy - 35),
        (cx + 32, cy - 15),
        (cx + 34, cy + 18),
        (cx + 12, cy + 34),
        (cx - 16, cy + 32),
        (cx - 32, cy + 14),
    ]

    # Ombre de base
    pygame.draw.polygon(surf, COLOR_ROCK_SHADOW, points)

    # Facette éclairée (Nord-Ouest)
    highlight_points = [
        (cx - 30, cy - 10),
        (cx - 18, cy - 32),
        (cx + 10, cy - 35),
        (cx + 5, cy - 8),
        (cx - 12, cy + 2),
    ]
    pygame.draw.polygon(surf, COLOR_ROCK_LIGHT, highlight_points)

    # Facette médiane
    mid_points = [
        (cx + 10, cy - 35),
        (cx + 32, cy - 15),
        (cx + 14, cy + 4),
        (cx + 5, cy - 8),
    ]
    pygame.draw.polygon(surf, COLOR_ROCK_BASE, mid_points)

    # Lignes de structure internes (crêtes rocheuses)
    pygame.draw.line(surf, COLOR_ROCK_OUTLINE, (cx - 18, cy - 32), (cx - 12, cy + 2), 2)
    pygame.draw.line(surf, COLOR_ROCK_OUTLINE, (cx + 10, cy - 35), (cx + 5, cy - 8), 2)
    pygame.draw.line(surf, COLOR_ROCK_OUTLINE, (cx + 5, cy - 8), (cx + 14, cy + 4), 2)
    pygame.draw.line(surf, COLOR_ROCK_OUTLINE, (cx - 12, cy + 2), (cx + 14, cy + 4), 2)
    pygame.draw.line(surf, COLOR_ROCK_OUTLINE, (cx + 14, cy + 4), (cx + 12, cy + 34), 2)

    # Contour cartoon sombre
    pygame.draw.polygon(surf, COLOR_ROCK_OUTLINE, points, width=3)

    return surf


def generate_rock_small(size=48) -> pygame.Surface:
    """Génère un petit rocher désertique."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size / 2.0, size / 2.0
    points = [
        (cx - 16, cy - 6),
        (cx - 8, cy - 18),
        (cx + 12, cy - 16),
        (cx + 20, cy),
        (cx + 14, cy + 18),
        (cx - 8, cy + 18),
        (cx - 18, cy + 8),
    ]
    pygame.draw.polygon(surf, COLOR_ROCK_SHADOW, points)
    pygame.draw.polygon(surf, COLOR_ROCK_LIGHT, [points[0], points[1], points[2], (cx, cy), (cx - 8, cy + 2)])
    pygame.draw.polygon(surf, COLOR_ROCK_OUTLINE, points, width=3)
    return surf


def generate_cactus(size=64) -> pygame.Surface:
    """Génère un cactus cartoon désertique avec branches et fleur décorative."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2

    # Tronc central
    trunk = pygame.Rect(cx - 8, cy - 24, 16, 48)
    pygame.draw.rect(surf, COLOR_CACTUS_BASE, trunk, border_radius=8)
    # Ligne d'éclairage
    pygame.draw.line(surf, COLOR_CACTUS_LIGHT, (trunk.left + 3, trunk.top + 6), (trunk.left + 3, trunk.bottom - 4), 3)

    # Branche gauche
    b_left_h = pygame.Rect(cx - 24, cy - 4, 18, 10)
    b_left_v = pygame.Rect(cx - 24, cy - 18, 10, 18)
    pygame.draw.rect(surf, COLOR_CACTUS_BASE, b_left_h, border_radius=4)
    pygame.draw.rect(surf, COLOR_CACTUS_BASE, b_left_v, border_radius=4)

    # Branche droite (plus haute)
    b_right_h = pygame.Rect(cx + 6, cy - 12, 18, 10)
    b_right_v = pygame.Rect(cx + 14, cy - 24, 10, 18)
    pygame.draw.rect(surf, COLOR_CACTUS_BASE, b_right_h, border_radius=4)
    pygame.draw.rect(surf, COLOR_CACTUS_BASE, b_right_v, border_radius=4)

    # Contours cartoon
    pygame.draw.rect(surf, COLOR_CACTUS_OUTLINE, trunk, width=2, border_radius=8)
    pygame.draw.rect(surf, COLOR_CACTUS_OUTLINE, b_left_h, width=2, border_radius=4)
    pygame.draw.rect(surf, COLOR_CACTUS_OUTLINE, b_left_v, width=2, border_radius=4)
    pygame.draw.rect(surf, COLOR_CACTUS_OUTLINE, b_right_h, width=2, border_radius=4)
    pygame.draw.rect(surf, COLOR_CACTUS_OUTLINE, b_right_v, width=2, border_radius=4)

    # Petite fleur rouge au sommet
    pygame.draw.circle(surf, COLOR_CACTUS_FLOWER, (cx, cy - 23), 5)
    pygame.draw.circle(surf, (255, 230, 80), (cx, cy - 23), 2)

    return surf


def generate_bush(size=54) -> pygame.Surface:
    """Génère un buisson succulent désertique doux."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2

    circles = [
        (cx - 10, cy - 6, 15, COLOR_CACTUS_DARK),
        (cx + 10, cy - 6, 14, COLOR_CACTUS_BASE),
        (cx, cy + 8, 16, COLOR_CACTUS_DARK),
        (cx - 4, cy - 2, 14, COLOR_CACTUS_LIGHT),
        (cx + 4, cy + 4, 12, COLOR_CACTUS_BASE),
    ]
    for x, y, r, col in circles:
        pygame.draw.circle(surf, col, (x, y), r)
        pygame.draw.circle(surf, COLOR_CACTUS_OUTLINE, (x, y), r, 2)

    return surf


def generate_border_tile(size=32) -> pygame.Surface:
    """Génère un bloc de muret / forteresse pour délimiter l'arène."""
    surf = pygame.Surface((size, size))
    surf.fill(COLOR_WOOD_BORDER)
    # Pierre intérieure
    inner = pygame.Rect(2, 2, size - 4, size - 4)
    pygame.draw.rect(surf, (140, 110, 75), inner)
    # Biseau supérieur
    pygame.draw.line(surf, (190, 160, 120), inner.topleft, inner.topright, 2)
    pygame.draw.line(surf, (190, 160, 120), inner.topleft, inner.bottomleft, 2)
    # Biseau inférieur
    pygame.draw.line(surf, (90, 70, 45), inner.bottomleft, inner.bottomright, 2)
    pygame.draw.line(surf, (90, 70, 45), inner.topright, inner.bottomright, 2)
    return surf


def generate_tank_sprite(color_name: str = "red", width: int = 68, height: int = 52) -> pygame.Surface:
    """Génère un sprite de tank cartoon 2D vue du dessus avec chenilles, châssis, tourelle et canon."""
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    is_red = color_name.lower() == "red"

    # Nuances de couleur cartoon
    c_primary = (225, 55, 50) if is_red else (42, 185, 95)
    c_highlight = (250, 110, 105) if is_red else (95, 225, 140)
    c_shadow = (155, 25, 25) if is_red else (22, 115, 52)
    c_turret = (185, 35, 35) if is_red else (28, 140, 68)
    c_turret_light = (235, 80, 80) if is_red else (65, 205, 115)
    c_outline = (25, 20, 25)

    # 1. Chenilles (Treads)
    tread_color = (48, 50, 58)
    tread_notch = (82, 86, 98)

    # Chenille haute
    top_tread = pygame.Rect(4, 2, 58, 12)
    pygame.draw.rect(surf, tread_color, top_tread, border_radius=4)
    for x in range(top_tread.left + 5, top_tread.right - 4, 7):
        pygame.draw.line(surf, tread_notch, (x, top_tread.top + 2), (x, top_tread.bottom - 2), 2)
    pygame.draw.rect(surf, c_outline, top_tread, width=2, border_radius=4)

    # Chenille basse
    bot_tread = pygame.Rect(4, height - 14, 58, 12)
    pygame.draw.rect(surf, tread_color, bot_tread, border_radius=4)
    for x in range(bot_tread.left + 5, bot_tread.right - 4, 7):
        pygame.draw.line(surf, tread_notch, (x, bot_tread.top + 2), (x, bot_tread.bottom - 2), 2)
    pygame.draw.rect(surf, c_outline, bot_tread, width=2, border_radius=4)

    # 2. Châssis (Hull)
    hull_rect = pygame.Rect(10, 10, 46, 32)
    pygame.draw.rect(surf, c_primary, hull_rect, border_radius=6)
    # Ligne de biseau / reflet sur l'arrête supérieure du châssis
    pygame.draw.line(surf, c_highlight, (hull_rect.left + 4, hull_rect.top + 3), (hull_rect.right - 4, hull_rect.top + 3), 2)
    # Ombre sous le châssis
    pygame.draw.line(surf, c_shadow, (hull_rect.left + 4, hull_rect.bottom - 3), (hull_rect.right - 4, hull_rect.bottom - 3), 2)

    # Plaque de blindage avant biseautée
    front_plate = [(hull_rect.right - 8, hull_rect.top + 4), (hull_rect.right, hull_rect.top + 10),
                   (hull_rect.right, hull_rect.bottom - 10), (hull_rect.right - 8, hull_rect.bottom - 4)]
    pygame.draw.polygon(surf, c_highlight, front_plate)

    # Rivets métalliques aux 4 coins du châssis
    rivets = [
        (hull_rect.left + 6, hull_rect.top + 7),
        (hull_rect.left + 6, hull_rect.bottom - 7),
        (hull_rect.right - 10, hull_rect.top + 7),
        (hull_rect.right - 10, hull_rect.bottom - 7),
    ]
    for rx, ry in rivets:
        pygame.draw.circle(surf, (220, 225, 235), (rx, ry), 2)
        pygame.draw.circle(surf, c_outline, (rx, ry), 1)

    pygame.draw.rect(surf, c_outline, hull_rect, width=2, border_radius=6)

    # 3. Canon orienté vers l'Est (Muzzle à droite)
    barrel_rect = pygame.Rect(32, 23, 30, 6)
    pygame.draw.rect(surf, (55, 60, 70), barrel_rect, border_radius=2)
    # Reflet supérieur sur le canon
    pygame.draw.line(surf, (110, 118, 130), (barrel_rect.left, barrel_rect.top + 1), (barrel_rect.right, barrel_rect.top + 1), 1)
    pygame.draw.rect(surf, c_outline, barrel_rect, width=2, border_radius=2)

    # Frein de bouche au bout du canon (Muzzle brake)
    brake_rect = pygame.Rect(barrel_rect.right - 2, 21, 6, 10)
    pygame.draw.rect(surf, (40, 44, 52), brake_rect, border_radius=2)
    pygame.draw.rect(surf, c_outline, brake_rect, width=2, border_radius=2)
    # Ouverture noire
    pygame.draw.line(surf, (15, 15, 18), (brake_rect.right - 1, 23), (brake_rect.right - 1, 29), 2)

    # 4. Tourelle circulaire
    turret_center = (32, 26)
    turret_radius = 13
    pygame.draw.circle(surf, c_turret, turret_center, turret_radius)
    # Anneau de lumière supérieur
    pygame.draw.arc(surf, c_turret_light, (turret_center[0] - turret_radius + 2, turret_center[1] - turret_radius + 2,
                                           (turret_radius - 2) * 2, (turret_radius - 2) * 2),
                    math.pi * 0.25, math.pi * 1.1, 2)
    # Ombre inférieure
    pygame.draw.arc(surf, c_shadow, (turret_center[0] - turret_radius + 2, turret_center[1] - turret_radius + 2,
                                     (turret_radius - 2) * 2, (turret_radius - 2) * 2),
                    math.pi * 1.25, math.pi * 2.1, 2)
    pygame.draw.circle(surf, c_outline, turret_center, turret_radius, 2)

    # Trappe de commandement (Hatch)
    hatch_center = (28, 24)
    pygame.draw.circle(surf, (60, 65, 75), hatch_center, 5)
    pygame.draw.circle(surf, (110, 115, 125), hatch_center, 3)
    pygame.draw.circle(surf, c_outline, hatch_center, 5, 1)

    return surf


def generate_bullet_sprite(width: int = 18, height: int = 10) -> pygame.Surface:
    """Génère un obus balistique cartoon avec ogive dorée et traînée de feu."""
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    # Corps de l'obus (cuivre / or)
    body_rect = pygame.Rect(2, 2, 12, 6)
    pygame.draw.rect(surf, (245, 180, 30), body_rect, border_radius=2)
    # Ogive pointue avant
    pygame.draw.polygon(surf, (255, 230, 80), [(12, 2), (17, 5), (12, 8)])
    # Flamme arrière
    pygame.draw.polygon(surf, (240, 70, 30), [(3, 3), (0, 5), (3, 7)])
    # Contour sombre
    pygame.draw.rect(surf, (40, 25, 10), (1, 1, 16, 8), width=1, border_radius=3)
    return surf


def main():
    print("Génération des sprites 2D dans assets/...")

    # 1. Carte désertique
    bg = generate_desert_background(1600, 900)
    pygame.image.save(bg, str(MAPS_DIR / "desert_background.png"))
    print(" -> assets/maps/desert_background.png généré.")

    border_tile = generate_border_tile(32)
    pygame.image.save(border_tile, str(MAPS_DIR / "border_tile.png"))
    print(" -> assets/maps/border_tile.png généré.")

    # 2. Obstacles
    crate = generate_crate(64, damaged=False)
    pygame.image.save(crate, str(OBSTACLES_DIR / "crate.png"))
    print(" -> assets/obstacles/crate.png généré.")

    crate_dmg = generate_crate(64, damaged=True)
    pygame.image.save(crate_dmg, str(OBSTACLES_DIR / "crate_damaged.png"))
    print(" -> assets/obstacles/crate_damaged.png généré.")

    bar_h = generate_barrier_horizontal(120, 40)
    pygame.image.save(bar_h, str(OBSTACLES_DIR / "barrier_horizontal.png"))
    print(" -> assets/obstacles/barrier_horizontal.png généré.")

    bar_v = generate_barrier_vertical(40, 120)
    pygame.image.save(bar_v, str(OBSTACLES_DIR / "barrier_vertical.png"))
    print(" -> assets/obstacles/barrier_vertical.png généré.")

    rock_lg = generate_rock(80)
    pygame.image.save(rock_lg, str(OBSTACLES_DIR / "rock_large.png"))
    print(" -> assets/obstacles/rock_large.png généré.")

    rock_sm = generate_rock_small(48)
    pygame.image.save(rock_sm, str(OBSTACLES_DIR / "rock_small.png"))
    print(" -> assets/obstacles/rock_small.png généré.")

    cactus = generate_cactus(64)
    pygame.image.save(cactus, str(OBSTACLES_DIR / "plant_cactus.png"))
    print(" -> assets/obstacles/plant_cactus.png généré.")

    bush = generate_bush(54)
    pygame.image.save(bush, str(OBSTACLES_DIR / "plant_bush.png"))
    print(" -> assets/obstacles/plant_bush.png généré.")

    # 3. Tanks rouges et verts
    TANKS_DIR = ASSETS_DIR / "tanks"
    SPRITES_TANKS_DIR = ASSETS_DIR / "sprites" / "tanks"
    TANKS_DIR.mkdir(parents=True, exist_ok=True)
    SPRITES_TANKS_DIR.mkdir(parents=True, exist_ok=True)

    tank_red = generate_tank_sprite("red", 68, 52)
    pygame.image.save(tank_red, str(TANKS_DIR / "tank_red.png"))
    pygame.image.save(tank_red, str(SPRITES_TANKS_DIR / "tank_red.png"))
    print(" -> assets/tanks/tank_red.png généré.")

    tank_green = generate_tank_sprite("green", 68, 52)
    pygame.image.save(tank_green, str(TANKS_DIR / "tank_green.png"))
    pygame.image.save(tank_green, str(SPRITES_TANKS_DIR / "tank_green.png"))
    print(" -> assets/tanks/tank_green.png généré.")

    # 4. Projectiles
    PROJECTILES_DIR = ASSETS_DIR / "projectiles"
    SPRITES_PROJ_DIR = ASSETS_DIR / "sprites" / "projectiles"
    PROJECTILES_DIR.mkdir(parents=True, exist_ok=True)
    SPRITES_PROJ_DIR.mkdir(parents=True, exist_ok=True)

    bullet = generate_bullet_sprite(18, 10)
    pygame.image.save(bullet, str(PROJECTILES_DIR / "bullet.png"))
    pygame.image.save(bullet, str(SPRITES_PROJ_DIR / "bullet.png"))
    print(" -> assets/projectiles/bullet.png généré.")

    # 5. Icônes d'interface
    try:
        from generate_icons import generate_all_icons
        generate_all_icons(ASSETS_DIR / "icons")
        print(" -> assets/icons/ (28 icônes) généré avec succès.")
    except Exception as e:
        print(f" -> Avertissement génération icônes: {e}")

    print("Tous les assets graphiques PNG ont été générés avec succès !")


if __name__ == "__main__":
    main()

