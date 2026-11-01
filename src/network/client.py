"""Client Réseau TCP (Threadé).

Gère la connexion au serveur hôte, la réception asynchrone des paquets
dans un thread dédié et fournit des files d'attente thread-safe
pour l'intégration avec la boucle Pygame.
"""

import socket
import threading
import queue
from typing import Optional

from src.network.protocol import NetworkPacket, NetworkProtocol
from src.core.config import GameConfig


class NetworkClient:
    """Client réseau TCP non-bloquant pour le joueur distant."""

    def __init__(self, host: str = GameConfig.network.DEFAULT_HOST, port: int = GameConfig.network.DEFAULT_PORT) -> None:
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.is_connected = False
        
        self.inbound_queue: queue.Queue[NetworkPacket] = queue.Queue()
        self.outbound_queue: queue.Queue[NetworkPacket] = queue.Queue()
        
        self._receive_thread: Optional[threading.Thread] = None
        self._send_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def connect(self) -> bool:
        """Établit la connexion avec l'hôte LAN."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(GameConfig.network.TIMEOUT_SECONDS)
            self.socket.connect((self.host, self.port))
            self.is_connected = True
            self._stop_event.clear()

            # Démarrage des threads de transmission
            self._receive_thread = threading.Thread(target=self._run_receiver, daemon=True)
            self._send_thread = threading.Thread(target=self._run_sender, daemon=True)
            self._receive_thread.start()
            self._send_thread.start()
            return True
        except (socket.error, OSError):
            self.disconnect()
            return False

    def send_packet(self, packet: NetworkPacket) -> None:
        """Met en file d'attente un paquet à expédier."""
        if self.is_connected:
            self.outbound_queue.put(packet)

    def poll_packet(self) -> Optional[NetworkPacket]:
        """Récupère le prochain paquet reçu sans bloquer."""
        try:
            return self.inbound_queue.get_nowait()
        except queue.Empty:
            return None

    def _run_receiver(self) -> None:
        """Boucle d'écoute réseau exécutée dans un thread d'arrière-plan."""
        buffer = bytearray()
        while not self._stop_event.is_set() and self.socket:
            try:
                chunk = self.socket.recv(GameConfig.network.BUFFER_SIZE)
                if not chunk:
                    break
                buffer.extend(chunk)
                packets = NetworkProtocol.decode_stream(buffer)
                for pkt in packets:
                    self.inbound_queue.put(pkt)
            except socket.timeout:
                continue
            except (socket.error, OSError):
                break
        self.disconnect()

    def _run_sender(self) -> None:
        """Boucle d'envoi réseau exécutée dans un thread d'arrière-plan."""
        while not self._stop_event.is_set() and self.socket:
            try:
                packet = self.outbound_queue.get(timeout=0.1)
                data = NetworkProtocol.encode_packet(packet)
                self.socket.sendall(data)
            except queue.Empty:
                continue
            except (socket.error, OSError):
                break

    def disconnect(self) -> None:
        """Ferme la connexion proprement et arrête les threads."""
        self._stop_event.set()
        self.is_connected = False
        if self.socket:
            try:
                self.socket.close()
            except OSError:
                pass
            self.socket = None

