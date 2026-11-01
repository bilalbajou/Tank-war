"""Tests unitaires du système de combat balistique, tirs et dégâts."""

import os
import math
import pygame
import pytest

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, BORDER_THICKNESS
from players.tank import Tank
from game.projectile import Projectile
from game.projectile_manager import ProjectileManager
from game.obstacle import Obstacle, ObstacleType


@pytest.fixture
def arena_bounds():
    return pygame.Rect(
        BORDER_THICKNESS,
        BORDER_THICKNESS,
        SCREEN_WIDTH - 2 * BORDER_THICKNESS,
        SCREEN_HEIGHT - 2 * BORDER_THICKNESS
    )


def test_projectile_creation_at_cannon_tip():
    """Vérifie que l'obus part de l'extrémité du canon et non du centre du char."""
    tank = Tank(player_id=1, color_name="red", initial_position=(500, 400), initial_rotation=0.0)

    # Orientation vers l'Est (0°)
    muzzle_pos = tank.get_cannon_tip_position()
    assert pytest.approx(muzzle_pos.x, 0.01) == 500.0 + 38.0
    assert pytest.approx(muzzle_pos.y, 0.01) == 400.0

    # Tir d'un projectile
    bullet = tank.shoot()
    assert bullet is not None
    assert bullet.owner_id == 1
    assert pytest.approx(bullet.position.x, 0.01) == muzzle_pos.x
    assert pytest.approx(bullet.position.y, 0.01) == muzzle_pos.y
    assert bullet.direction.x == 1.0 and bullet.direction.y == 0.0


def test_projectile_direction_according_to_rotation():
    """Vérifie l'orientation balistique selon les 4 angles cardinaux."""
    angles = [0.0, 90.0, 180.0, 270.0]
    expected_dirs = [(1, 0), (0, 1), (-1, 0), (0, -1)]

    for angle, (ex, ey) in zip(angles, expected_dirs):
        tank = Tank(player_id=1, color_name="red", initial_position=(500, 500), initial_rotation=angle)
        bullet = tank.shoot()
        assert bullet is not None
        assert pytest.approx(bullet.direction.x, 0.01) == ex
        assert pytest.approx(bullet.direction.y, 0.01) == ey


def test_fire_cooldown_enforcement():
    """Vérifie l'application stricte du temps de rechargement (cooldown)."""
    cooldown = 0.5
    tank = Tank(player_id=1, color_name="red", initial_position=(300, 300), fire_cooldown=cooldown)

    # 1. Premier tir réussi
    b1 = tank.shoot()
    assert b1 is not None
    assert not tank.can_shoot()

    # 2. Deuxième tir immédiat refusé
    b2 = tank.shoot()
    assert b2 is None

    # 3. Écoulement partiel du cooldown (0.2s sur 0.5s)
    tank.update(0.2, obstacles=[])
    assert not tank.can_shoot()
    assert tank.shoot() is None

    # 4. Écoulement total du cooldown (0.35s supplémentaires)
    tank.update(0.35, obstacles=[])
    assert tank.can_shoot()
    b3 = tank.shoot()
    assert b3 is not None


def test_tank_cannot_hit_itself(arena_bounds):
    """Vérifie que le char n'est jamais endommagé par ses propres obus."""
    manager = ProjectileManager()
    tank = Tank(player_id=1, color_name="red", initial_position=(400, 400), initial_rotation=0.0)

    # Tir
    bullet = manager.spawn_projectile(tank)
    assert bullet is not None
    assert len(manager.projectiles) == 1

    # Avance le projectile directement sur la trajectoire
    for _ in range(10):
        manager.update(0.01, obstacles=[], tanks=[tank], bounds_rect=arena_bounds)

    # Le tank propriétaire reste indemne
    assert tank.vie == 3
    assert bullet.is_alive  # L'obus traverse son propre char sans collisionner


def test_projectile_hits_opponent_tank(arena_bounds):
    """Vérifie que l'obus touche le char adverse et lui inflige des dégâts."""
    manager = ProjectileManager()
    t1 = Tank(player_id=1, color_name="red", initial_position=(300, 450), initial_rotation=0.0, bullet_damage=1)
    t2 = Tank(player_id=2, color_name="green", initial_position=(450, 450), initial_rotation=180.0)

    assert t2.vie == 3

    # T1 tire vers l'Est en direction de T2
    bullet = manager.spawn_projectile(t1)
    assert bullet is not None

    # Met à jour jusqu'à l'impact (distance 150 px avec vitesse 650 px/s prend ~0.23s)
    for _ in range(15):
        manager.update(0.02, obstacles=[], tanks=[t1, t2], bounds_rect=arena_bounds)

    # T2 a été touché, perd 1 vie (passe à 2 vies), l'obus est détruit
    assert t2.vie == 2
    assert not bullet.is_alive
    assert len(manager.projectiles) == 0


def test_projectile_hits_destructible_crate(arena_bounds):
    """Vérifie que l'obus détruit les caisses et disparaît à l'impact."""
    manager = ProjectileManager()
    t1 = Tank(player_id=1, color_name="red", initial_position=(300, 450), initial_rotation=0.0, bullet_damage=25)
    
    # Caisse de 64x64 centrée en (400, 450)
    crate = Obstacle(ObstacleType.CRATE, 400, 450, destructible=True, health=100)
    assert crate.health == 100

    bullet = manager.spawn_projectile(t1)

    for _ in range(15):
        manager.update(0.02, obstacles=[crate], tanks=[t1], bounds_rect=arena_bounds)

    # L'obus a frappé la caisse et a disparu
    assert not bullet.is_alive
    assert crate.health == 75


def test_projectile_destruction_on_arena_bounds(arena_bounds):
    """Vérifie que les obus disparaissent dès qu'ils quittent l'aire de jeu."""
    manager = ProjectileManager()
    # Tank tirant vers la droite tout près de la bordure Est
    near_east_edge = arena_bounds.right - 20
    t1 = Tank(player_id=1, color_name="red", initial_position=(near_east_edge, 450), initial_rotation=0.0)

    bullet = manager.spawn_projectile(t1)
    assert bullet is not None

    # Après une fraction de seconde, le projectile quitte les limites
    manager.update(0.1, obstacles=[], tanks=[t1], bounds_rect=arena_bounds)
    assert not bullet.is_alive
    assert len(manager.projectiles) == 0


def test_both_tanks_can_shoot_simultaneously(arena_bounds):
    """Vérifie que deux joueurs peuvent faire feu dans la même trame sans conflit."""
    manager = ProjectileManager()
    t1 = Tank(player_id=1, color_name="red", initial_position=(200, 300), initial_rotation=0.0)
    t2 = Tank(player_id=2, color_name="green", initial_position=(1400, 300), initial_rotation=180.0)

    b1 = manager.spawn_projectile(t1)
    b2 = manager.spawn_projectile(t2)

    assert b1 is not None and b2 is not None
    assert len(manager.projectiles) == 2
    assert b1.owner_id == 1
    assert b2.owner_id == 2
    assert b1.direction.x == 1.0
    assert b2.direction.x == -1.0

