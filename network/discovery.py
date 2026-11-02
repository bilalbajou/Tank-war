"""Module de Découverte Automatique Réseau Local (Zero-Config LAN Discovery).

Fournit :
- LANBeacon : Diffuseur UDP en broadcast pour l'Hôte (PC 1) annonçant l'existence de la partie.
- LANDiscoveryListener : Écouteur UDP passif pour le Client (PC 2) détectant automatiquement les hôtes actifs sur le Wi-Fi.
- DiscoveredServer : Fiche descriptive d'un serveur détecté (nom, IP, port, joueurs, statut).
"""

from __future__ import annotations
import json
import socket
import threading
import time
from dataclasses import dataclass
from typing import Optional, List, Dict


DEFAULT_DISCOVERY_PORT = 4245
DISCOVERY_MAGIC = "TANK_WAR_LAN"
PROTOCOL_VERSION = "1.0"


@dataclass
class DiscoveredServer:
    """Représente une partie active détectée sur le réseau local."""
    server_name: str
    host_ip: str
    port: int
    player_count: int
    max_players: int
    status: str
    last_seen: float

    @property
    def address_str(self) -> str:
        """Retourne l'adresse formatée 'IP:PORT'."""
        return f"{self.host_ip}:{self.port}"

    @property
    def is_full(self) -> bool:
        """Indique si le serveur a atteint sa capacité maximale."""
        return self.player_count >= self.max_players or self.status == "full"


class LANBeacon:
    """Balise UDP diffusant périodiquement la présence du serveur hôte sur le réseau local."""

    def __init__(
        self,
        host_ip: str,
        port: int = 4242,
        server_name: Optional[str] = None,
        discovery_port: int = DEFAULT_DISCOVERY_PORT,
        broadcast_interval: float = 0.8,
    ) -> None:
        self.host_ip = host_ip
        self.port = port
        self.discovery_port = discovery_port
        self.broadcast_interval = broadcast_interval

        if server_name:
            self.server_name = server_name
        else:
            try:
                hostname = socket.gethostname()
            except Exception:
                hostname = "Hôte"
            self.server_name = f"Partie de {hostname}"

        self.player_count = 1
        self.max_players = 2
        self.status = "waiting"

        self._socket: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.is_running = False

    def start(self) -> bool:
        """Active la diffusion UDP en tâche de fond non-bloquante."""
        if self.is_running:
            return True

        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self._socket.settimeout(0.2)

            self._stop_event.clear()
            self.is_running = True

            self._thread = threading.Thread(target=self._broadcast_loop, daemon=True)
            self._thread.start()
            return True
        except (socket.error, OSError):
            self.stop()
            return False

    def _broadcast_loop(self) -> None:
        """Boucle de transmission périodique en broadcast."""
        while not self._stop_event.is_set() and self._socket:
            payload = {
                "magic": DISCOVERY_MAGIC,
                "version": PROTOCOL_VERSION,
                "server_name": self.server_name,
                "host_ip": self.host_ip,
                "port": self.port,
                "player_count": self.player_count,
                "max_players": self.max_players,
                "status": self.status,
            }
            data = json.dumps(payload).encode("utf-8")

            # 1. Émission vers le broadcast global
            try:
                self._socket.sendto(data, ("<broadcast>", self.discovery_port))
            except (socket.error, OSError):
                try:
                    self._socket.sendto(data, ("255.255.255.255", self.discovery_port))
                except (socket.error, OSError):
                    pass

            # 2. Émission également vers localhost pour tests locaux et isolation
            try:
                self._socket.sendto(data, ("127.0.0.1", self.discovery_port))
            except (socket.error, OSError):
                pass

            # Attente fractionnée pour réactivité d'arrêt
            self._stop_event.wait(self.broadcast_interval)

    def update_status(self, player_count: int, status: str = "waiting") -> None:
        """Met à jour les informations diffusées dans la balise."""
        self.player_count = player_count
        self.status = status

    def stop(self) -> None:
        """Arrête la balise et ferme la socket UDP."""
        self._stop_event.set()
        self.is_running = False

        if self._socket:
            try:
                self._socket.close()
            except OSError:
                pass
            self._socket = None

    def __enter__(self) -> LANBeacon:
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()


class LANDiscoveryListener:
    """Écouteur passif captant les balises de serveurs sur le réseau Wi-Fi local."""

    def __init__(
        self,
        discovery_port: int = DEFAULT_DISCOVERY_PORT,
        server_ttl: float = 2.4,
    ) -> None:
        self.discovery_port = discovery_port
        self.server_ttl = server_ttl

        self._servers: Dict[str, DiscoveredServer] = {}
        self._lock = threading.Lock()

        self._socket: Optional[socket.socket] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.is_running = False

    def start(self) -> bool:
        """Démarre l'écoute passive des annonces de serveurs."""
        if self.is_running:
            return True

        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # Sur les systèmes le supportant, activer également SO_REUSEPORT
            if hasattr(socket, "SO_REUSEPORT"):
                try:
                    self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                except (socket.error, OSError):
                    pass

            self._socket.bind(("", self.discovery_port))
            self._socket.settimeout(0.2)

            self._stop_event.clear()
            self.is_running = True

            self._thread = threading.Thread(target=self._listen_loop, daemon=True)
            self._thread.start()
            return True
        except (socket.error, OSError):
            self.stop()
            return False

    def _listen_loop(self) -> None:
        """Boucle de réception UDP et de nettoyage des serveurs inactifs."""
        while not self._stop_event.is_set() and self._socket:
            # 1. Écoute de paquets entrants
            try:
                data, addr = self._socket.recvfrom(2048)
                payload = json.loads(data.decode("utf-8"))

                if payload.get("magic") == DISCOVERY_MAGIC:
                    host_ip = payload.get("host_ip") or addr[0]
                    # Si l'IP reçue est localhost ou 0.0.0.0, adapter selon l'expéditeur réel
                    if host_ip in ("0.0.0.0", ""):
                        host_ip = addr[0]

                    port = int(payload.get("port", 4242))
                    key = f"{host_ip}:{port}"

                    server = DiscoveredServer(
                        server_name=str(payload.get("server_name", f"Partie {host_ip}")),
                        host_ip=host_ip,
                        port=port,
                        player_count=int(payload.get("player_count", 1)),
                        max_players=int(payload.get("max_players", 2)),
                        status=str(payload.get("status", "waiting")),
                        last_seen=time.perf_counter(),
                    )

                    with self._lock:
                        self._servers[key] = server

            except socket.timeout:
                pass
            except (json.JSONDecodeError, UnicodeDecodeError, ValueError, KeyError):
                continue
            except (socket.error, OSError):
                break

            # 2. Purge des serveurs dont la balise n'a plus été reçue depuis plus de `server_ttl`
            now = time.perf_counter()
            with self._lock:
                expired = [
                    k for k, s in self._servers.items()
                    if (now - s.last_seen) > self.server_ttl
                ]
                for k in expired:
                    del self._servers[k]

    def get_servers(self) -> List[DiscoveredServer]:
        """Retourne la liste instantanée des serveurs détectés actifs."""
        with self._lock:
            # Nettoyage à la volée
            now = time.perf_counter()
            active = [
                s for s in self._servers.values()
                if (now - s.last_seen) <= self.server_ttl
            ]
            # Tri par nom de serveur
            return sorted(active, key=lambda s: s.server_name.lower())

    def clear(self) -> None:
        """Vide la liste des serveurs mémorisés."""
        with self._lock:
            self._servers.clear()

    def stop(self) -> None:
        """Arrête l'écoute et libère la socket UDP."""
        self._stop_event.set()
        self.is_running = False

        if self._socket:
            try:
                self._socket.close()
            except OSError:
                pass
            self._socket = None

    def __enter__(self) -> LANDiscoveryListener:
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop()

