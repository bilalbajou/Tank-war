"""Générateur de sprites de tanks 2D cartoon pour Tank War (Arena Duel).

Génère deux sprites de tanks transparents 32-bit (format 68x52 px) :
- Joueur 1 : Tank Rouge
- Joueur 2 : Tank Vert

Orientation de référence : 0° (orienté vers l'Est / la droite).
"""

import os
import pygame
from pathlib import Path

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
TANKS_SPRITES_DIR = ASSETS_DIR / "sprites" / "tanks"
TANKS_ALT_DIR = ASSETS_DIR / "tanks"

TANKS_SPRITES_DIR.mkdir(parents=True, exist_ok=True)
TANKS_ALT_DIR.mkdir(parents=True, exist_ok=True)


def create_tank_surface(
    body_color: tuple[int, int, int],
    dark_body: tuple[int, int, int],
    light_body: tuple[int, int, int],
    turret_color: tuple[int, int, int],
    accent_color: tuple[int, int, int],
    width: int = 68,
    height: int = 52
) -> pygame.Surface:
    """Dessine un tank cartoon Top-Down orienté vers la droite (0°)."""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    cx, cy = width // 2 - 2, height // 2

    # 1. Chenilles supérieures et inférieures (tracks)
    track_w = width - 18
    track_h = 11
    track_color = (48, 52, 60)
    track_dark = (28, 30, 36)
    track_light = (75, 80, 92)

    for track_y in (cy - 24, cy + 13):
        t_rect = pygame.Rect(4, track_y, track_w, track_h)
        # Fond chenille
        pygame.draw.rect(surface, track_color, t_rect, border_radius=4)
        # Biseau éclairé
        pygame.draw.line(surface, track_light, (t_rect.left + 3, t_rect.top + 1), (t_rect.right - 3, t_rect.top + 1), 1)
        # Segments de chenille (crampons)
        for seg_x in range(t_rect.left + 6, t_rect.right - 4, 6):
            pygame.draw.line(surface, track_dark, (seg_x, t_rect.top + 2), (seg_x, t_rect.bottom - 2), 2)
        # Contour sombre
        pygame.draw.rect(surface, track_dark, t_rect, width=2, border_radius=4)

    # 2. Châssis principal du tank (blindage central)
    body_w = width - 24
    body_h = height - 20
    body_rect = pygame.Rect(cx - body_w // 2, cy - body_h // 2, body_w, body_h)

    # Corps de blindage
    pygame.draw.rect(surface, body_color, body_rect, border_radius=6)

    # Biseau clair supérieur et sombre inférieur
    pygame.draw.line(surface, light_body, (body_rect.left + 4, body_rect.top + 2), (body_rect.right - 4, body_rect.top + 2), 2)
    pygame.draw.line(surface, light_body, (body_rect.left + 2, body_rect.top + 4), (body_rect.left + 2, body_rect.bottom - 4), 2)
    pygame.draw.line(surface, dark_body, (body_rect.left + 4, body_rect.bottom - 2), (body_rect.right - 4, body_rect.bottom - 2), 2)

    # Plaques d'aération arrière (moteur)
    vent_x = body_rect.left + 4
    for vy in range(cy - 8, cy + 9, 5):
        pygame.draw.line(surface, dark_body, (vent_x, vy), (vent_x + 6, vy), 2)

    # Rivets sur les coins de blindage
    rivet_color = (230, 235, 245)
    rivets = [
        (body_rect.left + 6, body_rect.top + 6),
        (body_rect.left + 6, body_rect.bottom - 6),
        (body_rect.right - 6, body_rect.top + 6),
        (body_rect.right - 6, body_rect.bottom - 6),
    ]
    for rx, ry in rivets:
        pygame.draw.circle(surface, rivet_color, (rx, ry), 2)
        pygame.draw.circle(surface, (30, 30, 30), (rx, ry), 1)

    # Contour cartoon du châssis
    pygame.draw.rect(surface, (25, 25, 30), body_rect, width=2, border_radius=6)

    # 3. Canon principal (pointant vers l'avant à droite)
    cannon_len = 26
    cannon_h = 7
    cannon_rect = pygame.Rect(cx + 4, cy - cannon_h // 2, cannon_len, cannon_h)
    
    # Corps du canon
    pygame.draw.rect(surface, (70, 75, 85), cannon_rect, border_radius=2)
    pygame.draw.line(surface, (120, 130, 145), (cannon_rect.left, cannon_rect.top + 1), (cannon_rect.right, cannon_rect.top + 1), 2)
    # Frein de bouche à l'extrémité
    muzzle_rect = pygame.Rect(cannon_rect.right - 4, cy - 6, 6, 12)
    pygame.draw.rect(surface, (45, 50, 58), muzzle_rect, border_radius=2)
    pygame.draw.rect(surface, (20, 20, 25), muzzle_rect, width=1, border_radius=2)
    pygame.draw.rect(surface, (20, 20, 25), cannon_rect, width=1, border_radius=2)

    # 4. Tourelle rotative centrale
    turret_radius = 14
    pygame.draw.circle(surface, turret_color, (cx, cy), turret_radius)
    pygame.draw.circle(surface, light_body, (cx - 2, cy - 2), turret_radius - 3, width=2)
    pygame.draw.circle(surface, (25, 25, 30), (cx, cy), turret_radius, width=2)

    # Écoutille du commandant (hatch)
    hatch_radius = 6
    pygame.draw.circle(surface, accent_color, (cx - 3, cy), hatch_radius)
    pygame.draw.circle(surface, (25, 25, 30), (cx - 3, cy), hatch_radius, width=1)

    # Visière ou périscope
    pygame.draw.rect(surface, (80, 210, 255), (cx + 5, cy - 3, 4, 6), border_radius=1)
    pygame.draw.rect(surface, (20, 20, 25), (cx + 5, cy - 3, 4, 6), width=1, border_radius=1)

    return surface


def main():
    print("Génération des sprites de tanks...")

    # Tank 1 : Rouge
    tank_red = create_tank_surface(
        body_color=(231, 76, 60),      # Rouge vif
        dark_body=(169, 50, 38),       # Ombre rouge sombre
        light_body=(245, 140, 130),    # Reflet clair
        turret_color=(192, 57, 43),    # Tourelle rouge foncé
        accent_color=(52, 73, 94),     # Écoutille acier
    )
    pygame.image.save(tank_red, str(TANKS_SPRITES_DIR / "tank_red.png"))
    pygame.image.save(tank_red, str(TANKS_ALT_DIR / "tank_red.png"))
    print(" -> assets/sprites/tanks/tank_red.png généré.")

    # Tank 2 : Vert
    tank_green = create_tank_surface(
        body_color=(46, 204, 113),     # Vert émeraude vif
        dark_body=(30, 132, 73),       # Ombre vert foncé
        light_body=(130, 235, 170),    # Reflet clair
        turret_color=(39, 174, 96),    # Tourelle vert foncé
        accent_color=(44, 62, 80),     # Écoutille acier
    )
    pygame.image.save(tank_green, str(TANKS_SPRITES_DIR / "tank_green.png"))
    pygame.image.save(tank_green, str(TANKS_ALT_DIR / "tank_green.png"))
    print(" -> assets/sprites/tanks/tank_green.png généré.")

    print("Sprites de tanks générés avec succès !")


if __name__ == "__main__":
    main()

