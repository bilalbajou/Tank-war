"""Écrans secondaires pour Tank War : Hébergement, Connexion, Pause et Fin de Partie.

Fournit :
- HostScreen : Lance l'écoute réseau TCP, affiche l'IP LAN et attend le Joueur 2 sans blocage.
- JoinScreen : Champ de saisie d'IP, tentative asynchrone non-bloquante et diagnostics d'erreurs clairs.
- PauseOverlay : Menu de pause interactif (Reprendre, Recommencer, Menu).
- GameOverScreen : Proclamation du vainqueur, score final et options Rejouer / Menu.
"""

from __future__ import annotations
import math
import threading
import time
from typing import Callable, Optional
import pygame

from settings import SCREEN_WIDTH, SCREEN_HEIGHT
from interface.components import (
    UIButton,
    UITextInput,
    COLOR_GOLD_LIGHT,
    COLOR_GREEN,
    COLOR_RED,
    COLOR_BLUE,
    COLOR_TEXT_SHADOW,
    COLOR_TEXT_WHITE,
    draw_cartoon_panel,
)
from network.server import NetworkServer, get_local_ip
from network.client import NetworkClient
from network.discovery import LANDiscoveryListener, DiscoveredServer


# =============================================================================
# 1. ÉCRAN D'HÉBERGEMENT (PC 1 - SERVEUR HÔTE)
# =============================================================================
class HostScreen:
    """Écran d'attente lors de l'hébergement d'une partie LAN."""

    def __init__(
        self,
        server: NetworkServer,
        on_client_joined: Callable[[], None],
        on_cancel: Callable[[], None],
    ) -> None:
        self.server = server
        self.on_client_joined = on_client_joined
        self.on_cancel = on_cancel

        self.font_title = pygame.font.SysFont("Segoe UI", 36, bold=True)
        self.font_ip = pygame.font.SysFont("Segoe UI", 36, bold=True)
        self.font_info = pygame.font.SysFont("Segoe UI", 20)
        self.font_status = pygame.font.SysFont("Segoe UI", 22, bold=True)

        btn_w = 260
        btn_h = 56
        self.btn_cancel = UIButton(
            pygame.Rect((SCREEN_WIDTH - btn_w) // 2, 680, btn_w, btn_h),
            text="ANNULER",
            scheme="red",
            font_size=20,
            icon_name="network/back",
            icon_size=(24, 24),
            on_click=self.on_cancel,
        )

        self.anim_time = 0.0

    def handle_event(self, event: pygame.event.Event) -> None:
        """Gère les entrées clavier (Échap pour annuler) et souris."""
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.on_cancel()
            return
        self.btn_cancel.handle_event(event)

    def update(self, dt: float) -> None:
        """Surveille l'arrivée du Joueur 2 sans bloquer la boucle de rendu."""
        self.anim_time += dt
        self.btn_cancel.update(dt)

        # Dès que le client est connecté, bascule vers le Lobby
        if self.server.has_client_connected():
            self.on_client_joined()

    def draw(self, surface: pygame.Surface) -> None:
        """Affiche les instructions d'hébergement et l'IP LAN à communiquer."""
        # Voile d'ambiance désertique sombre
        surface.fill((22, 20, 24))

        panel_w = 760
        panel_h = 600
        panel_rect = pygame.Rect((SCREEN_WIDTH - panel_w) // 2, 140, panel_w, panel_h)
        draw_cartoon_panel(
            surface,
            panel_rect,
            title="📡  HÉBERGER UNE PARTIE LAN",
            subtitle="Le PC 1 fait autorité sur la physique et l'arbitrage du match",
            border_color=(211, 84, 0),
            border_radius=20,
        )

        center_x = SCREEN_WIDTH // 2

        # 1. Étiquette IP Locale
        lbl_info = self.font_info.render("Communiquez cette adresse IP au Joueur 2 :", True, (210, 215, 225))
        surface.blit(lbl_info, lbl_info.get_rect(center=(center_x, 270)))

        # 2. Boîte en valeur de l'adresse IP (largeur dynamique et centrage parfait)
        from interface.icon_manager import icon_manager
        ip_str = f"{self.server.local_ip}:{self.server.port}"
        txt_ip = self.font_ip.render(ip_str, True, COLOR_GOLD_LIGHT)

        icon_w, icon_h = 32, 32
        spacing = 16
        padding_x = 28
        content_w = icon_w + spacing + txt_ip.get_width()
        box_w = max(440, content_w + padding_x * 2)
        box_h = 68
        ip_box = pygame.Rect(center_x - box_w // 2, 308, box_w, box_h)

        pygame.draw.rect(surface, (15, 17, 22), ip_box, border_radius=12)
        pygame.draw.rect(surface, COLOR_GOLD_LIGHT, ip_box, width=3, border_radius=12)

        # Icône Wi-Fi et adresse IP groupées et centrées ensemble dans le cadre
        start_x = ip_box.centerx - content_w // 2
        icon_manager.draw_icon(surface, "network/wifi", (start_x, ip_box.centery - icon_h // 2), size=(icon_w, icon_h))
        surface.blit(txt_ip, (start_x + icon_w + spacing, ip_box.centery - txt_ip.get_height() // 2))

        # 3. Radar / Point clignotant de recherche
        pulse_alpha = int(128 + 127 * math.sin(self.anim_time * 4.0))
        icon_manager.draw_icon(surface, "menu/host", (center_x - 195, 412), size=(28, 28))

        stat_text = "En attente de connexion du Joueur 2..."
        txt_status = self.font_status.render(stat_text, True, (245, 215, 120))
        surface.blit(txt_status, (center_x - 155, 416))

        # 4. Badge auto-détection LAN (Zero-Config)
        badge_text = "🟢 Diffusion UDP active : Détectable automatiquement sur le Wi-Fi local"
        txt_badge = self.font_info.render(badge_text, True, (46, 204, 113))
        surface.blit(txt_badge, txt_badge.get_rect(center=(center_x, 460)))

        # 5. Conseils réseau
        hint_text = "Assurez-vous que les 2 ordinateurs sont connectés au même réseau Wi-Fi local."
        txt_hint = self.font_info.render(hint_text, True, (160, 165, 175))
        surface.blit(txt_hint, txt_hint.get_rect(center=(center_x, 505)))

        # Bouton d'annulation
        self.btn_cancel.draw(surface)


# =============================================================================
# 2. ÉCRAN DE RECONNEXION / CLIENT (PC 2)
# =============================================================================
class JoinScreen:
    """Écran de connexion au serveur avec Détection Automatique LAN (Zero-Config) et saisie manuelle."""

    STATE_IDLE = "idle"
    STATE_CONNECTING = "connecting"
    STATE_SUCCESS = "success"
    STATE_ERROR = "error"

    def __init__(
        self,
        on_connected: Callable[[NetworkClient], None],
        on_cancel: Callable[[], None],
    ) -> None:
        self.on_connected = on_connected
        self.on_cancel = on_cancel

        self.client: Optional[NetworkClient] = None
        self.connection_state = self.STATE_IDLE
        self.error_message = ""
        self._connect_thread: Optional[threading.Thread] = None

        # Module de découverte automatique en tâche de fond (Zero-Config)
        self.discovery_listener: Optional[LANDiscoveryListener] = LANDiscoveryListener()
        self.discovery_listener.start()
        self.discovered_servers: list[DiscoveredServer] = []
        self.server_buttons: dict[str, UIButton] = {}

        self.font_info = pygame.font.SysFont("Segoe UI", 18)
        self.font_status = pygame.font.SysFont("Segoe UI", 20, bold=True)
        self.font_section = pygame.font.SysFont("Segoe UI", 16, bold=True)
        self.font_server_name = pygame.font.SysFont("Segoe UI", 18, bold=True)
        self.font_server_sub = pygame.font.SysFont("Segoe UI", 14)

        center_x = SCREEN_WIDTH // 2

        # Champ de saisie pour l'IP hôte (avec port optionnel)
        self.input_ip = UITextInput(
            pygame.Rect(center_x - 180, 480, 360, 50),
            initial_text="127.0.0.1",
            placeholder="192.168.1.XX",
            max_length=21,
            allowed_chars="0123456789.:",
        )

        # Boutons d'action
        btn_w = 220
        btn_h = 54
        self.btn_connect = UIButton(
            pygame.Rect(center_x - 240, 600, btn_w, btn_h),
            text="SE CONNECTER",
            scheme="green",
            font_size=20,
            icon_name="network/connect",
            icon_size=(24, 24),
            on_click=self.start_connection,
        )
        self.btn_cancel = UIButton(
            pygame.Rect(center_x + 20, 600, btn_w, btn_h),
            text="RETOUR",
            scheme="red",
            font_size=20,
            icon_name="network/back",
            icon_size=(24, 24),
            on_click=self.cancel,
        )

        self.anim_time = 0.0

    def connect_to_server(self, host: str, port: int = 4242) -> None:
        """Connecte directement à un serveur détecté automatiquement en un seul clic."""
        self.input_ip.text = f"{host}:{port}"
        self.start_connection(host=host, port=port)

    def start_connection(self, host: Optional[str] = None, port: Optional[int] = None) -> None:
        """Lance la tentative de connexion réseau dans un thread séparé (zéro gel d'écran)."""
        if self.connection_state == self.STATE_CONNECTING:
            return

        if host is None:
            target_ip_str = self.input_ip.text.strip()
            if not target_ip_str:
                target_ip_str = self.input_ip.placeholder

            # Découpage hôte et port éventuel (ex: "192.168.1.45:4242")
            use_port = 4242
            if ":" in target_ip_str:
                parts = target_ip_str.split(":", 1)
                use_host = parts[0]
                try:
                    use_port = int(parts[1])
                except ValueError:
                    use_port = 4242
            else:
                use_host = target_ip_str
        else:
            use_host = host
            use_port = port or 4242

        self.connection_state = self.STATE_CONNECTING
        self.error_message = ""

        # Instanciation du client
        self.client = NetworkClient(host_ip=use_host, port=use_port)

        # Thread de connexion asynchrone
        self._connect_thread = threading.Thread(
            target=self._async_connect_task,
            args=(self.client,),
            daemon=True,
        )
        self._connect_thread.start()

    def _async_connect_task(self, client: NetworkClient) -> None:
        """Exécuté dans un thread séparé avec timeout de 3.5s."""
        success = client.connect(timeout=3.5)
        if success and client.is_connected:
            self.connection_state = self.STATE_SUCCESS
        else:
            self.connection_state = self.STATE_ERROR
            self.error_message = "Impossible de joindre l'hôte (Vérifiez l'adresse IP et le Wi-Fi)"

    def cancel(self) -> None:
        """Annule la tentative, arrête l'écoute et quitte l'écran."""
        if self.discovery_listener:
            self.discovery_listener.stop()
            self.discovery_listener = None
        if self.client and self.client.is_connected:
            self.client.disconnect()
        self.client = None
        self.connection_state = self.STATE_IDLE
        self.on_cancel()

    def handle_event(self, event: pygame.event.Event) -> None:
        """Gère les entrées de formulaire et les clics sur serveurs détectés."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.cancel()
                return

        # Clics sur les boutons des serveurs découverts
        for btn in list(self.server_buttons.values()):
            btn.handle_event(event)

        enter_pressed = self.input_ip.handle_event(event)
        if enter_pressed:
            self.start_connection()

        self.btn_connect.handle_event(event)
        self.btn_cancel.handle_event(event)

    def update(self, dt: float) -> None:
        """Met à jour les animations, synchronise les serveurs découverts et détecte la connexion."""
        self.anim_time += dt
        self.input_ip.update(dt)
        self.btn_connect.update(dt)
        self.btn_cancel.update(dt)

        # Actualisation de la liste des serveurs découverts depuis l'écouteur UDP
        if self.discovery_listener:
            self.discovered_servers = self.discovery_listener.get_servers()

        current_keys = set()
        box_servers_x = (SCREEN_WIDTH - 840) // 2 + 40
        box_servers_w = 840 - 80

        for idx, s in enumerate(self.discovered_servers[:2]):
            key = s.address_str
            current_keys.add(key)
            card_y = 220 + idx * 80
            btn_w, btn_h = 145, 42
            btn_x = box_servers_x + box_servers_w - btn_w - 20
            btn_y = card_y + 15

            if key not in self.server_buttons:
                btn = UIButton(
                    pygame.Rect(btn_x, btn_y, btn_w, btn_h),
                    text="REJOINDRE",
                    scheme="green",
                    font_size=16,
                    icon_name="network/connect",
                    icon_size=(20, 20),
                    on_click=lambda h=s.host_ip, p=s.port: self.connect_to_server(h, p),
                )
                self.server_buttons[key] = btn
            else:
                self.server_buttons[key].rect.topleft = (btn_x, btn_y)
            self.server_buttons[key].update(dt)

        # Nettoyer les boutons des serveurs expirés
        for k in list(self.server_buttons.keys()):
            if k not in current_keys:
                del self.server_buttons[k]

        if self.connection_state == self.STATE_SUCCESS and self.client:
            if self.discovery_listener:
                self.discovery_listener.stop()
                self.discovery_listener = None
            self.on_connected(self.client)

    def draw(self, surface: pygame.Surface) -> None:
        """Dessine l'écran de connexion avec les parties détectées et la saisie manuelle."""
        surface.fill((22, 20, 24))

        panel_w = 840
        panel_h = 690
        panel_rect = pygame.Rect((SCREEN_WIDTH - panel_w) // 2, 95, panel_w, panel_h)
        draw_cartoon_panel(
            surface,
            panel_rect,
            title="🔗  REJOINDRE UNE PARTIE LAN",
            subtitle="Détection automatique sur le Wi-Fi (Zero-Config) ou connexion manuelle",
            border_color=(52, 152, 219),
            border_radius=20,
        )

        center_x = SCREEN_WIDTH // 2
        from interface.icon_manager import icon_manager

        # ---------------------------------------------------------------------
        # 1. SECTION AUTO-DÉTECTION (PARTIES SUR LE RÉSEAU LOCAL)
        # ---------------------------------------------------------------------
        lbl_sec1 = self.font_section.render("📡 PARTIES DÉTECTÉES SUR LE RÉSEAU LOCAL (SCAN AUTOMATIQUE) :", True, (241, 196, 15))
        surface.blit(lbl_sec1, (panel_rect.x + 40, 185))

        box_servers = pygame.Rect(panel_rect.x + 40, 212, panel_w - 80, 172)
        pygame.draw.rect(surface, (15, 17, 23), box_servers, border_radius=12)
        pygame.draw.rect(surface, (40, 48, 65), box_servers, width=2, border_radius=12)

        if self.discovered_servers:
            for idx, s in enumerate(self.discovered_servers[:2]):
                card_y = box_servers.y + 8 + idx * 80
                card_rect = pygame.Rect(box_servers.x + 10, card_y, box_servers.w - 20, 72)

                # Fond de la carte de serveur
                pygame.draw.rect(surface, (24, 30, 42), card_rect, border_radius=8)
                pygame.draw.rect(surface, (52, 152, 219), card_rect, width=2, border_radius=8)

                # Icône de char / serveur
                icon_manager.draw_icon(surface, "network/wifi", (card_rect.x + 16, card_rect.centery - 16), size=(32, 32))

                # Nom et informations de la partie
                txt_name = self.font_server_name.render(s.server_name, True, COLOR_GOLD_LIGHT)
                surface.blit(txt_name, (card_rect.x + 60, card_rect.y + 12))

                sub_info = f"IP : {s.address_str}   |   Joueurs : {s.player_count}/{s.max_players}   |   Statut : {s.status.upper()}"
                txt_sub = self.font_server_sub.render(sub_info, True, (170, 185, 205))
                surface.blit(txt_sub, (card_rect.x + 60, card_rect.y + 42))

                # Bouton Rejoindre dédié
                if s.address_str in self.server_buttons:
                    self.server_buttons[s.address_str].draw(surface)
        else:
            # Indicateur radar de recherche
            radar_r = 16 + int(math.sin(self.anim_time * 4.0) * 4)
            pygame.draw.circle(surface, (52, 152, 219), (center_x, box_servers.centery - 20), radar_r, width=2)
            icon_manager.draw_icon(surface, "network/wifi", (center_x - 12, box_servers.centery - 32), size=(24, 24))

            txt_scan = self.font_info.render("Recherche automatique d'hôtes sur votre réseau Wi-Fi local...", True, (215, 225, 235))
            surface.blit(txt_scan, txt_scan.get_rect(center=(center_x, box_servers.centery + 16)))

            txt_hint = self.font_server_sub.render("Dès que le PC 1 clique sur 'Héberger une partie', elle apparaîtra ici en 1 clic.", True, (140, 150, 165))
            surface.blit(txt_hint, txt_hint.get_rect(center=(center_x, box_servers.centery + 44)))

        # ---------------------------------------------------------------------
        # 2. SECTION CONNEXION MANUELLE
        # ---------------------------------------------------------------------
        lbl_sec2 = self.font_section.render("⌨️ OU CONNEXION MANUELLE PAR IP :", True, (200, 210, 225))
        surface.blit(lbl_sec2, (panel_rect.x + 40, 412))

        lbl_ip_prompt = self.font_server_sub.render("Entrez l'adresse IP de l'hôte (avec port optionnel) :", True, (160, 170, 185))
        surface.blit(lbl_ip_prompt, (panel_rect.x + 40, 442))

        # Champ de texte avec icône d'adresse IP
        icon_manager.draw_icon(surface, "network/ip", (self.input_ip.rect.x - 44, self.input_ip.rect.centery - 16), size=(32, 32))
        self.input_ip.draw(surface)

        # ---------------------------------------------------------------------
        # 3. MESSAGES DE STATUT / ERREUR DYNAMIQUES
        # ---------------------------------------------------------------------
        if self.connection_state == self.STATE_CONNECTING:
            spinner_offset = int(math.sin(self.anim_time * 6.0) * 8.0)
            status_text = "Connexion en cours à l'hôte..."
            txt_st = self.font_status.render(status_text, True, (241, 196, 15))
            st_rect = txt_st.get_rect(center=(center_x, 552))
            icon_manager.draw_icon(surface, "network/wifi", (st_rect.left - 34, st_rect.centery - 12), size=(24, 24))
            surface.blit(txt_st, st_rect)
            pygame.draw.circle(surface, (241, 196, 15), (st_rect.right + 16, st_rect.centery + spinner_offset), 5)

        elif self.connection_state == self.STATE_ERROR:
            txt_err = self.font_status.render(self.error_message, True, COLOR_RED)
            st_rect = txt_err.get_rect(center=(center_x + 16, 552))
            icon_manager.draw_icon(surface, "network/disconnected", (st_rect.left - 32, st_rect.centery - 12), size=(24, 24))
            surface.blit(txt_err, st_rect)

        elif self.connection_state == self.STATE_SUCCESS:
            txt_ok = self.font_status.render("Connecté avec succès !", True, COLOR_GREEN)
            st_rect = txt_ok.get_rect(center=(center_x + 16, 552))
            icon_manager.draw_icon(surface, "network/connected", (st_rect.left - 32, st_rect.centery - 12), size=(24, 24))
            surface.blit(txt_ok, st_rect)

        # Boutons d'action
        self.btn_connect.draw(surface)
        self.btn_cancel.draw(surface)


# =============================================================================
# 3. OVERLAY DE PAUSE
# =============================================================================
class PauseOverlay:
    """Menu interactif de mise en pause du combat."""

    def __init__(
        self,
        on_resume: Callable[[], None],
        on_restart: Callable[[], None],
        on_menu: Callable[[], None],
    ) -> None:
        self.on_resume = on_resume
        self.on_restart = on_restart
        self.on_menu = on_menu

        btn_w = 340
        btn_h = 56
        center_x = (SCREEN_WIDTH - btn_w) // 2
        start_y = 350
        gap = 72

        self.buttons = [
            UIButton(pygame.Rect(center_x, start_y, btn_w, btn_h), "REPRENDRE", scheme="green", icon_name="pause/resume", icon_size=(26, 26), on_click=self.on_resume),
            UIButton(pygame.Rect(center_x, start_y + gap, btn_w, btn_h), "RECOMMENCER", scheme="amber", icon_name="pause/restart", icon_size=(26, 26), on_click=self.on_restart),
            UIButton(pygame.Rect(center_x, start_y + gap * 2, btn_w, btn_h), "RETOUR AU MENU", scheme="red", icon_name="pause/menu", icon_size=(26, 26), on_click=self.on_menu),
        ]
        self.selected_index = 0
        self.buttons[0].is_selected = True

    def handle_event(self, event: pygame.event.Event) -> None:
        """Gère la navigation au clavier et à la souris."""
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_p):
                self.on_resume()
                return
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.buttons[self.selected_index].is_selected = False
                self.selected_index = (self.selected_index + 1) % len(self.buttons)
                self.buttons[self.selected_index].is_selected = True
            elif event.key in (pygame.K_UP, pygame.K_z, pygame.K_w):
                self.buttons[self.selected_index].is_selected = False
                self.selected_index = (self.selected_index - 1) % len(self.buttons)
                self.buttons[self.selected_index].is_selected = True
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
                self.buttons[self.selected_index].trigger()
                return

        for i, btn in enumerate(self.buttons):
            if event.type == pygame.MOUSEMOTION and btn.rect.collidepoint(event.pos):
                self.buttons[self.selected_index].is_selected = False
                self.selected_index = i
                btn.is_selected = True
            btn.handle_event(event)

    def update(self, dt: float) -> None:
        """Anime les boutons."""
        for btn in self.buttons:
            btn.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        """Affiche le voile assombrissant et le panneau de pause."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 12, 16, 210))
        surface.blit(overlay, (0, 0))

        box_w = 480
        box_h = 420
        box_rect = pygame.Rect((SCREEN_WIDTH - box_w) // 2, 220, box_w, box_h)
        draw_cartoon_panel(
            surface,
            box_rect,
            title="PAUSE",
            subtitle="Partie temporairement suspendue",
            border_color=(243, 156, 18),
            border_radius=18,
        )

        from interface.icon_manager import icon_manager
        icon_manager.draw_icon(surface, "hud/pause", (box_rect.x + 36, box_rect.y + 18), size=(32, 32))

        for btn in self.buttons:
            btn.draw(surface)


# =============================================================================
# 4. ÉCRAN DE FIN DE PARTIE (GAME OVER / VICTOIRE / DÉFAITE)
# =============================================================================
class GameOverOverlay:
    """Écran complet de proclamation du résultat final avec boutons Rejouer et Menu."""

    def __init__(
        self,
        on_replay: Callable[[], None],
        on_menu: Callable[[], None],
    ) -> None:
        self.on_replay = on_replay
        self.on_menu = on_menu

        self.font_title = pygame.font.SysFont("Segoe UI", 48, bold=True)
        self.font_sub = pygame.font.SysFont("Segoe UI", 24, bold=True)
        self.font_score = pygame.font.SysFont("Segoe UI", 36, bold=True)

        btn_w = 260
        btn_h = 58
        center_x = SCREEN_WIDTH // 2

        self.btn_replay = UIButton(
            pygame.Rect(center_x - 280, 560, btn_w, btn_h),
            text="REJOUER (R)",
            scheme="green",
            font_size=20,
            icon_name="results/replay",
            icon_size=(24, 24),
            on_click=self.on_replay,
        )
        self.btn_menu = UIButton(
            pygame.Rect(center_x + 20, 560, btn_w, btn_h),
            text="MENU PRINCIPAL",
            scheme="amber",
            font_size=20,
            icon_name="results/home",
            icon_size=(24, 24),
            on_click=self.on_menu,
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        """Gère les raccourcis R (rejouer) et Échap (menu)."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.on_replay()
                return
            elif event.key == pygame.K_ESCAPE:
                self.on_menu()
                return

        self.btn_replay.handle_event(event)
        self.btn_menu.handle_event(event)

    def update(self, dt: float) -> None:
        """Met à jour les animations."""
        self.btn_replay.update(dt)
        self.btn_menu.update(dt)

    def draw(
        self,
        surface: pygame.Surface,
        winner_id: Optional[int],
        p1_score: int,
        p2_score: int,
        win_reason: str,
        local_player_id: Optional[int] = None,
    ) -> None:
        """Affiche le panneau proclamant la victoire ou la défaite."""
        # Voile d'assombrissement
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((12, 14, 18, 220))
        surface.blit(overlay, (0, 0))

        box_w = 680
        box_h = 460
        box_rect = pygame.Rect((SCREEN_WIDTH - box_w) // 2, 200, box_w, box_h)
        draw_cartoon_panel(
            surface,
            box_rect,
            border_color=(243, 156, 18) if winner_id else (160, 170, 180),
            border_radius=20,
        )

        center_x = SCREEN_WIDTH // 2

        # 1. Titre adapté au joueur (Victoire / Défaite personnalisée si en réseau)
        is_victory = False
        is_defeat = False
        if local_player_id is not None:
            if winner_id == local_player_id:
                title_str = "VICTOIRE !"
                title_color = COLOR_GREEN
                is_victory = True
            elif winner_id is not None:
                title_str = "DÉFAITE..."
                title_color = COLOR_RED
                is_defeat = True
            else:
                title_str = "MATCH NUL !"
                title_color = COLOR_GOLD_LIGHT
        else:
            if winner_id == 1:
                title_str = "VICTOIRE DU JOUEUR 1 (ROUGE) !"
                title_color = (231, 76, 60)
                is_victory = True
            elif winner_id == 2:
                title_str = "VICTOIRE DU JOUEUR 2 (VERT) !"
                title_color = (46, 204, 113)
                is_victory = True
            else:
                title_str = "MATCH NUL !"
                title_color = COLOR_GOLD_LIGHT

        from interface.icon_manager import icon_manager
        txt_title = self.font_title.render(title_str, True, title_color)
        title_rect = txt_title.get_rect(center=(center_x, box_rect.y + 70))

        if is_victory:
            icon_manager.draw_icon(surface, "results/victory", (title_rect.left - 52, title_rect.centery - 20), size=(40, 40))
        elif is_defeat:
            icon_manager.draw_icon(surface, "results/defeat", (title_rect.left - 52, title_rect.centery - 20), size=(40, 40))

        surface.blit(txt_title, title_rect)

        # 2. Motif / raison
        txt_reason = self.font_sub.render(win_reason, True, (230, 235, 245))
        surface.blit(txt_reason, txt_reason.get_rect(center=(center_x, box_rect.y + 140)))

        # 3. Score Final
        score_text = f"SCORE FINAL :  {p1_score}  -  {p2_score}"
        txt_score = self.font_score.render(score_text, True, COLOR_GOLD_LIGHT)
        surface.blit(txt_score, txt_score.get_rect(center=(center_x, box_rect.y + 210)))

        # Boutons
        self.btn_replay.draw(surface)
        self.btn_menu.draw(surface)

