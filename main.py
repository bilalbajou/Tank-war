"""Point d'entrée principal pour Arena Duel (Tank War).

Fournit :
1. Menu Principal interactif complet (clavier et souris) :
   - Mode Solo & Intelligence Artificielle (3 difficultés : Facile, Moyen, Difficile)
   - Duel Local (2 joueurs sur le même clavier)
   - Héberger une partie LAN (PC 1 - Serveur Autoritaire)
   - Rejoindre une partie LAN (PC 2 - Client distant)
   - Quitter

2. Écrans d'Hébergement et de Connexion :
   - Affichage de l'adresse IP locale et du port
   - Champ de saisie d'IP interactif avec connexion asynchrone non-bloquante

3. Salon d'attente (Lobby) :
   - Fiches des 2 joueurs avec silhouettes de chars
   - Sélecteur de difficulté IA en direct (Facile / Moyen / Difficile)
   - Statut de préparation en temps réel
   - Compte à rebours animé dès que les 2 joueurs sont prêts

4. Combat 2D à 60 FPS constants :
   - HUD complet (3 vies, score à 5, chrono 90s, bonus)
   - Machine à états IA (Patrouille, Traque, Combat, Repli, Collecte de bonus)
   - Menu Pause (Échap / P) avec Reprendre, Recommencer et Menu
   - Écran de Victoire / Défaite avec Rejouer et Menu

5. Raccourcis en ligne de commande :
   - python main.py                     -> Menu d'accueil interactif
   - python main.py --ai [--difficulty] -> Démarre directement en mode Solo contre l'IA
   - python main.py --host              -> Démarre directement en mode Hôte
   - python main.py --join <IP_HOTE>    -> Démarre directement en mode Client
   - python main.py --local             -> Démarre directement en mode 2 joueurs local
"""

from __future__ import annotations
import sys
import argparse
import math
from enum import Enum, auto
from typing import Optional
import pygame

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    WINDOW_TITLE,
    BORDER_THICKNESS,
    PLAYER_1_SPAWN,
    PLAYER_2_SPAWN,
)
from game.map import ArenaMap
from game.projectile_manager import ProjectileManager
from game.game_state import MatchState
from game.powerup import PowerUpManager
from players.tank import Tank
from players.controls import TankControls
from interface.hud import HUD
from interface.menu import MainMenu
from interface.lobby import LobbyScreen
from interface.screens import HostScreen, JoinScreen, PauseOverlay, GameOverOverlay
from network.server import NetworkServer
from network.client import NetworkClient
from network.protocol import NetworkProtocol
from game.sound_manager import sound_manager
from game.effects import effects_manager
from game.ai_controller import TankAIController, AIDifficulty


class AppState(Enum):
    """États de l'application gérés par la machine à états."""
    MENU = auto()
    HOST_WAIT = auto()
    JOIN_PROMPT = auto()
    LOBBY = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()


class GameApp:
    """Orchestrateur central de Tank War : navigation, menus, réseau et boucle de combat."""

    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(WINDOW_TITLE)

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.DOUBLEBUF)
        self.clock = pygame.time.Clock()
        self.running = True

        # Mode de jeu ("local", "host", "client", "ai")
        self.play_mode = "local"
        self.ai_controller: Optional[TankAIController] = None
        self.ai_difficulty = "medium"
        self.state = AppState.MENU

        # Entités de jeu et moteur
        self.arena_map = ArenaMap(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.match_state = MatchState(target_score=5, match_duration=90.0, lives_per_round=3)
        self.powerup_manager = PowerUpManager(spawn_interval=12.0, max_active=2)
        self.projectile_manager = ProjectileManager()
        self.hud = HUD()

        self.playable_bounds = pygame.Rect(
            BORDER_THICKNESS,
            BORDER_THICKNESS,
            SCREEN_WIDTH - 2 * BORDER_THICKNESS,
            SCREEN_HEIGHT - 2 * BORDER_THICKNESS,
        )

        # Chars des joueurs
        self.tank1: Optional[Tank] = None
        self.tank2: Optional[Tank] = None

        # Couche Réseau
        self.server: Optional[NetworkServer] = None
        self.client: Optional[NetworkClient] = None
        self.default_port = 4242

        # Écrans d'interface
        self.menu_screen = MainMenu(
            on_play_local=self.start_local,
            on_host_game=self.start_hosting,
            on_join_game=self.start_joining,
            on_quit=self.quit,
            on_play_ai=self.start_solo_ai,
        )
        self.host_screen: Optional[HostScreen] = None
        self.join_screen: Optional[JoinScreen] = None
        self.lobby_screen: Optional[LobbyScreen] = None

        self.pause_overlay = PauseOverlay(
            on_resume=self.resume_game,
            on_restart=self.restart_match,
            on_menu=self.return_to_menu,
        )

        self.game_over_overlay = GameOverOverlay(
            on_replay=self.restart_match,
            on_menu=self.return_to_menu,
        )

        # Sprite réutilisable pour obus réseau client
        self.bullet_sprite = pygame.Surface((18, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(self.bullet_sprite, (255, 200, 30), (0, 1, 18, 8))
        pygame.draw.ellipse(self.bullet_sprite, (240, 60, 30), (10, 1, 8, 8))

        self.show_debug = False
        self.font_status = pygame.font.SysFont("Segoe UI", 16, bold=True)

    # -------------------------------------------------------------------------
    # TRANSITIONS DE NAVIGATION
    # -------------------------------------------------------------------------
    def start_local(self) -> None:
        """Démarre le mode 2 joueurs local via le salon de préparation."""
        self.play_mode = "local"
        self.setup_tanks()
        self.lobby_screen = LobbyScreen(
            mode="local",
            on_start_game=self.start_gameplay,
            on_leave=self.return_to_menu,
        )
        self.state = AppState.LOBBY

    def start_solo_ai(self) -> None:
        """Démarre le mode solo contre l'Intelligence Artificielle."""
        self.play_mode = "ai"
        self.cleanup_network()
        self.setup_tanks()
        self.lobby_screen = LobbyScreen(
            mode="ai",
            on_start_game=self.start_gameplay,
            on_leave=self.return_to_menu,
        )
        self.state = AppState.LOBBY

    def start_hosting(self, port: Optional[int] = None) -> None:
        """Démarre l'hôte LAN et affiche l'écran d'attente avec IP locale."""
        self.play_mode = "host"
        use_port = port or self.default_port
        self.cleanup_network()

        self.server = NetworkServer(host="0.0.0.0", port=use_port)
        if not self.server.start():
            print(f"[ERREUR] Impossible de lier le port {use_port}")
            self.return_to_menu()
            return

        self.host_screen = HostScreen(
            server=self.server,
            on_client_joined=self.on_host_client_connected,
            on_cancel=self.return_to_menu,
        )
        self.state = AppState.HOST_WAIT

    def on_host_client_connected(self) -> None:
        """Appelé lorsque le Joueur 2 rejoint le serveur hôte."""
        self.setup_tanks()
        self.lobby_screen = LobbyScreen(
            mode="host",
            on_start_game=self.start_gameplay,
            on_leave=self.return_to_menu,
            server=self.server,
        )
        self.state = AppState.LOBBY

    def start_joining(self) -> None:
        """Ouvre l'écran de saisie d'IP pour rejoindre un hôte."""
        self.play_mode = "client"
        self.cleanup_network()
        self.join_screen = JoinScreen(
            on_connected=self.on_client_connected,
            on_cancel=self.return_to_menu,
        )
        self.state = AppState.JOIN_PROMPT

    def on_client_connected(self, client: NetworkClient) -> None:
        """Appelé dès que la connexion au PC 1 réussit."""
        self.client = client
        self.setup_tanks()
        self.lobby_screen = LobbyScreen(
            mode="client",
            on_start_game=self.start_gameplay,
            on_leave=self.return_to_menu,
            client=self.client,
        )
        self.state = AppState.LOBBY

    def start_gameplay(self) -> None:
        """Lance le match et active la boucle de combat."""
        if self.play_mode == "ai" and self.lobby_screen and hasattr(self.lobby_screen, "ai_difficulty"):
            self.ai_difficulty = self.lobby_screen.ai_difficulty
        self.reset_match()
        self.state = AppState.PLAYING

    def pause_game(self) -> None:
        """Met le combat en pause."""
        self.state = AppState.PAUSED

    def resume_game(self) -> None:
        """Reprend le combat."""
        self.state = AppState.PLAYING

    def trigger_game_over(self) -> None:
        """Déclenche la proclamation sonore, les confettis et bascule vers GAME_OVER."""
        self.state = AppState.GAME_OVER
        effects_manager.trigger_victory(SCREEN_WIDTH, SCREEN_HEIGHT)

        # Audio selon le point de vue du joueur
        if self.play_mode == "local":
            sound_manager.play_victory()
        elif self.play_mode == "ai":
            if self.match_state.winner_id == 1:
                sound_manager.play_victory()
            else:
                sound_manager.play_defeat()
        elif self.play_mode == "host":
            if self.match_state.winner_id == 1:
                sound_manager.play_victory()
            else:
                sound_manager.play_defeat()
        elif self.play_mode == "client":
            if self.match_state.winner_id == 2:
                sound_manager.play_victory()
            else:
                sound_manager.play_defeat()

    def restart_match(self) -> None:
        """Relance une nouvelle manche depuis le début."""
        self.reset_match()
        self.state = AppState.PLAYING

    def return_to_menu(self) -> None:
        """Quitte la partie en cours et revient au menu principal."""
        self.cleanup_network()
        self.reset_match()
        self.state = AppState.MENU

    def quit(self) -> None:
        """Arrête la boucle principale et ferme l'application."""
        self.running = False

    # -------------------------------------------------------------------------
    # GESTION DES ENTITÉS ET DU RÉSEAU
    # -------------------------------------------------------------------------
    def setup_tanks(self) -> None:
        """Instancie les chars selon le mode de jeu."""
        p1_ctrl = TankControls.create_player_1_controls() if self.play_mode != "client" else None
        p2_ctrl = TankControls.create_player_2_controls() if self.play_mode == "local" else None

        self.tank1 = Tank(
            player_id=1,
            color_name="red",
            initial_position=(PLAYER_1_SPAWN[0], PLAYER_1_SPAWN[1]),
            initial_rotation=PLAYER_1_SPAWN[2],
            controls=p1_ctrl,
            speed=220.0,
            max_health=3,
            fire_cooldown=0.45,
            bullet_damage=1,
        )

        self.tank2 = Tank(
            player_id=2,
            color_name="green",
            initial_position=(PLAYER_2_SPAWN[0], PLAYER_2_SPAWN[1]),
            initial_rotation=PLAYER_2_SPAWN[2],
            controls=p2_ctrl,
            speed=220.0,
            max_health=3,
            fire_cooldown=0.45,
            bullet_damage=1,
        )

        if self.play_mode == "ai":
            diff = AIDifficulty(self.ai_difficulty)
            self.ai_controller = TankAIController(
                tank=self.tank2,
                target_tank=self.tank1,
                arena_map=self.arena_map,
                powerup_manager=self.powerup_manager,
                difficulty=diff,
            )
        else:
            self.ai_controller = None

    def reset_match(self) -> None:
        """Remet à zéro l'arène, les scores, les bonus et repositionne les tanks."""
        self.match_state.reset()
        self.arena_map.reset()
        self.powerup_manager.clear()
        self.projectile_manager.clear()
        effects_manager.clear()
        effects_manager.stop_victory()

        if not self.tank1 or not self.tank2:
            self.setup_tanks()

        if self.tank1:
            self.tank1.respawn((PLAYER_1_SPAWN[0], PLAYER_1_SPAWN[1]), PLAYER_1_SPAWN[2])
        if self.tank2:
            self.tank2.respawn((PLAYER_2_SPAWN[0], PLAYER_2_SPAWN[1]), PLAYER_2_SPAWN[2])

        if self.play_mode == "ai":
            diff = AIDifficulty(self.ai_difficulty)
            if self.ai_controller:
                self.ai_controller.tank = self.tank2
                self.ai_controller.target = self.tank1
                self.ai_controller.set_difficulty(diff)
                self.ai_controller.reset()
            else:
                self.ai_controller = TankAIController(
                    tank=self.tank2,
                    target_tank=self.tank1,
                    arena_map=self.arena_map,
                    powerup_manager=self.powerup_manager,
                    difficulty=diff,
                )

    def cleanup_network(self) -> None:
        """Libère proprement toutes les sockets réseau et écouteurs de découverte."""
        if self.client:
            self.client.disconnect()
            self.client = None
        if self.server:
            self.server.stop()
            self.server = None
        if self.join_screen:
            if hasattr(self.join_screen, "discovery_listener") and self.join_screen.discovery_listener:
                self.join_screen.discovery_listener.stop()
                self.join_screen.discovery_listener = None

    # -------------------------------------------------------------------------
    # BOUCLE PRINCIPALE & TRAITEMENT DES ÉVÉNEMENTS
    # -------------------------------------------------------------------------
    def run(self) -> int:
        """Boucle de cycle de vie principale à 60 FPS."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            # 1. Gestion des événements Pygame
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break

                # Dispatching selon l'état actif
                if self.state == AppState.MENU:
                    self.menu_screen.handle_event(event)

                elif self.state == AppState.HOST_WAIT:
                    if self.host_screen:
                        self.host_screen.handle_event(event)

                elif self.state == AppState.JOIN_PROMPT:
                    if self.join_screen:
                        self.join_screen.handle_event(event)

                elif self.state == AppState.LOBBY:
                    if self.lobby_screen:
                        self.lobby_screen.handle_event(event)

                elif self.state == AppState.PLAYING:
                    if event.type == pygame.KEYDOWN:
                        if event.key in (pygame.K_ESCAPE, pygame.K_p):
                            self.pause_game()
                        elif event.key == pygame.K_F1:
                            self.show_debug = not self.show_debug
                        elif event.key == pygame.K_r and self.play_mode != "client":
                            self.reset_match()

                elif self.state == AppState.PAUSED:
                    self.pause_overlay.handle_event(event)

                elif self.state == AppState.GAME_OVER:
                    self.game_over_overlay.handle_event(event)

            # 2. Mise à jour logique
            self.update(dt)

            # 3. Rendu visuel
            self.draw()
            pygame.display.flip()

        self.cleanup_network()
        pygame.quit()
        return 0

    def update(self, dt: float) -> None:
        """Met à jour l'écran ou le gameplay actif."""
        if self.state == AppState.MENU:
            self.menu_screen.update(dt)

        elif self.state == AppState.HOST_WAIT:
            if self.host_screen:
                self.host_screen.update(dt)

        elif self.state == AppState.JOIN_PROMPT:
            if self.join_screen:
                self.join_screen.update(dt)

        elif self.state == AppState.LOBBY:
            if self.lobby_screen:
                self.lobby_screen.update(dt)

        elif self.state == AppState.PAUSED:
            self.pause_overlay.update(dt)

        elif self.state == AppState.GAME_OVER:
            self.game_over_overlay.update(dt)

        elif self.state == AppState.PLAYING:
            self._update_playing(dt)

        if self.state in (AppState.PLAYING, AppState.PAUSED, AppState.GAME_OVER):
            effects_manager.update(dt)

    def _update_playing(self, dt: float) -> None:
        """Met à jour le combat selon le mode (Hôte autoritaire, Client ou Local)."""
        if not self.tank1 or not self.tank2:
            return

        # =====================================================================
        # MODE CLIENT (PC 2)
        # =====================================================================
        if self.play_mode == "client" and self.client:
            if not self.client.is_connected:
                return

            # Échantillonnage des touches du Joueur 2 et transmission au serveur
            keys = pygame.key.get_pressed()
            up = bool(keys[pygame.K_UP])
            down = bool(keys[pygame.K_DOWN])
            left = bool(keys[pygame.K_LEFT])
            right = bool(keys[pygame.K_RIGHT])
            shoot = bool(keys[pygame.K_RETURN] or keys[pygame.K_KP_ENTER] or keys[pygame.K_SPACE])

            self.client.send_inputs(up=up, down=down, left=left, right=right, shoot=shoot)

            # Réception du dernier instantané d'état émis par l'hôte à 30 Hz
            snapshot = self.client.poll_snapshot()
            if snapshot:
                tanks_data = snapshot.get("tanks", {})
                if "1" in tanks_data:
                    d1 = tanks_data["1"]
                    self.tank1.position.x = d1["x"]
                    self.tank1.position.y = d1["y"]
                    self.tank1.rotation = d1["rot"]
                    self.tank1.vie = d1["lives"]
                    self.tank1.shield_timer = d1["shield"]
                    self.tank1.speed_timer = d1["speed"]
                    self.tank1.rapid_fire_timer = d1["rapid"]
                    self.tank1._update_rotation_sprite()

                if "2" in tanks_data:
                    d2 = tanks_data["2"]
                    self.tank2.position.x = d2["x"]
                    self.tank2.position.y = d2["y"]
                    self.tank2.rotation = d2["rot"]
                    self.tank2.vie = d2["lives"]
                    self.tank2.shield_timer = d2["shield"]
                    self.tank2.speed_timer = d2["speed"]
                    self.tank2.rapid_fire_timer = d2["rapid"]
                    self.tank2._update_rotation_sprite()

                scores = snapshot.get("scores", {})
                self.match_state.p1_score = scores.get("p1", 0)
                self.match_state.p2_score = scores.get("p2", 0)
                self.match_state.time_remaining = float(snapshot.get("time_remaining", 90.0))

                gstate = snapshot.get("game_state", {})
                self.match_state.is_sudden_death = bool(gstate.get("is_sudden_death", False))
                self.match_state.is_game_over = bool(gstate.get("is_game_over", False))
                self.match_state.winner_id = gstate.get("winner_id")
                self.match_state.win_reason = gstate.get("win_reason", "")

                # Synchronisation des destructions de caisses
                destroyed_indices = snapshot.get("destroyed_obstacles", [])
                self.arena_map.apply_destroyed_crate_indices(destroyed_indices)

            self.arena_map.update(dt)

            if self.match_state.is_game_over:
                self.trigger_game_over()

        # =====================================================================
        # MODE HÔTE / MODE LOCAL (PC 1 - SERVEUR AUTORITAIRE)
        # =====================================================================
        else:
            # Traitement des commandes reçues par le réseau pour le Joueur 2
            if self.play_mode == "host" and self.server:
                client_input = self.server.poll_client_inputs()
                if client_input and self.server.has_client_connected():
                    dx, dy = 0.0, 0.0
                    if client_input.get("up"):
                        dy -= 1.0
                    if client_input.get("down"):
                        dy += 1.0
                    if client_input.get("left"):
                        dx -= 1.0
                    if client_input.get("right"):
                        dx += 1.0

                    dir_vec = pygame.Vector2(dx, dy)
                    if dir_vec.length_squared() > 0:
                        self.tank2.direction = dir_vec.normalize()
                        angle_deg = math.degrees(math.atan2(dir_vec.y, dir_vec.x)) % 360.0
                        if angle_deg != self.tank2.rotation:
                            self.tank2.rotation = angle_deg
                            self.tank2._update_rotation_sprite()
                    else:
                        self.tank2.direction = pygame.Vector2(0.0, 0.0)

                    if client_input.get("shoot") and self.tank2.is_alive and not self.match_state.is_game_over:
                        self.projectile_manager.spawn_projectile(self.tank2)
                else:
                    self.tank2.direction = pygame.Vector2(0.0, 0.0)

            # Traitement de l'Intelligence Artificielle en Mode Solo
            elif self.play_mode == "ai" and self.ai_controller and self.tank2.is_alive and not self.match_state.is_game_over:
                ai_dir, ai_shoot = self.ai_controller.update(dt)
                self.tank2.direction = ai_dir
                if ai_shoot and self.tank2.can_shoot():
                    self.projectile_manager.spawn_projectile(self.tank2)

            # Simulation autoritaire
            if not self.match_state.is_game_over:
                self.match_state.update(dt)
                self.arena_map.update(dt)
                self.powerup_manager.update(dt, [self.tank1, self.tank2])

                # Tir P1 (Local / Hôte)
                if self.tank1.is_alive and self.tank1.controls and self.tank1.controls.is_firing():
                    self.projectile_manager.spawn_projectile(self.tank1)

                # Tir P2 (Mode local uniquement)
                if self.play_mode == "local" and self.tank2.is_alive and self.tank2.controls and self.tank2.controls.is_firing():
                    self.projectile_manager.spawn_projectile(self.tank2)

                obstacle_rects = self.arena_map.get_collision_rects()
                if self.tank1.is_alive:
                    self.tank1.update(dt, obstacle_rects, bounds_rect=self.playable_bounds, other_tank_rect=self.tank2.hitbox if self.tank2.is_alive else None)
                if self.tank2.is_alive:
                    self.tank2.update(dt, obstacle_rects, bounds_rect=self.playable_bounds, other_tank_rect=self.tank1.hitbox if self.tank1.is_alive else None)

                self.projectile_manager.update(
                    dt,
                    self.arena_map.obstacles,
                    [self.tank1, self.tank2],
                    self.playable_bounds,
                    arena_map=self.arena_map,
                    match_state=self.match_state,
                )

                # Respawn si élimination
                if self.match_state.respawn_needed:
                    self.tank1.respawn((PLAYER_1_SPAWN[0], PLAYER_1_SPAWN[1]), PLAYER_1_SPAWN[2])
                    self.tank2.respawn((PLAYER_2_SPAWN[0], PLAYER_2_SPAWN[1]), PLAYER_2_SPAWN[2])
                    self.projectile_manager.clear()
                    self.match_state.acknowledge_respawn()
                    if self.ai_controller:
                        self.ai_controller.reset()

            # Diffusion des instantanés à 30 Hz vers le client
            if self.play_mode == "host" and self.server and self.server.has_client_connected() and self.server.should_broadcast_snapshot():
                snapshot = NetworkProtocol.create_snapshot(
                    seq=0,
                    tanks_data={
                        "1": {
                            "x": round(self.tank1.position.x, 1),
                            "y": round(self.tank1.position.y, 1),
                            "rot": round(self.tank1.rotation, 1),
                            "lives": self.tank1.vie,
                            "max_lives": self.tank1.max_vie,
                            "shield": round(self.tank1.shield_timer, 1),
                            "speed": round(self.tank1.speed_timer, 1),
                            "rapid": round(self.tank1.rapid_fire_timer, 1),
                            "is_alive": self.tank1.is_alive,
                        },
                        "2": {
                            "x": round(self.tank2.position.x, 1),
                            "y": round(self.tank2.position.y, 1),
                            "rot": round(self.tank2.rotation, 1),
                            "lives": self.tank2.vie,
                            "max_lives": self.tank2.max_vie,
                            "shield": round(self.tank2.shield_timer, 1),
                            "speed": round(self.tank2.speed_timer, 1),
                            "rapid": round(self.tank2.rapid_fire_timer, 1),
                            "is_alive": self.tank2.is_alive,
                        },
                    },
                    projectiles_data=[
                        {"x": round(p.position.x, 1), "y": round(p.position.y, 1), "rot": round(p.rotation, 1), "owner": p.owner_id}
                        for p in self.projectile_manager.projectiles if p.is_alive
                    ],
                    powerups_data=[
                        {"type": pup.powerup_type.value, "x": round(pup.position.x, 1), "y": round(pup.position.y, 1)}
                        for pup in self.powerup_manager.active_powerups if not pup.is_collected
                    ],
                    destroyed_obstacles_indices=self.arena_map.get_destroyed_crate_indices(),
                    p1_score=self.match_state.p1_score,
                    p2_score=self.match_state.p2_score,
                    time_remaining=self.match_state.time_remaining,
                    is_sudden_death=self.match_state.is_sudden_death,
                    is_game_over=self.match_state.is_game_over,
                    winner_id=self.match_state.winner_id,
                    win_reason=self.match_state.win_reason,
                )
                self.server.broadcast_snapshot(snapshot)

            if self.match_state.is_game_over:
                self.trigger_game_over()

    # -------------------------------------------------------------------------
    # RENDU VISUEL
    # -------------------------------------------------------------------------
    def draw(self) -> None:
        """Dessine l'état actif."""
        if self.state == AppState.MENU:
            self.menu_screen.draw(self.screen)

        elif self.state == AppState.HOST_WAIT:
            if self.host_screen:
                self.host_screen.draw(self.screen)

        elif self.state == AppState.JOIN_PROMPT:
            if self.join_screen:
                self.join_screen.draw(self.screen)

        elif self.state == AppState.LOBBY:
            if self.lobby_screen:
                self.lobby_screen.draw(self.screen)

        elif self.state in (AppState.PLAYING, AppState.PAUSED, AppState.GAME_OVER):
            self._draw_battlefield()

            # Surimpression en cas de Pause
            if self.state == AppState.PAUSED:
                self.pause_overlay.draw(self.screen)

            # Surimpression en cas de Fin de Partie
            elif self.state == AppState.GAME_OVER:
                local_id = 1 if self.play_mode in ("host", "ai") else (2 if self.play_mode == "client" else None)
                self.game_over_overlay.draw(
                    self.screen,
                    winner_id=self.match_state.winner_id,
                    p1_score=self.match_state.p1_score,
                    p2_score=self.match_state.p2_score,
                    win_reason=self.match_state.win_reason,
                    local_player_id=local_id,
                )

    def _draw_battlefield(self) -> None:
        """Rendu graphique du terrain, des chars, projectiles et du HUD."""
        self.arena_map.draw(self.screen)

        if self.play_mode == "client" and self.client:
            # En mode client, affichage des bonus et obus d'après le dernier snapshot
            snapshot = self.client.latest_snapshot
            if snapshot:
                for p in snapshot.get("powerups", []):
                    pos_x, pos_y = p["x"], p["y"]
                    glow = (100, 200, 255) if p["type"] == "shield" else (
                        (255, 230, 100) if p["type"] == "speed" else (255, 120, 80)
                    )
                    pygame.draw.circle(self.screen, glow, (int(pos_x), int(pos_y)), 16, width=2)
                    pygame.draw.circle(self.screen, glow, (int(pos_x), int(pos_y)), 8)

                for b in snapshot.get("projectiles", []):
                    rot = b.get("rot", 0.0)
                    rot_surf = pygame.transform.rotate(self.bullet_sprite, -rot)
                    self.screen.blit(rot_surf, rot_surf.get_rect(center=(int(b["x"]), int(b["y"]))))
        else:
            self.powerup_manager.draw(self.screen)
            self.projectile_manager.draw(self.screen)

        if self.tank1 and self.tank1.is_alive:
            self.tank1.draw(self.screen)
        if self.tank2 and self.tank2.is_alive:
            self.tank2.draw(self.screen)

        if self.show_debug:
            self.arena_map.draw_debug(self.screen)
            if self.tank1 and self.tank1.is_alive:
                pygame.draw.rect(self.screen, (255, 255, 0), self.tank1.hitbox, width=2)
            if self.tank2 and self.tank2.is_alive:
                pygame.draw.rect(self.screen, (255, 255, 0), self.tank2.hitbox, width=2)

        # Particules et effets visuels (explosions, étincelles, confettis)
        effects_manager.draw(self.screen)

        # Affichage du HUD
        if self.tank1 and self.tank2:
            self.hud.draw(self.screen, self.match_state, self.tank1, self.tank2, self.clock.get_fps())

        # Bandeau de statut en bas
        if self.play_mode == "host" and self.server:
            if self.server.has_client_connected():
                st_text = f"🟢 JOUEUR 2 CONNECTÉ | IP : {self.server.local_ip}:{self.server.port}"
                color = (46, 204, 113)
            else:
                st_text = f"📡 EN ATTENTE DU JOUEUR 2 | IP LOCALE : {self.server.local_ip}:{self.server.port}"
                color = (241, 196, 15)
            surf_st = self.font_status.render(st_text, True, color)
            self.screen.blit(surf_st, (20, SCREEN_HEIGHT - 30))

        elif self.play_mode == "client" and self.client:
            st_text = f"🟢 CONNECTÉ À L'HÔTE ({self.client.host_ip}:{self.client.port})"
            surf_st = self.font_status.render(st_text, True, (46, 204, 113))
            self.screen.blit(surf_st, (20, SCREEN_HEIGHT - 30))

        elif self.play_mode == "ai":
            labels = {
                "easy": "FACILE (RECRUE)",
                "medium": "MOYEN (VÉTÉRAN)",
                "hard": "DIFFICILE (ÉLITE)",
            }
            diff_label = labels.get(self.ai_difficulty, self.ai_difficulty.upper())
            st_text = f"🤖 MODE SOLO CONTRE L'IA | DIFFICULTÉ : {diff_label}"
            surf_st = self.font_status.render(st_text, True, (52, 152, 219))
            self.screen.blit(surf_st, (20, SCREEN_HEIGHT - 30))


def parse_arguments() -> argparse.Namespace:
    """Analyse les arguments passés en ligne de commande."""
    parser = argparse.ArgumentParser(description="Tank War : Arena Duel (Multijoueur LAN TCP & Mode Solo IA)")
    parser.add_argument("--host", action="store_true", help="Démarre directement en tant qu'Hôte LAN")
    parser.add_argument("--join", "--client", type=str, default=None, dest="join_ip", help="Se connecte à l'IP de l'Hôte")
    parser.add_argument("--port", type=int, default=4242, help="Port TCP (par défaut : 4242)")
    parser.add_argument("--local", action="store_true", help="Démarre directement en mode 2 joueurs local")
    parser.add_argument("--ai", "--solo", action="store_true", dest="solo_ai", help="Démarre directement en mode Solo contre l'IA")
    parser.add_argument("--difficulty", type=str, choices=["easy", "medium", "hard"], default="medium", help="Niveau de difficulté de l'IA (easy, medium, hard)")
    return parser.parse_args()


def main() -> int:
    """Point d'entrée du programme."""
    args = parse_arguments()
    app = GameApp()

    if args.join_ip:
        client = NetworkClient(host_ip=args.join_ip, port=args.port)
        if client.connect(timeout=3.0):
            app.on_client_connected(client)
        else:
            print(f"[ERREUR] Impossible de se connecter à {args.join_ip}:{args.port}")
            app.start_joining()
    elif args.host:
        app.start_hosting(port=args.port)
    elif args.solo_ai:
        app.ai_difficulty = args.difficulty
        app.start_solo_ai()
        if app.lobby_screen:
            app.lobby_screen.ai_difficulty = args.difficulty
            labels = {
                "easy": "IA : FACILE (RECRUE)",
                "medium": "IA : MOYEN (VÉTÉRAN)",
                "hard": "IA : DIFFICILE (ÉLITE)",
            }
            app.lobby_screen.btn_diff.text = labels[args.difficulty]
    elif args.local:
        app.start_local()

    return app.run()


if __name__ == "__main__":
    sys.exit(main())
