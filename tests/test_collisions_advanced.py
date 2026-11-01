"""Tests avancés du système de collision : Anti-tunneling, types d'obstacles et destruction."""

import os
import pygame
import pytest

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, BORDER_THICKNESS
from game.collision import CollisionHandler
from game.obstacle import Obstacle, ObstacleType, Decoration, DecorationType
from game.map import ArenaMap
from game.projectile_manager import ProjectileManager
from players.tank import Tank


@pytest.fixture
def arena_bounds():
    return pygame.Rect(
        BORDER_THICKNESS,
        BORDER_THICKNESS,
        SCREEN_WIDTH - 2 * BORDER_THICKNESS,
        SCREEN_HEIGHT - 2 * BORDER_THICKNESS
    )


def test_anti_tunneling_high_speed_barrier(arena_bounds):
    """Vérifie l'absence absolue de traversée (anti-tunneling) même à vitesse extrême (ex: 2000 px/s)."""
    # Barrière verticale mince (largeur 40px) en x = 600
    barrier_rect = pygame.Rect(600, 300, 40, 200)
    obstacles = [barrier_rect]

    # Tank en x = 500 (à 100px de la barrière), fonçant vers la droite à 2000 px/s
    tank = Tank(player_id=1, color_name="red", initial_position=(500, 400), speed=2000.0)
    tank.direction = pygame.Vector2(1.0, 0.0)

    # Déplacement sur un pas de temps long (0.1s => saut théorique de 200px sans CCD !)
    dt = 0.1
    tank.move(dt, obstacles=obstacles, bounds_rect=arena_bounds)

    # Le tank DOIT s'arrêter net contre la face Ouest de la barrière
    assert tank.hitbox.right <= barrier_rect.left
    assert not tank.hitbox.colliderect(barrier_rect)
    assert tank.position.x < barrier_rect.left


def test_anti_tunneling_high_speed_wall_boundary(arena_bounds):
    """Vérifie que même à vitesse extrême, un tank ne traverse jamais les murs extérieurs."""
    # Tank en x = 800, fonçant vers la bordure Ouest à 5000 px/s
    tank = Tank(player_id=1, color_name="red", initial_position=(200, 450), speed=5000.0)
    tank.direction = pygame.Vector2(-1.0, 0.0)

    # Déplacement violent
    tank.move(0.1, obstacles=[], bounds_rect=arena_bounds)

    # Doit être collé contre le bord sans sortir
    assert tank.hitbox.left >= arena_bounds.left
    assert tank.position.x >= arena_bounds.left + tank.HITBOX_WIDTH // 2


def test_metal_barrier_properties():
    """Vérifie les propriétés d'une barrière métallique (bloque tout, indestructible)."""
    barrier = Obstacle(ObstacleType.BARRIER_HORIZONTAL, 400, 400, destructible=False)
    assert barrier.blocks_movement is True
    assert barrier.blocks_projectiles is True
    assert barrier.destructible is False

    # Tentative d'infliger des dégâts
    destroyed = barrier.take_damage(100)
    assert not destroyed
    assert barrier.is_alive is True
    assert barrier.blocks_movement is True
    assert barrier.blocks_projectiles is True


def test_wooden_crate_properties_and_destruction():
    """Vérifie le cycle de vie d'une caisse en bois destructible."""
    crate = Obstacle(ObstacleType.CRATE, 400, 400, destructible=True, health=100)
    assert crate.blocks_movement is True
    assert crate.blocks_projectiles is True
    assert crate.destructible is True

    # Premier tir (25 dégâts)
    destroyed = crate.take_damage(25)
    assert not destroyed
    assert crate.health == 75
    assert crate.is_alive is True
    assert crate.blocks_movement is True

    # Dégâts fatals (75 restants)
    destroyed = crate.take_damage(75)
    assert destroyed is True
    assert crate.health == 0
    assert crate.is_alive is False
    # Une fois détruite, elle ne bloque plus
    assert crate.blocks_movement is False
    assert crate.blocks_projectiles is False


def test_decoration_properties():
    """Vérifie que les décorations végétales ne bloquent ni tanks ni projectiles."""
    cactus = Decoration(DecorationType.CACTUS, 300, 300)
    bush = Decoration(DecorationType.BUSH, 350, 350)

    assert cactus.blocks_movement is False
    assert cactus.blocks_projectiles is False
    assert bush.blocks_movement is False
    assert bush.blocks_projectiles is False


def test_crate_destruction_clears_path_in_map(arena_bounds):
    """Vérifie qu'une caisse détruite est purgée de la carte et libère le passage pour les tanks et tirs."""
    arena_map = ArenaMap(SCREEN_WIDTH, SCREEN_HEIGHT)
    pm = ProjectileManager()

    # Trouve une caisse destructible
    crate = next(obs for obs in arena_map.obstacles if obs.obstacle_type == ObstacleType.CRATE and obs.destructible)
    crate_center = (crate.rect.centerx, crate.rect.centery)
    crate_left = crate.rect.left

    # Place un tank dans la zone dégagée face à la caisse
    tank = Tank(player_id=1, color_name="red", initial_position=(crate_left - 45, crate_center[1]), initial_rotation=0.0, bullet_damage=50)

    # 1. Deux tirs pour détruire la caisse (100 PV)
    bullet1 = pm.spawn_projectile(tank)
    for _ in range(15):
        pm.update(0.02, arena_map.obstacles, [tank], arena_bounds, arena_map=arena_map)

    # Réinitialise cooldown pour tirer une 2e fois
    tank.current_cooldown = 0.0
    bullet2 = pm.spawn_projectile(tank)
    for _ in range(15):
        pm.update(0.02, arena_map.obstacles, [tank], arena_bounds, arena_map=arena_map)

    # La caisse a été détruite
    assert not crate.is_alive

    # Mise à jour de la carte : purge de la caisse détruite
    arena_map.update(0.016)

    # La caisse n'est plus dans la liste des obstacles
    assert crate not in arena_map.obstacles
    assert not any(obs.rect == crate.rect for obs in arena_map.obstacles)

    # Des particules d'animation de débris ont été générées
    assert len(arena_map.debris_particles) > 0

    # Le tank peut maintenant avancer librement à travers l'ancien emplacement de la caisse !
    tank.direction = pygame.Vector2(1.0, 0.0)
    for _ in range(30):
        tank.move(0.02, obstacles=arena_map.get_collision_rects(), bounds_rect=arena_bounds)

    # Le tank a franchi l'ancien centre de la caisse sans être bloqué
    assert tank.position.x > crate_center[0]
