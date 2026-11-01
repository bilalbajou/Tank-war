"""Tableau des scores et écran de fin de partie (Scoreboard) pour Tank War.

Gère l'affichage des résultats finaux, la proclamation du vainqueur,
le récapitulatif des scores et le bandeau d'alerte de Mort Subite.
"""

from typing import Optional
import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from game.game_state import MatchState


class Scoreboard:
    """Gestionnaire des écrans de proclamation et de transition de match."""

    def __init__(self) -> None:
        self.font_title = pygame.font.SysFont("Segoe UI", 48, bold=True)
        self.font_subtitle = pygame.font.SysFont("Segoe UI", 26, bold=True)
        self.font_score = pygame.font.SysFont("Segoe UI", 36, bold=True)
        self.font_info = pygame.font.SysFont("Segoe UI", 20)

    def draw_game_over(self, surface: pygame.Surface, match_state: MatchState) -> None:
        """Affiche le panneau d'écran de fin de match et le vainqueur."""
        if not match_state.is_game_over:
            return

        # Voile d'assombrissement semi-transparent
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((12, 14, 18, 200))
        surface.blit(overlay, (0, 0))

        # Panneau central
        box_w = 680
        box_h = 360
        box_x = (SCREEN_WIDTH - box_w) // 2
        box_y = (SCREEN_HEIGHT - box_h) // 2

        box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        box_surf.fill((25, 28, 36, 240))
        pygame.draw.rect(box_surf, (90, 105, 130), box_surf.get_rect(), width=3, border_radius=14)
        surface.blit(box_surf, (box_x, box_y))

        # 1. Proclamation du Vainqueur avec icône
        from interface.icon_manager import icon_manager
        winner_id = match_state.winner_id
        is_victory = winner_id in (1, 2)
        if winner_id == 1:
            title_text = "VICTOIRE DU JOUEUR 1 !"
            title_color = (231, 76, 60)
        elif winner_id == 2:
            title_text = "VICTOIRE DU JOUEUR 2 !"
            title_color = (46, 204, 113)
        else:
            title_text = "MATCH NUL !"
            title_color = (241, 196, 15)

        title_surf = self.font_title.render(title_text, True, title_color)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, box_y + 60))

        if is_victory:
            icon_manager.draw_icon(surface, "results/victory", (title_rect.left - 54, title_rect.centery - 22), size=(44, 44))
        else:
            icon_manager.draw_icon(surface, "results/defeat", (title_rect.left - 54, title_rect.centery - 22), size=(44, 44))

        surface.blit(title_surf, title_rect)

        # 2. Motif / Raison de la victoire
        reason_surf = self.font_subtitle.render(match_state.win_reason, True, (240, 244, 250))
        reason_rect = reason_surf.get_rect(center=(SCREEN_WIDTH // 2, box_y + 125))
        surface.blit(reason_surf, reason_rect)

        # 3. Score Final
        score_text = f"Score Final : {match_state.p1_score}  -  {match_state.p2_score}"
        score_surf = self.font_score.render(score_text, True, (255, 215, 0))
        score_rect = score_surf.get_rect(center=(SCREEN_WIDTH // 2, box_y + 195))
        surface.blit(score_surf, score_rect)

        # Ligne de séparation
        pygame.draw.line(surface, (70, 80, 95), (box_x + 50, box_y + 245), (box_x + box_w - 50, box_y + 245), 2)

        # 4. Instructions pour rejouer
        prompt_text = "Appuyez sur [R] pour rejouer ou [Échap] pour quitter"
        prompt_surf = self.font_info.render(prompt_text, True, (180, 190, 205))
        prompt_rect = prompt_surf.get_rect(center=(SCREEN_WIDTH // 2, box_y + 295))
        surface.blit(prompt_surf, prompt_rect)

    def draw_sudden_death_banner(self, surface: pygame.Surface) -> None:
        """Affiche un bandeau d'alerte temporaire lors de l'activation de la mort subite."""
        banner_w = 420
        banner_h = 44
        banner_x = (SCREEN_WIDTH - banner_w) // 2
        banner_y = 96

        surf = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
        surf.fill((180, 40, 40, 220))
        pygame.draw.rect(surf, (255, 215, 0), surf.get_rect(), width=2, border_radius=8)

        text = self.font_subtitle.render("MORT SUBITE : 1 COUP FATAL", True, (255, 255, 255))
        text_rect = text.get_rect(center=(banner_w // 2, banner_h // 2))
        surf.blit(text, text_rect)
        surface.blit(surf, (banner_x, banner_y))

