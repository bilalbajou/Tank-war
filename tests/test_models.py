"""Tests des modèles de jeu, du monde et de la physique."""

import pytest
from src.game.models.entity import Vector2D
from src.game.models.tank import Tank
from src.game.models.projectile import Projectile
from src.game.models.obstacle import Obstacle, ObstacleType
from src.game.world.arena import Arena
from src.game.world.collision import CollisionSystem
from src.input.command import PlayerCommand


def test_vector2d_operations():
    v1 = Vector2D(3.0, 4.0)
    assert v1.length() == 5.0

    v2 = Vector2D(1.0, 2.0)
    v_sum = v1 + v2
    assert v_sum.x == 4.0 and v_sum.y == 6.0

    v_scaled = v2 * 2.5
    assert v_scaled.x == 2.5 and v_scaled.y == 5.0

    v_norm = v1.normalize()
    assert pytest.approx(v_norm.length()) == 1.0


def test_tank_damage_and_lifecycle():
    tank = Tank(player_id="player_1", position=Vector2D(100.0, 100.0))
    assert tank.health == 100
    assert tank.is_alive

    tank.take_damage(30)
    assert tank.health == 70
    assert tank.is_alive

    tank.take_damage(80)
    assert tank.health == 0
    assert not tank.is_alive


def test_arena_spawns_and_bounds():
    arena = Arena(width=1600, height=900)
    p1_pos, p1_rot = arena.get_spawn(1)
    p2_pos, p2_rot = arena.get_spawn(2)

    assert p1_pos.x == 150.0
    assert p2_pos.x == 1600 - 150.0
    assert p1_rot == 0.0
    assert p2_rot == 180.0

    assert arena.is_within_bounds(Vector2D(800, 450))
    assert not arena.is_within_bounds(Vector2D(-10, 450))
    assert not arena.is_within_bounds(Vector2D(1650, 450))


def test_collision_aabb():
    obs1 = Obstacle("o1", ObstacleType.CRATE, Vector2D(100, 100), width=50, height=50)
    obs2 = Obstacle("o2", ObstacleType.CRATE, Vector2D(120, 100), width=50, height=50)
    obs3 = Obstacle("o3", ObstacleType.CRATE, Vector2D(300, 300), width=50, height=50)

    assert CollisionSystem.check_aabb_collision(obs1, obs2)
    assert not CollisionSystem.check_aabb_collision(obs1, obs3)


def test_player_command_serialization():
    cmd = PlayerCommand(
        player_id="p1",
        sequence_number=42,
        move_forward=1.0,
        rotate=-1.0,
        fire=True
    )
    cmd_dict = cmd.to_dict()
    cmd_restored = PlayerCommand.from_dict(cmd_dict)

    assert cmd_restored.player_id == "p1"
    assert cmd_restored.sequence_number == 42
    assert cmd_restored.move_forward == 1.0
    assert cmd_restored.rotate == -1.0
    assert cmd_restored.fire is True

