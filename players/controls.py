"""Système de contrôle des tanks pour chaque joueur.

Gère les saisies clavier, produit un vecteur de déplacement normalisé dans 8 directions
et capture les commandes de tir par joueur.
"""

from typing import Iterable, Optional
import pygame


class TankControls:
    """Contrôleur de saisie pour un tank."""

    def __init__(
        self,
        up_keys: Iterable[int],
        down_keys: Iterable[int],
        left_keys: Iterable[int],
        right_keys: Iterable[int],
        fire_keys: Iterable[int] = (),
        name: str = "Controller"
    ) -> None:
        self.up_keys = set(up_keys)
        self.down_keys = set(down_keys)
        self.left_keys = set(left_keys)
        self.right_keys = set(right_keys)
        self.fire_keys = set(fire_keys)
        self.name = name

    def get_movement_vector(self) -> pygame.Vector2:
        """Échantillonne l'état du clavier et retourne un vecteur normalisé dans 8 directions."""
        keys = pygame.key.get_pressed()

        dx = 0.0
        dy = 0.0

        if any(keys[k] for k in self.up_keys):
            dy -= 1.0
        if any(keys[k] for k in self.down_keys):
            dy += 1.0
        if any(keys[k] for k in self.left_keys):
            dx -= 1.0
        if any(keys[k] for k in self.right_keys):
            dx += 1.0

        vector = pygame.Vector2(dx, dy)
        if vector.length_squared() > 0:
            return vector.normalize()
        return pygame.Vector2(0.0, 0.0)

    def is_firing(self) -> bool:
        """Vérifie si la touche de tir assignée au joueur est enfoncée."""
        if not self.fire_keys:
            return False
        keys = pygame.key.get_pressed()
        return any(keys[k] for k in self.fire_keys)

    @classmethod
    def create_player_1_controls(cls) -> "TankControls":
        """Contrôles Joueur 1 : Déplacement ZQSD + Tir ESPACE."""
        return cls(
            up_keys=[pygame.K_z, pygame.K_w],
            down_keys=[pygame.K_s],
            left_keys=[pygame.K_q, pygame.K_a],
            right_keys=[pygame.K_d],
            fire_keys=[pygame.K_SPACE],
            name="P1 (ZQSD / Espace)"
        )

    @classmethod
    def create_player_2_controls(cls) -> "TankControls":
        """Contrôles Joueur 2 : Déplacement Flèches + Tir ENTRÉE."""
        return cls(
            up_keys=[pygame.K_UP],
            down_keys=[pygame.K_DOWN],
            left_keys=[pygame.K_LEFT],
            right_keys=[pygame.K_RIGHT],
            fire_keys=[pygame.K_RETURN, pygame.K_KP_ENTER],
            name="P2 (Flèches / Entrée)"
        )
