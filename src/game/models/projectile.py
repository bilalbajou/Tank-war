"""Modèle métier du Projectile (Obus de tank)."""

import math
from src.game.models.entity import Entity, Vector2D
from src.core.config import GameConfig


class Projectile(Entity):
    """Représentation logique d'un obus tiré par un tank."""

    def __init__(
        self,
        projectile_id: str,
        owner_id: str,
        position: Vector2D,
        rotation: float
    ) -> None:
        super().__init__(
            entity_id=projectile_id,
            position=position,
            width=GameConfig.projectile.RADIUS * 2,
            height=GameConfig.projectile.RADIUS * 2,
            rotation=rotation
        )
        self.owner_id = owner_id
        self.speed = GameConfig.projectile.SPEED
        self.damage = GameConfig.projectile.DAMAGE
        self.lifetime_remaining = GameConfig.projectile.MAX_LIFETIME

        # Calcul du vecteur vitesse en fonction de l'angle (degrés)
        rad = math.radians(rotation)
        self.velocity = Vector2D(math.cos(rad) * self.speed, math.sin(rad) * self.speed)

    def update(self, dt: float) -> None:
        """Déplacement et vieillissement du projectile."""
        self.position = self.position + (self.velocity * dt)
        self.lifetime_remaining -= dt
        if self.lifetime_remaining <= 0:
            self.is_alive = False

