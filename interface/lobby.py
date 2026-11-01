"""Salon d'attente (Lobby) pour Tank War : Arena Duel.

Présente :
- Cartes détaillées des deux joueurs (Joueur 1 Rouge & Joueur 2 Vert).
- Silhouette animée de leur char de combat.
- Statut de préparation en temps réel ('En attente...' / 'Prêt !').
- Bouton 'Prêt' interactif (souris et clavier).
- Compte à rebours animé (3, 2, 1) lorsque les deux joueurs sont prêts.
- Synchronisation réseau de l'état prêt entre le serveur et le client.
"""

from __future__ import annotations
import math
from typing import Callable, Optional
import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from interface.components import (
    UIButton,
    COLOR_GOLD_LIGHT,
    COLOR_GREEN,
    COLOR_RED,
    COLOR_BLUE,
    COLOR_TEXT_SHADOW,
    COLOR_TEXT_WHITE,
    draw_cartoon_panel,
)
from network.server import NetworkServer
from network.client import NetworkClient


class LobbyScreen:
    """Gestionnaire de l'écran de salon avant match."""

    def __init__(
        self,
        mode: str,  # "host", "client", ou "local"
        on_start_game: Callable[[], None],
        on_leave: Callable[[], None],
        server: Optional[NetworkServer] = None,
        client: Optional[NetworkClient] = None,
    ) -> None:
        self.mode = mode
        self.on_start_game = on_start_game
        self.on_leave = on_leave
        self.server = server
        self.client = client

        # États de préparation
        self.p1_ready = False
        self.p2_ready = False

        # Compte à rebours avant lancement
        self.countdown: Optional[float] = None
        self.is_starting = False

        # Typographies
        self.font_player_title = pygame.font.SysFont("Segoe UI", 32, bold=True)
        self.font_role = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self.font_status = pygame.font.SysFont("Segoe UI", 26, bold=True)
        self.font_countdown = pygame.font.SysFont("Segoe UI", 56, bold=True)
        self.font_info = pygame.font.SysFont("Segoe UI", 18)

        # Boutons
        btn_w = 260
        btn_h = 58
        center_x = SCREEN_WIDTH // 2

        ready_text = "TOUS PRÊTS" if self.mode == "local" else "JE SUIS PRÊT"
        self.btn_ready = UIButton(
            pygame.Rect(center_x - 280, 680, btn_w, btn_h),
            text=ready_text,
            scheme="green",
            font_size=20,
            icon_name="network/connected",
            icon_size=(24, 24),
            on_click=self.toggle_local_ready,
        )

        self.btn_leave = UIButton(
            pygame.Rect(center_x + 20, 680, btn_w, btn_h),
            text="QUITTER",
            scheme="red",
            font_size=20,
            icon_name="menu/exit",
            icon_size=(24, 24),
            on_click=self.leave,
        )

        self.anim_time = 0.0

    def toggle_local_ready(self) -> None:
        """Bascule l'état de préparation du joueur local."""
        if self.mode == "host":
            self.p1_ready = not self.p1_ready
            self.btn_ready.text = "ANNULER" if self.p1_ready else "JE SUIS PRÊT"
            self.btn_ready.scheme = "red" if self.p1_ready else "green"
            self.btn_ready.icon_name = "network/disconnected" if self.p1_ready else "network/connected"

        elif self.mode == "client":
            self.p2_ready = not self.p2_ready
            self.btn_ready.text = "ANNULER" if self.p2_ready else "JE SUIS PRÊT"
            self.btn_ready.scheme = "red" if self.p2_ready else "green"
            self.btn_ready.icon_name = "network/disconnected" if self.p2_ready else "network/connected"
            if self.client:
                self.client.send_ready(self.p2_ready)

        elif self.mode == "local":
            # En mode local, un appui sur prêt bascule les 2 joueurs ou lance direct
            self.p1_ready = not self.p1_ready
            self.p2_ready = self.p1_ready
            self.btn_ready.text = "ANNULER" if self.p1_ready else "TOUS PRÊTS"
            self.btn_ready.scheme = "red" if self.p1_ready else "green"
            self.btn_ready.icon_name = "network/disconnected" if self.p1_ready else "network/connected"

    def leave(self) -> None:
        """Ferme la session et quitte le salon."""
        if self.client:
            self.client.disconnect()
        if self.server:
            self.server.stop()
        self.on_leave()

    def handle_event(self, event: pygame.event.Event) -> None:
        """Gère les raccourcis clavier et les clics."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.leave()
                return
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.toggle_local_ready()
                return

        self.btn_ready.handle_event(event)
        self.btn_leave.handle_event(event)

    def update(self, dt: float) -> None:
        """Met à jour les animations, synchronise les états et gère le compte à rebours."""
        self.anim_time += dt
        self.btn_ready.update(dt)
        self.btn_leave.update(dt)

        # 1. Synchronisation réseau en mode Hôte
        if self.mode == "host" and self.server:
            # Récupère l'état prêt du client distant
            self.server.poll_client_inputs()
            self.p2_ready = self.server.client_ready

            # Détection de l'état "tous prêts"
            if self.p1_ready and self.p2_ready and self.server.has_client_connected():
                if self.countdown is None:
                    self.countdown = 3.0

                self.countdown -= dt
                if self.countdown <= 0.0:
                    self.server.broadcast_lobby_state(self.p1_ready, self.p2_ready, countdown=0.0, game_started=True)
                    self.on_start_game()
                    return
                else:
                    self.server.broadcast_lobby_state(self.p1_ready, self.p2_ready, countdown=self.countdown, game_started=False)
            else:
                self.countdown = None
                self.server.broadcast_lobby_state(self.p1_ready, self.p2_ready, countdown=None, game_started=False)

        # 2. Synchronisation réseau en mode Client
        elif self.mode == "client" and self.client:
            lobby_state = self.client.poll_lobby_state()
            if lobby_state:
                self.p1_ready = bool(lobby_state.get("p1_ready", False))
                self.countdown = lobby_state.get("countdown")
                if lobby_state.get("game_started"):
                    self.on_start_game()
                    return

            if self.countdown is not None and self.countdown <= 0.0:
                self.on_start_game()
                return

        # 3. Mode Local
        elif self.mode == "local":
            if self.p1_ready and self.p2_ready:
                if self.countdown is None:
                    self.countdown = 2.0
                self.countdown -= dt
                if self.countdown <= 0.0:
                    self.on_start_game()
                    return
            else:
                self.countdown = None

    def draw(self, surface: pygame.Surface) -> None:
        """Dessine l'écran du lobby avec les fiches des 2 joueurs."""
        surface.fill((22, 20, 24))

        panel_w = 980
        panel_h = 720
        panel_rect = pygame.Rect((SCREEN_WIDTH - panel_w) // 2, 70, panel_w, panel_h)
        draw_cartoon_panel(
            surface,
            panel_rect,
            title="LOBBY DU COMBAT",
            subtitle="Préparez-vous au duel dans l'arène désertique",
            border_color=(243, 156, 18),
            border_radius=22,
        )

        center_x = SCREEN_WIDTH // 2

        # 1. Carte du Joueur 1 (Gauche - Rouge)
        card_w = 380
        card_h = 360
        card_y = 170
        self._draw_player_card(
            surface,
            rect=pygame.Rect(panel_rect.x + 60, card_y, card_w, card_h),
            player_num=1,
            name="Joueur 1 (Rouge)",
            role="HÔTE DE LA PARTIE" if self.mode != "local" else "JOUEUR 1 (ZQSD)",
            is_ready=self.p1_ready,
            color=(231, 76, 60),
            tank_color="red",
        )

        # Insigne "VS" central
        vs_font = pygame.font.SysFont("Segoe UI", 40, bold=True)
        txt_vs = vs_font.render("VS", True, COLOR_GOLD_LIGHT)
        shadow_vs = vs_font.render("VS", True, COLOR_TEXT_SHADOW)
        vs_rect = txt_vs.get_rect(center=(center_x, card_y + card_h // 2))
        surface.blit(shadow_vs, (vs_rect.x + 2, vs_rect.y + 2))
        surface.blit(txt_vs, vs_rect)

        # 2. Carte du Joueur 2 (Droite - Vert)
        is_client_connected = True
        if self.mode == "host" and self.server:
            is_client_connected = self.server.has_client_connected()

        p2_role = "CLIENT DISTANT" if self.mode != "local" else "JOUEUR 2 (FLÈCHES)"
        if not is_client_connected:
            p2_status_str = "En attente de connexion..."
        else:
            p2_status_str = None

        self._draw_player_card(
            surface,
            rect=pygame.Rect(panel_rect.right - 60 - card_w, card_y, card_w, card_h),
            player_num=2,
            name="Joueur 2 (Vert)",
            role=p2_role,
            is_ready=self.p2_ready if is_client_connected else False,
            color=(46, 204, 113),
            tank_color="green",
            custom_status=p2_status_str,
        )

        # 3. Compte à rebours animé
        if self.countdown is not None:
            count_int = max(1, int(math.ceil(self.countdown)))
            cd_text = f"LANCEMENT DU MATCH DANS {count_int}..."
            txt_cd = self.font_countdown.render(cd_text, True, COLOR_GOLD_LIGHT)
            shadow_cd = self.font_countdown.render(cd_text, True, COLOR_TEXT_SHADOW)
            cd_rect = txt_cd.get_rect(center=(center_x, 580))
            surface.blit(shadow_cd, (cd_rect.x + 2, cd_rect.y + 3))
            surface.blit(txt_cd, cd_rect)
        else:
            hint_str = "Appuyez sur 'Je suis prêt' pour lancer le match lorsque les deux joueurs sont connectés."
            txt_hint = self.font_info.render(hint_str, True, (170, 180, 195))
            surface.blit(txt_hint, txt_hint.get_rect(center=(center_x, 580)))

        # Boutons
        self.btn_ready.draw(surface)
        self.btn_leave.draw(surface)

    def _draw_player_card(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        player_num: int,
        name: str,
        role: str,
        is_ready: bool,
        color: tuple[int, int, int],
        tank_color: str,
        custom_status: Optional[str] = None,
    ) -> None:
        """Dessine une fiche de joueur personnalisée avec avatar de char et badge prêt."""
        # Fond de la fiche
        card_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        card_surf.fill((16, 18, 24, 210))
        border_c = COLOR_GREEN if is_ready else (80, 90, 105)
        pygame.draw.rect(card_surf, border_c, card_surf.get_rect(), width=3, border_radius=16)
        surface.blit(card_surf, rect)

        center_x = rect.centerx

        # Nom et rôle
        txt_name = self.font_player_title.render(name, True, color)
        surface.blit(txt_name, txt_name.get_rect(center=(center_x, rect.y + 45)))

        txt_role = self.font_role.render(role, True, (160, 175, 190))
        surface.blit(txt_role, txt_role.get_rect(center=(center_x, rect.y + 80)))

        # Silhouette de char au centre
        self._draw_tank_avatar(surface, center_x, rect.y + 175, tank_color)

        # Badge de statut
        from interface.icon_manager import icon_manager
        badge_rect = pygame.Rect(center_x - 130, rect.y + 270, 260, 52)
        if custom_status:
            bg_badge = (45, 48, 56)
            txt_badge_str = custom_status
            txt_badge_color = (200, 205, 215)
            badge_icon = "network/wifi"
        elif is_ready:
            bg_badge = (30, 130, 60)
            txt_badge_str = "PRÊT AU COMBAT !"
            txt_badge_color = (235, 255, 240)
            badge_icon = "network/connected"
        else:
            bg_badge = (140, 90, 20)
            txt_badge_str = "EN ATTENTE..."
            txt_badge_color = (255, 240, 200)
            badge_icon = "hud/timer"

        pygame.draw.rect(surface, bg_badge, badge_rect, border_radius=10)
        pygame.draw.rect(surface, (border_c[0], border_c[1], border_c[2]), badge_rect, width=2, border_radius=10)

        txt_badge = self.font_status.render(txt_badge_str, True, txt_badge_color)
        total_content_w = 26 + 10 + txt_badge.get_width()
        start_x = badge_rect.centerx - total_content_w // 2

        icon_manager.draw_icon(surface, badge_icon, (start_x, badge_rect.centery - 13), size=(26, 26))
        surface.blit(txt_badge, (start_x + 36, badge_rect.centery - txt_badge.get_height() // 2))

    def _draw_tank_avatar(self, surface: pygame.Surface, x: int, y: int, color_name: str) -> None:
        """Dessine un avatar agrandi de tank orienté face à l'adversaire."""
        tank_surf = pygame.Surface((110, 75), pygame.SRCALPHA)
        primary = (220, 60, 50) if color_name == "red" else (46, 204, 113)
        darker = (150, 30, 25) if color_name == "red" else (30, 140, 70)

        # Chenilles
        pygame.draw.rect(tank_surf, (35, 38, 44), (0, 0, 110, 18), border_radius=4)
        pygame.draw.rect(tank_surf, (35, 38, 44), (0, 57, 110, 18), border_radius=4)
        # Châssis
        pygame.draw.rect(tank_surf, primary, (15, 12, 80, 51), border_radius=8)
        # Tourelle
        pygame.draw.circle(tank_surf, darker, (55, 37), 20)
        # Canon orienté
        canon_rect = (55, 33, 48, 9) if color_name == "red" else (7, 33, 48, 9)
        pygame.draw.rect(tank_surf, (28, 30, 35), canon_rect, border_radius=3)

        surface.blit(tank_surf, tank_surf.get_rect(center=(x, y)))

