"""Protocole de communication TCP et sérialisation JSON.

Gère l'encadrement des messages (framing par préfixe de taille sur 4 octets)
pour éviter les problèmes de fragmentation et de fusion inhérents aux flux TCP.
"""

from __future__ import annotations
import json
import struct
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Any, Optional


class PacketType(str, Enum):
    """Types de paquets échangés sur le réseau local."""
    HANDSHAKE = "HANDSHAKE"          # Demande de connexion du client
    WELCOME = "WELCOME"              # Confirmation du serveur et attribution de l'ID joueur
    INPUT_COMMAND = "INPUT_COMMAND"  # Envoi des entrées d'un joueur vers le serveur
    WORLD_SNAPSHOT = "WORLD_SNAPSHOT"# Diffusion de l'état du monde par le serveur
    PING = "PING"                    # Maintien de la connexion et calcul de latence
    DISCONNECT = "DISCONNECT"        # Notification de départ volontaire


@dataclass
class NetworkPacket:
    """Structure d'un paquet de données standardisé."""
    packet_type: PacketType
    sender_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0

    def to_json(self) -> str:
        """Sérialise le paquet en chaîne de caractères JSON."""
        return json.dumps({
            "packet_type": self.packet_type.value,
            "sender_id": self.sender_id,
            "payload": self.payload,
            "timestamp": self.timestamp,
        })

    @classmethod
    def from_json(cls, json_str: str) -> "NetworkPacket":
        """Instancie un paquet à partir d'une chaîne JSON."""
        data = json.loads(json_str)
        return cls(
            packet_type=PacketType(data["packet_type"]),
            sender_id=data["sender_id"],
            payload=data.get("payload", {}),
            timestamp=float(data.get("timestamp", 0.0)),
        )


class NetworkProtocol:
    """Encodeur et décodeur de trames réseau encadrées (Length-Prefixed)."""

    HEADER_FORMAT = "!I"  # 4 octets non-signés (taille du corps JSON)
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    @classmethod
    def encode_packet(cls, packet: NetworkPacket) -> bytes:
        """Encode un paquet avec son en-tête de longueur sur 4 octets."""
        json_bytes = packet.to_json().encode("utf-8")
        header = struct.pack(cls.HEADER_FORMAT, len(json_bytes))
        return header + json_bytes

    @classmethod
    def decode_stream(cls, buffer: bytearray) -> list[NetworkPacket]:
        """Extrait tous les paquets complets du buffer et retourne la liste des paquets décodés."""
        packets: list[NetworkPacket] = []

        while len(buffer) >= cls.HEADER_SIZE:
            # Lecture de la taille annoncée
            payload_len = struct.unpack(cls.HEADER_FORMAT, buffer[:cls.HEADER_SIZE])[0]
            total_message_len = cls.HEADER_SIZE + payload_len

            if len(buffer) < total_message_len:
                # Trame incomplète, attente de plus d'octets
                break

            # Extraction et suppression du message du buffer
            json_bytes = buffer[cls.HEADER_SIZE:total_message_len]
            del buffer[:total_message_len]

            try:
                packet = NetworkPacket.from_json(json_bytes.decode("utf-8"))
                packets.append(packet)
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

        return packets

