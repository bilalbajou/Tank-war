"""Générateur procédural d'icônes 2D cartoon pour TANK WAR (Arena Duel).

Génère toutes les icônes au format PNG 32-bit avec transparence alpha dans assets/icons/ :
- assets/icons/menu/       (play, host, join, settings, controls, exit)
- assets/icons/network/    (wifi, ip, connect, back, connected, disconnected)
- assets/icons/hud/        (health, ammo, score, timer, shield, speed, pause)
- assets/icons/pause/      (resume, restart, settings, menu, quit)
- assets/icons/results/    (victory, defeat, replay, home)
"""

from __future__ import annotations
import math
import os
from pathlib import Path
import pygame

# Mode sans tête pour exécution autonome ou en tests
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

BASE_DIR = Path(__file__).resolve().parent
ICONS_DIR = BASE_DIR / "assets" / "icons"

# Palette de couleurs cartoon / militaire / arcade
C_OUTLINE = (20, 24, 30)
C_HIGHLIGHT = (255, 255, 255, 180)
C_SHADOW = (15, 18, 22, 120)

C_GOLD_BASE = (245, 166, 35)
C_GOLD_LIGHT = (254, 211, 48)
C_GOLD_DARK = (211, 84, 0)

C_GREEN_BASE = (46, 204, 113)
C_GREEN_LIGHT = (160, 245, 195)
C_GREEN_DARK = (39, 174, 96)

C_RED_BASE = (231, 76, 60)
C_RED_LIGHT = (255, 170, 160)
C_RED_DARK = (192, 57, 43)

C_BLUE_BASE = (52, 152, 219)
C_BLUE_LIGHT = (165, 215, 255)
C_BLUE_DARK = (41, 128, 185)

C_CYAN_BASE = (26, 188, 156)
C_CYAN_LIGHT = (118, 230, 208)
C_CYAN_DARK = (22, 160, 133)

C_STEEL_BASE = (149, 165, 166)
C_STEEL_LIGHT = (200, 214, 215)
C_STEEL_DARK = (90, 105, 110)

C_DARK_SLATE = (44, 62, 80)
C_DARKER_SLATE = (28, 40, 51)


def create_blank_surface(size: int = 64) -> pygame.Surface:
    """Crée une surface transparente 32-bit de dimensions size x size."""
    return pygame.Surface((size, size), pygame.SRCALPHA)


# =============================================================================
# 1. ICÔNES MENU PRINCIPAL
# =============================================================================
def draw_icon_play(size: int = 64) -> pygame.Surface:
    """Triangle de lecture / combat vert vif avec reflet glossy et contour."""
    surf = create_blank_surface(size)
    s = size / 64.0

    # Points du triangle orienté vers la droite
    pts = [
        (16 * s, 12 * s),
        (52 * s, 32 * s),
        (16 * s, 52 * s),
    ]
    # Ombre portée
    pts_shadow = [(x + 2 * s, y + 3 * s) for x, y in pts]
    pygame.draw.polygon(surf, C_SHADOW, pts_shadow)

    # Fond du triangle
    pygame.draw.polygon(surf, C_GREEN_BASE, pts)

    # Moitié supérieure claire (effet de relief)
    pts_top = [
        (16 * s, 12 * s),
        (52 * s, 32 * s),
        (16 * s, 32 * s),
    ]
    pygame.draw.polygon(surf, C_GREEN_LIGHT, pts_top)

    # Contour sombre
    pygame.draw.polygon(surf, C_OUTLINE, pts, width=max(2, int(3 * s)))
    # Reflet spéculaire
    pygame.draw.line(surf, (255, 255, 255, 200), (20 * s, 18 * s), (38 * s, 28 * s), max(1, int(2 * s)))

    return surf


def draw_icon_host(size: int = 64) -> pygame.Surface:
    """Châssis serveur en rack avec LEDs réseau et fentes de ventilation."""
    surf = create_blank_surface(size)
    s = size / 64.0

    # Ombre générale
    pygame.draw.rect(surf, C_SHADOW, pygame.Rect(10 * s, 18 * s, 46 * s, 38 * s), border_radius=int(6 * s))

    # Rack 1 (Haut)
    r1 = pygame.Rect(10 * s, 14 * s, 44 * s, 16 * s)
    pygame.draw.rect(surf, C_DARK_SLATE, r1, border_radius=int(4 * s))
    pygame.draw.rect(surf, C_OUTLINE, r1, width=max(1, int(2 * s)), border_radius=int(4 * s))
    # LEDs rack 1
    pygame.draw.circle(surf, C_GREEN_BASE, (18 * s, 22 * s), int(3 * s))
    pygame.draw.circle(surf, (255, 255, 255), (17 * s, 21 * s), int(1 * s))
    pygame.draw.circle(surf, C_CYAN_BASE, (26 * s, 22 * s), int(2.5 * s))
    # Fentes de ventilation
    for x in range(34, 48, 4):
        pygame.draw.line(surf, C_STEEL_DARK, (x * s, 18 * s), (x * s, 26 * s), max(1, int(1.5 * s)))

    # Rack 2 (Bas)
    r2 = pygame.Rect(10 * s, 34 * s, 44 * s, 16 * s)
    pygame.draw.rect(surf, C_DARK_SLATE, r2, border_radius=int(4 * s))
    pygame.draw.rect(surf, C_OUTLINE, r2, width=max(1, int(2 * s)), border_radius=int(4 * s))
    # LEDs rack 2
    pygame.draw.circle(surf, C_GOLD_BASE, (18 * s, 42 * s), int(3 * s))
    pygame.draw.circle(surf, C_BLUE_BASE, (26 * s, 42 * s), int(2.5 * s))
    for x in range(34, 48, 4):
        pygame.draw.line(surf, C_STEEL_DARK, (x * s, 38 * s), (x * s, 46 * s), max(1, int(1.5 * s)))

    # Antenne radio hôte sur le dessus
    pygame.draw.line(surf, C_OUTLINE, (44 * s, 14 * s), (44 * s, 6 * s), max(1, int(2.5 * s)))
    pygame.draw.circle(surf, C_RED_BASE, (44 * s, 6 * s), int(3.5 * s))

    return surf


def draw_icon_join(size: int = 64) -> pygame.Surface:
    """Deux maillons de chaîne / nœuds réseau reliés avec onde de liaison."""
    surf = create_blank_surface(size)
    s = size / 64.0

    # Ombre portée
    pygame.draw.circle(surf, C_SHADOW, (22 * s, 34 * s), int(13 * s))
    pygame.draw.circle(surf, C_SHADOW, (44 * s, 34 * s), int(13 * s))

    # Nœud 1 (Gauche - PC 1)
    pygame.draw.circle(surf, C_BLUE_BASE, (20 * s, 32 * s), int(12 * s))
    pygame.draw.circle(surf, C_BLUE_LIGHT, (17 * s, 29 * s), int(5 * s))
    pygame.draw.circle(surf, C_OUTLINE, (20 * s, 32 * s), int(12 * s), width=max(1, int(2.5 * s)))

    # Nœud 2 (Droite - PC 2)
    pygame.draw.circle(surf, C_GREEN_BASE, (44 * s, 32 * s), int(12 * s))
    pygame.draw.circle(surf, C_GREEN_LIGHT, (41 * s, 29 * s), int(5 * s))
    pygame.draw.circle(surf, C_OUTLINE, (44 * s, 32 * s), int(12 * s), width=max(1, int(2.5 * s)))

    # Faisceau de connexion reliant les deux nœuds
    beam_rect = pygame.Rect(26 * s, 28 * s, 12 * s, 8 * s)
    pygame.draw.rect(surf, C_CYAN_BASE, beam_rect, border_radius=int(3 * s))
    pygame.draw.rect(surf, C_OUTLINE, beam_rect, width=max(1, int(2 * s)), border_radius=int(3 * s))
    # Onde au centre
    pygame.draw.line(surf, (255, 255, 255), (28 * s, 32 * s), (36 * s, 32 * s), max(1, int(2 * s)))

    return surf


def draw_icon_settings(size: int = 64) -> pygame.Surface:
    """Roue dentée mécanique à 6 dents avec moyeu central."""
    surf = create_blank_surface(size)
    s = size / 64.0
    cx, cy = 32 * s, 32 * s
    r_outer = 22 * s
    r_inner = 15 * s
    r_hole = 7 * s

    # Dents de l'engrenage (6 dents)
    for i in range(6):
        ang = i * (math.pi / 3)
        tooth_w = 7 * s
        tx = cx + math.cos(ang) * (r_outer + 3 * s)
        ty = cy + math.sin(ang) * (r_outer + 3 * s)
        t_rect = pygame.Rect(0, 0, tooth_w, tooth_w)
        t_rect.center = (int(tx), int(ty))
        pygame.draw.rect(surf, C_STEEL_DARK, t_rect, border_radius=int(2 * s))

    # Corps circulaire principal
    pygame.draw.circle(surf, C_STEEL_BASE, (cx, cy), int(r_outer))
    pygame.draw.circle(surf, C_STEEL_LIGHT, (cx - 2 * s, cy - 2 * s), int(r_outer - 4 * s))
    pygame.draw.circle(surf, C_OUTLINE, (cx, cy), int(r_outer), width=max(1, int(2.5 * s)))

    # Trou central
    pygame.draw.circle(surf, C_OUTLINE, (cx, cy), int(r_hole))
    pygame.draw.circle(surf, (30, 35, 42), (cx, cy), int(r_hole - 1 * s))

    return surf


def draw_icon_controls(size: int = 64) -> pygame.Surface:
    """Clavier / Manette d'arcade avec touches de direction en relief."""
    surf = create_blank_surface(size)
    s = size / 64.0

    # Corps de manette / pavé
    pad_rect = pygame.Rect(8 * s, 14 * s, 48 * s, 36 * s)
    pygame.draw.rect(surf, C_SHADOW, pygame.Rect(10 * s, 17 * s, 48 * s, 36 * s), border_radius=int(10 * s))
    pygame.draw.rect(surf, C_DARK_SLATE, pad_rect, border_radius=int(10 * s))
    pygame.draw.rect(surf, C_OUTLINE, pad_rect, width=max(1, int(2.5 * s)), border_radius=int(10 * s))

    # Croix directionnelle (D-Pad) à gauche
    cx, cy = 23 * s, 32 * s
    arm_w, arm_l = 5 * s, 8 * s
    # Vertical
    pygame.draw.rect(surf, C_STEEL_LIGHT, pygame.Rect(cx - arm_w / 2, cy - arm_l, arm_w, arm_l * 2), border_radius=int(1.5 * s))
    # Horizontal
    pygame.draw.rect(surf, C_STEEL_LIGHT, pygame.Rect(cx - arm_l, cy - arm_w / 2, arm_l * 2, arm_w), border_radius=int(1.5 * s))
    pygame.draw.circle(surf, C_OUTLINE, (cx, cy), int(3 * s))

    # Boutons d'action à droite (A, B, X, Y)
    pygame.draw.circle(surf, C_RED_BASE, (44 * s, 26 * s), int(3.5 * s))
    pygame.draw.circle(surf, C_GREEN_BASE, (44 * s, 38 * s), int(3.5 * s))
    pygame.draw.circle(surf, C_BLUE_BASE, (38 * s, 32 * s), int(3.5 * s))
    pygame.draw.circle(surf, C_GOLD_BASE, (50 * s, 32 * s), int(3.5 * s))

    return surf


def draw_icon_exit(size: int = 64) -> pygame.Surface:
    """Porte de sortie de secours avec flèche d'échappement vers la droite."""
    surf = create_blank_surface(size)
    s = size / 64.0

    # Cadre de porte
    door_rect = pygame.Rect(10 * s, 12 * s, 24 * s, 40 * s)
    pygame.draw.rect(surf, C_SHADOW, pygame.Rect(12 * s, 14 * s, 24 * s, 40 * s), border_radius=int(3 * s))
    pygame.draw.rect(surf, C_RED_DARK, door_rect, border_radius=int(3 * s))
    pygame.draw.rect(surf, C_OUTLINE, door_rect, width=max(1, int(2.5 * s)), border_radius=int(3 * s))

    # Panneau de porte entrouvert
    panel = pygame.Rect(14 * s, 16 * s, 16 * s, 32 * s)
    pygame.draw.rect(surf, C_RED_BASE, panel, border_radius=int(2 * s))
    # Poignée
    pygame.draw.circle(surf, C_GOLD_LIGHT, (26 * s, 32 * s), int(2.5 * s))

    # Flèche verte / blanche d'échappement vers la droite
    arrow_pts = [
        (28 * s, 32 * s),
        (46 * s, 32 * s),
        (46 * s, 24 * s),
        (58 * s, 32 * s),
        (46 * s, 40 * s),
        (46 * s, 32 * s),
    ]
    pygame.draw.polygon(surf, C_GREEN_BASE, arrow_pts)
    pygame.draw.polygon(surf, C_OUTLINE, arrow_pts, width=max(1, int(2 * s)))

    return surf


# =============================================================================
# 2. ICÔNES RÉSEAU & CONNEXION
# =============================================================================
def draw_icon_wifi(size: int = 64) -> pygame.Surface:
    """Signal Wi-Fi avec 3 ondes concentriques et point central."""
    surf = create_blank_surface(size)
    s = size / 64.0
    cx, cy = 32 * s, 48 * s

    # Point central
    pygame.draw.circle(surf, C_CYAN_BASE, (cx, cy), int(5 * s))
    pygame.draw.circle(surf, C_OUTLINE, (cx, cy), int(5 * s), width=max(1, int(1.5 * s)))

    # Arc 1 (Intermédiaire)
    rect1 = pygame.Rect(cx - 15 * s, cy - 15 * s, 30 * s, 30 * s)
    pygame.draw.arc(surf, C_CYAN_BASE, rect1, math.pi * 0.25, math.pi * 0.75, max(2, int(4 * s)))

    # Arc 2 (Large)
    rect2 = pygame.Rect(cx - 25 * s, cy - 25 * s, 50 * s, 50 * s)
    pygame.draw.arc(surf, C_CYAN_LIGHT, rect2, math.pi * 0.25, math.pi * 0.75, max(2, int(4.5 * s)))

    return surf


def draw_icon_ip(size: int = 64) -> pygame.Surface:
    """Globe terrestre stylisé avec grille réseau de méridiens."""
    surf = create_blank_surface(size)
    s = size / 64.0
    cx, cy = 32 * s, 32 * s
    r = 22 * s

    # Ombre
    pygame.draw.circle(surf, C_SHADOW, (cx + 2 * s, cy + 3 * s), int(r))

    # Corps sphérique
    pygame.draw.circle(surf, C_BLUE_BASE, (cx, cy), int(r))
    pygame.draw.circle(surf, C_BLUE_LIGHT, (cx - 4 * s, cy - 4 * s), int(r - 4 * s))
    pygame.draw.circle(surf, C_OUTLINE, (cx, cy), int(r), width=max(1, int(2.5 * s)))

    # Lignes d'équateur et de méridien
    pygame.draw.line(surf, (255, 255, 255, 180), (cx - r + 3 * s, cy), (cx + r - 3 * s, cy), max(1, int(2 * s)))
    pygame.draw.line(surf, (255, 255, 255, 180), (cx, cy - r + 3 * s), (cx, cy + r - 3 * s), max(1, int(2 * s)))
    # Ovale de latitude
    lat_rect = pygame.Rect(cx - r * 0.65, cy - r * 0.45, r * 1.3, r * 0.9)
    pygame.draw.ellipse(surf, (255, 255, 255, 150), lat_rect, max(1, int(1.5 * s)))

    return surf


def draw_icon_connect(size: int = 64) -> pygame.Surface:
    """Prise mâle et femelle s'emboîtant avec impulsion électrique."""
    surf = create_blank_surface(size)
    s = size / 64.0

    # Prise gauche
    r_left = pygame.Rect(10 * s, 24 * s, 16 * s, 16 * s)
    pygame.draw.rect(surf, C_GOLD_BASE, r_left, border_radius=int(3 * s))
    pygame.draw.rect(surf, C_OUTLINE, r_left, width=max(1, int(2 * s)), border_radius=int(3 * s))
    # Broches
    pygame.draw.line(surf, C_STEEL_LIGHT, (26 * s, 28 * s), (32 * s, 28 * s), max(1, int(3 * s)))
    pygame.draw.line(surf, C_STEEL_LIGHT, (26 * s, 36 * s), (32 * s, 36 * s), max(1, int(3 * s)))

    # Prise droite
    r_right = pygame.Rect(38 * s, 24 * s, 16 * s, 16 * s)
    pygame.draw.rect(surf, C_BLUE_BASE, r_right, border_radius=int(3 * s))
    pygame.draw.rect(surf, C_OUTLINE, r_right, width=max(1, int(2 * s)), border_radius=int(3 * s))

    # Étincelle de connexion centrale
    spark_pts = [
        (34 * s, 26 * s),
        (37 * s, 32 * s),
        (33 * s, 32 * s),
        (36 * s, 38 * s),
    ]
    pygame.draw.lines(surf, C_GOLD_LIGHT, False, spark_pts, max(1, int(2.5 * s)))

    return surf


def draw_icon_back(size: int = 64) -> pygame.Surface:
    """Flèche épaisse de retour pointant vers la gauche."""
    surf = create_blank_surface(size)
    s = size / 64.0

    pts = [
        (14 * s, 32 * s),
        (32 * s, 14 * s),
        (32 * s, 24 * s),
        (52 * s, 24 * s),
        (52 * s, 40 * s),
        (32 * s, 40 * s),
        (32 * s, 50 * s),
    ]
    # Ombre
    pts_shadow = [(x + 2 * s, y + 3 * s) for x, y in pts]
    pygame.draw.polygon(surf, C_SHADOW, pts_shadow)

    # Corps rouge/orange
    pygame.draw.polygon(surf, C_RED_BASE, pts)
    pygame.draw.polygon(surf, C_RED_LIGHT, [pts[0], pts[1], pts[2], (32 * s, 32 * s)])
    pygame.draw.polygon(surf, C_OUTLINE, pts, width=max(1, int(2.5 * s)))

    return surf


def draw_icon_connected(size: int = 64) -> pygame.Surface:
    """Coche de validation verte éclatante."""
    surf = create_blank_surface(size)
    s = size / 64.0

    # Disque vert de fond
    pygame.draw.circle(surf, C_GREEN_BASE, (32 * s, 32 * s), int(24 * s))
    pygame.draw.circle(surf, C_GREEN_LIGHT, (30 * s, 30 * s), int(20 * s))
    pygame.draw.circle(surf, C_OUTLINE, (32 * s, 32 * s), int(24 * s), width=max(1, int(2.5 * s)))

    # Coche blanche
    pts = [
        (20 * s, 32 * s),
        (28 * s, 42 * s),
        (46 * s, 20 * s),
    ]
    pygame.draw.lines(surf, (255, 255, 255), False, pts, max(2, int(6 * s)))
    pygame.draw.circle(surf, (255, 255, 255), (int(20 * s), int(32 * s)), int(2.5 * s))
    pygame.draw.circle(surf, (255, 255, 255), (int(46 * s), int(20 * s)), int(2.5 * s))

    return surf


def draw_icon_disconnected(size: int = 64) -> pygame.Surface:
    """Croix rouge de rupture / déconnexion."""
    surf = create_blank_surface(size)
    s = size / 64.0

    # Disque rouge de fond
    pygame.draw.circle(surf, C_RED_BASE, (32 * s, 32 * s), int(24 * s))
    pygame.draw.circle(surf, C_RED_LIGHT, (30 * s, 30 * s), int(20 * s))
    pygame.draw.circle(surf, C_OUTLINE, (32 * s, 32 * s), int(24 * s), width=max(1, int(2.5 * s)))

    # Croix blanche (X)
    pygame.draw.line(surf, (255, 255, 255), (22 * s, 22 * s), (42 * s, 42 * s), max(2, int(6 * s)))
    pygame.draw.line(surf, (255, 255, 255), (42 * s, 22 * s), (22 * s, 42 * s), max(2, int(6 * s)))

    return surf


# =============================================================================
# 3. ICÔNES HUD (AFFICHAGE TÊTE HAUTE)
# =============================================================================
def draw_icon_health(size: int = 64) -> pygame.Surface:
    """Cœur de vie blindé avec reflet cartoon."""
    surf = create_blank_surface(size)
    s = size / 64.0

    # Deux cercles et un triangle inversé pour le cœur
    cx1, cy1 = 23 * s, 24 * s
    cx2, cy2 = 41 * s, 24 * s
    r = 13 * s

    # Ombre
    pygame.draw.circle(surf, C_SHADOW, (cx1 + 2 * s, cy1 + 3 * s), int(r))
    pygame.draw.circle(surf, C_SHADOW, (cx2 + 2 * s, cy2 + 3 * s), int(r))

    pygame.draw.circle(surf, C_RED_BASE, (cx1, cy1), int(r))
    pygame.draw.circle(surf, C_RED_BASE, (cx2, cy2), int(r))

    pts_bottom = [
        (10 * s, 26 * s),
        (54 * s, 26 * s),
        (32 * s, 54 * s),
    ]
    pygame.draw.polygon(surf, C_RED_BASE, pts_bottom)

    # Reflet glossy
    pygame.draw.circle(surf, C_RED_LIGHT, (cx1 - 3 * s, cy1 - 3 * s), int(5 * s))
    pygame.draw.circle(surf, (255, 255, 255, 220), (cx1 - 4 * s, cy1 - 4 * s), int(2 * s))

    # Contour
    pygame.draw.polygon(surf, C_OUTLINE, [(32 * s, 17 * s), (10 * s, 26 * s), (32 * s, 54 * s), (54 * s, 26 * s)], width=max(1, int(2.5 * s)))

    return surf


def draw_icon_ammo(size: int = 64) -> pygame.Surface:
    """Obus lourd doré avec tête conique en cuivre."""
    surf = create_blank_surface(size)
    s = size / 64.0

    # Corps cylindrique
    body_rect = pygame.Rect(20 * s, 26 * s, 24 * s, 26 * s)
    pygame.draw.rect(surf, C_GOLD_BASE, body_rect, border_radius=int(2 * s))
    # Reflet clair
    pygame.draw.line(surf, C_GOLD_LIGHT, (24 * s, 28 * s), (24 * s, 50 * s), max(1, int(3 * s)))
    pygame.draw.rect(surf, C_OUTLINE, body_rect, width=max(1, int(2 * s)), border_radius=int(2 * s))

    # Ogive pointue
    head_pts = [
        (20 * s, 26 * s),
        (32 * s, 8 * s),
        (44 * s, 26 * s),
    ]
    pygame.draw.polygon(surf, C_RED_BASE, head_pts)
    pygame.draw.polygon(surf, C_OUTLINE, head_pts, width=max(1, int(2 * s)))

    # Culot
    base_rect = pygame.Rect(18 * s, 52 * s, 28 * s, 5 * s)
    pygame.draw.rect(surf, C_DARK_SLATE, base_rect, border_radius=int(2 * s))
    pygame.draw.rect(surf, C_OUTLINE, base_rect, width=max(1, int(1.5 * s)), border_radius=int(2 * s))

    return surf


def draw_icon_score(size: int = 64) -> pygame.Surface:
    """Trophée de victoire doré avec anses arrondies."""
    surf = create_blank_surface(size)
    s = size / 64.0

    # Calice
    cup_rect = pygame.Rect(18 * s, 12 * s, 28 * s, 24 * s)
    pygame.draw.rect(surf, C_GOLD_BASE, cup_rect, border_bottom_left_radius=int(14 * s), border_bottom_right_radius=int(14 * s))
    pygame.draw.rect(surf, C_GOLD_LIGHT, pygame.Rect(20 * s, 14 * s, 12 * s, 18 * s), border_bottom_left_radius=int(10 * s))
    pygame.draw.rect(surf, C_OUTLINE, cup_rect, width=max(1, int(2.5 * s)), border_bottom_left_radius=int(14 * s), border_bottom_right_radius=int(14 * s))

    # Anses gauche et droite
    pygame.draw.arc(surf, C_GOLD_BASE, pygame.Rect(9 * s, 14 * s, 16 * s, 16 * s), math.pi * 0.5, math.pi * 1.5, max(1, int(3.5 * s)))
    pygame.draw.arc(surf, C_GOLD_BASE, pygame.Rect(39 * s, 14 * s, 16 * s, 16 * s), -math.pi * 0.5, math.pi * 0.5, max(1, int(3.5 * s)))

    # Pied et socle
    pygame.draw.rect(surf, C_GOLD_DARK, pygame.Rect(28 * s, 36 * s, 8 * s, 10 * s))
    base_rect = pygame.Rect(18 * s, 46 * s, 28 * s, 8 * s)
    pygame.draw.rect(surf, C_DARK_SLATE, base_rect, border_radius=int(3 * s))
    pygame.draw.rect(surf, C_OUTLINE, base_rect, width=max(1, int(2 * s)), border_radius=int(3 * s))

    # Étoile centrale
    pygame.draw.circle(surf, (255, 255, 255), (32 * s, 22 * s), int(3 * s))

    return surf


def draw_icon_timer(size: int = 64) -> pygame.Surface:
    """Chronomètre de combat avec couronne supérieure et aiguille."""
    surf = create_blank_surface(size)
    s = size / 64.0
    cx, cy = 32 * s, 36 * s
    r = 20 * s

    # Bouton poussoir du haut
    pygame.draw.rect(surf, C_STEEL_DARK, pygame.Rect(28 * s, 8 * s, 8 * s, 6 * s), border_radius=int(2 * s))
    pygame.draw.rect(surf, C_OUTLINE, pygame.Rect(28 * s, 8 * s, 8 * s, 6 * s), width=max(1, int(1.5 * s)))

    # Cadran extérieur
    pygame.draw.circle(surf, C_STEEL_BASE, (cx, cy), int(r))
    pygame.draw.circle(surf, (245, 247, 250), (cx, cy), int(r - 4 * s))
    pygame.draw.circle(surf, C_OUTLINE, (cx, cy), int(r), width=max(1, int(2.5 * s)))

    # Graduations (12h, 3h, 6h, 9h)
    pygame.draw.line(surf, C_OUTLINE, (cx, cy - r + 5 * s), (cx, cy - r + 8 * s), max(1, int(2 * s)))
    pygame.draw.line(surf, C_OUTLINE, (cx, cy + r - 8 * s), (cx, cy + r - 5 * s), max(1, int(2 * s)))
    pygame.draw.line(surf, C_OUTLINE, (cx - r + 5 * s, cy), (cx - r + 8 * s, cy), max(1, int(2 * s)))
    pygame.draw.line(surf, C_OUTLINE, (cx + r - 8 * s, cy), (cx + r - 5 * s, cy), max(1, int(2 * s)))

    # Aiguille des secondes rouge
    pygame.draw.line(surf, C_RED_BASE, (cx, cy), (cx + 8 * s, cy - 8 * s), max(1, int(2.5 * s)))
    pygame.draw.circle(surf, C_OUTLINE, (cx, cy), int(3 * s))

    return surf


def draw_icon_shield(size: int = 64) -> pygame.Surface:
    """Bouclier héraldique bleu énergétique avec noyau cyan."""
    surf = create_blank_surface(size)
    s = size / 64.0

    pts = [
        (16 * s, 12 * s),
        (48 * s, 12 * s),
        (48 * s, 34 * s),
        (32 * s, 54 * s),
        (16 * s, 34 * s),
    ]
    # Ombre
    pts_shadow = [(x + 2 * s, y + 3 * s) for x, y in pts]
    pygame.draw.polygon(surf, C_SHADOW, pts_shadow)

    # Corps du bouclier
    pygame.draw.polygon(surf, C_BLUE_BASE, pts)
    # Moitié gauche plus claire
    pts_left = [pts[0], (32 * s, 12 * s), (32 * s, 54 * s), pts[4]]
    pygame.draw.polygon(surf, C_BLUE_LIGHT, pts_left)
    pygame.draw.polygon(surf, C_OUTLINE, pts, width=max(1, int(2.5 * s)))

    # Croix d'énergie centrale
    pygame.draw.line(surf, (255, 255, 255), (32 * s, 18 * s), (32 * s, 42 * s), max(1, int(3 * s)))
    pygame.draw.line(surf, (255, 255, 255), (22 * s, 28 * s), (42 * s, 28 * s), max(1, int(3 * s)))

    return surf


def draw_icon_speed(size: int = 64) -> pygame.Surface:
    """Éclair d'accélération jaune vif avec traînée d'énergie."""
    surf = create_blank_surface(size)
    s = size / 64.0

    pts = [
        (36 * s, 8 * s),
        (18 * s, 32 * s),
        (32 * s, 32 * s),
        (24 * s, 56 * s),
        (48 * s, 26 * s),
        (34 * s, 26 * s),
    ]
    # Ombre
    pts_shadow = [(x + 2 * s, y + 3 * s) for x, y in pts]
    pygame.draw.polygon(surf, C_SHADOW, pts_shadow)

    # Corps de l'éclair
    pygame.draw.polygon(surf, C_GOLD_BASE, pts)
    pygame.draw.polygon(surf, C_GOLD_LIGHT, [pts[0], pts[1], pts[2]])
    pygame.draw.polygon(surf, C_OUTLINE, pts, width=max(1, int(2.5 * s)))
    # Reflet blanc au centre
    pygame.draw.line(surf, (255, 255, 255), (33 * s, 16 * s), (25 * s, 30 * s), max(1, int(2 * s)))

    return surf


def draw_icon_pause(size: int = 64) -> pygame.Surface:
    """Deux barres verticales de pause cartoon."""
    surf = create_blank_surface(size)
    s = size / 64.0

    # Barre gauche
    b1 = pygame.Rect(16 * s, 14 * s, 11 * s, 36 * s)
    pygame.draw.rect(surf, C_SHADOW, pygame.Rect(18 * s, 16 * s, 11 * s, 36 * s), border_radius=int(4 * s))
    pygame.draw.rect(surf, C_GOLD_BASE, b1, border_radius=int(4 * s))
    pygame.draw.rect(surf, C_GOLD_LIGHT, pygame.Rect(18 * s, 16 * s, 4 * s, 30 * s), border_radius=int(2 * s))
    pygame.draw.rect(surf, C_OUTLINE, b1, width=max(1, int(2 * s)), border_radius=int(4 * s))

    # Barre droite
    b2 = pygame.Rect(37 * s, 14 * s, 11 * s, 36 * s)
    pygame.draw.rect(surf, C_SHADOW, pygame.Rect(39 * s, 16 * s, 11 * s, 36 * s), border_radius=int(4 * s))
    pygame.draw.rect(surf, C_GOLD_BASE, b2, border_radius=int(4 * s))
    pygame.draw.rect(surf, C_GOLD_LIGHT, pygame.Rect(39 * s, 16 * s, 4 * s, 30 * s), border_radius=int(2 * s))
    pygame.draw.rect(surf, C_OUTLINE, b2, width=max(1, int(2 * s)), border_radius=int(4 * s))

    return surf


# =============================================================================
# 4. ICÔNES MENU PAUSE
# =============================================================================
def draw_icon_restart(size: int = 64) -> pygame.Surface:
    """Flèche circulaire de rafraîchissement / rechargement."""
    surf = create_blank_surface(size)
    s = size / 64.0
    cx, cy = 32 * s, 32 * s
    r = 18 * s

    # Arc circulaire 270 degrés
    rect = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
    pygame.draw.arc(surf, C_GOLD_BASE, rect, -math.pi * 0.2, math.pi * 1.3, max(2, int(5 * s)))
    pygame.draw.arc(surf, C_OUTLINE, rect, -math.pi * 0.2, math.pi * 1.3, max(1, int(1.5 * s)))

    # Pointe de flèche à l'extrémité supérieure
    tip_pts = [
        (46 * s, 20 * s),
        (56 * s, 30 * s),
        (38 * s, 32 * s),
    ]
    pygame.draw.polygon(surf, C_GOLD_LIGHT, tip_pts)
    pygame.draw.polygon(surf, C_OUTLINE, tip_pts, width=max(1, int(2 * s)))

    return surf


def draw_icon_home(size: int = 64) -> pygame.Surface:
    """Bunker / maison d'accueil avec toit et porte."""
    surf = create_blank_surface(size)
    s = size / 64.0

    # Base carrée
    base_rect = pygame.Rect(16 * s, 26 * s, 32 * s, 26 * s)
    pygame.draw.rect(surf, C_SHADOW, pygame.Rect(18 * s, 28 * s, 32 * s, 26 * s), border_radius=int(2 * s))
    pygame.draw.rect(surf, C_STEEL_BASE, base_rect, border_radius=int(2 * s))
    pygame.draw.rect(surf, C_OUTLINE, base_rect, width=max(1, int(2 * s)), border_radius=int(2 * s))

    # Toit triangulaire
    roof_pts = [
        (10 * s, 28 * s),
        (32 * s, 10 * s),
        (54 * s, 28 * s),
    ]
    pygame.draw.polygon(surf, C_RED_BASE, roof_pts)
    pygame.draw.polygon(surf, C_RED_LIGHT, [(14 * s, 27 * s), (32 * s, 13 * s), (32 * s, 27 * s)])
    pygame.draw.polygon(surf, C_OUTLINE, roof_pts, width=max(1, int(2.5 * s)))

    # Porte centrale
    door_rect = pygame.Rect(26 * s, 36 * s, 12 * s, 16 * s)
    pygame.draw.rect(surf, C_DARK_SLATE, door_rect, border_top_left_radius=int(4 * s), border_top_right_radius=int(4 * s))
    pygame.draw.circle(surf, C_GOLD_LIGHT, (35 * s, 44 * s), int(1.5 * s))

    return surf


# =============================================================================
# 5. ICÔNES ÉCRAN DE RÉSULTATS (VICTOIRE / DÉFAITE)
# =============================================================================
def draw_icon_victory(size: int = 64) -> pygame.Surface:
    """Grande couronne de lauriers et trophée étoilé."""
    surf = create_blank_surface(size)
    s = size / 64.0

    # Couronne de laurier (arcs dorés de chaque côté)
    pygame.draw.arc(surf, C_GREEN_BASE, pygame.Rect(8 * s, 10 * s, 48 * s, 44 * s), math.pi * 0.7, math.pi * 1.8, max(2, int(4 * s)))
    pygame.draw.arc(surf, C_GREEN_BASE, pygame.Rect(8 * s, 10 * s, 48 * s, 44 * s), -math.pi * 0.8, math.pi * 0.3, max(2, int(4 * s)))

    # Trophée central
    cup = draw_icon_score(int(46 * s))
    surf.blit(cup, (9 * s, 8 * s))

    # Étoile dorée au sommet
    pygame.draw.circle(surf, C_GOLD_LIGHT, (32 * s, 8 * s), int(4 * s))

    return surf


def draw_icon_defeat(size: int = 64) -> pygame.Surface:
    """Casque de combat fêlé / crâne stylisé."""
    surf = create_blank_surface(size)
    s = size / 64.0
    cx, cy = 32 * s, 30 * s

    # Dôme du crâne
    pygame.draw.circle(surf, C_STEEL_LIGHT, (cx, cy), int(18 * s))
    # Mâchoire inférieure
    jaw_rect = pygame.Rect(22 * s, 36 * s, 20 * s, 14 * s)
    pygame.draw.rect(surf, C_STEEL_LIGHT, jaw_rect, border_radius=int(3 * s))
    pygame.draw.rect(surf, C_OUTLINE, jaw_rect, width=max(1, int(2 * s)), border_radius=int(3 * s))

    # Yeux noirs menaçants
    pygame.draw.circle(surf, C_OUTLINE, (25 * s, 30 * s), int(5 * s))
    pygame.draw.circle(surf, C_OUTLINE, (39 * s, 30 * s), int(5 * s))
    pygame.draw.circle(surf, C_RED_BASE, (26 * s, 30 * s), int(2 * s))
    pygame.draw.circle(surf, C_RED_BASE, (38 * s, 30 * s), int(2 * s))

    # Cavité nasale triangulaire
    pygame.draw.polygon(surf, C_OUTLINE, [(32 * s, 35 * s), (30 * s, 40 * s), (34 * s, 40 * s)])

    # Fissure / Impact sur le front
    pygame.draw.lines(surf, C_OUTLINE, False, [(32 * s, 14 * s), (28 * s, 20 * s), (32 * s, 24 * s)], max(1, int(2 * s)))

    return surf


def generate_all_icons(base_dir: Optional[Path] = None) -> dict[str, Path]:
    """Génère l'ensemble des 26 icônes et les enregistre dans assets/icons/."""
    target_dir = base_dir or ICONS_DIR
    generated_files = {}

    subdirs = {
        "menu": target_dir / "menu",
        "network": target_dir / "network",
        "hud": target_dir / "hud",
        "pause": target_dir / "pause",
        "results": target_dir / "results",
    }

    for d in subdirs.values():
        d.mkdir(parents=True, exist_ok=True)

    # 1. Menu principal
    icons_menu = {
        "play.png": draw_icon_play,
        "host.png": draw_icon_host,
        "join.png": draw_icon_join,
        "settings.png": draw_icon_settings,
        "controls.png": draw_icon_controls,
        "exit.png": draw_icon_exit,
    }
    for filename, fn in icons_menu.items():
        surf = fn(64)
        path = subdirs["menu"] / filename
        pygame.image.save(surf, str(path))
        generated_files[f"menu/{filename}"] = path

    # 2. Réseau & Connexion
    icons_net = {
        "wifi.png": draw_icon_wifi,
        "ip.png": draw_icon_ip,
        "connect.png": draw_icon_connect,
        "back.png": draw_icon_back,
        "connected.png": draw_icon_connected,
        "disconnected.png": draw_icon_disconnected,
    }
    for filename, fn in icons_net.items():
        surf = fn(64)
        path = subdirs["network"] / filename
        pygame.image.save(surf, str(path))
        generated_files[f"network/{filename}"] = path

    # 3. HUD
    icons_hud = {
        "health.png": draw_icon_health,
        "ammo.png": draw_icon_ammo,
        "score.png": draw_icon_score,
        "timer.png": draw_icon_timer,
        "shield.png": draw_icon_shield,
        "speed.png": draw_icon_speed,
        "pause.png": draw_icon_pause,
    }
    for filename, fn in icons_hud.items():
        surf = fn(64)
        path = subdirs["hud"] / filename
        pygame.image.save(surf, str(path))
        generated_files[f"hud/{filename}"] = path

    # 4. Pause
    icons_pause = {
        "resume.png": draw_icon_play,
        "restart.png": draw_icon_restart,
        "settings.png": draw_icon_settings,
        "menu.png": draw_icon_home,
        "quit.png": draw_icon_exit,
    }
    for filename, fn in icons_pause.items():
        surf = fn(64)
        path = subdirs["pause"] / filename
        pygame.image.save(surf, str(path))
        generated_files[f"pause/{filename}"] = path

    # 5. Résultats
    icons_results = {
        "victory.png": draw_icon_victory,
        "defeat.png": draw_icon_defeat,
        "replay.png": draw_icon_restart,
        "home.png": draw_icon_home,
    }
    for filename, fn in icons_results.items():
        surf = fn(64)
        path = subdirs["results"] / filename
        pygame.image.save(surf, str(path))
        generated_files[f"results/{filename}"] = path

    return generated_files


if __name__ == "__main__":
    print("Génération des 26 icônes cartoon dans assets/icons/...")
    files = generate_all_icons()
    for name, p in files.items():
        print(f" -> {name} enregistré ({p})")
    print(f"Succès : {len(files)} icônes générées !")

