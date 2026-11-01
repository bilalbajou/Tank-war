"""Affichage tête haute (Heads-Up Display - HUD).

Affiche les jauges de vie des 2 joueurs, les scores, le compteur de FPS
et l'état de la connexion.
"""

import pygame
from src.core.config import GameConfig
from src.rendering.asset_manager import AssetManager


class HUD:
    """Composant de rendu de l'interface superposée au jeu."""

    def __init__(self, config: type[GameConfig] = GameConfig) -> None:
        self.config = config
        self.asset_manager = AssetManager.get_instance()

    def render(
        self,
        surface: pygame.Surface,
        p1_health: int = 100,
        p2_health: int = 100,
        p1_score: int = 0,
        p2_score: int = 0,
        current_fps: float = 60.0
    ) -> None:
        """Dessine l'ensemble des éléments du HUD sur la surface cible."""
        # Jauge Joueur 1 (Bleu - Gauche)
        self._render_health_bar(surface, 50, 30, 250, 24, p1_health, self.config.colors.PLAYER_ONE, "P1 (Hôte)")

        # Jauge Joueur 2 (Rouge - Droite)
        self._render_health_bar(surface, self.config.display.SCREEN_WIDTH - 300, 30, 250, 24, p2_health, self.config.colors.PLAYER_TWO, "P2 (Client)")

        # Score central
        font = self.asset_manager.get_font(28)
        score_text = f"{p1_score}  -  {p2_score}"
        score_surf = font.render(score_text, True, self.config.colors.TEXT_WHITE)
        score_rect = score_surf.get_rect(center=(self.config.display.SCREEN_WIDTH // 2, 42))
        surface.blit(score_surf, score_rect)

        # Indicateur FPS
        small_font = self.asset_manager.get_font(16)
        fps_surf = small_font.render(f"FPS: {int(current_fps)} / 60", True, self.config.colors.TEXT_MUTED)
        surface.blit(fps_surf, (self.config.display.SCREEN_WIDTH - 120, self.config.display.SCREEN_HEIGHT - 30))

    def _render_health_bar(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        width: int,
        height: int,
        health: int,
        color: tuple[int, int, int],
        label: str
    ) -> None:
        """Dessine une jauge de santé stylisée."""
        font = self.asset_manager.get_font(18)
        label_surf = font.render(label, True, self.config.colors.TEXT_WHITE)
        surface.blit(label_surf, (x, y - 22))

        # Fond de la jauge
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, self.config.colors.HEALTH_BAR_BG, bg_rect, border_radius=4)

        # Remplissage de la jauge
        ratio = max(0.0, min(1.0, health / self.config.tank.MAX_HEALTH))
        fg_width = int(width * ratio)
        if fg_width > 0:
            fg_rect = pygame.Rect(x, y, fg_width, height)
            pygame.draw.rect(surface, color, fg_rect, border_radius=4)

        # Bordure extérieure
        pygame.draw.rect(surface, (20, 20, 20), bg_rect, width=2, border_radius=4)

