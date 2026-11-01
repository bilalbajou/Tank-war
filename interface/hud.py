"""Affichage Tête Haute (HUD) pour Tank War (Arena Duel).

Affiche :
- Les 3 vies de chaque joueur sous forme d'icônes de cœurs/blindage.
- Le score actuel de chaque joueur et l'objectif de 5 points.
- Le chronomètre de 90 secondes avec bascule en Mort Subite.
- L'état et la durée restante des power-ups actifs pour chaque char.
"""

from typing import Optional
import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from game.game_state import MatchState
from players.tank import Tank


class HUD:
    """Gestionnaire de l'interface graphique en cours de combat."""

    def __init__(self) -> None:
        self.font_score = pygame.font.SysFont("Segoe UI", 32, bold=True)
        self.font_timer = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.font_player = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self.font_small = pygame.font.SysFont("Segoe UI", 14)

    def draw(
        self,
        surface: pygame.Surface,
        match_state: MatchState,
        tank1: Tank,
        tank2: Tank,
        fps: float = 60.0
    ) -> None:
        """Dessine l'ensemble des éléments d'information sur la surface de jeu."""
        # 1. Panneau supérieur central (Fond sombre translucide)
        panel_w = 760
        panel_h = 74
        panel_x = (SCREEN_WIDTH - panel_w) // 2
        panel_y = 12

        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((18, 20, 26, 215))
        pygame.draw.rect(panel_surf, (80, 90, 110, 150), panel_surf.get_rect(), width=2, border_radius=10)
        surface.blit(panel_surf, (panel_x, panel_y))

        # 2. Section Joueur 1 (Gauche)
        self._draw_player_section(
            surface,
            player_num=1,
            name="J1 (ROUGE)",
            lives=tank1.vie,
            max_lives=tank1.max_vie,
            color=(231, 76, 60),
            anchor_x=panel_x + 24,
            anchor_y=panel_y + 12,
            tank=tank1
        )

        # 3. Section Centrale : Score & Chronomètre
        self._draw_center_section(surface, match_state, panel_x + panel_w // 2, panel_y + 10)

        # 4. Section Joueur 2 (Droite)
        self._draw_player_section(
            surface,
            player_num=2,
            name="J2 (VERT)",
            lives=tank2.vie,
            max_lives=tank2.max_vie,
            color=(46, 204, 113),
            anchor_x=panel_x + panel_w - 180,
            anchor_y=panel_y + 12,
            tank=tank2
        )

        # 5. Raccourci pause en haut à droite
        from interface.icon_manager import icon_manager
        icon_manager.draw_icon(surface, "hud/pause", (panel_x + panel_w + 14, panel_y + 24), size=(22, 22))
        pause_txt = self.font_small.render("[P]", True, (160, 170, 185))
        surface.blit(pause_txt, (panel_x + panel_w + 40, panel_y + 28))

        # 6. Compteur FPS discret en bas à droite
        fps_text = f"FPS: {int(fps)}"
        fps_surf = self.font_small.render(fps_text, True, (160, 165, 175))
        surface.blit(fps_surf, (SCREEN_WIDTH - 80, SCREEN_HEIGHT - 26))

    def _draw_player_section(
        self,
        surface: pygame.Surface,
        player_num: int,
        name: str,
        lives: int,
        max_lives: int,
        color: tuple[int, int, int],
        anchor_x: int,
        anchor_y: int,
        tank: Tank
    ) -> None:
        """Affiche le nom, les cœurs de vie et les power-ups actifs d'un joueur."""
        from interface.icon_manager import icon_manager

        # Nom du joueur
        name_surf = self.font_player.render(name, True, color)
        surface.blit(name_surf, (anchor_x, anchor_y))

        # Cœurs de vie sous forme d'icônes réelles health.png
        heart_y = anchor_y + 24
        for i in range(max_lives):
            hx = anchor_x + i * 24
            state = "normal" if i < lives else "disabled"
            icon_manager.draw_icon(surface, "hud/health", (hx, heart_y), size=(20, 20), state=state)

        # Indicateur de munition / rechargement du canon
        ammo_x = anchor_x + max_lives * 24 + 10
        ammo_state = "normal" if tank.current_cooldown <= 0.0 else "disabled"
        icon_manager.draw_icon(surface, "hud/ammo", (ammo_x, heart_y - 2), size=(22, 22), state=ammo_state)

        # Badges des power-ups actifs sous le panneau
        badge_y = anchor_y + 70
        badge_x = anchor_x
        if tank.shield_timer > 0.0:
            self._draw_powerup_badge(surface, "BOUCLIER", f"{tank.shield_timer:.1f}s", (52, 152, 219), badge_x, badge_y, "hud/shield")
            badge_x += 108
        if tank.speed_timer > 0.0:
            self._draw_powerup_badge(surface, "VITESSE", f"{tank.speed_timer:.1f}s", (241, 196, 15), badge_x, badge_y, "hud/speed")
            badge_x += 102
        if tank.rapid_fire_timer > 0.0:
            self._draw_powerup_badge(surface, "TIR RAPIDE", f"{tank.rapid_fire_timer:.1f}s", (231, 76, 60), badge_x, badge_y, "hud/ammo")

    def _draw_powerup_badge(
        self,
        surface: pygame.Surface,
        label: str,
        duration_str: str,
        color: tuple[int, int, int],
        x: int,
        y: int,
        icon_name: Optional[str] = None
    ) -> None:
        """Dessine une pilule informative avec icône pour un bonus actif."""
        from interface.icon_manager import icon_manager
        text = f"{label} {duration_str}"
        text_surf = self.font_small.render(text, True, (250, 250, 250))
        icon_w = 20 if icon_name else 0
        w = text_surf.get_width() + 14 + icon_w
        h = max(24, text_surf.get_height() + 8)

        badge_rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, color, badge_rect, border_radius=7)
        pygame.draw.rect(surface, (20, 20, 20), badge_rect, width=1, border_radius=7)

        cur_x = x + 6
        if icon_name:
            icon_manager.draw_icon(surface, icon_name, (cur_x, y + (h - 16) // 2), size=(16, 16))
            cur_x += 20

        surface.blit(text_surf, (cur_x, y + (h - text_surf.get_height()) // 2))

    def _draw_center_section(
        self,
        surface: pygame.Surface,
        match_state: MatchState,
        center_x: int,
        top_y: int
    ) -> None:
        """Affiche le score central (P1 vs P2) avec trophée et chronomètre avec icône."""
        from interface.icon_manager import icon_manager

        # Trophée central au-dessus du score
        icon_manager.draw_icon(surface, "hud/score", (center_x - 12, top_y + 2), size=(24, 24))

        # Score central format : "2  -  1"
        score_text = f"{match_state.p1_score}   -   {match_state.p2_score}"
        score_surf = self.font_score.render(score_text, True, (245, 245, 245))
        score_rect = score_surf.get_rect(center=(center_x, top_y + 26))
        surface.blit(score_surf, score_rect)

        # Chronomètre ou Mort Subite
        if match_state.is_sudden_death:
            timer_text = "MORT SUBITE"
            timer_color = (255, 204, 0)
        else:
            total_sec = max(0, int(match_state.time_remaining))
            minutes = total_sec // 60
            seconds = total_sec % 60
            timer_text = f"{minutes:02d}:{seconds:02d}"
            timer_color = (245, 80, 80) if total_sec <= 15 else (210, 215, 225)

        timer_surf = self.font_timer.render(timer_text, True, timer_color)
        total_timer_w = 20 + 8 + timer_surf.get_width()
        start_t_x = center_x - total_timer_w // 2

        icon_manager.draw_icon(surface, "hud/timer", (start_t_x, top_y + 45), size=(20, 20))
        surface.blit(timer_surf, (start_t_x + 26, top_y + 44))

