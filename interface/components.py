"""Composants d'interface utilisateur (UI) réutilisables au style cartoon 2D.

Fournit :
- UIButton : Bouton interactif compatible souris et clavier (survol, clic, focus, ombre, biseau).
- UITextInput : Champ de saisie texte avec curseur clignotant, filtre de caractères et collage.
- UIPanel : Boîte modale et panneau translucide avec bordures arrondies cartoon.
"""

from __future__ import annotations
import time
from typing import Callable, Optional, Tuple
import pygame

# Palette désertique cartoon
COLOR_UI_BG = (22, 25, 32, 230)
COLOR_UI_BORDER = (85, 95, 115)
COLOR_GOLD = (243, 156, 18)
COLOR_GOLD_LIGHT = (254, 211, 48)
COLOR_GOLD_DARK = (185, 90, 8)
COLOR_TEXT_WHITE = (245, 247, 250)
COLOR_TEXT_SHADOW = (15, 18, 22)
COLOR_GREEN = (46, 204, 113)
COLOR_RED = (231, 76, 60)
COLOR_BLUE = (52, 152, 219)


class UIButton:
    """Bouton cartoon interactif avec retours visuels (souris et clavier)."""

    SCHEMES = {
        "amber": {
            "top": (245, 166, 35),
            "bottom": (211, 84, 0),
            "border": (150, 60, 0),
            "shadow": (80, 30, 0),
            "highlight": (255, 220, 120),
        },
        "green": {
            "top": (46, 204, 113),
            "bottom": (39, 174, 96),
            "border": (25, 120, 65),
            "shadow": (15, 60, 35),
            "highlight": (160, 245, 195),
        },
        "red": {
            "top": (231, 76, 60),
            "bottom": (192, 57, 43),
            "border": (130, 35, 25),
            "shadow": (70, 20, 15),
            "highlight": (255, 170, 160),
        },
        "blue": {
            "top": (52, 152, 219),
            "bottom": (41, 128, 185),
            "border": (25, 85, 125),
            "shadow": (15, 45, 70),
            "highlight": (165, 215, 255),
        },
        "dark": {
            "top": (52, 73, 94),
            "bottom": (44, 62, 80),
            "border": (28, 40, 51),
            "shadow": (15, 22, 28),
            "highlight": (120, 145, 170),
        },
    }

    def __init__(
        self,
        rect: pygame.Rect,
        text: str,
        scheme: str = "amber",
        font: Optional[pygame.font.Font] = None,
        font_size: int = 24,
        on_click: Optional[Callable[[], None]] = None,
        sound_hover: Optional[pygame.mixer.Sound] = None,
        sound_click: Optional[pygame.mixer.Sound] = None,
        icon_name: Optional[str] = None,
        icon_size: Tuple[int, int] = (28, 28),
        icon_spacing: int = 12,
        corner_radius: int = 14,
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.original_y = self.rect.y
        self.text = text
        self.scheme = scheme if scheme in self.SCHEMES else "amber"
        self.font = font or pygame.font.SysFont("Segoe UI", font_size, bold=True)
        self.on_click = on_click
        self.sound_hover = sound_hover
        self.sound_click = sound_click
        self.icon_name = icon_name
        self.icon_size = icon_size
        self.icon_spacing = icon_spacing
        self.corner_radius = corner_radius

        self.is_hovered = False
        self.is_selected = False  # Sélection par le clavier
        self.is_pressed = False
        self.enabled = True

        # Animation fluide de décalage vertical (lift)
        self.lift_y = 0.0

    def update(self, dt: float) -> None:
        """Met à jour les animations d'élévation et d'enfoncement."""
        target_lift = 0.0
        if self.enabled:
            if self.is_pressed:
                target_lift = 3.0  # Enfoncement
            elif self.is_hovered or self.is_selected:
                target_lift = -3.0  # Élévation au survol

        # Interpolation fluide
        self.lift_y += (target_lift - self.lift_y) * min(1.0, dt * 15.0)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Gère les entrées souris et retourne True si le bouton a été activé."""
        if not self.enabled:
            return False

        if event.type == pygame.MOUSEMOTION:
            was_hovered = self.is_hovered
            self.is_hovered = self.rect.collidepoint(event.pos)
            if not was_hovered and self.is_hovered and self.sound_hover:
                try:
                    self.sound_hover.play()
                except Exception:
                    pass

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_pressed = True

        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.is_pressed and self.rect.collidepoint(event.pos):
                self.is_pressed = False
                if self.sound_click:
                    try:
                        self.sound_click.play()
                    except Exception:
                        pass
                if self.on_click:
                    self.on_click()
                return True
            self.is_pressed = False

        return False

    def trigger(self) -> None:
        """Déclenche manuellement l'action du bouton (raccourci clavier / Entrée)."""
        if self.enabled:
            if self.sound_click:
                try:
                    self.sound_click.play()
                except Exception:
                    pass
            if self.on_click:
                self.on_click()

    def draw(self, surface: pygame.Surface) -> None:
        """Dessine le bouton avec ombre portée, coins arrondis, biseau cartoon, icône et texte."""
        colors = self.SCHEMES[self.scheme]
        radius = self.corner_radius

        # Détermination de l'état visuel du bouton
        if not self.enabled:
            btn_state = "disabled"
        elif self.is_pressed:
            btn_state = "pressed"
        elif self.is_hovered or self.is_selected:
            btn_state = "hover"
        else:
            btn_state = "normal"

        # Modulation de luminosité selon l'état (réponse tactile au clic et au survol)
        c_top = colors["top"]
        c_bottom = colors["bottom"]
        if self.is_pressed:
            c_top = tuple(max(0, c - 28) for c in c_top)
            c_bottom = tuple(max(0, c - 28) for c in c_bottom)
        elif self.is_hovered or self.is_selected:
            c_top = tuple(min(255, c + 22) for c in c_top)
            c_bottom = tuple(min(255, c + 15) for c in c_bottom)

        # 1. Ombre portée au sol
        shadow_rect = pygame.Rect(self.rect.x, self.original_y + 6, self.rect.w, self.rect.h)
        pygame.draw.rect(surface, colors["shadow"], shadow_rect, border_radius=radius)

        # 2. Rectangle effectif avec décalage lift (animation d'élévation ou enfoncement)
        current_y = int(self.original_y + self.lift_y)
        btn_rect = pygame.Rect(self.rect.x, current_y, self.rect.w, self.rect.h)

        # Bordure cartoon sombre
        border_color = COLOR_GOLD_LIGHT if (self.is_hovered or self.is_selected) else colors["border"]
        border_width = 3 if (self.is_hovered or self.is_selected) else 2

        # Corps du bouton (Dégradé simulé : moitié haute claire, moitié basse foncée)
        pygame.draw.rect(surface, c_bottom, btn_rect, border_radius=radius)
        top_half = pygame.Rect(btn_rect.x, btn_rect.y, btn_rect.w, btn_rect.h // 2)
        pygame.draw.rect(surface, c_top, top_half, border_top_left_radius=radius, border_top_right_radius=radius)

        # Biseau supérieur clair (Glossy highlight)
        highlight_rect = pygame.Rect(btn_rect.x + 4, btn_rect.y + 2, btn_rect.w - 8, 3)
        pygame.draw.rect(surface, colors["highlight"], highlight_rect, border_radius=2)

        # Lueur de sélection (Focus clavier ou survol souris)
        if self.is_hovered or self.is_selected:
            pygame.draw.rect(surface, COLOR_GOLD_LIGHT, btn_rect.inflate(4, 4), width=2, border_radius=radius + 2)

        # Contour principal
        pygame.draw.rect(surface, border_color, btn_rect, width=border_width, border_radius=radius)

        # 3. Rendu de l'Icône et du Texte
        txt_surf = self.font.render(self.text, True, COLOR_TEXT_WHITE if self.enabled else (140, 145, 155))
        shadow_surf = self.font.render(self.text, True, COLOR_TEXT_SHADOW)

        icon_surf = None
        if self.icon_name:
            try:
                from interface.icon_manager import icon_manager
                icon_surf = icon_manager.get_icon(self.icon_name, size=self.icon_size, state=btn_state)
            except Exception:
                icon_surf = None

        if icon_surf and self.text:
            icon_w, icon_h = icon_surf.get_size()
            txt_w, txt_h = txt_surf.get_size()
            total_w = icon_w + self.icon_spacing + txt_w
            start_x = btn_rect.centerx - total_w // 2

            icon_rect = icon_surf.get_rect(midleft=(start_x, btn_rect.centery))
            txt_rect = txt_surf.get_rect(midleft=(start_x + icon_w + self.icon_spacing, btn_rect.centery))

            surface.blit(icon_surf, icon_rect)
            surface.blit(shadow_surf, (txt_rect.x + 1, txt_rect.y + 2))
            surface.blit(txt_surf, txt_rect)
        elif icon_surf and not self.text:
            icon_rect = icon_surf.get_rect(center=btn_rect.center)
            surface.blit(icon_surf, icon_rect)
        else:
            txt_rect = txt_surf.get_rect(center=btn_rect.center)
            surface.blit(shadow_surf, (txt_rect.x + 1, txt_rect.y + 2))
            surface.blit(txt_surf, txt_rect)


class UITextInput:
    """Champ de saisie interactif pour l'adresse IP et le port."""

    def __init__(
        self,
        rect: pygame.Rect,
        initial_text: str = "",
        placeholder: str = "127.0.0.1",
        max_length: int = 21,
        allowed_chars: str = "0123456789.:",
        font: Optional[pygame.font.Font] = None,
    ) -> None:
        self.rect = pygame.Rect(rect)
        self.text = initial_text
        self.placeholder = placeholder
        self.max_length = max_length
        self.allowed_chars = allowed_chars
        self.font = font or pygame.font.SysFont("Segoe UI", 24, bold=True)

        self.is_focused = True
        self.cursor_visible = True
        self.cursor_timer = 0.0

    def update(self, dt: float) -> None:
        """Fait clignoter le curseur textuel."""
        self.cursor_timer += dt
        if self.cursor_timer >= 0.45:
            self.cursor_timer = 0.0
            self.cursor_visible = not self.cursor_visible

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Traite les touches clavier et retourne True en cas d'appui sur Entrée."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.is_focused = self.rect.collidepoint(event.pos)
            return False

        if not self.is_focused:
            return False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.is_focused = False
            elif event.key == pygame.K_v and (event.mod & pygame.KMOD_CTRL):
                # Collage depuis le presse-papier si pygame.scrap est disponible
                try:
                    if pygame.scrap.get_init():
                        clip = pygame.scrap.get(pygame.SCRAP_TEXT)
                        if clip:
                            clean_text = "".join(c for c in clip.decode("utf-8", "ignore") if c in self.allowed_chars)
                            self.text = (self.text + clean_text)[:self.max_length]
                except Exception:
                    pass
            else:
                # Ajout de caractères autorisés
                if event.unicode and event.unicode in self.allowed_chars:
                    if len(self.text) < self.max_length:
                        self.text += event.unicode
        return False

    def draw(self, surface: pygame.Surface) -> None:
        """Affiche le champ de saisie avec bordure en surbrillance."""
        radius = 8
        # Fond sombre
        pygame.draw.rect(surface, (18, 22, 28), self.rect, border_radius=radius)

        # Bordure active ou neutre
        border_color = COLOR_GOLD_LIGHT if self.is_focused else COLOR_UI_BORDER
        border_width = 3 if self.is_focused else 2
        pygame.draw.rect(surface, border_color, self.rect, width=border_width, border_radius=radius)

        # Texte ou placeholder
        display_text = self.text if self.text else self.placeholder
        text_color = COLOR_TEXT_WHITE if self.text else (120, 130, 145)

        txt_surf = self.font.render(display_text, True, text_color)
        txt_rect = txt_surf.get_rect(midleft=(self.rect.x + 16, self.rect.centery))
        surface.blit(txt_surf, txt_rect)

        # Curseur vertical clignotant
        if self.is_focused and self.cursor_visible:
            cursor_x = txt_rect.right + 2 if self.text else self.rect.x + 16
            cursor_top = self.rect.centery - 12
            cursor_bottom = self.rect.centery + 12
            pygame.draw.line(surface, COLOR_GOLD_LIGHT, (cursor_x, cursor_top), (cursor_x, cursor_bottom), width=2)


def draw_cartoon_panel(
    surface: pygame.Surface,
    rect: pygame.Rect,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    border_color: Tuple[int, int, int] = COLOR_UI_BORDER,
    bg_color: Tuple[int, int, int, int] = COLOR_UI_BG,
    border_radius: int = 16,
) -> None:
    """Dessine un panneau de fenêtre cartoon translucide avec ombre et en-tête."""
    # 1. Ombre portée externe
    shadow_rect = pygame.Rect(rect.x + 4, rect.y + 6, rect.w, rect.h)
    shadow_surf = pygame.Surface((shadow_rect.w, shadow_rect.h), pygame.SRCALPHA)
    shadow_surf.fill((0, 0, 0, 110))
    surface.blit(shadow_surf, (shadow_rect.x, shadow_rect.y))

    # 2. Panneau central
    panel_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    panel_surf.fill(bg_color)
    pygame.draw.rect(panel_surf, border_color, panel_surf.get_rect(), width=3, border_radius=border_radius)
    surface.blit(panel_surf, (rect.x, rect.y))

    # 3. Ligne de biseau supérieure
    highlight_rect = pygame.Rect(rect.x + 6, rect.y + 3, rect.w - 12, 2)
    pygame.draw.rect(surface, (140, 160, 190, 80), highlight_rect, border_radius=1)

    # 4. Titre éventuel
    if title:
        font_title = pygame.font.SysFont("Segoe UI", 30, bold=True)
        txt_title = font_title.render(title, True, COLOR_GOLD_LIGHT)
        shadow_title = font_title.render(title, True, COLOR_TEXT_SHADOW)
        title_rect = txt_title.get_rect(center=(rect.centerx, rect.y + 36))
        surface.blit(shadow_title, (title_rect.x + 1, title_rect.y + 2))
        surface.blit(txt_title, title_rect)

        # Ligne de séparation sous le titre
        pygame.draw.line(
            surface,
            (border_color[0], border_color[1], border_color[2], 120),
            (rect.x + 40, rect.y + 64),
            (rect.right - 40, rect.y + 64),
            2,
        )

    if subtitle:
        font_sub = pygame.font.SysFont("Segoe UI", 16)
        txt_sub = font_sub.render(subtitle, True, (190, 200, 215))
        sub_rect = txt_sub.get_rect(center=(rect.centerx, rect.y + 80))
        surface.blit(txt_sub, sub_rect)

