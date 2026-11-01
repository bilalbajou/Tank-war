"""Tests du protocole réseau et de la sérialisation."""

from src.network.protocol import NetworkPacket, NetworkProtocol, PacketType


def test_packet_json_roundtrip():
    packet = NetworkPacket(
        packet_type=PacketType.INPUT_COMMAND,
        sender_id="player_1",
        payload={"move": 1.0, "fire": True},
        timestamp=12345.67
    )
    json_str = packet.to_json()
    restored = NetworkPacket.from_json(json_str)

    assert restored.packet_type == PacketType.INPUT_COMMAND
    assert restored.sender_id == "player_1"
    assert restored.payload == {"move": 1.0, "fire": True}
    assert restored.timestamp == 12345.67


def test_protocol_framing_and_stream_decoding():
    p1 = NetworkPacket(PacketType.HANDSHAKE, "client_a", {"nickname": "Tanker"})
    p2 = NetworkPacket(PacketType.PING, "client_a", {})

    # Encodage de deux paquets collés dans le même flux TCP
    stream_bytes = bytearray(NetworkProtocol.encode_packet(p1) + NetworkProtocol.encode_packet(p2))

    decoded_packets = NetworkProtocol.decode_stream(stream_bytes)
    assert len(decoded_packets) == 2
    assert decoded_packets[0].packet_type == PacketType.HANDSHAKE
    assert decoded_packets[1].packet_type == PacketType.PING
    # Le buffer doit être vidé
    assert len(stream_bytes) == 0


def test_partial_frame_buffering():
    p = NetworkPacket(PacketType.WELCOME, "server", {"assigned_id": "player_2"})
    full_bytes = NetworkProtocol.encode_packet(p)

    # Simulation d'une réception tronquée (les 5 premiers octets uniquement)
    fragment = bytearray(full_bytes[:5])
    decoded = NetworkProtocol.decode_stream(fragment)
    assert len(decoded) == 0  # Rien ne doit être décodé
    assert len(fragment) == 5  # Les octets restent en attente dans le buffer

    # Arrivée du reste de la trame
    fragment.extend(full_bytes[5:])
    decoded = NetworkProtocol.decode_stream(fragment)
    assert len(decoded) == 1
    assert decoded[0].packet_type == PacketType.WELCOME

