"""Tests unitaires du système de combat, de progression, des règles et des power-ups."""

import os
import pygame
import pytest

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()

from game.game_state import MatchState
from game.powerup import PowerUp, PowerUpType, PowerUpManager
from players.tank import Tank


def test_initial_lives_and_hits():
    """Vérifie que chaque joueur commence avec 3 vies et perd 1 vie par tir adverse."""
    state = MatchState()
    assert state.p1_lives == 3
    assert state.p2_lives == 3

    # Joueur 1 subit un tir
    eliminated = state.register_hit(victim_id=1)
    assert not eliminated
    assert state.p1_lives == 2
    assert state.p2_score == 0

    # Deuxième tir sur J1
    eliminated = state.register_hit(victim_id=1)
    assert not eliminated
    assert state.p1_lives == 1


def test_elimination_awards_point_and_triggers_respawn():
    """Vérifie que la perte des 3 vies accorde 1 point à l'adversaire et déclenche le respawn."""
    state = MatchState(target_score=5)
    
    # J2 perd 3 vies consécutives
    state.register_hit(victim_id=2)
    state.register_hit(victim_id=2)
    eliminated = state.register_hit(victim_id=2)

    assert eliminated is True
    assert state.p1_score == 1
    assert state.p2_score == 0
    assert state.respawn_needed is True
    # Réinitialisation des vies pour la manche suivante
    assert state.p1_lives == 3
    assert state.p2_lives == 3
    assert not state.is_game_over

    state.acknowledge_respawn()
    assert state.respawn_needed is False


def test_first_to_5_points_wins():
    """Vérifie que le premier joueur à 5 points remporte la victoire."""
    state = MatchState(target_score=5)

    # 4 manches remportées par J1
    for _ in range(4):
        for _ in range(3):
            state.register_hit(victim_id=2)
        state.acknowledge_respawn()

    assert state.p1_score == 4
    assert not state.is_game_over

    # 5ème manche remportée par J1 (décisive)
    for _ in range(3):
        state.register_hit(victim_id=2)

    assert state.p1_score == 5
    assert state.is_game_over is True
    assert state.winner_id == 1
    assert "Premier à 5 points" in state.win_reason


def test_match_timer_expiration_and_higher_score():
    """Vérifie qu'à l'expiration des 90 secondes, le joueur ayant le meilleur score gagne."""
    state = MatchState(match_duration=90.0)
    
    # J1 a marqué 1 point
    for _ in range(3):
        state.register_hit(victim_id=2)
    state.acknowledge_respawn()
    assert state.p1_score == 1
    assert state.p2_score == 0

    # Écoulement de 90 secondes
    state.update(90.0)

    assert state.time_remaining == 0.0
    assert state.is_game_over is True
    assert state.winner_id == 1
    assert "Temps écoulé" in state.win_reason


def test_draw_at_90s_triggers_sudden_death():
    """Vérifie qu'une égalité à l'expiration déclenche la Mort Subite."""
    state = MatchState(match_duration=90.0)
    
    # 1 partout
    for _ in range(3):
        state.register_hit(victim_id=2)
    state.acknowledge_respawn()
    for _ in range(3):
        state.register_hit(victim_id=1)
    state.acknowledge_respawn()

    assert state.p1_score == 1
    assert state.p2_score == 1

    # Fin du temps
    state.update(90.0)

    assert state.is_game_over is False
    assert state.is_sudden_death is True
    assert state.p1_lives == 1
    assert state.p2_lives == 1

    # En mort subite, le premier coup fatal donne la victoire immédiate
    eliminated = state.register_hit(victim_id=1)
    assert eliminated is True
    assert state.is_game_over is True
    assert state.winner_id == 2
    assert "Mort Subite" in state.win_reason


def test_shield_powerup_absorbs_damage():
    """Vérifie que le bouclier absorbe les coups sans perte de vie."""
    tank = Tank(player_id=1, color_name="red", initial_position=(100, 100), max_health=3)
    assert tank.vie == 3

    # Activation du bouclier pour 5 secondes
    tank.apply_powerup("shield", duration=5.0)
    assert tank.has_shield is True

    # Coup reçu sous bouclier
    hit_taken = tank.take_damage(1)
    assert hit_taken is False
    assert tank.vie == 3  # Vies intactes !

    # Expiration du bouclier (5.1s)
    tank.update(5.1, obstacles=[])
    assert tank.has_shield is False

    # Coup reçu après expiration
    hit_taken = tank.take_damage(1)
    assert hit_taken is True
    assert tank.vie == 2  # Perd 1 vie !


def test_speed_powerup_increases_velocity():
    """Vérifie l'augmentation de vitesse de 50% sous power-up vitesse."""
    base_speed = 200.0
    tank = Tank(player_id=1, color_name="red", initial_position=(100, 100), speed=base_speed)
    assert tank.effective_speed == base_speed

    tank.apply_powerup("speed", duration=8.0)
    assert tank.effective_speed == base_speed * 1.5

    tank.update(8.1, obstacles=[])
    assert tank.effective_speed == base_speed


def test_rapid_fire_powerup_halves_cooldown():
    """Vérifie la réduction de 50% du temps de rechargement sous tir rapide."""
    base_cd = 0.5
    tank = Tank(player_id=1, color_name="red", initial_position=(100, 100), fire_cooldown=base_cd)
    assert tank.effective_cooldown == base_cd

    tank.apply_powerup("rapid_fire", duration=8.0)
    assert tank.effective_cooldown == base_cd * 0.5

    tank.update(8.1, obstacles=[])
    assert tank.effective_cooldown == base_cd


def test_powerup_pickup_and_manager():
    """Vérifie la collecte d'un power-up au sol par un char."""
    pm = PowerUpManager()
    tank = Tank(player_id=1, color_name="red", initial_position=(500, 500))

    # Génère un bouclier à l'emplacement exact du tank
    pup = pm.spawn_powerup(powerup_type=PowerUpType.SHIELD, position=(500, 500))
    assert len(pm.active_powerups) == 1
    assert tank.has_shield is False

    # Mise à jour avec détection de contact
    events = pm.update(0.016, [tank])
    assert len(events) == 1
    assert events[0] == (1, PowerUpType.SHIELD)
    assert tank.has_shield is True
    assert len(pm.active_powerups) == 0  # Consommé et retiré de l'arène


def test_match_state_reset():
    """Vérifie la réinitialisation complète de l'état du match."""
    state = MatchState()
    state.p1_score = 3
    state.p2_score = 2
    state.p1_lives = 1
    state.time_remaining = 30.0
    state.is_sudden_death = True

    state.reset()
    assert state.p1_score == 0
    assert state.p2_score == 0
    assert state.p1_lives == 3
    assert state.p2_lives == 3
    assert state.time_remaining == 90.0
    assert state.is_sudden_death is False
    assert state.is_game_over is False
    assert state.winner_id is None

