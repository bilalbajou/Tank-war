"""Tests unitaires de l'architecture réseau TCP : Protocole, framing \\n, client-serveur et synchronisation."""

import socket
import time
import pytest

from network.protocol import MessageType, NetworkProtocol
from network.connection import NetworkConnection
from network.server import NetworkServer
from network.client import NetworkClient


def find_free_port() -> int:
    """Trouve un port TCP disponible pour le test."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_protocol_message_builders():
    """Vérifie la sérialisation des messages du protocole."""
    handshake = NetworkProtocol.create_handshake("Tester")
    assert handshake["type"] == MessageType.HANDSHAKE.value
    assert handshake["name"] == "Tester"

    ack = NetworkProtocol.create_handshake_ack(assigned_id=2)
    assert ack["type"] == MessageType.HANDSHAKE_ACK.value
    assert ack["assigned_id"] == 2

    inp = NetworkProtocol.create_input_message(
        player_id=2, seq=10, up=True, down=False, left=False, right=True, shoot=True
    )
    assert inp["type"] == MessageType.INPUT.value
    assert inp["up"] is True
    assert inp["shoot"] is True

    snap = NetworkProtocol.create_snapshot(
        seq=1,
        tanks_data={"1": {"x": 100, "y": 200}},
        projectiles_data=[],
        powerups_data=[],
        destroyed_obstacles_indices=[],
        p1_score=2,
        p2_score=1,
        time_remaining=85.5,
        is_sudden_death=False,
        is_game_over=False,
        winner_id=None,
        win_reason=""
    )
    assert snap["type"] == MessageType.SNAPSHOT.value
    assert snap["scores"]["p1"] == 2
    assert snap["time_remaining"] == 85.5


def test_newline_framing_and_chunked_reception():
    """Vérifie que le framing par caractère '\\n' reconstitue fidèlement les messages scindés ou fusionnés."""
    # Création d'une paire de sockets interconnectées
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind(("127.0.0.1", 0))
    server_sock.listen(1)
    port = server_sock.getsockname()[1]

    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_sock.connect(("127.0.0.1", port))
    conn_sock, _ = server_sock.accept()

    conn = NetworkConnection(conn_sock)

    # 1. Envoi de deux messages collés dans le même paquet TCP
    payload = b'{"msg": 1}\n{"msg": 2}\n'
    client_sock.sendall(payload)

    time.sleep(0.05)
    m1 = conn.poll_message()
    m2 = conn.poll_message()
    assert m1 == {"msg": 1}
    assert m2 == {"msg": 2}

    # 2. Envoi d'un message fragmenté en 2 tronçons
    client_sock.sendall(b'{"part":')
    time.sleep(0.03)
    assert conn.poll_message() is None  # Message incomplet, en attente
    client_sock.sendall(b' "complete"}\n')

    time.sleep(0.05)
    m3 = conn.poll_message()
    assert m3 == {"part": "complete"}

    conn.close()
    client_sock.close()
    server_sock.close()


def test_server_client_connection_and_handshake():
    """Vérifie la connexion, le handshake et la reconnaissance de connexion."""
    port = find_free_port()
    server = NetworkServer(host="127.0.0.1", port=port)
    assert server.start() is True

    client = NetworkClient(host_ip="127.0.0.1", port=port)
    connected = client.connect(timeout=2.0)
    assert connected is True
    assert client.is_connected is True

    # Attente brève de l'enregistrement côté serveur
    time.sleep(0.1)
    server.poll_client_inputs()
    assert server.has_client_connected() is True

    client.disconnect()
    server.stop()


def test_input_transmission_from_client_to_server():
    """Vérifie l'acheminement des commandes clavier du client vers le serveur."""
    port = find_free_port()
    server = NetworkServer(host="127.0.0.1", port=port)
    server.start()

    client = NetworkClient(host_ip="127.0.0.1", port=port)
    client.connect(timeout=2.0)
    time.sleep(0.05)

    # Envoi d'une commande
    client.send_inputs(up=True, down=False, left=True, right=False, shoot=True, force=True)
    time.sleep(0.05)

    # Lecture sur le serveur
    inputs = server.poll_client_inputs()
    assert inputs is not None
    assert inputs.get("type") == MessageType.INPUT.value
    assert inputs.get("up") is True
    assert inputs.get("left") is True
    assert inputs.get("shoot") is True

    client.disconnect()
    server.stop()


def test_snapshot_broadcast_from_server_to_client():
    """Vérifie la diffusion de l'état officiel du serveur au client."""
    port = find_free_port()
    server = NetworkServer(host="127.0.0.1", port=port)
    server.start()

    client = NetworkClient(host_ip="127.0.0.1", port=port)
    client.connect(timeout=2.0)
    time.sleep(0.05)
    server.poll_client_inputs()

    # Création et diffusion d'un instantané
    snapshot = NetworkProtocol.create_snapshot(
        seq=42,
        tanks_data={"1": {"x": 200, "y": 450, "rot": 0.0}},
        projectiles_data=[],
        powerups_data=[],
        destroyed_obstacles_indices=[],
        p1_score=3,
        p2_score=2,
        time_remaining=64.2,
        is_sudden_death=False,
        is_game_over=False,
        winner_id=None,
        win_reason=""
    )
    sent = server.broadcast_snapshot(snapshot)
    assert sent is True

    time.sleep(0.05)
    received = client.poll_snapshot()
    assert received is not None
    assert received["seq"] == 1
    assert received["scores"]["p1"] == 3
    assert received["scores"]["p2"] == 2
    assert received["time_remaining"] == 64.2

    client.disconnect()
    server.stop()


def test_reject_additional_connections():
    """Vérifie qu'un troisième client est refusé pour respecter la limite stricte de 2 joueurs."""
    port = find_free_port()
    server = NetworkServer(host="127.0.0.1", port=port)
    server.start()

    # Client 1 (Joueur 2 officiel)
    client1 = NetworkClient(host_ip="127.0.0.1", port=port)
    assert client1.connect(timeout=2.0) is True
    time.sleep(0.05)
    server.poll_client_inputs()

    # Tentative d'un second client distant (3e joueur non admis)
    client2 = NetworkClient(host_ip="127.0.0.1", port=port)
    accepted = client2.connect(timeout=1.0)
    # Soit la connexion est fermée immédiatement, soit le socket est coupé
    time.sleep(0.05)
    assert not client2.is_connected or not client2.connection or not client2.connection.is_connected

    client1.disconnect()
    server.stop()


def test_destroyed_crates_synchronization_via_snapshot():
    """Vérifie la transmission des indices de caisses détruites et leur application sur la carte."""
    from game.map import ArenaMap

    server_map = ArenaMap()
    client_map = ArenaMap()

    assert len(server_map.all_initial_crates) > 0
    assert len(client_map.all_initial_crates) == len(server_map.all_initial_crates)
    initial_obstacle_count = len(client_map.obstacles)

    # Destruction d'une caisse sur le serveur
    target_crate = server_map.all_initial_crates[0]
    target_crate.is_alive = False
    server_map.update(0.1)

    destroyed_indices = server_map.get_destroyed_crate_indices()
    assert 0 in destroyed_indices

    # Création du snapshot avec l'indice
    snapshot = NetworkProtocol.create_snapshot(
        seq=10,
        tanks_data={},
        projectiles_data=[],
        powerups_data=[],
        destroyed_obstacles_indices=destroyed_indices,
        p1_score=0,
        p2_score=0,
        time_remaining=90.0,
        is_sudden_death=False,
        is_game_over=False,
        winner_id=None,
        win_reason=""
    )

    # Réception et application côté client
    received_destroyed = snapshot.get("destroyed_obstacles", [])
    client_map.apply_destroyed_crate_indices(received_destroyed)

    assert len(client_map.obstacles) == initial_obstacle_count - 1
    assert client_map.all_initial_crates[0] not in client_map.obstacles
    assert len(client_map.debris_particles) > 0


def test_client_clean_disconnection_and_reconnection():
    """Vérifie la déconnexion propre du Joueur 2 et la reconnexion réussie d'un nouveau client."""
    port = find_free_port()
    server = NetworkServer(host="127.0.0.1", port=port)
    server.start()

    # 1. Première connexion
    client1 = NetworkClient(host_ip="127.0.0.1", port=port)
    assert client1.connect(timeout=2.0) is True
    time.sleep(0.05)
    server.poll_client_inputs()
    assert server.has_client_connected() is True

    # 2. Déconnexion propre
    client1.disconnect()
    time.sleep(0.05)
    server.poll_client_inputs()
    assert server.has_client_connected() is False

    # 3. Reconnexion d'un second client
    client2 = NetworkClient(host_ip="127.0.0.1", port=port)
    assert client2.connect(timeout=2.0) is True
    time.sleep(0.05)
    server.poll_client_inputs()
    assert server.has_client_connected() is True

    # Envoi d'entrées depuis le client reconnecté
    client2.send_inputs(up=True, down=False, left=False, right=True, shoot=True, force=True)
    time.sleep(0.05)
    inputs = server.poll_client_inputs()
    assert inputs is not None
    assert inputs.get("shoot") is True

    client2.disconnect()
    server.stop()


def test_client_abrupt_disconnect_handling():
    """Vérifie la détection et le nettoyage lors d'une rupture brutale de socket (perte de connexion)."""
    port = find_free_port()
    server = NetworkServer(host="127.0.0.1", port=port)
    server.start()

    client = NetworkClient(host_ip="127.0.0.1", port=port)
    assert client.connect(timeout=2.0) is True
    time.sleep(0.05)
    server.poll_client_inputs()
    assert server.has_client_connected() is True

    # Fermeture brutale de la socket TCP sans paquet 'disconnect'
    if client.connection and client.connection.sock:
        client.connection.sock.close()

    time.sleep(0.08)
    server.poll_client_inputs()
    assert server.has_client_connected() is False

    # Le serveur doit pouvoir accueillir un nouveau client après la coupure
    client_new = NetworkClient(host_ip="127.0.0.1", port=port)
    assert client_new.connect(timeout=2.0) is True
    time.sleep(0.05)
    server.poll_client_inputs()
    assert server.has_client_connected() is True

    client_new.disconnect()
    server.stop()


def test_lobby_ready_synchronization_over_network():
    """Vérifie l'échange des statuts 'Prêt !' et de compte à rebours via le protocole réseau."""
    port = find_free_port()
    server = NetworkServer(host="127.0.0.1", port=port)
    server.start()

    client = NetworkClient(host_ip="127.0.0.1", port=port)
    assert client.connect(timeout=2.0) is True
    time.sleep(0.05)
    server.poll_client_inputs()

    # Le client informe qu'il est prêt
    client.send_ready(True)
    time.sleep(0.05)
    server.poll_client_inputs()
    assert server.client_ready is True

    # Le serveur diffuse l'état complet du lobby
    server.broadcast_lobby_state(p1_ready=True, p2_ready=True, countdown=3.0, game_started=False)
    time.sleep(0.05)
    lobby_state = client.poll_lobby_state()
    assert lobby_state is not None
    assert lobby_state.get("p1_ready") is True
    assert lobby_state.get("p2_ready") is True
    assert lobby_state.get("countdown") == 3.0

    client.disconnect()
    server.stop()


