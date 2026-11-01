"""Tests unitaires et d'intégration de l'interface utilisateur complète (UI) :

Valide :
- UIButton : États normal, hover, pressed, lift, clics souris et activation clavier.
- UITextInput : Saisie, filtration des caractères, suppression par retour arrière et validation Entrée.
- MainMenu : Navigation clavier (Haut/Bas/Entrée/Échap), synchronisation souris et transitions.
- HostScreen : Affichage de l'IP, attente non-bloquante du client et annulation.
- JoinScreen : Saisie de l'hôte, gestion des états (idle, connecting, error) et annulation.
- LobbyScreen : Fiches des joueurs, bascule de l'état prêt, synchronisation et compte à rebours.
- PauseOverlay : Reprise, redémarrage et retour au menu.
- GameOverOverlay : Proclamation personnalisée de victoire/défaite, rejouer et retour au menu.
- GameApp : Machine à états globale et transitions complètes.
"""

from __future__ import annotations
import os
import pygame
import pytest

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

from interface.components import UIButton, UITextInput
from interface.menu import MainMenu
from interface.screens import HostScreen, JoinScreen, PauseOverlay, GameOverOverlay
from interface.lobby import LobbyScreen
from main import GameApp, AppState


# =============================================================================
# 1. TESTS DES COMPOSANTS (BOUTONS & SAISIE)
# =============================================================================
def test_ui_button_hover_click_and_trigger():
    """Vérifie les réactions aux événements souris et clavier du bouton cartoon."""
    clicked = False

    def on_click():
        nonlocal clicked
        clicked = True

    btn = UIButton(
        rect=pygame.Rect(100, 100, 200, 50),
        text="TEST BOUTON",
        scheme="amber",
        on_click=on_click,
    )

    # 1. Survol souris
    evt_motion_in = pygame.event.Event(pygame.MOUSEMOTION, {"pos": (150, 120)})
    btn.handle_event(evt_motion_in)
    assert btn.is_hovered is True

    evt_motion_out = pygame.event.Event(pygame.MOUSEMOTION, {"pos": (50, 50)})
    btn.handle_event(evt_motion_out)
    assert btn.is_hovered is False

    # 2. Clic souris
    btn.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (150, 120), "button": 1}))
    assert btn.is_pressed is True

    btn.handle_event(pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": (150, 120), "button": 1}))
    assert btn.is_pressed is False
    assert clicked is True

    # 3. Déclenchement clavier direct
    clicked = False
    btn.trigger()
    assert clicked is True

    # 4. Dessin sur surface factice sans erreur
    surface = pygame.Surface((400, 300))
    btn.update(0.016)
    btn.draw(surface)


def test_ui_text_input_editing():
    """Vérifie la saisie, le filtrage et la validation du champ texte."""
    inp = UITextInput(
        rect=pygame.Rect(50, 50, 200, 40),
        initial_text="192.168.1.",
        allowed_chars="0123456789.",
        max_length=15,
    )

    # Ajout d'un caractère autorisé ('4')
    inp.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_4, "unicode": "4", "mod": 0}))
    assert inp.text == "192.168.1.4"

    # Caractère non autorisé ('a') -> doit être ignoré
    inp.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_a, "unicode": "a", "mod": 0}))
    assert inp.text == "192.168.1.4"

    # Suppression par retour arrière
    inp.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_BACKSPACE, "unicode": "", "mod": 0}))
    assert inp.text == "192.168.1."

    # Validation par Entrée
    ret = inp.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN, "unicode": "\r", "mod": 0}))
    assert ret is True

    surface = pygame.Surface((300, 100))
    inp.update(0.1)
    inp.draw(surface)


# =============================================================================
# 2. TESTS DU MENU PRINCIPAL
# =============================================================================
def test_main_menu_navigation():
    """Vérifie la navigation au clavier et l'activation des boutons du menu principal."""
    actions = []

    menu = MainMenu(
        on_play_local=lambda: actions.append("local"),
        on_host_game=lambda: actions.append("host"),
        on_join_game=lambda: actions.append("join"),
        on_quit=lambda: actions.append("quit"),
    )

    assert menu.selected_index == 0
    assert menu.buttons[0].is_selected is True

    # Navigation vers le bas
    menu.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_DOWN}))
    assert menu.selected_index == 1
    assert menu.buttons[1].is_selected is True

    # Validation Entrée -> active "Héberger"
    menu.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))
    assert "host" in actions

    # Navigation vers le haut
    menu.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_UP}))
    assert menu.selected_index == 0
    menu.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE}))
    assert "local" in actions

    # Dessin
    surface = pygame.Surface((1600, 900))
    menu.update(0.016)
    menu.draw(surface)


# =============================================================================
# 3. TESTS DE L'ÉCRAN D'HÉBERGEMENT ET DE RECONNEXION
# =============================================================================
def test_host_screen_lifecycle():
    """Vérifie la détection de connexion du Joueur 2 et l'annulation."""
    class MockServer:
        local_ip = "192.168.1.100"
        port = 4242
        connected = False

        def has_client_connected(self):
            return self.connected

    server = MockServer()
    joined = False
    cancelled = False

    screen = HostScreen(
        server=server,
        on_client_joined=lambda: nonlocal_joined(),
        on_cancel=lambda: nonlocal_cancelled(),
    )

    def nonlocal_joined():
        nonlocal joined
        joined = True

    def nonlocal_cancelled():
        nonlocal cancelled
        cancelled = True

    # Mise à jour sans client
    screen.update(0.1)
    assert joined is False

    # Le client se connecte
    server.connected = True
    screen.update(0.1)
    assert joined is True

    # Annulation avec Échap
    screen.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE}))
    assert cancelled is True

    surface = pygame.Surface((1600, 900))
    screen.draw(surface)


def test_join_screen_input_and_cancel():
    """Vérifie la saisie d'IP et l'annulation dans l'écran de reconnexion."""
    connected_client = None
    cancelled = False

    screen = JoinScreen(
        on_connected=lambda c: nonlocal_conn(c),
        on_cancel=lambda: nonlocal_cancel(),
    )

    def nonlocal_conn(c):
        nonlocal connected_client
        connected_client = c

    def nonlocal_cancel():
        nonlocal cancelled
        cancelled = True

    screen.input_ip.text = "192.168.1.55"
    assert screen.connection_state == JoinScreen.STATE_IDLE

    # Annulation via Échap
    screen.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE}))
    assert cancelled is True

    surface = pygame.Surface((1600, 900))
    screen.update(0.016)
    screen.draw(surface)


# =============================================================================
# 4. TESTS DU LOBBY
# =============================================================================
def test_lobby_screen_ready_and_countdown():
    """Vérifie l'activation de l'état prêt et le compte à rebours vers le démarrage."""
    started = False
    left = False

    lobby = LobbyScreen(
        mode="local",
        on_start_game=lambda: nonlocal_start(),
        on_leave=lambda: nonlocal_leave(),
    )

    def nonlocal_start():
        nonlocal started
        started = True

    def nonlocal_leave():
        nonlocal left
        left = True

    assert lobby.p1_ready is False
    assert lobby.countdown is None

    # Bascule état prêt avec Espace
    lobby.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_SPACE}))
    assert lobby.p1_ready is True
    assert lobby.p2_ready is True

    # Déclenchement du compte à rebours
    lobby.update(0.1)
    assert lobby.countdown is not None

    # Écoulement du compte à rebours (2 secondes)
    lobby.update(2.5)
    assert started is True

    # Quitter via Échap
    lobby.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE}))
    assert left is True

    surface = pygame.Surface((1600, 900))
    lobby.draw(surface)


# =============================================================================
# 5. TESTS DES OVERLAYS (PAUSE & GAME OVER)
# =============================================================================
def test_pause_overlay_callbacks():
    """Vérifie les boutons et raccourcis de reprise, recommencer et retour au menu."""
    resumed = False
    restarted = False
    menu_called = False

    overlay = PauseOverlay(
        on_resume=lambda: nonlocal_resume(),
        on_restart=lambda: nonlocal_restart(),
        on_menu=lambda: nonlocal_menu(),
    )

    def nonlocal_resume():
        nonlocal resumed
        resumed = True

    def nonlocal_restart():
        nonlocal restarted
        restarted = True

    def nonlocal_menu():
        nonlocal menu_called
        menu_called = True

    # Échap reprend directement
    overlay.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE}))
    assert resumed is True

    # Navigation vers Recommencer (index 1) et validation
    overlay.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_DOWN}))
    assert overlay.selected_index == 1
    overlay.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))
    assert restarted is True

    surface = pygame.Surface((1600, 900))
    overlay.update(0.016)
    overlay.draw(surface)


def test_game_over_overlay_callbacks():
    """Vérifie les boutons Rejouer et Menu de l'écran de fin de match."""
    replayed = False
    menu_called = False

    overlay = GameOverOverlay(
        on_replay=lambda: nonlocal_replay(),
        on_menu=lambda: nonlocal_menu(),
    )

    def nonlocal_replay():
        nonlocal replayed
        replayed = True

    def nonlocal_menu():
        nonlocal menu_called
        menu_called = True

    # Touche R pour rejouer
    overlay.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_r}))
    assert replayed is True

    # Touche Échap pour quitter vers le menu
    overlay.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE}))
    assert menu_called is True

    surface = pygame.Surface((1600, 900))
    overlay.update(0.016)
    overlay.draw(
        surface,
        winner_id=1,
        p1_score=5,
        p2_score=3,
        win_reason="Score de 5 points atteint",
        local_player_id=1,
    )


# =============================================================================
# 6. TESTS DE LA MACHINE À ÉTATS CENTRALE (GAMEAPP)
# =============================================================================
def test_game_app_state_machine_transitions():
    """Vérifie le cycle de vie complet de l'application et les transitions entre écrans."""
    app = GameApp()
    assert app.state == AppState.MENU

    # 1. Transition vers le Lobby Local
    app.start_local()
    assert app.state == AppState.LOBBY
    assert app.play_mode == "local"

    # 2. Démarrage du Combat
    app.start_gameplay()
    assert app.state == AppState.PLAYING
    assert app.tank1 is not None and app.tank2 is not None

    # 3. Mise en pause
    app.pause_game()
    assert app.state == AppState.PAUSED

    # 4. Reprise du combat
    app.resume_game()
    assert app.state == AppState.PLAYING

    # 5. Redémarrage de la manche
    app.restart_match()
    assert app.state == AppState.PLAYING
    assert app.match_state.p1_score == 0
    assert app.match_state.p2_score == 0

    # 6. Retour au Menu Principal
    app.return_to_menu()
    assert app.state == AppState.MENU
    assert app.server is None
    assert app.client is None

    # Rendu du menu sans exception
    app.draw()

