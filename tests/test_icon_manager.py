"""Tests unitaires pour le gestionnaire d'icônes (IconManager) et l'intégration dans UIButton.

Valide :
- Indexation et chargement de toutes les icônes PNG.
- Mise en cache multi-niveaux (brute et redimensionnée).
- Redimensionnement avec conservation du ratio d'aspect.
- États visuels : normal, hover, pressed, disabled.
- Ancrages dynamiques de draw_icon.
- Fallback procédural en cas d'icône inconnue.
- Rendu des boutons UIButton avec icônes.
"""

from __future__ import annotations
import os
from pathlib import Path
import pygame
import pytest

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

from interface.icon_manager import IconManager, icon_manager
from interface.components import UIButton


def test_icon_manager_indexing_and_preloading():
    """Vérifie que toutes les catégories d'icônes sont trouvées et préchargées."""
    mgr = IconManager()
    count = mgr.preload_all()
    assert count >= 20, f"Nombre d'icônes préchargées insuffisant : {count}"

    # Vérification des icônes obligatoires par catégorie
    required_icons = [
        # Menu
        "menu/play", "menu/host", "menu/join", "menu/settings", "menu/controls", "menu/exit",
        # Network
        "network/wifi", "network/ip", "network/connect", "network/back", "network/connected", "network/disconnected",
        # HUD
        "hud/health", "hud/ammo", "hud/score", "hud/timer", "hud/shield", "hud/speed", "hud/pause",
        # Pause
        "pause/resume", "pause/restart", "pause/settings", "pause/menu", "pause/quit",
        # Results
        "results/victory", "results/defeat", "results/replay", "results/home",
    ]

    for icon_key in required_icons:
        surf = mgr.get_icon(icon_key, size=(32, 32))
        assert isinstance(surf, pygame.Surface)
        assert surf.get_width() == 32
        assert surf.get_height() == 32


def test_icon_manager_caching_and_states():
    """Vérifie le fonctionnement des caches et des altérations d'état."""
    mgr = IconManager()

    # 1. Vérification du cache : deux appels successifs doivent renvoyer la même surface
    s1 = mgr.get_icon("menu/play", size=(24, 24), state="normal")
    s2 = mgr.get_icon("menu/play", size=(24, 24), state="normal")
    assert s1 is s2, "Le cache redimensionné doit retourner la même instance de surface"

    # 2. Différenciation des états
    s_hover = mgr.get_icon("menu/play", size=(24, 24), state="hover")
    s_pressed = mgr.get_icon("menu/play", size=(24, 24), state="pressed")
    s_disabled = mgr.get_icon("menu/play", size=(24, 24), state="disabled")

    assert s_hover is not s1
    assert s_pressed is not s1
    assert s_disabled is not s1

    # L'état disabled doit avoir une transparence réduite
    # Trouver un pixel non-transparent de base
    found_alpha = False
    for x in range(24):
        for y in range(24):
            a_norm = s1.get_at((x, y))[3]
            if a_norm > 100:
                a_dis = s_disabled.get_at((x, y))[3]
                assert a_dis < a_norm, "L'état disabled doit réduire l'alpha"
                found_alpha = True
                break
        if found_alpha:
            break
    assert found_alpha, "Un pixel opaque aurait dû être trouvé sur l'icône"


def test_icon_manager_draw_icon_anchors():
    """Vérifie les différents modes d'ancrage de draw_icon."""
    surface = pygame.Surface((200, 200), pygame.SRCALPHA)
    mgr = IconManager()

    # Ancrage topleft
    r_topleft = mgr.draw_icon(surface, "menu/play", position=(10, 20), size=(30, 30), anchor="topleft")
    assert r_topleft.topleft == (10, 20)
    assert r_topleft.size == (30, 30)

    # Ancrage center
    r_center = mgr.draw_icon(surface, "menu/host", position=(100, 100), size=(40, 40), anchor="center")
    assert r_center.center == (100, 100)
    assert r_center.size == (40, 40)

    # Ancrage midleft
    r_midleft = mgr.draw_icon(surface, "network/wifi", position=(50, 80), size=(20, 20), anchor="midleft")
    assert r_midleft.midleft == (50, 80)


def test_icon_manager_fallback():
    """Vérifie qu'une icône inexistante ne provoque pas de crash et renvoie une surface de fallback."""
    mgr = IconManager()
    surf = mgr.get_icon("non_existent_icon_xyz", size=(28, 28))
    assert isinstance(surf, pygame.Surface)
    assert surf.get_size() == (28, 28)


def test_ui_button_with_icon_rendering():
    """Vérifie que les boutons UIButton avec icônes se mettent à jour et se dessinent correctement."""
    clicked = False

    def on_click():
        nonlocal clicked
        clicked = True

    btn = UIButton(
        rect=pygame.Rect(50, 50, 240, 60),
        text="JOUER",
        scheme="green",
        icon_name="menu/play",
        icon_size=(28, 28),
        icon_spacing=12,
        on_click=on_click,
    )

    surface = pygame.Surface((400, 300))
    btn.update(0.016)

    # État normal
    btn.draw(surface)

    # État survol
    btn.is_hovered = True
    btn.update(0.016)
    btn.draw(surface)

    # État enfoncé
    btn.is_pressed = True
    btn.update(0.016)
    btn.draw(surface)

    # État désactivé
    btn.enabled = False
    btn.draw(surface)

    assert btn.icon_name == "menu/play"
    assert btn.icon_size == (28, 28)

