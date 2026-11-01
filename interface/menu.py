"""Menu Principal pour Tank War : Arena Duel.

Présente :
- Logo stylisé Arena Duel avec tank rouge et vert en illustration.
- Bouton 'Jouer (Local)' : duel 2 joueurs sur le même ordinateur.
- Bouton 'Héberger une partie' : lance le serveur TCP pour le jeu en Wi-Fi local.
- Bouton 'Rejoindre une partie' : saisie de l'IP pour se connecter au PC 1.
- Bouton 'Quitter'.
- Support intégral et fluide du clavier (Haut/Bas/Entrée/Échap) et de la souris.
"""

from __future__ import annotations
import math
from typing import Callable, Optional
import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_SAND
from interface.components import (
    UIButton,
    COLOR_GOLD_LIGHT,
    COLOR_TEXT_SHADOW,
    COLOR_TEXT_WHITE,
    draw_cartoon_panel,
)


class MainMenu:
    """Gestionnaire de l'écran d'accueil et du menu principal."""

    def __init__(
        self,
        on_play_local: Callable[[], None],
        on_host_game: Callable[[], None],
        on_join_game: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        self.on_play_local = on_play_local
        self.on_host_game = on_host_game
        self.on_join_game = on_join_game
        self.on_quit = on_quit

        # Typographies
        self.font_logo = pygame.font.SysFont("Segoe UI", 68, bold=True)
        self.font_subtitle = pygame.font.SysFont("Segoe UI", 22, bold=True)
        self.font_footer = pygame.font.SysFont("Segoe UI", 15)

        # Création des boutons centrés
        btn_w = 440
        btn_h = 64
        start_y = 380
        spacing = 86
        center_x = (SCREEN_WIDTH - btn_w) // 2

        self.buttons: list[UIButton] = [
            UIButton(
                pygame.Rect(center_x, start_y, btn_w, btn_h),
                text="JOUER (LOCAL)",
                scheme="green",
                font_size=24,
                icon_name="menu/play",
                icon_size=(30, 30),
                on_click=self.on_play_local,
            ),
            UIButton(
                pygame.Rect(center_x, start_y + spacing, btn_w, btn_h),
                text="HÉBERGER UNE PARTIE",
                scheme="amber",
                font_size=24,
                icon_name="menu/host",
                icon_size=(30, 30),
                on_click=self.on_host_game,
            ),
            UIButton(
                pygame.Rect(center_x, start_y + spacing * 2, btn_w, btn_h),
                text="REJOINDRE UNE PARTIE",
                scheme="blue",
                font_size=24,
                icon_name="menu/join",
                icon_size=(30, 30),
                on_click=self.on_join_game,
            ),
            UIButton(
                pygame.Rect(center_x, start_y + spacing * 3, btn_w, btn_h),
                text="QUITTER",
                scheme="red",
                font_size=24,
                icon_name="menu/exit",
                icon_size=(30, 30),
                on_click=self.on_quit,
            ),
        ]

        # Index du bouton sélectionné au clavier (-1 = aucun)
        self.selected_index = 0
        self.buttons[self.selected_index].is_selected = True

        # Animation subtile du logo
        self.anim_time = 0.0

    def select_next(self) -> None:
        """Déplace la sélection clavier vers le bas."""
        self.buttons[self.selected_index].is_selected = False
        self.selected_index = (self.selected_index + 1) % len(self.buttons)
        self.buttons[self.selected_index].is_selected = True

    def select_prev(self) -> None:
        """Déplace la sélection clavier vers le haut."""
        self.buttons[self.selected_index].is_selected = False
        self.selected_index = (self.selected_index - 1) % len(self.buttons)
        self.buttons[self.selected_index].is_selected = True

    def activate_selected(self) -> None:
        """Active le bouton actuellement sélectionné."""
        if 0 <= self.selected_index < len(self.buttons):
            self.buttons[self.selected_index].trigger()

    def handle_event(self, event: pygame.event.Event) -> None:
        """Gère les entrées clavier et souris pour la navigation."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.select_next()
            elif event.key in (pygame.K_UP, pygame.K_z, pygame.K_w):
                self.select_prev()
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                self.activate_selected()
            elif event.key == pygame.K_ESCAPE:
                self.on_quit()

        # Événements souris pour les boutons
        for i, btn in enumerate(self.buttons):
            if event.type == pygame.MOUSEMOTION:
                if btn.rect.collidepoint(event.pos):
                    # Synchroniser la sélection clavier avec la souris
                    self.buttons[self.selected_index].is_selected = False
                    self.selected_index = i
                    btn.is_selected = True
            btn.handle_event(event)

    def update(self, dt: float) -> None:
        """Met à jour les animations du menu."""
        self.anim_time += dt
        for btn in self.buttons:
            btn.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        """Dessine l'ensemble du menu d'accueil."""
        # 1. Arrière-plan ambiance désert crépusculaire avec motif de dunes
        self._draw_desert_backdrop(surface)

        # 2. Panneau central translucide
        panel_w = 640
        panel_h = 760
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = 70
        draw_cartoon_panel(
            surface,
            pygame.Rect(panel_x, panel_y, panel_w, panel_h),
            border_color=(120, 100, 75),
            bg_color=(24, 20, 18, 220),
            border_radius=22,
        )

        # 3. Logo stylisé et animations
        self._draw_logo(surface, panel_x + panel_w // 2, panel_y + 110)

        # 4. Dessin des boutons interactifs
        for btn in self.buttons:
            btn.draw(surface)

        # 5. Pied de page avec icône contrôles
        from interface.icon_manager import icon_manager
        footer_text = "Contrôles : ZQSD / Flèches pour naviguer • Entrée pour valider • Échap pour quitter"
        txt_footer = self.font_footer.render(footer_text, True, (160, 150, 140))
        total_footer_w = txt_footer.get_width() + 32
        start_footer_x = (SCREEN_WIDTH - total_footer_w) // 2
        icon_manager.draw_icon(surface, "menu/controls", (start_footer_x, SCREEN_HEIGHT - 43), size=(22, 22))
        surface.blit(txt_footer, (start_footer_x + 30, SCREEN_HEIGHT - 40))

    def _draw_logo(self, surface: pygame.Surface, center_x: int, center_y: int) -> None:
        """Dessine l'insigne militaire et le titre animé."""
        float_offset = math.sin(self.anim_time * 2.5) * 4.0

        # Titre principal "ARENA DUEL"
        title_str = "ARENA DUEL"
        title_surf = self.font_logo.render(title_str, True, COLOR_GOLD_LIGHT)
        title_shadow = self.font_logo.render(title_str, True, COLOR_TEXT_SHADOW)
        title_rect = title_surf.get_rect(center=(center_x, center_y + int(float_offset)))

        # Double ombre pour relief cartoon
        surface.blit(title_shadow, (title_rect.x + 3, title_rect.y + 4))
        surface.blit(title_surf, title_rect)

        # Sous-titre "TANK WAR : DUEL EN ARÈNE DÉSERTIQUE"
        sub_str = "★ TANK WAR : DUEL TACTIQUE 2D ★"
        sub_surf = self.font_subtitle.render(sub_str, True, (230, 200, 150))
        sub_shadow = self.font_subtitle.render(sub_str, True, COLOR_TEXT_SHADOW)
        sub_rect = sub_surf.get_rect(center=(center_x, center_y + 54 + int(float_offset)))
        surface.blit(sub_shadow, (sub_rect.x + 1, sub_rect.y + 2))
        surface.blit(sub_surf, sub_rect)

        # Ligne dorée stylisée sous le logo
        line_w = 340
        pygame.draw.line(
            surface,
            (211, 84, 0),
            (center_x - line_w // 2, center_y + 80),
            (center_x + line_w // 2, center_y + 80),
            3,
        )
        pygame.draw.circle(surface, COLOR_GOLD_LIGHT, (center_x, center_y + 80), 5)

        # Illustrations miniatures des deux chars entourant le logo
        self._draw_mini_tank(surface, center_x - 220, center_y + 20, "red", angle=-15)
        self._draw_mini_tank(surface, center_x + 220, center_y + 20, "green", angle=195)

    def _draw_mini_tank(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        color_name: str,
        angle: float,
    ) -> None:
        """Dessine une silhouette miniature stylisée d'un char."""
        tank_surf = pygame.Surface((48, 36), pygame.SRCALPHA)
        primary = (220, 60, 50) if color_name == "red" else (40, 180, 90)
        darker = (150, 30, 25) if color_name == "red" else (25, 120, 60)

        # Chenilles
        pygame.draw.rect(tank_surf, (40, 40, 45), (0, 0, 48, 8), border_radius=3)
        pygame.draw.rect(tank_surf, (40, 40, 45), (0, 28, 48, 8), border_radius=3)
        # Châssis
        pygame.draw.rect(tank_surf, primary, (6, 6, 36, 24), border_radius=5)
        # Tourelle
        pygame.draw.circle(tank_surf, darker, (24, 18), 9)
        # Canon
        pygame.draw.rect(tank_surf, (30, 30, 35), (24, 16, 22, 5), border_radius=2)

        rot_surf = pygame.transform.rotate(tank_surf, angle)
        surface.blit(rot_surf, rot_surf.get_rect(center=(x, y)))

    def _draw_desert_backdrop(self, surface: pygame.Surface) -> None:
        """Dessine un ciel crépusculaire avec dunes de sable en silhouette."""
        # Dégradé vertical désertique
        surface.fill((34, 25, 20))
        h = SCREEN_HEIGHT

        # Dégradé vers le bas
        dune_color_back = (55, 38, 28)
        dune_color_mid = (85, 58, 38)
        dune_color_fore = (120, 85, 50)

        # Dunes ondulées
        pts_back = [
            (0, h),
            (0, h - 220),
            (400, h - 260),
            (900, h - 210),
            (1300, h - 280),
            (SCREEN_WIDTH, h - 230),
            (SCREEN_WIDTH, h),
        ]
        pygame.draw.polygon(surface, dune_color_back, pts_back)

        pts_mid = [
            (0, h),
            (0, h - 140),
            (500, h - 190),
            (1000, h - 130),
            (1450, h - 170),
            (SCREEN_WIDTH, h - 120),
            (SCREEN_WIDTH, h),
        ]
        pygame.draw.polygon(surface, dune_color_mid, pts_mid)

        pts_fore = [
            (0, h),
            (0, h - 70),
            (600, h - 110),
            (1200, h - 60),
            (SCREEN_WIDTH, h - 90),
            (SCREEN_WIDTH, h),
        ]
        pygame.draw.polygon(surface, dune_color_fore, pts_fore)

