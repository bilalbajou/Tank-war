"""Tests unitaires automatisés pour la gestion centralisée des assets (AssetManager).

Vérifie :
1. L'existence et la validité de toutes les icônes de récompenses (results/victory, results/defeat, hud/score, powerups).
2. Le bon chargement de toutes les images PNG avec préservation de la transparence alpha.
3. L'indépendance des chemins vis-à-vis du répertoire de travail courant (CWD).
4. La robustesse face aux assets manquants (génération de fallback procédural sans crash).
5. La conformité des caches de rotation et de l'interfaçage avec IconManager.
"""

import os
import sys
from pathlib import Path
import pytest
import pygame

os.environ["SDL_VIDEODRIVER"] = "dummy"

from assets.asset_manager import (
    AssetManager,
    asset_manager,
    PROJECT_ROOT,
    ASSETS_DIR,
    ICONS_DIR,
    POWERUPS_DIR,
    TANKS_DIR,
    OBSTACLES_DIR,
)
from interface.icon_manager import icon_manager


@pytest.fixture(autouse=True)
def setup_pygame():
    """Initialise Pygame en mode headless."""
    pygame.init()
    if not pygame.display.get_surface():
        pygame.display.set_mode((1600, 900))
    yield


def test_project_root_and_assets_dir_exist():
    """Vérifie que la racine du projet et le dossier assets existent et sont valides."""
    assert PROJECT_ROOT.exists()
    assert (PROJECT_ROOT / "main.py").exists()
    assert ASSETS_DIR.exists()
    assert ICONS_DIR.exists()
    assert POWERUPS_DIR.exists()


def test_reward_icons_exist_on_disk():
    """Vérifie que toutes les icônes de récompenses et résultats existent sur disque."""
    expected_reward_icons = [
        ICONS_DIR / "results" / "victory.png",
        ICONS_DIR / "results" / "defeat.png",
        ICONS_DIR / "results" / "replay.png",
        ICONS_DIR / "results" / "home.png",
        ICONS_DIR / "hud" / "score.png",
        ICONS_DIR / "hud" / "shield.png",
        ICONS_DIR / "hud" / "speed.png",
        ICONS_DIR / "hud" / "ammo.png",
        POWERUPS_DIR / "shield.png",
        POWERUPS_DIR / "speed.png",
        POWERUPS_DIR / "rapid_fire.png",
    ]
    for p in expected_reward_icons:
        assert p.exists(), f"L'icône requise {p.name} est introuvable dans {p.parent}"
        assert p.is_file(), f"{p} n'est pas un fichier valide"
        assert p.stat().st_size > 100, f"Le fichier {p} est anormalement petit ou corrompu"


def test_reward_icons_loaded_with_transparency():
    """Vérifie le chargement en mémoire avec couche alpha préservée pour les récompenses."""
    keys = ["results/victory", "results/defeat", "hud/score", "powerup_shield", "powerup_speed", "powerup_rapid_fire"]
    for key in keys:
        img = asset_manager.get_image(key)
        assert isinstance(img, pygame.Surface)
        assert img.get_width() > 0 and img.get_height() > 0
        # Vérifie que la surface a un canal alpha actif
        has_alpha = (img.get_flags() & pygame.SRCALPHA) != 0 or img.get_colorkey() is not None or img.get_masks()[3] != 0
        assert has_alpha, f"L'image {key} ne possède pas de couche alpha transparente valide"


def test_path_resolution_independent_of_cwd(monkeypatch):
    """Vérifie que la résolution des assets fonctionne même si le CWD est modifié."""
    # Changement temporaire du répertoire courant vers un autre dossier (ex: la racine C: ou le dossier parent)
    parent_dir = PROJECT_ROOT.parent
    monkeypatch.chdir(parent_dir)

    manager = AssetManager()
    path_victory = manager.get_path("results/victory")
    assert path_victory is not None
    assert path_victory.exists()

    img = manager.get_image("results/victory")
    assert img is not None
    assert img.get_width() > 0


def test_missing_asset_generates_fallback_without_crash():
    """Vérifie qu'un asset inexistant ne fait pas planter le jeu et retourne un fallback fonctionnel."""
    # Clé d'asset complètement inexistante
    missing_key = "non_existent_trophy_asset_xyz"
    surf = asset_manager.get_image(missing_key)

    assert isinstance(surf, pygame.Surface)
    assert surf.get_width() > 0
    assert surf.get_height() > 0


def test_icon_manager_integration_with_asset_manager():
    """Vérifie que l'IconManager s'appuie correctement sur le gestionnaire centralisé."""
    # Récupération de l'icône de victoire à différentes tailles et états
    icon_normal = icon_manager.get_icon("results/victory", size=(32, 32), state="normal")
    assert icon_normal.get_size() == (32, 32)

    icon_hover = icon_manager.get_icon("results/victory", size=(48, 48), state="hover")
    assert icon_hover.get_size() == (48, 48)

    icon_disabled = icon_manager.get_icon("results/defeat", size=(24, 24), state="disabled")
    assert icon_disabled.get_size() == (24, 24)


def test_tank_and_bullet_rotation_caches():
    """Vérifie le bon fonctionnement du cache de rotation pour tanks et projectiles."""
    # Chars rouge et vert
    rot_red_0 = asset_manager.get_rotated_tank("red", 0.0)
    rot_red_90 = asset_manager.get_rotated_tank("red", 90.0)
    rot_red_0_cached = asset_manager.get_rotated_tank("red", 0.0)
    assert rot_red_0 is rot_red_0_cached  # Même instance en cache

    # Obus
    rot_bullet_45 = asset_manager.get_rotated_bullet(45.0)
    rot_bullet_45_cached = asset_manager.get_rotated_bullet(45.0)
    assert rot_bullet_45 is rot_bullet_45_cached

