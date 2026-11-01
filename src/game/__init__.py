"""Module game : Logique métier pure, modèles du monde et entités.

Conçu sans dépendance directe à l'affichage Pygame pour permettre l'exécution
côté serveur (simulation headless) et faciliter les tests unitaires.
"""

from src.game.models.entity import Vector2D, Entity
from src.game.models.tank import Tank
from src.game.models.projectile import Projectile
from src.game.models.obstacle import Obstacle, ObstacleType
from src.game.world.arena import Arena
from src.game.world.collision import CollisionSystem
from src.game.session import GameSession

__all__ = [
    "Vector2D",
    "Entity",
    "Tank",
    "Projectile",
    "Obstacle",
    "ObstacleType",
    "Arena",
    "CollisionSystem",
    "GameSession",
]

