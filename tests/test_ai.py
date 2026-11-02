"""Tests unitaires et d'intégration pour le Mode Solo & l'Intelligence Artificielle (IA).

Couvre :
1. Configuration des profils de difficulté (Facile, Moyen, Difficile).
2. Raycasting de Ligne de Vue (Line of Sight) avec détection d'obstacles.
3. Alignement géométrique sur les 8 directions (snap_to_8_directions).
4. Machine à états comportementale (PATROL, CHASE, ATTACK, RETREAT, SEEK_POWERUP).
5. Système d'anti-blocage (Anti-Stuck).
6. Anticipation de trajectoire et visée prédictive (lead shots).
7. Conditions de tir et arbitrage tactique.
8. Intégration dans le Lobby et le Menu Principal.
9. Simulation headless d'un combat complet contre l'IA.
"""

import math
import os
import pytest
import pygame

# Configuration headless pour environnement de test
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, BORDER_THICKNESS, BULLET_SPEED
from players.tank import Tank
from players.controls import TankControls
from game.map import ArenaMap
from game.obstacle import Obstacle, ObstacleType, Decoration, DecorationType
from game.powerup import PowerUp, PowerUpManager, PowerUpType
from game.projectile_manager import ProjectileManager
from game.game_state import MatchState
from game.ai_controller import (
    TankAIController,
    AIDifficulty,
    AIState,
    snap_to_8_directions,
)
from interface.menu import MainMenu
from interface.lobby import LobbyScreen
from main import GameApp, AppState, parse_arguments


@pytest.fixture(scope="module", autouse=True)
def init_pygame():
    """Initialise Pygame et le sous-système d'affichage headless."""
    pygame.init()
    if not pygame.font.get_init():
        pygame.font.init()
    if not pygame.display.get_surface():
        pygame.display.set_mode((1600, 900))
    yield


@pytest.fixture
def test_setup():
    """Crée l'environnement de combat pour les tests de l'IA."""
    arena_map = ArenaMap(SCREEN_WIDTH, SCREEN_HEIGHT)
    powerup_mgr = PowerUpManager()

    tank1 = Tank(
        player_id=1,
        color_name="red",
        initial_position=(200.0, 450.0),
        initial_rotation=0.0,
        controls=TankControls.create_player_1_controls(),
    )

    tank2 = Tank(
        player_id=2,
        color_name="green",
        initial_position=(1400.0, 450.0),
        initial_rotation=180.0,
        controls=None,  # Contrôlé par l'IA
    )

    ai = TankAIController(
        tank=tank2,
        target_tank=tank1,
        arena_map=arena_map,
        difficulty=AIDifficulty.MEDIUM,
        powerup_manager=powerup_mgr,
    )

    return arena_map, powerup_mgr, tank1, tank2, ai


# =============================================================================
# 1. TESTS DE CONFIGURATION ET DIFFICULTÉ
# =============================================================================
def test_ai_difficulty_settings(test_setup):
    """Vérifie que chaque niveau de difficulté applique les paramètres tactiques adéquats."""
    _, _, _, _, ai = test_setup

    # Mode Facile (Recrue)
    ai.set_difficulty(AIDifficulty.EASY)
    assert ai.difficulty == AIDifficulty.EASY
    assert ai.reaction_delay >= 0.25
    assert ai.speed_multiplier < 1.0
    assert ai.aim_tolerance >= 30.0
    assert ai.lead_shots is False

    # Mode Moyen (Vétéran)
    ai.set_difficulty(AIDifficulty.MEDIUM)
    assert ai.difficulty == AIDifficulty.MEDIUM
    assert ai.speed_multiplier == 1.0
    assert ai.aim_tolerance == 25.0
    assert ai.lead_shots is False

    # Mode Difficile (Élite)
    ai.set_difficulty(AIDifficulty.HARD)
    assert ai.difficulty == AIDifficulty.HARD
    assert ai.reaction_delay <= 0.05
    assert ai.speed_multiplier == 1.0
    assert ai.aim_tolerance <= 22.5
    assert ai.lead_shots is True


# =============================================================================
# 2. TESTS DE RAYCASTING ET LIGNE DE VUE (LINE OF SIGHT)
# =============================================================================
def test_ai_line_of_sight(test_setup):
    """Vérifie que la ligne de vue distingue les obstacles bloquants des éléments décoratifs."""
    arena_map, _, tank1, tank2, ai = test_setup
    arena_map.obstacles.clear()
    arena_map.decorations.clear()

    # Positions de test dégagées
    pos_a = pygame.Vector2(100.0, 100.0)
    pos_b = pygame.Vector2(500.0, 100.0)

    # Ligne dégagée
    assert ai.has_line_of_sight(pos_a, pos_b) is True

    # Ajout d'une barrière métallique (bloque les tirs) entre les deux points
    arena_map.obstacles.append(Obstacle(ObstacleType.BARRIER_VERTICAL, 300, 100))
    assert ai.has_line_of_sight(pos_a, pos_b) is False

    # Retrait de la barrière et ajout d'une plante décorative (ne bloque pas les projectiles)
    arena_map.obstacles.clear()
    arena_map.decorations.append(Decoration(DecorationType.CACTUS, 300, 100))
    assert ai.has_line_of_sight(pos_a, pos_b) is True


# =============================================================================
# 3. TESTS D'ALIGNEMENT GÉOMÉTRIQUE SUR 8 DIRECTIONS
# =============================================================================
def test_snap_to_8_directions():
    """Vérifie le snapping angulaire précis sur les 8 axes cardinaux et diagonaux."""
    # Axe Est (0°)
    deg, vec = snap_to_8_directions(5.0)
    assert deg == 0.0
    assert pytest.approx(vec.x) == 1.0 and pytest.approx(vec.y) == 0.0

    # Axe Sud-Est (45°)
    deg, _ = snap_to_8_directions(42.0)
    assert deg == 45.0

    # Axe Sud (90°)
    deg, vec = snap_to_8_directions(88.0)
    assert deg == 90.0
    assert pytest.approx(vec.x) == 0.0 and pytest.approx(vec.y) == 1.0

    # Axe Ouest (180°)
    deg, _ = snap_to_8_directions(175.0)
    assert deg == 180.0

    # Axe Nord (270°)
    deg, _ = snap_to_8_directions(265.0)
    assert deg == 270.0


# =============================================================================
# 4. TESTS DE LA MACHINE À ÉTATS FINIS (FSM)
# =============================================================================
def test_ai_state_patrol_when_far(test_setup):
    """L'IA patrouille quand la cible est trop éloignée et hors de vue."""
    _, _, tank1, tank2, ai = test_setup
    tank1.position = pygame.Vector2(100.0, 100.0)
    tank2.position = pygame.Vector2(1500.0, 800.0)  # Distance > 1000 px

    ai.update(0.1)
    assert ai.state == AIState.PATROL


def test_ai_state_chase_when_intermediate_distance(test_setup):
    """L'IA traque le joueur quand il est à distance moyenne sans ligne directe."""
    arena_map, _, tank1, tank2, ai = test_setup
    tank1.position = pygame.Vector2(400.0, 400.0)
    tank2.position = pygame.Vector2(1050.0, 400.0)  # Distance 650 px

    # Bloquer la ligne de vue pour éviter le passage direct en ATTACK
    arena_map.obstacles.append(Obstacle(ObstacleType.BARRIER_VERTICAL, 700, 400))

    ai.update(0.1)
    assert ai.state == AIState.CHASE


def test_ai_state_attack_when_in_range_and_los(test_setup):
    """L'IA engage le combat dès qu'elle a une ligne de vue nette et une portée adéquate."""
    arena_map, _, tank1, tank2, ai = test_setup
    arena_map.obstacles.clear()

    tank1.position = pygame.Vector2(400.0, 400.0)
    tank2.position = pygame.Vector2(750.0, 400.0)  # Distance 350 px, pas d'obstacle

    ai.update(0.1)
    assert ai.state == AIState.ATTACK


def test_ai_state_retreat_on_shielded_player(test_setup):
    """L'IA bat en retraite immédiatement si le joueur a un bouclier actif."""
    arena_map, _, tank1, tank2, ai = test_setup
    arena_map.obstacles.clear()

    tank1.position = pygame.Vector2(400.0, 400.0)
    tank2.position = pygame.Vector2(650.0, 400.0)
    tank1.shield_timer = 5.0  # Joueur invincible

    ai.update(0.1)
    assert ai.state == AIState.RETREAT


def test_ai_state_seek_powerup(test_setup):
    """L'IA se détourne pour ramasser un bonus proche au sol."""
    _, powerup_mgr, tank1, tank2, ai = test_setup
    tank1.position = pygame.Vector2(100.0, 100.0)
    tank2.position = pygame.Vector2(800.0, 500.0)

    # Spawn d'un bonus bouclier à 150 px de l'IA
    pw = PowerUp(PowerUpType.SHIELD, (800.0, 350.0))
    powerup_mgr.active_powerups = [pw]

    ai.update(0.1)
    assert ai.state == AIState.SEEK_POWERUP


# =============================================================================
# 5. TEST DU SYSTÈME ANTI-BLOCAGE (ANTI-STUCK)
# =============================================================================
def test_ai_anti_stuck(test_setup):
    """Vérifie que l'anti-stuck détecte un piétinement contre un mur et ordonne une évasion."""
    _, _, _, tank2, ai = test_setup

    tank2.position = pygame.Vector2(500.0, 500.0)
    ai.last_pos = pygame.Vector2(500.0, 500.0)
    ai.stuck_check_timer = 0.40

    # L'IA veut avancer vers l'Est (1, 0) mais sa position ne bouge pas
    desired = pygame.Vector2(1.0, 0.0)
    evasion = ai._update_anti_stuck(0.1, desired)

    assert ai.is_stuck is True
    assert evasion is not None
    assert evasion.length_squared() > 0


# =============================================================================
# 6. TESTS DE L'ARBITRAGE DU TIR DE CANON
# =============================================================================
def test_ai_shooting_logic(test_setup):
    """Vérifie que l'IA ne tire que si elle est alignée et que la cible est vulnérable."""
    arena_map, _, tank1, tank2, ai = test_setup
    arena_map.obstacles.clear()
    ai.set_difficulty(AIDifficulty.HARD)

    # Alignement parfait sur l'axe X (tank1 à l'Ouest de tank2)
    tank1.position = pygame.Vector2(400.0, 500.0)
    tank2.position = pygame.Vector2(700.0, 500.0)
    tank2.rotation = 180.0
    tank2.current_cooldown = 0.0

    _, shoot = ai.update(0.1)
    assert shoot is True

    # Si le joueur active un bouclier -> Ne tire plus (économie de munitions)
    tank1.shield_timer = 3.0
    _, shoot = ai.update(0.1)
    assert shoot is False


# =============================================================================
# 7. TESTS DE L'INTERFACE & SALON D'ATTENTE (LOBBY IA)
# =============================================================================
def test_lobby_ai_mode():
    """Vérifie le comportement du salon en mode Solo IA (difficulté, bot prêt)."""
    game_started = [False]

    def on_start():
        game_started[0] = True

    lobby = LobbyScreen(mode="ai", on_start_game=on_start, on_leave=lambda: None)

    # Le bot IA est pré-configuré prêt
    assert lobby.p2_ready is True
    assert lobby.ai_difficulty == "medium"

    # Cycle de difficulté
    lobby.toggle_ai_difficulty()
    assert lobby.ai_difficulty == "hard"
    lobby.toggle_ai_difficulty()
    assert lobby.ai_difficulty == "easy"
    lobby.toggle_ai_difficulty()
    assert lobby.ai_difficulty == "medium"

    # Le joueur se prépare -> le compte à rebours s'enclenche
    lobby.toggle_local_ready()
    assert lobby.p1_ready is True
    lobby.update(0.1)
    assert lobby.countdown is not None


def test_main_menu_ai_button():
    """Vérifie que le menu principal expose le bouton Solo IA lorsque demandé."""
    ai_triggered = [False]

    def on_ai():
        ai_triggered[0] = True

    menu = MainMenu(
        on_play_local=lambda: None,
        on_host_game=lambda: None,
        on_join_game=lambda: None,
        on_quit=lambda: None,
        on_play_ai=on_ai,
    )

    # 5 boutons avec le mode Solo IA
    assert len(menu.buttons) == 5
    assert "SOLO" in menu.buttons[0].text
    menu.buttons[0].on_click()
    assert ai_triggered[0] is True


# =============================================================================
# 8. TESTS D'INTÉGRATION APPLICATION & GAMEPLAY SOLO IA
# =============================================================================
def test_game_app_ai_mode_transitions():
    """Vérifie le cycle de vie complet de l'application en mode Solo IA."""
    app = GameApp()
    assert app.state == AppState.MENU

    # 1. Lancement du mode Solo IA
    app.start_solo_ai()
    assert app.state == AppState.LOBBY
    assert app.play_mode == "ai"
    assert app.lobby_screen is not None
    assert app.lobby_screen.p2_ready is True

    # 2. Modification de difficulté dans le salon
    app.lobby_screen.toggle_ai_difficulty()  # medium -> hard
    assert app.lobby_screen.ai_difficulty == "hard"

    # 3. Lancement du combat
    app.start_gameplay()
    assert app.state == AppState.PLAYING
    assert app.ai_difficulty == "hard"
    assert app.ai_controller is not None
    assert app.ai_controller.difficulty == AIDifficulty.HARD
    assert app.tank2.controls is None  # Tank 2 piloté par l'IA

    # 4. Simulation de plusieurs cycles de combat (30 ticks = 0.5s)
    for _ in range(30):
        app.update(1.0 / 60.0)

    # 5. Rendu graphique sans erreur
    app.draw()

    # 6. Fin de match et Proclamation de Victoire
    app.match_state.is_game_over = True
    app.match_state.winner_id = 1
    app.trigger_game_over()
    assert app.state == AppState.GAME_OVER

    # Rendu graphique Game Over
    app.draw()

    # 7. Retour au Menu Principal
    app.return_to_menu()
    assert app.state == AppState.MENU


def test_cli_argument_parsing():
    """Vérifie la prise en charge des drapeaux en ligne de commande pour le mode Solo IA."""
    import sys

    # Drapeau --ai avec --difficulty hard
    sys.argv = ["main.py", "--ai", "--difficulty", "hard"]
    args = parse_arguments()
    assert args.solo_ai is True
    assert args.difficulty == "hard"

    # Drapeau alias --solo
    sys.argv = ["main.py", "--solo"]
    args = parse_arguments()
    assert args.solo_ai is True
    assert args.difficulty == "medium"

