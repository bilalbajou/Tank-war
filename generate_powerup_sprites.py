"""Générateur de sprites 2D cartoon pour les Power-Ups de Tank War.

Génère 3 icônes de power-ups transparentes 32-bit (format 36x36 px) :
- Bouclier temporaire (shield.png)
- Vitesse accrue (speed.png)
- Tir rapide (rapid_fire.png)
"""

import os
import pygame
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
POWERUP_SPRITES_DIR = ASSETS_DIR / "sprites" / "powerups"
POWERUP_ALT_DIR = ASSETS_DIR / "powerups"

POWERUP_SPRITES_DIR.mkdir(parents=True, exist_ok=True)
POWERUP_ALT_DIR.mkdir(parents=True, exist_ok=True)


def create_shield_sprite(size: int = 36) -> pygame.Surface:
    """Génère un écusson de bouclier énergétique bleu/cyan."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2

    # Aura circulaire extérieure
    pygame.draw.circle(surf, (41, 128, 185, 100), (cx, cy), 16)

    # Écusson médiéval/futuriste
    points = [
        (cx - 11, cy - 11),
        (cx + 11, cy - 11),
        (cx + 11, cy + 3),
        (cx, cy + 13),
        (cx - 11, cy + 3),
    ]
    pygame.draw.polygon(surf, (52, 152, 219), points)
    # Reflet intérieur clair
    inner_points = [
        (cx - 8, cy - 8),
        (cx, cy - 8),
        (cx, cy + 9),
        (cx - 8, cy + 2),
    ]
    pygame.draw.polygon(surf, (174, 214, 241), inner_points)
    # Bordure métallique
    pygame.draw.polygon(surf, (240, 244, 248), points, width=2)
    # Symbole croix / protection
    pygame.draw.rect(surf, (255, 255, 255), (cx - 2, cy - 6, 4, 11), border_radius=1)
    pygame.draw.rect(surf, (255, 255, 255), (cx - 6, cy - 3, 12, 4), border_radius=1)
    return surf


def create_speed_sprite(size: int = 36) -> pygame.Surface:
    """Génère un éclair d'énergie jaune/orange symbolisant la vitesse."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2

    # Aura circulaire dorée
    pygame.draw.circle(surf, (243, 156, 18, 100), (cx, cy), 16)

    # Éclair stylisé
    points = [
        (cx + 1, cy - 13),
        (cx - 9, cy - 1),
        (cx - 1, cy - 1),
        (cx - 4, cy + 13),
        (cx + 9, cy + 1),
        (cx + 1, cy + 1),
    ]
    pygame.draw.polygon(surf, (241, 196, 15), points)
    # Biseau éclairé
    pygame.draw.polygon(surf, (254, 249, 231), [points[0], points[1], points[2]])
    # Contour sombre cartoon
    pygame.draw.polygon(surf, (120, 66, 18), points, width=2)
    return surf


def create_rapid_fire_sprite(size: int = 36) -> pygame.Surface:
    """Génère une double munition enflammée rouge/orange symbolisant le tir rapide."""
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2

    # Aura rougeoyante
    pygame.draw.circle(surf, (231, 76, 60, 100), (cx, cy), 16)

    # Obus 1 (gauche, légèrement décalé)
    for ox in (-5, 5):
        rect = pygame.Rect(cx + ox - 3, cy - 4, 6, 12)
        pygame.draw.rect(surf, (245, 176, 65), rect, border_radius=1)
        tip_pts = [(rect.left, rect.top), (rect.centerx, rect.top - 6), (rect.right, rect.top)]
        pygame.draw.polygon(surf, (231, 76, 60), tip_pts)
        pygame.draw.rect(surf, (78, 20, 14), rect, width=1, border_radius=1)
        pygame.draw.polygon(surf, (78, 20, 14), tip_pts, width=1)

    # Étincelles explosives supérieures
    pygame.draw.circle(surf, (255, 230, 80), (cx, cy - 11), 3)
    return surf


def main():
    print("Génération des sprites de Power-Ups...")
    shield = create_shield_sprite(36)
    speed = create_speed_sprite(36)
    rapid = create_rapid_fire_sprite(36)

    pygame.image.save(shield, str(POWERUP_SPRITES_DIR / "shield.png"))
    pygame.image.save(shield, str(POWERUP_ALT_DIR / "shield.png"))

    pygame.image.save(speed, str(POWERUP_SPRITES_DIR / "speed.png"))
    pygame.image.save(speed, str(POWERUP_ALT_DIR / "speed.png"))

    pygame.image.save(rapid, str(POWERUP_SPRITES_DIR / "rapid_fire.png"))
    pygame.image.save(rapid, str(POWERUP_ALT_DIR / "rapid_fire.png"))
    print(" -> Sprites shield.png, speed.png et rapid_fire.png générés avec succès !")


if __name__ == "__main__":
    main()

