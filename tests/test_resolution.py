"""Tests unitaires automatisés pour le système de résolution logique adaptative (ResolutionManager).

Vérifie :
1. Le respect des proportions 16:9 et du ratio d'aspect sur toutes les résolutions cibles :
   - 1280 × 720 (HD)
   - 1366 × 768 (WXGA)
   - 1440 × 900 (16:10 avec Letterbox)
   - 1600 × 900 (Natif 1:1)
   - 1920 × 1080 (Full HD)
   - 2560 × 1440 (2K QHD)
   - 2560 × 1080 (21:9 Ultrawide avec Pillarbox)
2. La précision de conversion bidirectionnelle des coordonnées souris (window <-> logical).
3. L'adaptation dynamique lors du redimensionnement de la fenêtre (VIDEORESIZE).
4. La projection visuelle sur la surface cible sans étirement ni déformation graphique.
"""

import os
import pytest
import pygame

# Environnement de test sans affichage physique requis
os.environ["SDL_VIDEODRIVER"] = "dummy"

from interface.resolution_manager import (
    ResolutionManager,
    LOGICAL_WIDTH,
    LOGICAL_HEIGHT,
    LOGICAL_SIZE,
    LOGICAL_ASPECT_RATIO,
    SUPPORTED_PRESETS,
)


@pytest.fixture(autouse=True)
def setup_pygame():
    """Initialise le sous-système Pygame avant chaque test."""
    pygame.init()
    if not pygame.display.get_surface():
        pygame.display.set_mode((LOGICAL_WIDTH, LOGICAL_HEIGHT))
    yield


def test_logical_reference_resolution_constants():
    """Vérifie la définition de la résolution logique de référence 1600x900 (16:9)."""
    assert LOGICAL_WIDTH == 1600
    assert LOGICAL_HEIGHT == 900
    assert LOGICAL_SIZE == (1600, 900)
    assert abs(LOGICAL_ASPECT_RATIO - (16.0 / 9.0)) < 1e-5


def test_resolution_presets_proportions():
    """Vérifie le calcul d'échelle et le centrage letterbox sur les résolutions demandées."""
    rm = ResolutionManager()

    # 1. 1280 × 720 (HD - Ratio 16:9 strict)
    rm.real_width, rm.real_height = 1280, 720
    rm.recalculate_viewport()
    assert abs(rm.scale_factor - 0.8) < 1e-4
    assert rm.scaled_width == 1280
    assert rm.scaled_height == 720
    assert rm.offset_x == 0
    assert rm.offset_y == 0
    assert rm.viewport_rect == pygame.Rect(0, 0, 1280, 720)

    # 2. 1366 × 768 (WXGA standard ordinateurs portables)
    rm.real_width, rm.real_height = 1366, 768
    rm.recalculate_viewport()
    expected_scale = min(1366 / 1600, 768 / 900)  # ~0.85333
    assert abs(rm.scale_factor - expected_scale) < 1e-4
    assert rm.scaled_height == 768
    assert rm.offset_y == 0
    assert rm.offset_x >= 0  # Léger centrage horizontal de 0 ou 1 pixel

    # 3. 1440 × 900 (16:10 - Format large nécessitant un Letterbox horizontal)
    rm.real_width, rm.real_height = 1440, 900
    rm.recalculate_viewport()
    # Facteur limité par la largeur : 1440 / 1600 = 0.9
    assert abs(rm.scale_factor - 0.9) < 1e-4
    assert rm.scaled_width == 1440
    assert rm.scaled_height == 810  # 900 * 0.9
    assert rm.offset_x == 0
    assert rm.offset_y == 45  # Marge de (900 - 810) // 2 = 45 px en haut et en bas
    assert rm.viewport_rect == pygame.Rect(0, 45, 1440, 810)

    # 4. 1600 × 900 (Référence native 1:1)
    rm.real_width, rm.real_height = 1600, 900
    rm.recalculate_viewport()
    assert rm.scale_factor == 1.0
    assert rm.scaled_width == 1600
    assert rm.scaled_height == 900
    assert rm.offset_x == 0
    assert rm.offset_y == 0

    # 5. 1920 × 1080 (Full HD - Ratio 16:9 strict)
    rm.real_width, rm.real_height = 1920, 1080
    rm.recalculate_viewport()
    assert abs(rm.scale_factor - 1.2) < 1e-4
    assert rm.scaled_width == 1920
    assert rm.scaled_height == 1080
    assert rm.offset_x == 0
    assert rm.offset_y == 0

    # 6. 2560 × 1440 (2K QHD - Ratio 16:9 strict)
    rm.real_width, rm.real_height = 2560, 1440
    rm.recalculate_viewport()
    assert abs(rm.scale_factor - 1.6) < 1e-4
    assert rm.scaled_width == 2560
    assert rm.scaled_height == 1440
    assert rm.offset_x == 0
    assert rm.offset_y == 0

    # 7. 2560 × 1080 (21:9 Ultrawide - Nécessite un Pillarbox vertical à gauche et à droite)
    rm.real_width, rm.real_height = 2560, 1080
    rm.recalculate_viewport()
    # Facteur limité par la hauteur : 1080 / 900 = 1.2
    assert abs(rm.scale_factor - 1.2) < 1e-4
    assert rm.scaled_width == 1920
    assert rm.scaled_height == 1080
    assert rm.offset_x == (2560 - 1920) // 2  # 320 px de bande noire à gauche et à droite
    assert rm.offset_y == 0


def test_mouse_coordinate_translation_across_resolutions():
    """Vérifie la conversion bidirectionnelle exacte entre l'écran physique et l'espace logique."""
    rm = ResolutionManager()

    # Cas 1 : 1280x720 (Échelle 0.8)
    rm.real_width, rm.real_height = 1280, 720
    rm.recalculate_viewport()

    # Le centre de la fenêtre (640, 360) doit correspondre au centre logique (800, 450)
    logical_pos = rm.window_to_logical((640, 360))
    assert logical_pos == (800, 450)
    window_pos = rm.logical_to_window((800, 450))
    assert window_pos == (640, 360)

    # Coin supérieur gauche
    assert rm.window_to_logical((0, 0)) == (0, 0)
    assert rm.logical_to_window((0, 0)) == (0, 0)

    # Coin inférieur droit
    assert rm.window_to_logical((1280, 720)) == (1600, 900)

    # Cas 2 : 1440x900 avec bandes noires haut/bas de 45px
    rm.real_width, rm.real_height = 1440, 900
    rm.recalculate_viewport()

    # Point au début de la zone active (offset_y = 45)
    assert rm.window_to_logical((0, 45)) == (0, 0)
    # Centre de l'arène
    assert rm.window_to_logical((720, 450)) == (800, 450)


def test_process_event_translates_mouse_events():
    """Vérifie que process_event adapte les coordonnées des événements Pygame MOUSE."""
    rm = ResolutionManager()
    rm.real_width, rm.real_height = 1280, 720
    rm.recalculate_viewport()

    # 1. Clic de souris (MOUSEBUTTONDOWN)
    raw_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": (640, 360), "button": 1})
    adapted_click = rm.process_event(raw_click)
    assert adapted_click.pos == (800, 450)
    assert adapted_click.button == 1

    # 2. Relâchement de souris (MOUSEBUTTONUP)
    raw_up = pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": (1280, 720), "button": 1})
    adapted_up = rm.process_event(raw_up)
    assert adapted_up.pos == (1600, 900)

    # 3. Déplacement de souris (MOUSEMOTION)
    raw_motion = pygame.event.Event(pygame.MOUSEMOTION, {"pos": (320, 180), "rel": (8, 8), "buttons": (0, 0, 0)})
    adapted_motion = rm.process_event(raw_motion)
    assert adapted_motion.pos == (400, 225)
    # Le déplacement relatif rel doit également être rapporté à l'échelle
    assert adapted_motion.rel == (10, 10)  # 8 / 0.8 = 10


def test_videoresize_event_updates_viewport():
    """Vérifie que l'événement de redimensionnement de fenêtre met à jour le viewport sans crash."""
    rm = ResolutionManager()
    resize_event = pygame.event.Event(pygame.VIDEORESIZE, {"w": 1920, "h": 1080})
    rm.process_event(resize_event)

    assert rm.real_width == 1920
    assert rm.real_height == 1080
    assert abs(rm.scale_factor - 1.2) < 1e-4
    assert rm.viewport_rect == pygame.Rect(0, 0, 1920, 1080)


def test_virtual_surface_rendering_projection():
    """Vérifie la projection visuelle de la surface virtuelle 1600x900 sur une cible redimensionnée."""
    rm = ResolutionManager()
    rm.real_width, rm.real_height = 1280, 720
    rm.recalculate_viewport()

    # Dessin d'un rectangle distinctif sur la surface virtuelle
    rm.virtual_surface.fill((235, 209, 153))  # Couleur sable
    test_rect = pygame.Rect(100, 100, 200, 100)
    pygame.draw.rect(rm.virtual_surface, (231, 76, 60), test_rect)

    # Création d'une surface cible représentant la fenêtre réelle
    target_window = pygame.Surface((1280, 720))
    rm.render_to_screen(target_window=target_window)

    # Vérification que le pixel projeté à l'échelle (100 * 0.8, 100 * 0.8) = (80, 80) a la couleur rouge
    projected_color = target_window.get_at((120, 120))  # Milieu du rectangle projeté
    assert projected_color[0] > 200  # Composante rouge dominante
    assert projected_color[1] < 100  # Composante verte faible


def test_letterbox_margin_color_fill():
    """Vérifie que les marges letterbox sont remplies en noir hors de la zone de jeu."""
    rm = ResolutionManager()
    rm.real_width, rm.real_height = 1440, 900  # Marge de 45px en haut et bas
    rm.recalculate_viewport()

    target_window = pygame.Surface((1440, 900))
    rm.virtual_surface.fill((255, 255, 255))
    rm.render_to_screen(target_window=target_window)

    # Le pixel dans la bande noire supérieure (Y=10) doit être noir/sombre
    margin_color = target_window.get_at((720, 10))
    assert margin_color[0] <= 15
    assert margin_color[1] <= 15
    assert margin_color[2] <= 20

    # Le pixel dans la zone active (Y=100 > 45) doit être blanc
    active_color = target_window.get_at((720, 100))
    assert active_color[0] >= 240

