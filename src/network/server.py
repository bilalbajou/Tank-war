"""Serveur Réseau TCP (Threadé).

Gère l'écoute des connexions entrantes pour un maximum de 2 joueurs sur le réseau local (LAN).
Centralise la validation des commandes et la diffusion des instantanés du monde.
"""

import socket
import threading
import queue
from typing import Optional

from src.network.protocol import NetworkPacket, NetworkProtocol
from src.core.config import GameConfig


class NetworkServer:
    """Serveur faisant autorité pour héberger une partie en réseau local."""

    def __init__(self, host: str = "0.0.0.0", port: int = GameConfig.network.DEFAULT_PORT) -> None:
        self.host = host
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.clients: dict[str, socket.socket] = {}
        self.is_running = False

        self.incoming_commands: queue.Queue[NetworkPacket] = queue.Queue()
        self._listener_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self) -> bool:
        """Démarre le serveur d'écoute TCP."""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(GameConfig.network.MAX_PLAYERS)
            self.server_socket.settimeout(1.0)
            self.is_running = True
            self._stop_event.clear()

            self._listener_thread = threading.Thread(target=self._accept_loop, daemon=True)
            self._listener_thread.start()
            return True
        except (socket.error, OSError):
            self.stop()
            return False

    def _accept_loop(self) -> None:
        """Boucle d'acceptation des nouveaux clients (maximum 2)."""
        while not self._stop_event.is_set() and self.server_socket:
            try:
                client_sock, client_addr = self.server_socket.accept()
                if len(self.clients) >= GameConfig.network.MAX_PLAYERS:
                    client_sock.close()
                    continue

                client_id = f"player_{len(self.clients) + 1}"
                self.clients[client_id] = client_sock
                
                # Démarrage d'un thread d'écoute pour ce client
                threading.Thread(
                    target=self._client_receive_loop,
                    args=(client_id, client_sock),
                    daemon=True
                ).start()
            except socket.timeout:
                continue
            except (socket.error, OSError):
                break

    def _client_receive_loop(self, client_id: str, client_sock: socket.socket) -> None:
        """Écoute continue des paquets envoyés par un client donné."""
        buffer = bytearray()
        while not self._stop_event.is_set():
            try:
                chunk = client_sock.recv(GameConfig.network.BUFFER_SIZE)
                if not chunk:
                    break
                buffer.extend(chunk)
                packets = NetworkProtocol.decode_stream(buffer)
                for pkt in packets:
                    self.incoming_commands.put(pkt)
            except (socket.error, OSError):
                break

        # Déconnexion du client
        if client_id in self.clients:
            del self.clients[client_id]
        try:
            client_sock.close()
        except OSError:
            pass

    def broadcast(self, packet: NetworkPacket) -> None:
        """Diffuse un paquet à l'ensemble des clients connectés."""
        data = NetworkProtocol.encode_packet(packet)
        disconnected = []
        for client_id, sock in self.clients.items():
            try:
                sock.sendall(data)
            except (socket.error, OSError):
                disconnected.append(client_id)

        for client_id in disconnected:
            if client_id in self.clients:
                del self.clients[client_id]

    def stop(self) -> None:
        """Arrête le serveur et ferme toutes les sockets."""
        self._stop_event.set()
        self.is_running = False
        for sock in self.clients.values():
            try:
                sock.close()
            except OSError:
                pass
        self.clients.clear()
        if self.server_socket:
            try:
                self.server_socket.close()
            except OSError:
                pass
            self.server_socket = None

