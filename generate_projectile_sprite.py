"""Générateur de sprite de projectile (obus) pour Tank War (Arena Duel).

Génère un obus cartoon doré avec ogive effilée et traînée lumineuse (18x10 px).
"""

import os
import pygame
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
PROJECTILE_SPRITES_DIR = ASSETS_DIR / "sprites" / "projectiles"
PROJECTILE_ALT_DIR = ASSETS_DIR / "projectiles"

PROJECTILE_SPRITES_DIR.mkdir(parents=True, exist_ok=True)
PROJECTILE_ALT_DIR.mkdir(parents=True, exist_ok=True)


def create_projectile_surface(width: int = 18, height: int = 10) -> pygame.Surface:
    """Dessine un obus 2D cartoon pointant vers l'Est (0°)."""
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    cy = height // 2

    # Corps de l'obus (rectangulaire avec ogive arrondie à droite)
    # Culot de la douille (gauche)
    pygame.draw.rect(surf, (180, 110, 30), (1, cy - 3, 4, 6), border_radius=1)
    pygame.draw.line(surf, (110, 65, 15), (1, cy - 3), (1, cy + 2), 1)

    # Corps cylindrique (doré / cuivre)
    body_rect = pygame.Rect(5, cy - 4, 7, 8)
    pygame.draw.rect(surf, (245, 190, 40), body_rect)
    pygame.draw.line(surf, (255, 240, 150), (5, cy - 2), (11, cy - 2), 1)
    pygame.draw.line(surf, (190, 130, 20), (5, cy + 2), (11, cy + 2), 1)

    # Ogive / Pointe perforante (cône vers la droite)
    tip_points = [
        (12, cy - 4),
        (width - 2, cy),
        (12, cy + 4)
    ]
    pygame.draw.polygon(surf, (230, 70, 40), tip_points)
    pygame.draw.polygon(surf, (255, 160, 120), [(12, cy - 3), (width - 4, cy), (12, cy)])
    
    # Contour sombre cartoon
    pygame.draw.lines(surf, (30, 25, 20), True, [
        (1, cy - 3), (5, cy - 4), (12, cy - 4), (width - 2, cy),
        (12, cy + 4), (5, cy + 4), (1, cy + 3)
    ], 1)

    return surf


def main():
    print("Génération du sprite de projectile...")
    bullet = create_projectile_surface(18, 10)
    pygame.image.save(bullet, str(PROJECTILE_SPRITES_DIR / "bullet.png"))
    pygame.image.save(bullet, str(PROJECTILE_ALT_DIR / "bullet.png"))
    print(" -> assets/sprites/projectiles/bullet.png généré.")


if __name__ == "__main__":
    main()

