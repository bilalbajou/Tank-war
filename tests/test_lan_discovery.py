"""Tests unitaires et d'intégration pour la Découverte Automatique LAN (Zero-Config).

Couvre :
1. Émission et réception UDP en broadcast (LANBeacon et LANDiscoveryListener).
2. Format du message de découverte (magic, version, nom d'hôte, IP, port, capacité).
3. Mise à jour dynamique de statut (joueurs connectés, état 'full').
4. Expiration et purge automatique des serveurs inactifs (TTL).
5. Intégration automatique dans NetworkServer.
6. Intégration UI dans JoinScreen (affichage des parties détectées, bouton REJOINDRE 1-clic).
"""

import os
import time
import pytest
import pygame

# Configuration headless pour environnement de test
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from network.discovery import (
    LANBeacon,
    LANDiscoveryListener,
    DiscoveredServer,
    DEFAULT_DISCOVERY_PORT,
    DISCOVERY_MAGIC,
)
from network.server import NetworkServer
from interface.screens import JoinScreen


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    """Initialise Pygame en mode headless."""
    pygame.init()
    if not pygame.font.get_init():
        pygame.font.init()
    if not pygame.display.get_surface():
        pygame.display.set_mode((1600, 900))
    yield


def test_discovered_server_dataclass():
    """Vérifie les propriétés d'aide du modèle DiscoveredServer."""
    srv = DiscoveredServer(
        server_name="Partie Alpha",
        host_ip="192.168.1.100",
        port=4242,
        player_count=1,
        max_players=2,
        status="waiting",
        last_seen=time.perf_counter(),
    )
    assert srv.address_str == "192.168.1.100:4242"
    assert srv.is_full is False

    srv_full = DiscoveredServer(
        server_name="Partie Bravo",
        host_ip="192.168.1.101",
        port=4243,
        player_count=2,
        max_players=2,
        status="full",
        last_seen=time.perf_counter(),
    )
    assert srv_full.is_full is True


def test_beacon_and_listener_discovery():
    """Vérifie la diffusion et la détection d'un hôte sur le réseau local via broadcast UDP."""
    port_test = 4255  # Port alternatif pour éviter collision si autre test actif
    listener = LANDiscoveryListener(discovery_port=port_test, server_ttl=3.0)
    assert listener.start() is True

    beacon = LANBeacon(
        host_ip="192.168.1.77",
        port=4242,
        server_name="Test Arena LAN",
        discovery_port=port_test,
        broadcast_interval=0.15,
    )
    assert beacon.start() is True

    # Attente brève de la réception du paquet UDP
    time.sleep(0.35)

    servers = listener.get_servers()
    assert len(servers) >= 1
    found = next((s for s in servers if s.host_ip == "192.168.1.77"), None)
    assert found is not None
    assert found.server_name == "Test Arena LAN"
    assert found.port == 4242
    assert found.player_count == 1
    assert found.max_players == 2
    assert found.status == "waiting"

    beacon.stop()
    listener.stop()


def test_beacon_status_update():
    """Vérifie que la balise transmet correctement les changements d'état (ex: joueur 2 connecté)."""
    port_test = 4256
    listener = LANDiscoveryListener(discovery_port=port_test, server_ttl=3.0)
    listener.start()

    beacon = LANBeacon(
        host_ip="192.168.1.88",
        port=4242,
        server_name="Partie Complète",
        discovery_port=port_test,
        broadcast_interval=0.1,
    )
    beacon.start()
    time.sleep(0.2)

    # Mise à jour du statut : serveur plein
    beacon.update_status(player_count=2, status="full")
    time.sleep(0.25)

    servers = listener.get_servers()
    found = next((s for s in servers if s.host_ip == "192.168.1.88"), None)
    assert found is not None
    assert found.player_count == 2
    assert found.status == "full"
    assert found.is_full is True

    beacon.stop()
    listener.stop()


def test_server_ttl_expiration_pruning():
    """Vérifie que les serveurs inactifs ou fermés disparaissent automatiquement de la liste."""
    port_test = 4257
    listener = LANDiscoveryListener(discovery_port=port_test, server_ttl=0.25)
    listener.start()

    beacon = LANBeacon(
        host_ip="192.168.1.99",
        port=4242,
        server_name="Serveur Éphémère",
        discovery_port=port_test,
        broadcast_interval=0.1,
    )
    beacon.start()
    time.sleep(0.2)

    assert any(s.host_ip == "192.168.1.99" for s in listener.get_servers())

    # Arrêt de la balise
    beacon.stop()

    # Après expiration du TTL (> 0.25s), le serveur doit disparaître
    time.sleep(0.4)
    assert not any(s.host_ip == "192.168.1.99" for s in listener.get_servers())

    listener.stop()


def test_network_server_integrated_beacon():
    """Vérifie que NetworkServer démarre et arrête automatiquement la balise LAN."""
    server = NetworkServer(host="127.0.0.1", port=4310, enable_discovery=True)
    assert server.start() is True
    assert server.beacon is not None
    assert server.beacon.is_running is True

    # Arrêt du serveur
    server.stop()
    assert server.beacon is None


def test_join_screen_auto_discovery_ui():
    """Vérifie l'affichage dynamique et le bouton 1-clic 'REJOINDRE' dans JoinScreen."""
    connected_target = [None]
    cancelled = [False]

    screen = JoinScreen(
        on_connected=lambda c: connected_target.append(c),
        on_cancel=lambda: cancelled.append(True),
    )

    assert screen.discovery_listener is not None

    # Injection d'un serveur détecté dans le listener pour validation UI
    srv_mock = DiscoveredServer(
        server_name="PC de Test (Hôte)",
        host_ip="192.168.1.42",
        port=4242,
        player_count=1,
        max_players=2,
        status="waiting",
        last_seen=time.perf_counter(),
    )
    # Remplir le cache interne du listener
    screen.discovery_listener._servers[srv_mock.address_str] = srv_mock

    # Mise à jour graphique
    screen.update(0.016)

    # Vérification qu'un bouton dédié 'REJOINDRE' a été généré
    assert srv_mock.address_str in screen.server_buttons
    btn_join = screen.server_buttons[srv_mock.address_str]
    assert btn_join.text == "REJOINDRE"

    # Rendu sans exception
    surface = pygame.Surface((1600, 900))
    screen.draw(surface)

    # Fermeture propre
    screen.cancel()
    assert screen.discovery_listener is None
