"""Écran de Menu Principal (Accueil).

Permet de choisir entre créer une partie LAN (Hôte), en rejoindre une (Client)
ou quitter le jeu.
"""

from typing import Callable, Optional
import pygame

from src.core.config import GameConfig
from src.rendering.asset_manager import AssetManager


class MenuButton:
    """Bouton interactif avec détection de survol et clic."""

    def __init__(self, rect: pygame.Rect, text: str, action_code: str) -> None:
        self.rect = rect
        self.text = text
        self.action_code = action_code
        self.is_hovered = False

    def check_hover(self, mouse_pos: tuple[int, int]) -> bool:
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered

    def render(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        bg_color = (60, 110, 200) if self.is_hovered else (40, 50, 70)
        border_color = (120, 180, 255) if self.is_hovered else (80, 95, 120)

        pygame.draw.rect(surface, bg_color, self.rect, border_radius=8)
        pygame.draw.rect(surface, border_color, self.rect, width=2, border_radius=8)

        text_surf = font.render(self.text, True, (250, 250, 250))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)


class StartMenu:
    """Menu d'accueil du jeu Arena Duel."""

    def __init__(self, config: type[GameConfig], on_action: Callable[[str], None]) -> None:
        self.config = config
        self.on_action = on_action
        self.asset_manager = AssetManager.get_instance()

        center_x = self.config.display.SCREEN_WIDTH // 2
        start_y = 420
        btn_width = 380
        btn_height = 54
        spacing = 24

        self.buttons = [
            MenuButton(
                pygame.Rect(center_x - btn_width // 2, start_y, btn_width, btn_height),
                "CRÉER UNE PARTIE (HÔTE LAN)",
                "HOST"
            ),
            MenuButton(
                pygame.Rect(center_x - btn_width // 2, start_y + btn_height + spacing, btn_width, btn_height),
                "REJOINDRE UNE PARTIE (CLIENT)",
                "JOIN"
            ),
            MenuButton(
                pygame.Rect(center_x - btn_width // 2, start_y + (btn_height + spacing) * 2, btn_width, btn_height),
                "QUITTER LE JEU",
                "QUIT"
            ),
        ]

    def handle_event(self, event: pygame.event.Event) -> None:
        """Gère les clics et interactions souris."""
        if event.type == pygame.MOUSEMOTION:
            for btn in self.buttons:
                btn.check_hover(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self.buttons:
                if btn.rect.collidepoint(event.pos):
                    self.on_action(btn.action_code)
                    break

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1 or event.key == pygame.K_KP1:
                self.on_action("HOST")
            elif event.key == pygame.K_2 or event.key == pygame.K_KP2:
                self.on_action("JOIN")
            elif event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                self.on_action("QUIT")

    def update(self, dt: float) -> None:
        """Mise à jour logique du menu."""
        pass

    def render(self, surface: pygame.Surface) -> None:
        """Affiche le menu stylisé."""
        surface.fill(self.config.colors.OVERLAY_BG)

        # Titre Principal
        title_font = self.asset_manager.get_font(64)
        subtitle_font = self.asset_manager.get_font(24)
        hint_font = self.asset_manager.get_font(18)

        title_surf = title_font.render("TANK WAR : ARENA DUEL", True, self.config.colors.TEXT_WHITE)
        title_rect = title_surf.get_rect(center=(self.config.display.SCREEN_WIDTH // 2, 220))
        surface.blit(title_surf, title_rect)

        # Sous-titre
        sub_surf = subtitle_font.render("Jeu de combat de tanks 2D en Réseau Local (LAN 2 Joueurs)", True, self.config.colors.SAND)
        sub_rect = sub_surf.get_rect(center=(self.config.display.SCREEN_WIDTH // 2, 280))
        surface.blit(sub_surf, sub_rect)

        # Ligne décorative
        sep_w = 400
        sep_x = (self.config.display.SCREEN_WIDTH - sep_w) // 2
        pygame.draw.line(surface, self.config.colors.SAND_DARK, (sep_x, 320), (sep_x + sep_w, 320), 2)

        # Boutons
        btn_font = self.asset_manager.get_font(20)
        for btn in self.buttons:
            btn.render(surface, btn_font)

        # Astuces clavier au bas de l'écran
        hint_surf = hint_font.render("Raccourcis : [1] Héberger  •  [2] Rejoindre  •  [Échap] Quitter", True, self.config.colors.TEXT_MUTED)
        hint_rect = hint_surf.get_rect(center=(self.config.display.SCREEN_WIDTH // 2, self.config.display.SCREEN_HEIGHT - 60))
        surface.blit(hint_surf, hint_rect)

