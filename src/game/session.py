"""Session de match (Arbitre et état global de la partie).

Gère la liste des joueurs connectés (max 2), les projectiles actifs
et l'état de la manche dans l'arène désertique.
"""

from typing import Optional
from src.game.world.arena import Arena
from src.game.models.tank import Tank
from src.game.models.projectile import Projectile


class GameSession:
    """Gestionnaire de session de jeu pour un duel à 2 joueurs."""

    def __init__(self, arena: Optional[Arena] = None) -> None:
        self.arena = arena or Arena()
        self.tanks: dict[str, Tank] = {}
        self.projectiles: list[Projectile] = []
        self.winner_id: Optional[str] = None
        self.is_match_over: bool = False

    def add_player(self, player_id: str) -> Optional[Tank]:
        """Inscrit un nouveau joueur (maximum 2)."""
        player_count = len(self.tanks)
        if player_count >= 2:
            return None

        player_num = player_count + 1
        spawn_pos, rotation = self.arena.get_spawn(player_num)
        
        tank = Tank(
            player_id=player_id,
            position=spawn_pos,
            rotation=rotation,
            color_id=player_num
        )
        self.tanks[player_id] = tank
        return tank

    def get_tank(self, player_id: str) -> Optional[Tank]:
        """Récupère l'instance du tank d'un joueur."""
        return self.tanks.get(player_id)

    def is_ready_to_start(self) -> bool:
        """Vérifie si les 2 joueurs sont présents."""
        return len(self.tanks) == 2

