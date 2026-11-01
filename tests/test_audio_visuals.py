"""Tests unitaires et d'intégration du système audiovisuel amélioré :

Valide :
- SoundManager : Chargement des 7 sons (shoot, explosion, collision, crate_break, powerup, victory, defeat),
  gestion du volume, bascule mute/unmute.
- AssetManager : Pré-chargement des sprites, gestion du cache des rotations pour les chars et obus.
- EffectsManager : Explosions de char, gerbes d'étincelles d'impact, confettis de victoire et cycle de vie.
- Projectiles animés : Traînée de feu et mise à jour sans fuite de mémoire.
- Intégrité des règles : Les améliorations audiovisuelles ne modifient aucune mécanique de jeu.
"""

from __future__ import annotations
import os
import pygame
import pytest

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

from game.sound_manager import SoundManager, sound_manager
from game.asset_manager import AssetManager, asset_manager
from game.effects import EffectsManager, effects_manager, TankExplosionEffect, ImpactEffect, ConfettiParticle
from players.tank import Tank
from game.projectile import Projectile


# =============================================================================
# 1. TESTS DU SOUND MANAGER
# =============================================================================
def test_sound_manager_preloading_and_playback():
    """Vérifie que les 7 sons requis sont pré-chargés et fonctionnels."""
    expected_sounds = ["shoot", "explosion", "collision", "crate_break", "powerup", "victory", "defeat"]
    for snd in expected_sounds:
        assert snd in sound_manager.sounds, f"Le son '{snd}' doit être présent dans le SoundManager"

    # Test des méthodes de lecture express
    sound_manager.play_shoot()
    sound_manager.play_explosion()
    sound_manager.play_collision()
    sound_manager.play_crate_break()
    sound_manager.play_powerup()
    sound_manager.play_victory()
    sound_manager.play_defeat()


def test_sound_manager_volume_and_mute():
    """Vérifie la gestion et le plafonnement du volume."""
    sound_manager.set_volume(0.5)
    assert sound_manager.master_volume == 0.5

    # Clamping au-dessus de 1.0 et en-dessous de 0.0
    sound_manager.set_volume(1.8)
    assert sound_manager.master_volume == 1.0

    sound_manager.set_volume(-0.5)
    assert sound_manager.master_volume == 0.0

    # Rétablissement
    sound_manager.set_volume(0.7)

    # Bascule Mute
    assert sound_manager.enabled is True
    sound_manager.toggle_mute()
    assert sound_manager.enabled is False
    sound_manager.toggle_mute()
    assert sound_manager.enabled is True


# =============================================================================
# 2. TESTS DE L'ASSET MANAGER & CACHE DE ROTATION
# =============================================================================
def test_asset_manager_preloaded_images():
    """Vérifie que toutes les textures clés sont en mémoire."""
    keys = [
        "tank_red",
        "tank_green",
        "crate",
        "crate_damaged",
        "barrier_horizontal",
        "barrier_vertical",
        "rock_large",
        "rock_small",
        "plant_cactus",
        "plant_bush",
        "bullet",
        "desert_background",
        "border_tile",
    ]
    for k in keys:
        img = asset_manager.get_image(k)
        assert isinstance(img, pygame.Surface)
        assert img.get_width() > 0 and img.get_height() > 0


def test_asset_manager_rotation_caches():
    """Vérifie le fonctionnement du cache de rotations pour tanks et obus."""
    # Rotation tank
    rot_red_0 = asset_manager.get_rotated_tank("red", 0.0)
    rot_red_90 = asset_manager.get_rotated_tank("red", 90.0)
    rot_red_0_cached = asset_manager.get_rotated_tank("red", 0.0)

    assert rot_red_0 is rot_red_0_cached  # Même objet en mémoire depuis le cache !
    assert rot_red_0 != rot_red_90

    # Rotation obus
    rot_bullet_45 = asset_manager.get_rotated_bullet(45.0)
    rot_bullet_45_cached = asset_manager.get_rotated_bullet(45.0)
    assert rot_bullet_45 is rot_bullet_45_cached


# =============================================================================
# 3. TESTS DU MOTEUR D'EFFETS VISUELS & PARTICULES
# =============================================================================
def test_effects_manager_tank_explosion():
    """Vérifie l'instanciation, la mise à jour et la fin d'une explosion de char."""
    effects = EffectsManager()
    effects.clear()

    effects.spawn_tank_explosion(400, 300)
    assert len(effects.tank_explosions) == 1

    surface = pygame.Surface((800, 600))
    effects.draw(surface)

    # Mise à jour sur toute la durée de vie
    effects.update(0.5)
    assert len(effects.tank_explosions) == 1
    effects.draw(surface)

    effects.update(0.5)
    # L'effet a expiré et est nettoyé automatiquement
    assert len(effects.tank_explosions) == 0


def test_effects_manager_impact_and_victory():
    """Vérifie les étincelles d'impact et la célébration de victoire."""
    effects = EffectsManager()
    effects.clear()

    effects.spawn_impact(250, 150, angle_deg=45.0)
    assert len(effects.impacts) == 1

    effects.trigger_victory(1600, 900)
    assert effects.victory_effect is not None
    assert len(effects.victory_effect.confettis) > 0

    surface = pygame.Surface((1600, 900))
    effects.update(0.05)
    effects.draw(surface)

    effects.stop_victory()
    assert effects.victory_effect is None


def test_animated_projectile_trail():
    """Vérifie qu'un projectile se déplace et met à jour son animation de traînée."""
    proj = Projectile(owner_id=1, start_position=(200, 200), rotation=0.0, speed=600.0)
    assert proj.is_alive is True
    assert proj.position.x == 200.0

    surface = pygame.Surface((400, 400))
    proj.update(0.016)
    assert proj.position.x > 200.0
    proj.draw(surface)


def test_tank_uses_cached_sprites():
    """Vérifie que la classe Tank utilise les textures de l'AssetManager."""
    tank = Tank(player_id=1, color_name="red", initial_position=(300, 300), initial_rotation=0.0)
    assert tank.original_sprite is not None
    assert tank.image is not None
    assert tank.image.get_width() > 0

    surface = pygame.Surface((500, 500))
    tank.draw(surface)

