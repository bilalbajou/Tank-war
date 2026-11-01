"""Protocole de communication réseau et sérialisation pour Arena Duel (Tank War).

Définit :
- Les types de messages standardisés.
- La structure des commandes saisies par le client (up, down, left, right, shoot).
- La structure de l'instantané d'état officiel diffusé par le serveur (snapshot).
"""

from enum import Enum
from typing import Any, Optional


class MessageType(str, Enum):
    """Types de paquets échangés entre le serveur hôte et le client distant."""
    HANDSHAKE = "handshake"
    HANDSHAKE_ACK = "handshake_ack"
    INPUT = "input"
    SNAPSHOT = "snapshot"
    PING = "ping"
    PONG = "pong"
    DISCONNECT = "disconnect"
    PLAYER_READY = "player_ready"
    LOBBY_STATE = "lobby_state"


class NetworkProtocol:
    """Fabrique et valide les messages du protocole réseau."""

    @staticmethod
    def create_handshake(player_name: str = "Player 2") -> dict[str, Any]:
        """Génère la requête de connexion initiale du client."""
        return {
            "type": MessageType.HANDSHAKE.value,
            "name": player_name,
            "version": "1.0",
        }

    @staticmethod
    def create_handshake_ack(assigned_id: int = 2, status: str = "accepted") -> dict[str, Any]:
        """Génère la réponse d'acceptation du serveur."""
        return {
            "type": MessageType.HANDSHAKE_ACK.value,
            "assigned_id": assigned_id,
            "status": status,
        }

    @staticmethod
    def create_input_message(
        player_id: int,
        seq: int,
        up: bool,
        down: bool,
        left: bool,
        right: bool,
        shoot: bool
    ) -> dict[str, Any]:
        """Génère le message de commande clavier transmis par le client."""
        return {
            "type": MessageType.INPUT.value,
            "player_id": player_id,
            "seq": seq,
            "up": bool(up),
            "down": bool(down),
            "left": bool(left),
            "right": bool(right),
            "shoot": bool(shoot),
        }

    @staticmethod
    def create_snapshot(
        seq: int,
        tanks_data: dict[str, Any],
        projectiles_data: list[dict[str, Any]],
        powerups_data: list[dict[str, Any]],
        destroyed_obstacles_indices: list[int],
        p1_score: int,
        p2_score: int,
        time_remaining: float,
        is_sudden_death: bool,
        is_game_over: bool,
        winner_id: Optional[int],
        win_reason: str
    ) -> dict[str, Any]:
        """Génère l'instantané d'état officiel calculé par le serveur."""
        return {
            "type": MessageType.SNAPSHOT.value,
            "seq": seq,
            "tanks": tanks_data,
            "projectiles": projectiles_data,
            "powerups": powerups_data,
            "destroyed_obstacles": destroyed_obstacles_indices,
            "scores": {"p1": p1_score, "p2": p2_score},
            "time_remaining": round(time_remaining, 1),
            "game_state": {
                "is_sudden_death": is_sudden_death,
                "is_game_over": is_game_over,
                "winner_id": winner_id,
                "win_reason": win_reason,
            },
        }

    @staticmethod
    def create_player_ready(player_id: int, ready: bool) -> dict[str, Any]:
        """Génère un message indiquant le statut 'prêt' d'un joueur dans le lobby."""
        return {
            "type": MessageType.PLAYER_READY.value,
            "player_id": player_id,
            "ready": bool(ready),
        }

    @staticmethod
    def create_lobby_state(
        p1_ready: bool,
        p2_ready: bool,
        countdown: Optional[float] = None,
        game_started: bool = False
    ) -> dict[str, Any]:
        """Génère l'état global du lobby diffusé par le serveur."""
        return {
            "type": MessageType.LOBBY_STATE.value,
            "p1_ready": bool(p1_ready),
            "p2_ready": bool(p2_ready),
            "countdown": round(countdown, 1) if countdown is not None else None,
            "game_started": bool(game_started),
        }

