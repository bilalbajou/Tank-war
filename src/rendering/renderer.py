"""Moteur de rendu graphique 2D pour Arena Duel.

Délègue l'affichage de l'arène désertique, des obstacles, des tanks,
des projectiles et du HUD sur la surface Pygame.
"""

import math
import pygame
from typing import Optional

from src.core.config import GameConfig
from game.map import ArenaMap
from src.rendering.asset_manager import AssetManager
from src.rendering.hud import HUD


class Renderer:
    """Responsable du dessin complet d'une trame visuelle."""

    def __init__(self, surface: pygame.Surface, config: type[GameConfig] = GameConfig) -> None:
        self.surface = surface
        self.config = config
        self.asset_manager = AssetManager.get_instance()
        self.hud = HUD(config)
        self.arena = ArenaMap(config.display.SCREEN_WIDTH, config.display.SCREEN_HEIGHT)

    def render_preview(self, fps: float = 60.0) -> None:
        """Affiche un aperçu dynamique complet de l'arène et de ses entités."""
        self.arena.draw(self.surface)
        self._render_preview_tanks()
        self.hud.render(self.surface, p1_health=100, p2_health=85, p1_score=2, p2_score=1, current_fps=fps)

    def _render_preview_tanks(self) -> None:
        """Affiche des représentations vectorielles temporaires des 2 tanks pour la prévisualisation."""
        # Joueur 1 (Position initiale spawn 1)
        p1_spawn, p1_angle = self.arena.get_spawn(1)
        self._draw_tank(p1_spawn, p1_angle, self.config.colors.PLAYER_ONE)

        # Joueur 2 (Position initiale spawn 2)
        p2_spawn, p2_angle = self.arena.get_spawn(2)
        self._draw_tank(p2_spawn, p2_angle, self.config.colors.PLAYER_TWO)

    def _draw_tank(self, center: tuple[float, float], angle_deg: float, color: tuple[int, int, int]) -> None:
        """Dessine un tank avec châssis, chenilles et canon orienté."""
        cx, cy = center
        w = self.config.tank.WIDTH
        h = self.config.tank.HEIGHT

        # Création d'une surface pour appliquer la rotation
        tank_surf = pygame.Surface((int(w + 20), int(h + 20)), pygame.SRCALPHA)
        center_local = (tank_surf.get_width() // 2, tank_surf.get_height() // 2)

        # Châssis principal
        chassis_rect = pygame.Rect(center_local[0] - w / 2, center_local[1] - h / 2, w, h)
        pygame.draw.rect(tank_surf, color, chassis_rect, border_radius=6)
        pygame.draw.rect(tank_surf, (20, 20, 20), chassis_rect, 2, border_radius=6)

        # Chenilles
        track_h = 10
        pygame.draw.rect(tank_surf, (40, 40, 40), (chassis_rect.left, chassis_rect.top - 2, w, track_h), border_radius=2)
        pygame.draw.rect(tank_surf, (40, 40, 40), (chassis_rect.left, chassis_rect.bottom - track_h + 2, w, track_h), border_radius=2)

        # Tourelle centrale
        pygame.draw.circle(tank_surf, (40, 40, 40), center_local, 14)
        
        # Canon pointant vers la droite (0°)
        pygame.draw.line(tank_surf, (20, 20, 20), center_local, (center_local[0] + 32, center_local[1]), 6)

        # Rotation
        rotated_surf = pygame.transform.rotate(tank_surf, -angle_deg)
        new_rect = rotated_surf.get_rect(center=(int(cx), int(cy)))
        self.surface.blit(rotated_surf, new_rect)

