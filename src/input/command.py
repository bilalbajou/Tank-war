"""Commandes utilisateur abstraites.

Découple le périphérique d'entrée physique (clavier, manette)
de la logique de déplacement et d'action du tank.
Ces commandes sont sérialisables en JSON pour le transport réseau.
"""

from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class PlayerCommand:
    """Instantané des actions demandées par un joueur."""
    player_id: str = ""
    sequence_number: int = 0
    move_forward: float = 0.0     # 1.0 (avance), -1.0 (recule), 0.0 (neutre)
    rotate: float = 0.0           # 1.0 (droite), -1.0 (gauche), 0.0 (neutre)
    fire: bool = False            # True si tir demandé

    def to_dict(self) -> dict[str, Any]:
        """Convertit la commande en dictionnaire sérialisable en JSON."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PlayerCommand":
        """Instancie une commande à partir d'un dictionnaire désérialisé."""
        return cls(
            player_id=data.get("player_id", ""),
            sequence_number=data.get("sequence_number", 0),
            move_forward=float(data.get("move_forward", 0.0)),
            rotate=float(data.get("rotate", 0.0)),
            fire=bool(data.get("fire", False)),
        )

