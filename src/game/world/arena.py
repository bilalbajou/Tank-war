"""Représentation de l'arène désertique fixe.

Contient les limites du terrain, les points de réapparition (spawns)
et l'ensemble des obstacles positionnés.
"""

from typing import Optional
from src.core.config import GameConfig
from src.game.models.entity import Vector2D
from src.game.models.obstacle import Obstacle, ObstacleType


class Arena:
    """Modèle logique de la carte de combat."""

    def __init__(self, width: int = 1600, height: int = 900) -> None:
        self.width = width
        self.height = height
        self.obstacles: list[Obstacle] = []
        
        # Points d'apparition préconfigurés pour les 2 joueurs
        self.spawn_points: dict[int, tuple[Vector2D, float]] = {
            1: (Vector2D(150.0, height / 2.0), 0.0),      # Joueur 1 à gauche, face à l'est (0°)
            2: (Vector2D(width - 150.0, height / 2.0), 180.0)  # Joueur 2 à droite, face à l'ouest (180°)
        }

        self._load_default_desert_layout()

    def _load_default_desert_layout(self) -> None:
        """Initialise la configuration fixe des obstacles désertiques."""
        # Zone centrale : Barrière de protection et caisses
        self.obstacles.extend([
            # Barrières centrales (roches / murets)
            Obstacle("b_center_top", ObstacleType.BARRIER, Vector2D(800, 300), 40, 160),
            Obstacle("b_center_bottom", ObstacleType.BARRIER, Vector2D(800, 600), 40, 160),
            
            # Caisses d'approvisionnement (couvertures)
            Obstacle("c_nw", ObstacleType.CRATE, Vector2D(450, 250), 60, 60, destructible=True),
            Obstacle("c_sw", ObstacleType.CRATE, Vector2D(450, 650), 60, 60, destructible=True),
            Obstacle("c_ne", ObstacleType.CRATE, Vector2D(1150, 250), 60, 60, destructible=True),
            Obstacle("c_se", ObstacleType.CRATE, Vector2D(1150, 650), 60, 60, destructible=True),
            
            # Buissons désertiques (ne bloquent pas les tirs)
            Obstacle("p_mid_1", ObstacleType.PLANT, Vector2D(650, 450), 50, 50, blocks_projectiles=False),
            Obstacle("p_mid_2", ObstacleType.PLANT, Vector2D(950, 450), 50, 50, blocks_projectiles=False),
            Obstacle("p_north", ObstacleType.PLANT, Vector2D(800, 150), 70, 70, blocks_projectiles=False),
            Obstacle("p_south", ObstacleType.PLANT, Vector2D(800, 750), 70, 70, blocks_projectiles=False),
        ])

    def get_spawn(self, player_number: int) -> tuple[Vector2D, float]:
        """Retourne le point d'apparition (position, rotation) d'un joueur."""
        return self.spawn_points.get(player_number, (Vector2D(100.0, 100.0), 0.0))

    def is_within_bounds(self, position: Vector2D, margin: float = 0.0) -> bool:
        """Vérifie si une coordonnée se trouve à l'intérieur des bordures de l'arène."""
        return (
            margin <= position.x <= self.width - margin
            and margin <= position.y <= self.height - margin
        )

