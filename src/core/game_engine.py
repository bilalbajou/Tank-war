"""Moteur principal du jeu (Game Engine).

Responsable du cycle de vie de l'application :
- Initialisation de la fenêtre et de la boucle Pygame à 60 FPS
- Calcul du Delta-Time (dt)
- Routage des événements système
- Coordination entre mise à jour d'état et rendu graphique
"""

import sys
import pygame
from typing import Optional

from src.core.config import GameConfig
from src.core.state_manager import GameState, StateManager
from src.rendering.renderer import Renderer
from src.input.input_handler import InputHandler
from src.ui.menu import StartMenu


class GameEngine:
    """Orchestrateur principal de l'application Pygame."""

    def __init__(self, config: Optional[type[GameConfig]] = None) -> None:
        self.config = config or GameConfig
        self.state_manager = StateManager(initial_state=GameState.MENU)
        
        # Initialisation de Pygame
        pygame.init()
        pygame.display.set_caption(self.config.display.WINDOW_TITLE)

        self.screen = pygame.display.set_mode(
            (self.config.display.SCREEN_WIDTH, self.config.display.SCREEN_HEIGHT),
            pygame.DOUBLEBUF
        )
        self.clock = pygame.time.Clock()
        self.is_running = False

        # Sous-systèmes
        self.input_handler = InputHandler()
        self.renderer = Renderer(self.screen, self.config)
        self.menu = StartMenu(self.config, self._on_menu_action)

    def _on_menu_action(self, action: str) -> None:
        """Gère les choix effectués dans le menu principal."""
        if action == "HOST":
            self.state_manager.change_state(GameState.PLAYING)
        elif action == "JOIN":
            self.state_manager.change_state(GameState.PLAYING)
        elif action == "QUIT":
            self.stop()

    def handle_events(self) -> None:
        """Traite les événements de la file d'attente Pygame."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.stop()
                return

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if self.state_manager.is_in(GameState.PLAYING):
                    self.state_manager.change_state(GameState.MENU)
                else:
                    self.stop()
                return

            # Propagation selon l'état actif
            if self.state_manager.is_in(GameState.MENU):
                self.menu.handle_event(event)
            elif self.state_manager.is_in(GameState.PLAYING):
                self.input_handler.process_event(event)

    def update(self, dt: float) -> None:
        """Met à jour la logique selon le delta-time (en secondes)."""
        if self.state_manager.is_in(GameState.MENU):
            self.menu.update(dt)
        elif self.state_manager.is_in(GameState.PLAYING):
            # Le gameplay et le réseau prendront place ici
            pass

    def render(self) -> None:
        """Délègue le rendu graphique selon l'état actuel."""
        if self.state_manager.is_in(GameState.MENU):
            self.menu.render(self.screen)
        elif self.state_manager.is_in(GameState.PLAYING):
            self.renderer.render_preview(self.clock.get_fps())

        pygame.display.flip()

    def run(self) -> None:
        """Lance la boucle principale du jeu."""
        self.is_running = True
        while self.is_running:
            # dt en secondes pour une physique indépendante du framerate
            dt = self.clock.tick(self.config.display.TARGET_FPS) / 1000.0
            
            self.handle_events()
            self.update(dt)
            self.render()

        self.cleanup()

    def stop(self) -> None:
        """Arrête la boucle de jeu."""
        self.is_running = False

    def cleanup(self) -> None:
        """Libère proprement les ressources."""
        pygame.quit()

