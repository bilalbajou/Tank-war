"""Module de connexion TCP avec messages délimités par newline (\\n).

Fournit une couche de transport robuste avec :
- TCP_NODELAY activé pour une latence minimale.
- Sérialisation et désérialisation JSON.
- Encadrement des messages par saut de ligne (\\n).
- Thread d'écoute asynchrone non-bloquant pour Pygame.
- File d'attente thread-safe (queue.Queue) pour la réception.
- Gestion propre des déconnexions et des erreurs d'E/S.
"""

from __future__ import annotations
import socket
import json
import threading
import queue
from typing import Any, Optional


class NetworkConnection:
    """Wrapper de socket TCP gérant l'émission et la réception en arrière-plan."""

    BUFFER_SIZE = 4096

    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock
        # Activation de TCP_NODELAY pour désactiver l'algorithme de Nagle (faible latence)
        try:
            self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except (OSError, AttributeError):
            pass

        self.is_connected = True
        self.incoming_messages: queue.Queue[dict[str, Any]] = queue.Queue()
        self._stop_event = threading.Event()
        self._receive_thread: Optional[threading.Thread] = None

        # Démarrage du thread d'écoute
        self._receive_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._receive_thread.start()

    def send(self, data: dict[str, Any]) -> bool:
        """Sérialise le dictionnaire en JSON, ajoute le caractère '\\n' et expédie."""
        if not self.is_connected:
            return False

        try:
            message_str = json.dumps(data, separators=(",", ":")) + "\n"
            self.sock.sendall(message_str.encode("utf-8"))
            return True
        except (socket.error, OSError):
            self.close()
            return False

    def poll_message(self) -> Optional[dict[str, Any]]:
        """Récupère le prochain message reçu sans bloquer la boucle Pygame."""
        try:
            return self.incoming_messages.get_nowait()
        except queue.Empty:
            return None

    def _listen_loop(self) -> None:
        """Boucle de réception exécutée dans un thread séparé avec découpage par '\\n'."""
        read_buffer = ""
        while not self._stop_event.is_set() and self.is_connected:
            try:
                chunk = self.sock.recv(self.BUFFER_SIZE)
                if not chunk:
                    # Connexion fermée par le pair
                    break

                read_buffer += chunk.decode("utf-8", errors="replace")

                # Extraction de tous les messages complets terminés par '\n'
                while "\n" in read_buffer:
                    line, read_buffer = read_buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        try:
                            data = json.loads(line)
                            self.incoming_messages.put(data)
                        except json.JSONDecodeError:
                            continue

            except (socket.timeout, BlockingIOError):
                continue
            except (socket.error, OSError):
                break

        self.close()

    def close(self) -> None:
        """Ferme la socket et arrête le thread d'écoute."""
        self.is_connected = False
        self._stop_event.set()
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self.sock.close()
        except OSError:
            pass

