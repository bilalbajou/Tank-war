"""Entités et primitives mathématiques du domaine de jeu.

Conçu pour fonctionner sans Pygame (Headless / Pure Python).
"""

from __future__ import annotations
from dataclasses import dataclass
from abc import ABC, abstractmethod
import math


@dataclass
class Vector2D:
    """Vecteur 2D mathématique utilisé pour la position et la vélocité."""
    x: float = 0.0
    y: float = 0.0

    def __add__(self, other: Vector2D) -> Vector2D:
        return Vector2D(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Vector2D) -> Vector2D:
        return Vector2D(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> Vector2D:
        return Vector2D(self.x * scalar, self.y * scalar)

    def length(self) -> float:
        """Norme euclidienne du vecteur."""
        return math.hypot(self.x, self.y)

    def normalize(self) -> Vector2D:
        """Retourne le vecteur normalisé unitaire."""
        l = self.length()
        if l == 0:
            return Vector2D(0.0, 0.0)
        return Vector2D(self.x / l, self.y / l)

    def distance_to(self, other: Vector2D) -> float:
        """Distance euclidienne vers un autre point."""
        return math.hypot(self.x - other.x, self.y - other.y)

    def to_tuple(self) -> tuple[float, float]:
        """Convertit en tuple (x, y)."""
        return (self.x, self.y)


class Entity(ABC):
    """Classe abstraite représentant toute entité du monde."""

    def __init__(
        self,
        entity_id: str,
        position: Vector2D,
        width: float,
        height: float,
        rotation: float = 0.0
    ) -> None:
        self.entity_id = entity_id
        self.position = position
        self.width = width
        self.height = height
        self.rotation = rotation  # Degrés (0-360)
        self.is_alive = True

    @property
    def bounding_box(self) -> tuple[float, float, float, float]:
        """Retourne le rectangle englobant AABB (min_x, min_y, max_x, max_y)."""
        half_w = self.width / 2.0
        half_h = self.height / 2.0
        return (
            self.position.x - half_w,
            self.position.y - half_h,
            self.position.x + half_w,
            self.position.y + half_h,
        )

    @abstractmethod
    def update(self, dt: float) -> None:
        """Met à jour l'entité pour un pas de temps donné."""
        pass

