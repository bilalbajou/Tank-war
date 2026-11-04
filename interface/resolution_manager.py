"""Gestionnaire de résolution logique et d'affichage adaptatif (ResolutionManager) pour Tank War.

Garantit une expérience visuelle et interactive parfaite sur toutes les résolutions d'écran :
- 1280 × 720 (HD)
- 1366 × 768 (WXGA standard portables)
- 1440 × 900 (16:10 WXGA+)
- 1600 × 900 (Résolution logique de référence 16:9)
- 1920 × 1080 (Full HD 1080p)
- 2560 × 1440 (2K QHD)
- Et toute résolution personnalisée en mode fenêtré ou plein écran.

Mécanisme :
1. Résolution logique native de référence fixée à 1600 × 900.
2. Rendu de l'arène, des menus, des chars et du HUD sur une surface virtuelle Pygame.
3. Mise à l'échelle proportionnelle haute fidélité (smoothscale) avec letterboxing / pillarboxing.
4. Translation instantanée des coordonnées de souris depuis l'espace fenêtre vers l'espace logique.
5. Gestion des modes fenêtré, redimensionnable et plein écran (F11 / Alt+Entrée).
6. Respect strict de la physique et des vitesses de déplacement (aucune distorsion).
"""

from __future__ import annotations
from typing import List, Optional, Tuple
import pygame

# =============================================================================
# CONSTANTES DE RÉSOLUTION LOGIQUE ET PRÉSÉLECTIONS
# =============================================================================
LOGICAL_WIDTH: int = 1600
LOGICAL_HEIGHT: int = 900
LOGICAL_SIZE: Tuple[int, int] = (LOGICAL_WIDTH, LOGICAL_HEIGHT)
LOGICAL_ASPECT_RATIO: float = LOGICAL_WIDTH / LOGICAL_HEIGHT  # 16:9 (1.7777...)

SUPPORTED_PRESETS: List[Tuple[int, int]] = [
    (1280, 720),   # 16:9 (HD)
    (1366, 768),   # ~16:9 (Portable)
    (1440, 900),   # 16:10 (Format large)
    (1600, 900),   # 16:9 (Référence native)
    (1920, 1080),  # 16:9 (Full HD)
    (2560, 1440),  # 16:9 (2K QHD)
]


class ResolutionManager:
    """Orchestrateur de résolution logique, de mise à l'échelle et de conversion de coordonnées."""

    _instance: Optional[ResolutionManager] = None

    def __new__(cls) -> ResolutionManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return

        self._initialized = True

        # Résolution logique (espace de coordonnées fixe du jeu)
        self.logical_width: int = LOGICAL_WIDTH
        self.logical_height: int = LOGICAL_HEIGHT

        # Résolution réelle de la fenêtre d'affichage
        self.real_width: int = LOGICAL_WIDTH
        self.real_height: int = LOGICAL_HEIGHT

        # Mode plein écran et mémoire de taille fenêtrée
        self.is_fullscreen: bool = False
        self.last_windowed_size: Tuple[int, int] = (LOGICAL_WIDTH, LOGICAL_HEIGHT)

        # Paramètres calculés du viewport
        self.scale_factor: float = 1.0
        self.scaled_width: int = LOGICAL_WIDTH
        self.scaled_height: int = LOGICAL_HEIGHT
        self.offset_x: int = 0
        self.offset_y: int = 0
        self.viewport_rect: pygame.Rect = pygame.Rect(0, 0, LOGICAL_WIDTH, LOGICAL_HEIGHT)

        # Surfaces Pygame
        self.virtual_surface: Optional[pygame.Surface] = None
        self.window_surface: Optional[pygame.Surface] = None

        # Qualité de filtrage
        self.use_smoothscale: bool = True

        # Initialisation par défaut de la surface virtuelle
        self._create_virtual_surface()

    def _create_virtual_surface(self) -> None:
        """Instancie la surface virtuelle de dessin à la résolution logique."""
        self.virtual_surface = pygame.Surface(LOGICAL_SIZE).convert() if pygame.display.get_surface() else pygame.Surface(LOGICAL_SIZE)

    def init_display(
        self,
        width: int = LOGICAL_WIDTH,
        height: int = LOGICAL_HEIGHT,
        fullscreen: bool = False,
        resizable: bool = True,
        title: str = "Tank War - Arena Duel",
    ) -> pygame.Surface:
        """Initialise la fenêtre Pygame et configure le viewport logique."""
        pygame.display.set_caption(title)

        flags = pygame.DOUBLEBUF
        if fullscreen:
            flags |= pygame.FULLSCREEN
            self.is_fullscreen = True
        elif resizable:
            flags |= pygame.RESIZABLE
            self.is_fullscreen = False

        self.real_width = max(640, int(width))
        self.real_height = max(360, int(height))
        if not fullscreen:
            self.last_windowed_size = (self.real_width, self.real_height)

        self.window_surface = pygame.display.set_mode((self.real_width, self.real_height), flags)
        self._create_virtual_surface()
        self.recalculate_viewport()

        return self.virtual_surface

    def recalculate_viewport(self) -> None:
        """Calcule le ratio d'aspect, le facteur d'échelle et le centrage letterbox/pillarbox."""
        if self.real_width <= 0 or self.real_height <= 0:
            return

        # Échelle proportionnelle uniforme qui préserve strictement le ratio 16:9
        scale_x = self.real_width / self.logical_width
        scale_y = self.real_height / self.logical_height
        self.scale_factor = min(scale_x, scale_y)

        # Dimensions réelles de la zone de jeu redimensionnée
        self.scaled_width = max(1, int(round(self.logical_width * self.scale_factor)))
        self.scaled_height = max(1, int(round(self.logical_height * self.scale_factor)))

        # Marges de centrage (Letterboxing en haut/bas ou Pillarboxing à gauche/droite)
        self.offset_x = (self.real_width - self.scaled_width) // 2
        self.offset_y = (self.real_height - self.scaled_height) // 2

        self.viewport_rect = pygame.Rect(self.offset_x, self.offset_y, self.scaled_width, self.scaled_height)

    def set_real_resolution(
        self,
        width: int,
        height: int,
        fullscreen: Optional[bool] = None,
        resizable: bool = True
    ) -> None:
        """Modifie la résolution physique de la fenêtre et réajuste le viewport."""
        self.real_width = max(640, int(width))
        self.real_height = max(360, int(height))

        if fullscreen is not None:
            self.is_fullscreen = fullscreen

        flags = pygame.DOUBLEBUF
        if self.is_fullscreen:
            flags |= pygame.FULLSCREEN
        elif resizable:
            flags |= pygame.RESIZABLE
            self.last_windowed_size = (self.real_width, self.real_height)

        if pygame.display.get_surface():
            self.window_surface = pygame.display.set_mode((self.real_width, self.real_height), flags)

        self.recalculate_viewport()

    def set_preset_resolution(self, width: int, height: int) -> None:
        """Applique l'une des résolutions prédéfinies supportées."""
        self.set_real_resolution(width, height, fullscreen=False)

    def cycle_resolution(self, forward: bool = True) -> Tuple[int, int]:
        """Bascule séquentiellement vers la résolution prédéfinie suivante."""
        current = (self.real_width, self.real_height)
        try:
            idx = SUPPORTED_PRESETS.index(current)
            next_idx = (idx + (1 if forward else -1)) % len(SUPPORTED_PRESETS)
        except ValueError:
            next_idx = 0

        target_w, target_h = SUPPORTED_PRESETS[next_idx]
        self.set_preset_resolution(target_w, target_h)
        return (target_w, target_h)

    def toggle_fullscreen(self) -> bool:
        """Bascule entre le mode plein écran et le mode fenêtré."""
        self.is_fullscreen = not self.is_fullscreen

        if self.is_fullscreen:
            # Récupération de la résolution actuelle du moniteur
            info = pygame.display.Info()
            target_w = info.current_w if info.current_w > 0 else self.real_width
            target_h = info.current_h if info.current_h > 0 else self.real_height
            self.set_real_resolution(target_w, target_h, fullscreen=True)
        else:
            # Restauration de la dernière taille fenêtrée mémorisée
            win_w, win_h = self.last_windowed_size
            self.set_real_resolution(win_w, win_h, fullscreen=False)

        return self.is_fullscreen

    # =========================================================================
    # CONVERSION DES COORDONNÉES ET GESTION DES ÉVÉNEMENTS
    # =========================================================================
    def window_to_logical(self, window_pos: Tuple[float, float]) -> Tuple[int, int]:
        """Convertit des coordonnées écran réelles en coordonnées virtuelles logiques 1600x900."""
        if self.scale_factor <= 0.0:
            return (int(window_pos[0]), int(window_pos[1]))

        # Soustraction du décalage de marge noire et division par le ratio d'échelle
        lx = (window_pos[0] - self.offset_x) / self.scale_factor
        ly = (window_pos[1] - self.offset_y) / self.scale_factor

        # Arrondi précis à l'entier le plus proche
        return (int(round(lx)), int(round(ly)))

    def logical_to_window(self, logical_pos: Tuple[float, float]) -> Tuple[int, int]:
        """Convertit des coordonnées logiques vers les coordonnées écran de la fenêtre."""
        wx = self.offset_x + logical_pos[0] * self.scale_factor
        wy = self.offset_y + logical_pos[1] * self.scale_factor
        return (int(round(wx)), int(round(wy)))

    def is_inside_viewport(self, window_pos: Tuple[float, float]) -> bool:
        """Indique si un clic ou curseur se situe dans la zone de jeu active (hors bandes noires)."""
        return self.viewport_rect.collidepoint((int(window_pos[0]), int(window_pos[1])))

    def get_mouse_pos(self) -> Tuple[int, int]:
        """Retourne la position logique courante de la souris (espace 1600x900)."""
        return self.window_to_logical(pygame.mouse.get_pos())

    def process_event(self, event: pygame.event.Event) -> pygame.event.Event:
        """Traite et adapte les événements d'entrée pour la résolution logique."""
        # 1. Gestion du redimensionnement de la fenêtre utilisateur
        if event.type == pygame.VIDEORESIZE:
            self.set_real_resolution(event.w, event.h)
            return event

        # 2. Raccourcis clavier globaux d'affichage :
        # - F11 ou Alt+Entrée : Plein écran
        # - F2 : Cycle parmi les résolutions prédéfinies
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11 or (event.key == pygame.K_RETURN and (event.mod & pygame.KMOD_ALT)):
                self.toggle_fullscreen()
                return event
            elif event.key == pygame.K_F2:
                self.cycle_resolution(forward=True)
                return event

        # 3. Translation transparente des coordonnées de souris
        if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            logical_pos = self.window_to_logical(event.pos)
            new_dict = dict(event.dict)
            new_dict["pos"] = logical_pos
            return pygame.event.Event(event.type, new_dict)

        elif event.type == pygame.MOUSEMOTION:
            logical_pos = self.window_to_logical(event.pos)
            rel_scale = max(0.0001, self.scale_factor)
            logical_rel = (
                int(round(event.rel[0] / rel_scale)),
                int(round(event.rel[1] / rel_scale))
            )
            new_dict = dict(event.dict)
            new_dict["pos"] = logical_pos
            new_dict["rel"] = logical_rel
            return pygame.event.Event(event.type, new_dict)

        return event

    # =========================================================================
    # RENDU ET PROJECTION SUR L'ÉCRAN RÉEL
    # =========================================================================
    def render_to_screen(self, target_window: Optional[pygame.Surface] = None) -> None:
        """Projette la surface virtuelle sur l'écran réel avec mise à l'échelle et letterboxing."""
        target = target_window or self.window_surface or pygame.display.get_surface()
        if not target or not self.virtual_surface:
            return

        # 1. Dessin des marges noires (Letterbox / Pillarbox)
        target.fill((10, 10, 14))

        # 2. Mise à l'échelle de la surface virtuelle
        if self.scaled_width == self.logical_width and self.scaled_height == self.logical_height:
            # 1:1 natif sans surcoût de redimensionnement
            target.blit(self.virtual_surface, (self.offset_x, self.offset_y))
        else:
            if self.use_smoothscale:
                try:
                    scaled = pygame.transform.smoothscale(
                        self.virtual_surface, (self.scaled_width, self.scaled_height)
                    )
                except Exception:
                    scaled = pygame.transform.scale(
                        self.virtual_surface, (self.scaled_width, self.scaled_height)
                    )
            else:
                scaled = pygame.transform.scale(
                    self.virtual_surface, (self.scaled_width, self.scaled_height)
                )

            target.blit(scaled, (self.offset_x, self.offset_y))

    def present(self) -> None:
        """Effectue le rendu sur l'écran réel puis rafraîchit l'affichage avec flip()."""
        self.render_to_screen()
        pygame.display.flip()


# =============================================================================
# INSTANCE GLOBALE SINGLETON
# =============================================================================
resolution_manager = ResolutionManager()

