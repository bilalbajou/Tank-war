"""Tests unitaires de la carte 2D et des obstacles."""

import os
import pygame
import pytest

# Exécution sans écran pour les tests
os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, BORDER_THICKNESS, PLAYER_1_SPAWN, PLAYER_2_SPAWN
from game.map import ArenaMap
from game.obstacle import ObstacleType, DecorationType


@pytest.fixture
def arena_map():
    return ArenaMap(SCREEN_WIDTH, SCREEN_HEIGHT)


def test_map_dimensions_and_boundaries(arena_map):
    assert arena_map.width == 1600
    assert arena_map.height == 900
    assert len(arena_map.border_rects) == 4

    # Mur Nord
    assert arena_map.border_rects[0] == pygame.Rect(0, 0, 1600, BORDER_THICKNESS)
    # Mur Sud
    assert arena_map.border_rects[1] == pygame.Rect(0, 900 - BORDER_THICKNESS, 1600, BORDER_THICKNESS)


def test_obstacles_have_rects_and_block_movement(arena_map):
    assert len(arena_map.obstacles) > 0
    for obs in arena_map.obstacles:
        assert isinstance(obs.rect, pygame.Rect)
        assert obs.blocks_movement is True
        # Vérifie que l'obstacle est à l'intérieur des bordures
        assert obs.rect.left >= BORDER_THICKNESS
        assert obs.rect.right <= 1600 - BORDER_THICKNESS
        assert obs.rect.top >= BORDER_THICKNESS
        assert obs.rect.bottom <= 900 - BORDER_THICKNESS


def test_decorations_do_not_block_movement(arena_map):
    assert len(arena_map.decorations) > 0
    for dec in arena_map.decorations:
        assert isinstance(dec.rect, pygame.Rect)
        assert dec.blocks_movement is False
        assert dec.blocks_projectiles is False


def test_spawns_are_unobstructed(arena_map):
    # Boîte d'encombrement du tank (ex: 70x55)
    p1_rect = pygame.Rect(0, 0, 80, 60)
    p1_rect.center = (PLAYER_1_SPAWN[0], PLAYER_1_SPAWN[1])

    p2_rect = pygame.Rect(0, 0, 80, 60)
    p2_rect.center = (PLAYER_2_SPAWN[0], PLAYER_2_SPAWN[1])

    collision_rects = arena_map.get_collision_rects()
    for rect in collision_rects:
        assert not p1_rect.colliderect(rect), f"Obstacle en collision avec le spawn P1: {rect}"
        assert not p2_rect.colliderect(rect), f"Obstacle en collision avec le spawn P2: {rect}"


def test_crate_damage_and_destruction(arena_map):
    crate = next(obs for obs in arena_map.obstacles if obs.obstacle_type == ObstacleType.CRATE and obs.destructible)
    initial_health = crate.health
    assert initial_health == 100

    destroyed = crate.take_damage(60)
    assert not destroyed
    assert crate.health == 40
    # Le sprite a été remplacé par le sprite endommagé

    destroyed_final = crate.take_damage(50)
    assert destroyed_final
    assert crate.health == 0

