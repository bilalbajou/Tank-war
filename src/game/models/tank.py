"""Modèle métier du Tank (Joueur).

Définit l'état et les caractéristiques physiques d'un tank dans l'arène.
"""

from src.game.models.entity import Entity, Vector2D
from src.core.config import GameConfig


class Tank(Entity):
    """Représentation logique d'un tank de joueur."""

    def __init__(
        self,
        player_id: str,
        position: Vector2D,
        rotation: float = 0.0,
        color_id: int = 1
    ) -> None:
        super().__init__(
            entity_id=player_id,
            position=position,
            width=GameConfig.tank.WIDTH,
            height=GameConfig.tank.HEIGHT,
            rotation=rotation
        )
        self.player_id = player_id
        self.color_id = color_id  # 1 = Joueur 1 (Bleu), 2 = Joueur 2 (Rouge)
        self.health = GameConfig.tank.MAX_HEALTH
        self.max_health = GameConfig.tank.MAX_HEALTH
        self.move_speed = GameConfig.tank.MOVE_SPEED
        self.rotation_speed = GameConfig.tank.ROTATION_SPEED
        self.fire_cooldown_remaining = 0.0
        self.score = 0

    def can_fire(self) -> bool:
        """Vérifie si le tank peut tirer (cooldown rechargé)."""
        return self.is_alive and self.fire_cooldown_remaining <= 0.0

    def take_damage(self, amount: int) -> None:
        """Applique des dégâts au tank."""
        self.health = max(0, self.health - amount)
        if self.health == 0:
            self.is_alive = False

    def update(self, dt: float) -> None:
        """Mise à jour du tank (décrément du cooldown de tir, etc.)."""
        if self.fire_cooldown_remaining > 0:
            self.fire_cooldown_remaining = max(0.0, self.fire_cooldown_remaining - dt)

