"""Serveur Réseau TCP Autoritaire pour Arena Duel (Tank War).

PC 1 (Hôte) :
- Héberge la socket serveur sur le réseau Wi-Fi local.
- Détecte l'adresse IP locale LAN à communiquer au joueur 2.
- Accepte 1 client distant (Joueur 2) et refuse toute connexion supplémentaire.
- Reçoit et valide les entrées clavier du Joueur 2.
- Diffuse l'état officiel (snapshot) à une cadence de 30 mises à jour par seconde.
- Opère dans un thread d'arrière-plan sans bloquer la boucle Pygame.
"""

from __future__ import annotations
import socket
import threading
import time
from typing import Any, Optional

from network.connection import NetworkConnection
from network.protocol import MessageType, NetworkProtocol


def get_local_ip() -> str:
    """Détecte l'adresse IP locale sur le réseau Wi-Fi local (LAN) sans dépendance à Internet."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 10.255.255.255 ou 192.168.1.255 permet d'identifier l'interface réseau active sans envoyer de paquet
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        pass

    try:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except Exception:
        return "127.0.0.1"


class NetworkServer:
    """Serveur faisant autorité pour une partie en réseau local à 2 joueurs."""

    DEFAULT_PORT = 4242
    TARGET_SYNC_RATE = 30  # 30 instantanés par seconde

    def __init__(self, host: str = "0.0.0.0", port: int = DEFAULT_PORT) -> None:
        self.host = host
        self.port = port
        self.local_ip = get_local_ip()

        self.server_socket: Optional[socket.socket] = None
        self.client_connection: Optional[NetworkConnection] = None
        self.is_running = False

        self._listener_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Dernières entrées reçues du Joueur 2
        self.latest_client_input: Optional[dict[str, Any]] = None
        self.client_connected_event = threading.Event()
        self.client_ready = False
        self.host_ready = False

        # Compteur d'instantanés et contrôle de fréquence
        self.snapshot_seq = 0
        self.sync_interval = 1.0 / self.TARGET_SYNC_RATE
        self.last_sync_time = 0.0

    def start(self) -> bool:
        """Démarre l'écoute TCP sur le port spécifié."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(2)
            self.server_socket.settimeout(0.5)

            self.is_running = True
            self._stop_event.clear()

            self._listener_thread = threading.Thread(target=self._accept_loop, daemon=True)
            self._listener_thread.start()
            return True
        except (socket.error, OSError) as e:
            self.stop()
            return False

    def _accept_loop(self) -> None:
        """Boucle d'acceptation des connexions. N'admet qu'un seul client distant (Joueur 2)."""
        while not self._stop_event.is_set() and self.server_socket:
            try:
                sock, addr = self.server_socket.accept()

                # Si un client distant est déjà connecté : refus immédiat pour maintenir la règle des 2 joueurs
                if self.client_connection and self.client_connection.is_connected:
                    try:
                        reject_msg = {"type": "reject", "reason": "server_full"}
                        sock.sendall((str(reject_msg) + "\n").encode("utf-8"))
                        sock.close()
                    except OSError:
                        pass
                    continue

                # Création de la connexion encapsulée
                conn = NetworkConnection(sock)
                self.client_connection = conn
                self.client_connected_event.set()

            except socket.timeout:
                continue
            except (socket.error, OSError):
                break

    def poll_client_inputs(self) -> Optional[dict[str, Any]]:
        """Dépile les messages reçus du client et met à jour les dernières commandes."""
        # Détection immédiate d'une déconnexion brutale
        if self.client_connection and not self.client_connection.is_connected:
            self.client_connection = None
            self.client_connected_event.clear()
            self.client_ready = False
            self.latest_client_input = None
            return None

        if not self.client_connection or not self.client_connection.is_connected:
            return None

        # Lecture de tous les messages en attente dans la file
        while True:
            msg = self.client_connection.poll_message()
            if msg is None:
                break

            msg_type = msg.get("type")
            if msg_type == MessageType.HANDSHAKE.value:
                # Validation et confirmation de connexion
                ack = NetworkProtocol.create_handshake_ack(assigned_id=2, status="accepted")
                self.client_connection.send(ack)

            elif msg_type == MessageType.INPUT.value:
                self.latest_client_input = msg

            elif msg_type == MessageType.PLAYER_READY.value:
                self.client_ready = bool(msg.get("ready", False))

            elif msg_type == MessageType.DISCONNECT.value:
                self.client_connection.close()
                self.client_connection = None
                self.client_connected_event.clear()
                self.client_ready = False
                self.latest_client_input = None
                break

        return self.latest_client_input

    def should_broadcast_snapshot(self) -> bool:
        """Vérifie si le délai d'intervalle de synchronisation (30 Hz) est écoulé."""
        now = time.perf_counter()
        if now - self.last_sync_time >= self.sync_interval:
            self.last_sync_time = now
            return True
        return False

    def broadcast_snapshot(self, snapshot_data: dict[str, Any]) -> bool:
        """Envoie l'état officiel du monde au client distant."""
        if not self.client_connection or not self.client_connection.is_connected:
            return False

        self.snapshot_seq += 1
        snapshot_data["seq"] = self.snapshot_seq
        return self.client_connection.send(snapshot_data)

    def broadcast_lobby_state(
        self,
        p1_ready: bool,
        p2_ready: bool,
        countdown: Optional[float] = None,
        game_started: bool = False
    ) -> bool:
        """Diffuse l'état du lobby et la confirmation de lancement au client distant."""
        if not self.client_connection or not self.client_connection.is_connected:
            return False
        msg = NetworkProtocol.create_lobby_state(
            p1_ready=p1_ready,
            p2_ready=p2_ready,
            countdown=countdown,
            game_started=game_started
        )
        return self.client_connection.send(msg)

    def has_client_connected(self) -> bool:
        """Retourne True si le Joueur 2 distant est actuellement connecté."""
        return self.client_connection is not None and self.client_connection.is_connected

    def stop(self) -> None:
        """Arrête le serveur et libère toutes les sockets."""
        self._stop_event.set()
        self.is_running = False

        if self.client_connection:
            self.client_connection.close()
            self.client_connection = None

        if self.server_socket:
            try:
                self.server_socket.close()
            except OSError:
                pass
            self.server_socket = None

