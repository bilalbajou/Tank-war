"""Tests unitaires du système de tanks, des contrôles et des collisions."""

import os
import math
import pygame
import pytest

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, BORDER_THICKNESS
from players.tank import Tank
from players.controls import TankControls
from game.collision import CollisionHandler


@pytest.fixture
def arena_bounds():
    return pygame.Rect(
        BORDER_THICKNESS,
        BORDER_THICKNESS,
        SCREEN_WIDTH - 2 * BORDER_THICKNESS,
        SCREEN_HEIGHT - 2 * BORDER_THICKNESS
    )


def test_8_direction_rotation_angles():
    """Vérifie le calcul des angles pour les 8 directions de déplacement."""
    directions_expected = [
        (pygame.Vector2(1, 0), 0.0),        # Est (Droite)
        (pygame.Vector2(1, 1), 45.0),       # Sud-Est
        (pygame.Vector2(0, 1), 90.0),       # Sud (Bas)
        (pygame.Vector2(-1, 1), 135.0),     # Sud-Ouest
        (pygame.Vector2(-1, 0), 180.0),     # Ouest (Gauche)
        (pygame.Vector2(-1, -1), 225.0),    # Nord-Ouest
        (pygame.Vector2(0, -1), 270.0),     # Nord (Haut)
        (pygame.Vector2(1, -1), 315.0),     # Nord-Est
    ]

    tank = Tank(player_id=1, color_name="red", initial_position=(500, 500))

    for dir_vec, expected_angle in directions_expected:
        norm_dir = dir_vec.normalize()
        rad = math.atan2(norm_dir.y, norm_dir.x)
        deg = math.degrees(rad) % 360.0
        assert pytest.approx(deg, 0.01) == expected_angle


def test_diagonal_speed_normalization():
    """Vérifie que la vitesse diagonale n'est pas multipliée par racine(2)."""
    dir_diag = pygame.Vector2(1.0, 1.0)
    norm = dir_diag.normalize()
    assert pytest.approx(norm.length(), 0.001) == 1.0
    assert pytest.approx(norm.x, 0.001) == math.sqrt(2) / 2
    assert pytest.approx(norm.y, 0.001) == math.sqrt(2) / 2


def test_delta_time_movement(arena_bounds):
    """Vérifie que le déplacement est rigoureusement proportionnel à dt."""
    speed = 200.0
    tank = Tank(player_id=1, color_name="red", initial_position=(500, 500), speed=speed)
    tank.direction = pygame.Vector2(1.0, 0.0)

    # Déplacement pendant 0.5 seconde
    dt = 0.5
    tank.move(dt, obstacles=[], bounds_rect=arena_bounds)
    assert pytest.approx(tank.position.x, 0.01) == 500.0 + (speed * dt)
    assert pytest.approx(tank.position.y, 0.01) == 500.0


def test_arena_boundary_collision(arena_bounds):
    """Vérifie que le tank ne peut pas traverser les murs de l'arène."""
    # Place le tank tout près du mur Ouest
    tank = Tank(player_id=1, color_name="red", initial_position=(arena_bounds.left + 26, 450), speed=300.0)
    tank.direction = pygame.Vector2(-1.0, 0.0)  # Fonce vers la gauche (dans le mur)

    # Tente de foncer 10 fois dans le mur
    for _ in range(10):
        tank.move(0.1, obstacles=[], bounds_rect=arena_bounds)

    # La hitbox doit rester strictement à l'intérieur
    assert tank.hitbox.left >= arena_bounds.left
    assert tank.position.x >= arena_bounds.left + tank.HITBOX_WIDTH // 2


def test_obstacle_collision_and_blocking(arena_bounds):
    """Vérifie que le tank est bloqué par un obstacle physique (ex: caisse)."""
    # Obstacle centré en (400, 450) de taille 64x64
    crate_rect = pygame.Rect(400 - 32, 450 - 32, 64, 64)
    obstacles = [crate_rect]

    # Tank placé à gauche de l'obstacle et fonçant vers la droite
    tank = Tank(player_id=1, color_name="red", initial_position=(300, 450), speed=200.0)
    tank.direction = pygame.Vector2(1.0, 0.0)

    # Avance jusqu'à toucher
    for _ in range(20):
        tank.move(0.05, obstacles=obstacles, bounds_rect=arena_bounds)

    # Le tank ne doit JAMAIS traverser la caisse
    assert not tank.hitbox.colliderect(crate_rect)
    assert tank.hitbox.right <= crate_rect.left


def test_tank_versus_tank_collision(arena_bounds):
    """Vérifie que deux tanks entrent en collision et se bloquent mutuellement."""
    tank1 = Tank(player_id=1, color_name="red", initial_position=(500, 450), speed=200.0)
    tank2 = Tank(player_id=2, color_name="green", initial_position=(580, 450), speed=200.0)

    tank1.direction = pygame.Vector2(1.0, 0.0)   # Tank 1 fonce vers Tank 2
    tank2.direction = pygame.Vector2(-1.0, 0.0)  # Tank 2 fonce vers Tank 1

    # Avance les deux tanks l'un vers l'autre
    for _ in range(15):
        tank1.move(0.05, obstacles=[], bounds_rect=arena_bounds, other_tank_rect=tank2.hitbox)
        tank2.move(0.05, obstacles=[], bounds_rect=arena_bounds, other_tank_rect=tank1.hitbox)

    # Ils ne doivent pas se chevaucher
    assert not tank1.hitbox.colliderect(tank2.hitbox)


def test_wall_sliding_mechanism(arena_bounds):
    """Vérifie le glissement le long d'une paroi lors d'un déplacement diagonal."""
    # Mur horizontal au-dessus du tank
    wall = pygame.Rect(400, 300, 200, 40)
    # Tank juste sous le mur, se déplaçant en diagonale Haut-Droite
    tank = Tank(player_id=1, color_name="red", initial_position=(450, 300 + 40 + 26), speed=200.0)
    tank.direction = pygame.Vector2(1.0, -1.0).normalize()

    initial_x = tank.position.x
    initial_y = tank.position.y

    tank.move(0.1, obstacles=[wall], bounds_rect=arena_bounds)

    # L'axe Y vers le haut était bloqué, mais l'axe X vers la droite a pu glisser !
    assert tank.position.x > initial_x
    assert not tank.hitbox.colliderect(wall)


def test_tank_health_and_damage():
    """Vérifie le cycle de vie et dégâts du tank (3 vies)."""
    tank = Tank(player_id=1, color_name="red", initial_position=(200, 200), max_health=3)
    assert tank.vie == 3
    assert tank.is_alive

    tank.take_damage(1)
    assert tank.vie == 2
    assert tank.is_alive

    tank.heal(1)
    assert tank.vie == 3

    tank.take_damage(3)
    assert tank.vie == 0
    assert not tank.is_alive

