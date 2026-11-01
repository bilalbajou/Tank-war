"""Modèle de Projectile (Obus de char) pour Tank War (Arena Duel).

Gère la trajectoire balistique, la vitesse vectorielle indépendante du FPS,
l'orientation selon le canon et la détection d'impact.
"""

import math
from pathlib import Path
from typing import Optional
import pygame

from settings import ASSETS_DIR
from game.asset_manager import asset_manager


class Projectile:
    """Représente un obus tiré par un tank."""

    def __init__(
        self,
        owner_id: int,
        start_position: tuple[float, float],
        rotation: float,
        speed: float = 650.0,
        damage: int = 25,
        radius: float = 6.0
    ) -> None:
        self.owner_id = owner_id
        self.position = pygame.Vector2(start_position[0], start_position[1])
        self.rotation = float(rotation)  # Degrés : 0 = Est, 90 = Sud, etc.
        self.speed = float(speed)
        self.damage = int(damage)
        self.radius = float(radius)
        self.is_alive = True

        # Calcul du vecteur directeur unitaire à partir de l'angle en degrés
        rad = math.radians(self.rotation)
        self.direction = pygame.Vector2(math.cos(rad), math.sin(rad))

        # Sprite de projectile mis en cache
        self.image = asset_manager.get_rotated_bullet(self.rotation)
        self.rect = self.image.get_rect(center=(int(self.position.x), int(self.position.y)))

        # Hitbox de collision (boîte compacte pour éviter les faux contacts)
        hitbox_dim = int(self.radius * 2)
        self.hitbox = pygame.Rect(0, 0, hitbox_dim, hitbox_dim)
        self.hitbox.center = (int(self.position.x), int(self.position.y))

        # Animation de traînée
        self.anim_time = 0.0

    def _load_sprite(self) -> pygame.Surface:
        """Charge le sprite PNG de l'obus ou génère un repli vectoriel doré."""
        candidate_paths = [
            ASSETS_DIR / "sprites" / "projectiles" / "bullet.png",
            ASSETS_DIR / "projectiles" / "bullet.png",
        ]
        for path in candidate_paths:
            if path.exists() and path.is_file():
                try:
                    return pygame.image.load(str(path)).convert_alpha()
                except pygame.error:
                    pass

        # Fallback vectoriel
        fallback = pygame.Surface((18, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(fallback, (255, 200, 30), (0, 1, 18, 8))
        pygame.draw.ellipse(fallback, (240, 60, 30), (10, 1, 8, 8))
        return fallback

    def update(self, dt: float) -> None:
        """Déplace le projectile de manière fluide et proportionnelle à dt."""
        if not self.is_alive:
            return

        self.anim_time += dt

        # Déplacement vectoriel
        self.position += self.direction * (self.speed * dt)

        # Mise à jour des rectangles Pygame
        cx, cy = int(self.position.x), int(self.position.y)
        self.rect.center = (cx, cy)
        self.hitbox.center = (cx, cy)

    def draw(self, surface: pygame.Surface) -> None:
        """Affiche le projectile avec une animation de traînée de feu ardente."""
        if not self.is_alive:
            return

        # Traînée lumineuse animée (particules arrière)
        pulse = 1.0 + 0.3 * math.sin(self.anim_time * 30.0)
        t1 = self.position - (self.direction * 7.0)
        t2 = self.position - (self.direction * 14.0)

        # Halo arrière
        pygame.draw.circle(surface, (255, 120, 20), (int(t1.x), int(t1.y)), int(3.5 * pulse))
        pygame.draw.circle(surface, (255, 230, 80), (int(t1.x), int(t1.y)), int(2.0 * pulse))
        pygame.draw.circle(surface, (200, 50, 10), (int(t2.x), int(t2.y)), 2)

        # Sprite de l'obus orienté
        surface.blit(self.image, self.rect)

