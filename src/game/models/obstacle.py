"""Modèles des obstacles de l'arène désertique."""

from enum import Enum, auto
from src.game.models.entity import Entity, Vector2D


class ObstacleType(Enum):
    """Types d'obstacles présents dans l'arène désertique."""
    CRATE = auto()       # Caisse en bois (bloque tank et tir)
    BARRIER = auto()     # Barrière métallique / roche (bloque tout, indestructible)
    PLANT = auto()       # Buisson désertique (laisse passer les tirs, camoufle ou ralentit)


class Obstacle(Entity):
    """Représentation logique d'un obstacle fixe sur la carte."""

    def __init__(
        self,
        obstacle_id: str,
        obstacle_type: ObstacleType,
        position: Vector2D,
        width: float,
        height: float,
        destructible: bool = False,
        blocks_movement: bool = True,
        blocks_projectiles: bool = True
    ) -> None:
        super().__init__(
            entity_id=obstacle_id,
            position=position,
            width=width,
            height=height
        )
        self.obstacle_type = obstacle_type
        self.destructible = destructible
        self.blocks_movement = blocks_movement
        self.blocks_projectiles = blocks_projectiles

    def update(self, dt: float) -> None:
        """Les obstacles statiques ne nécessitent pas de calcul de déplacement."""
        pass

