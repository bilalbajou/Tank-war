"""Client Réseau TCP pour Arena Duel (Tank War).

PC 2 (Client distant) :
- Se connecte à l'adresse IP locale de l'hôte (PC 1).
- Envoie ses commandes de touches (haut, bas, gauche, droite, tir).
- Reçoit et met en mémoire tampon les instantanés (snapshots) officiels émis à 30 Hz.
- Ne prend aucune décision d'arbitrage : affiche fidèlement le monde dicté par le serveur.
"""

from __future__ import annotations
import socket
import time
from typing import Any, Optional

from network.connection import NetworkConnection
from network.protocol import MessageType, NetworkProtocol


class NetworkClient:
    """Client TCP non-bloquant pour le Joueur 2 distant."""

    DEFAULT_PORT = 4242

    def __init__(self, host_ip: str, port: int = DEFAULT_PORT) -> None:
        self.host_ip = host_ip
        self.port = port
        self.connection: Optional[NetworkConnection] = None
        self.is_connected = False
        self.player_id = 2  # Le client est systématiquement le Joueur 2

        self.input_seq = 0
        self.latest_snapshot: Optional[dict[str, Any]] = None
        self.latest_lobby_state: Optional[dict[str, Any]] = None
        self.last_input_sent_time = 0.0
        self.input_send_interval = 1.0 / 30.0  # 30 envois d'entrées par seconde

    def connect(self, timeout: float = 4.0) -> bool:
        """Établit la connexion avec le serveur hôte et valide le handshake."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((self.host_ip, self.port))

            # Création de la connexion avec thread de réception séparé
            self.connection = NetworkConnection(sock)
            self.is_connected = True

            # Émission du handshake
            handshake = NetworkProtocol.create_handshake("Player 2 (Client)")
            self.connection.send(handshake)

            # Attente brève de l'accusé de réception (ACK)
            start_wait = time.perf_counter()
            while time.perf_counter() - start_wait < timeout:
                msg = self.connection.poll_message()
                if msg:
                    if msg.get("type") == MessageType.HANDSHAKE_ACK.value:
                        self.player_id = msg.get("assigned_id", 2)
                        return True
                    elif msg.get("type") == "reject":
                        self.disconnect()
                        return False
                time.sleep(0.01)

            # Si pas de réponse d'ACK avant timeout
            return True
        except (socket.error, OSError):
            self.disconnect()
            return False

    def send_inputs(
        self,
        up: bool,
        down: bool,
        left: bool,
        right: bool,
        shoot: bool,
        force: bool = False
    ) -> bool:
        """Transmet l'état des commandes clavier au serveur."""
        if not self.is_connected or not self.connection:
            return False

        now = time.perf_counter()
        if not force and (now - self.last_input_sent_time < self.input_send_interval):
            return True

        self.last_input_sent_time = now
        self.input_seq += 1

        msg = NetworkProtocol.create_input_message(
            player_id=self.player_id,
            seq=self.input_seq,
            up=up,
            down=down,
            left=left,
            right=right,
            shoot=shoot
        )
        return self.connection.send(msg)

    def poll_snapshot(self) -> Optional[dict[str, Any]]:
        """Dépile les messages reçus et retourne le plus récent instantané d'état du monde."""
        if self.connection and not self.connection.is_connected:
            self.is_connected = False

        if not self.is_connected or not self.connection:
            return None

        # Traitement de tous les messages en attente dans la file
        while True:
            msg = self.connection.poll_message()
            if msg is None:
                break

            msg_type = msg.get("type")
            if msg_type == MessageType.SNAPSHOT.value:
                self.latest_snapshot = msg
            elif msg_type == MessageType.LOBBY_STATE.value:
                self.latest_lobby_state = msg
            elif msg_type == MessageType.DISCONNECT.value:
                self.disconnect()
                break

        return self.latest_snapshot

    def poll_lobby_state(self) -> Optional[dict[str, Any]]:
        """Dépile les messages reçus et retourne le plus récent état du lobby."""
        if self.connection and not self.connection.is_connected:
            self.is_connected = False

        if not self.is_connected or not self.connection:
            return None

        while True:
            msg = self.connection.poll_message()
            if msg is None:
                break

            msg_type = msg.get("type")
            if msg_type == MessageType.LOBBY_STATE.value:
                self.latest_lobby_state = msg
            elif msg_type == MessageType.SNAPSHOT.value:
                self.latest_snapshot = msg
            elif msg_type == MessageType.DISCONNECT.value:
                self.disconnect()
                break

        return self.latest_lobby_state

    def send_ready(self, ready: bool) -> bool:
        """Informe le serveur hôte de l'état 'prêt' du Joueur 2."""
        if not self.is_connected or not self.connection:
            return False
        msg = NetworkProtocol.create_player_ready(player_id=self.player_id, ready=ready)
        return self.connection.send(msg)

    def disconnect(self) -> None:
        """Ferme proprement la connexion avec le serveur."""
        self.is_connected = False
        if self.connection:
            try:
                self.connection.send({"type": MessageType.DISCONNECT.value})
            except Exception:
                pass
            self.connection.close()
            self.connection = None

