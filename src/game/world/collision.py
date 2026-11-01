"""Système de détection de collisions 2D.

Implémente des algorithmes AABB (Axis-Aligned Bounding Box) et Cercle-Boîte
en pur Python pour une portabilité maximale et une indépendance graphique.
"""

from src.game.models.entity import Entity, Vector2D


class CollisionSystem:
    """Calculateur de collisions géométriques."""

    @staticmethod
    def check_aabb_collision(a: Entity, b: Entity) -> bool:
        """Détecte l'intersection entre deux rectangles alignés sur les axes."""
        min_ax, min_ay, max_ax, max_ay = a.bounding_box
        min_bx, min_by, max_bx, max_by = b.bounding_box

        return not (
            max_ax < min_bx or
            min_ax > max_bx or
            max_ay < min_by or
            min_ay > max_by
        )

    @staticmethod
    def check_circle_box_collision(
        circle_pos: Vector2D,
        radius: float,
        box_pos: Vector2D,
        box_width: float,
        box_height: float
    ) -> bool:
        """Détecte l'intersection entre un cercle (ex. projectile) et un rectangle (obstacle/tank)."""
        half_w = box_width / 2.0
        half_h = box_height / 2.0

        # Trouver le point le plus proche sur le rectangle
        closest_x = max(box_pos.x - half_w, min(circle_pos.x, box_pos.x + half_w))
        closest_y = max(box_pos.y - half_h, min(circle_pos.y, box_pos.y + half_h))

        # Calculer la distance entre le cercle et ce point
        dist_x = circle_pos.x - closest_x
        dist_y = circle_pos.y - closest_y
        distance_squared = (dist_x * dist_x) + (dist_y * dist_y)

        return distance_squared <= (radius * radius)

