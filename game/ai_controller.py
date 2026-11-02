"""Contrôleur d'Intelligence Artificielle (IA) pour Tank War (Arena Duel).

Fournit :
- TankAIController : Pilote autonome pour le char ennemi avec machine à états finis (FSM) :
  - PATROL : exploration et ronde tactique dans l'arène.
  - CHASE : traque du joueur et réduction de distance.
  - ATTACK : strafe latéral, alignement 8 directions et tir au canon.
  - RETREAT : repli tactique et mise à couvert (quand le joueur a un bouclier ou que l'IA a 1 vie).
  - SEEK_POWERUP : détection et collecte proactive des bonus au sol (bouclier, vitesse, tir rapide).
- AIDifficulty : Profils de difficulté configurables (Facile, Moyen, Difficile).
- Raycasting de ligne de vue (Line of Sight) optimisé avec clipline Pygame.
- Détection d'obstacle et système d'anti-blocage (Anti-Stuck).
- Visée prédictive en mode Difficile (anticipation de la trajectoire de l'obus).
"""

from __future__ import annotations
import math
import random
from enum import Enum
from typing import List, Optional, Sequence, Tuple
import pygame

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    BORDER_THICKNESS,
    BULLET_SPEED,
)
from game.map import ArenaMap
from game.obstacle import Obstacle
from game.powerup import PowerUp, PowerUpManager
from players.tank import Tank


class AIDifficulty(Enum):
    """Niveaux de difficulté pour le Tank IA."""
    EASY = "easy"        # Recrue : tirs espacés, pas d'anticipation, vitesse -15%
    MEDIUM = "medium"    # Vétéran : bon équilibre, collecte les bonus, esquive légère
    HARD = "hard"        # Élite : visée prédictive, strafe continu, repli tactique


class AIState(Enum):
    """États comportementaux de l'IA."""
    PATROL = "patrol"
    CHASE = "chase"
    ATTACK = "attack"
    RETREAT = "retreat"
    SEEK_POWERUP = "powerup"


# Les 8 directions cardinales et diagonales standard (en degrés et vecteurs unitaires)
EIGHT_DIRECTIONS: List[Tuple[float, pygame.Vector2]] = [
    (0.0, pygame.Vector2(1.0, 0.0)),
    (45.0, pygame.Vector2(1.0, 1.0).normalize()),
    (90.0, pygame.Vector2(0.0, 1.0)),
    (135.0, pygame.Vector2(-1.0, 1.0).normalize()),
    (180.0, pygame.Vector2(-1.0, 0.0)),
    (225.0, pygame.Vector2(-1.0, -1.0).normalize()),
    (270.0, pygame.Vector2(0.0, -1.0)),
    (315.0, pygame.Vector2(1.0, -1.0).normalize()),
]


def snap_to_8_directions(angle_deg: float) -> Tuple[float, pygame.Vector2]:
    """Aligne un angle continu sur la plus proche des 8 directions du jeu."""
    normalized = angle_deg % 360.0
    best_deg, best_vec = EIGHT_DIRECTIONS[0]
    min_diff = 360.0

    for deg, vec in EIGHT_DIRECTIONS:
        diff = abs(normalized - deg)
        if diff > 180.0:
            diff = 360.0 - diff
        if diff < min_diff:
            min_diff = diff
            best_deg = deg
            best_vec = vec

    return best_deg, pygame.Vector2(best_vec.x, best_vec.y)


class TankAIController:
    """Contrôleur IA autonome pilotant un Tank dans l'arène de duel."""

    def __init__(
        self,
        tank: Optional[Tank] = None,
        target_tank: Optional[Tank] = None,
        arena_map: Optional[ArenaMap] = None,
        difficulty: AIDifficulty = AIDifficulty.MEDIUM,
        powerup_manager: Optional[PowerUpManager] = None,
        bot_tank: Optional[Tank] = None,
    ) -> None:
        self.tank = tank if tank is not None else bot_tank
        self.target = target_tank
        self.arena_map = arena_map
        self.difficulty = difficulty
        self.powerup_manager = powerup_manager

        self.state = AIState.PATROL

        # Configuration selon la difficulté
        self.reaction_delay = 0.15
        self.speed_multiplier = 1.0
        self.aim_tolerance = 25.0  # Degrés max d'écart pour autoriser le tir
        self.lead_shots = False
        self._apply_difficulty_params()

        # Minuteurs internes
        self.state_timer = 0.0
        self.reaction_timer = 0.0
        self.strafe_timer = 0.0
        self.strafe_direction = 1.0  # +1.0 ou -1.0

        # Système anti-blocage (Anti-Stuck)
        init_x = self.tank.position.x if self.tank else 0.0
        init_y = self.tank.position.y if self.tank else 0.0
        self.last_pos = pygame.Vector2(init_x, init_y)
        self.stuck_check_timer = 0.0
        self.is_stuck = False
        self.unstuck_timer = 0.0
        self.unstuck_vector = pygame.Vector2(0.0, 0.0)

        # Points de patrouille tactiques répartis dans l'arène
        self.patrol_waypoints = [
            pygame.Vector2(250, 200),
            pygame.Vector2(SCREEN_WIDTH - 250, 200),
            pygame.Vector2(SCREEN_WIDTH - 250, SCREEN_HEIGHT - 200),
            pygame.Vector2(250, SCREEN_HEIGHT - 200),
            pygame.Vector2(SCREEN_WIDTH // 2, 220),
            pygame.Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 220),
        ]
        self.current_waypoint_idx = random.randint(0, len(self.patrol_waypoints) - 1)

    @property
    def bot_tank(self) -> Optional[Tank]:
        """Alias pour le char piloté par l'IA."""
        return self.tank

    @bot_tank.setter
    def bot_tank(self, value: Optional[Tank]) -> None:
        self.tank = value
        if value:
            self.last_pos = pygame.Vector2(value.position.x, value.position.y)

    @property
    def target_tank(self) -> Optional[Tank]:
        """Alias pour le char cible."""
        return self.target

    @target_tank.setter
    def target_tank(self, value: Optional[Tank]) -> None:
        self.target = value

    def reset(self) -> None:
        """Réinitialise les minuteurs et l'état interne de l'IA lors d'un nouveau round."""
        self.state = AIState.PATROL
        self.state_timer = 0.0
        self.reaction_timer = 0.0
        self.strafe_timer = 0.0
        self.is_stuck = False
        self.unstuck_timer = 0.0
        if self.tank:
            self.last_pos = pygame.Vector2(self.tank.position.x, self.tank.position.y)

    def _apply_difficulty_params(self) -> None:
        """Ajuste les coefficients de comportement selon la difficulté choisie."""
        if self.difficulty == AIDifficulty.EASY:
            self.reaction_delay = 0.32
            self.speed_multiplier = 0.85
            self.aim_tolerance = 30.0
            self.lead_shots = False
        elif self.difficulty == AIDifficulty.MEDIUM:
            self.reaction_delay = 0.15
            self.speed_multiplier = 1.0
            self.aim_tolerance = 25.0
            self.lead_shots = False
        elif self.difficulty == AIDifficulty.HARD:
            self.reaction_delay = 0.04
            self.speed_multiplier = 1.0
            self.aim_tolerance = 22.5
            self.lead_shots = True

    def set_difficulty(self, difficulty: AIDifficulty) -> None:
        """Modifie dynamiquement la difficulté."""
        self.difficulty = difficulty
        self._apply_difficulty_params()

    def has_line_of_sight(self, from_pos: pygame.Vector2, to_pos: pygame.Vector2) -> bool:
        """Vérifie si la ligne de tir est dégagée de tout obstacle bloquant les projectiles."""
        p1 = (from_pos.x, from_pos.y)
        p2 = (to_pos.x, to_pos.y)

        for obs in self.arena_map.obstacles:
            if obs.blocks_projectiles:
                if obs.rect.clipline(p1, p2):
                    return False
        return True

    def _find_nearest_powerup(self) -> Optional[PowerUp]:
        """Trouve le bonus au sol actif le plus proche."""
        if not self.powerup_manager or not self.powerup_manager.active_powerups:
            return None

        best_pw = None
        min_dist = float("inf")
        for pw in self.powerup_manager.active_powerups:
            if not pw.is_collected:
                dist = self.tank.position.distance_to(pw.position)
                if dist < min_dist:
                    min_dist = dist
                    best_pw = pw
        return best_pw

    def _update_anti_stuck(self, dt: float, desired_dir: pygame.Vector2) -> Optional[pygame.Vector2]:
        """Détecte si le tank est coincé contre un mur ou une caisse et produit une manœuvre d'évasion."""
        if self.is_stuck:
            self.unstuck_timer -= dt
            if self.unstuck_timer <= 0:
                self.is_stuck = False
            return self.unstuck_vector

        # Surveillance de déplacement
        self.stuck_check_timer += dt
        if self.stuck_check_timer >= 0.45:
            self.stuck_check_timer = 0.0
            moved_dist = self.tank.position.distance_to(self.last_pos)
            self.last_pos = pygame.Vector2(self.tank.position.x, self.tank.position.y)

            # Si l'IA souhaitait avancer mais a fait du surplace (< 8 px)
            if desired_dir.length_squared() > 0 and moved_dist < 8.0:
                self.is_stuck = True
                self.unstuck_timer = 0.40
                # Manœuvre perpendiculaire ou marche arrière
                perp = pygame.Vector2(-desired_dir.y, desired_dir.x)
                if random.random() < 0.5:
                    perp = -perp
                self.unstuck_vector = perp.normalize()
                return self.unstuck_vector

        return None

    def update(self, dt: float) -> Tuple[pygame.Vector2, bool]:
        """Met à jour l'IA et retourne (vecteur_direction, doit_tirer).

        Met également à jour directement l'orientation et le sprite du tank.
        """
        if not self.tank.is_alive or not self.target:
            return pygame.Vector2(0.0, 0.0), False

        self.state_timer += dt
        self.reaction_timer += dt
        self.strafe_timer += dt

        # Alternance de strafe latéral toutes les 1.8 secondes
        if self.strafe_timer >= 1.8:
            self.strafe_timer = 0.0
            self.strafe_direction = -self.strafe_direction

        to_target = self.target.position - self.tank.position
        dist_target = to_target.length()
        has_los = self.has_line_of_sight(self.tank.position, self.target.position)
        nearest_powerup = self._find_nearest_powerup()

        # =====================================================================
        # 1. ARBITRAGE DE L'ÉTAT COMPORTEMENTAL (FSM)
        # =====================================================================
        # Repli si la cible a un bouclier ou est invulnérable
        target_invulnerable = self.target.shield_timer > 0.0 or self.target.invulnerable_timer > 0.0
        ai_critical_hp = self.tank.vie <= 1 and self.target.vie >= 2

        if target_invulnerable or (ai_critical_hp and self.difficulty == AIDifficulty.HARD):
            self.state = AIState.RETREAT
        elif nearest_powerup and self.tank.position.distance_to(nearest_powerup.position) < 600:
            self.state = AIState.SEEK_POWERUP
        elif has_los and dist_target <= 580:
            self.state = AIState.ATTACK
        elif dist_target <= 750:
            self.state = AIState.CHASE
        else:
            self.state = AIState.PATROL

        # =====================================================================
        # 2. DÉCISION DE DÉPLACEMENT SELON L'ÉTAT
        # =====================================================================
        desired_move = pygame.Vector2(0.0, 0.0)

        if self.state == AIState.ATTACK:
            # En combat : maintenir distance optimale (~260-380 px) et strafer
            if dist_target > 380:
                desired_move += to_target.normalize() * 0.8
            elif dist_target < 240:
                desired_move -= to_target.normalize() * 0.9

            # Strafe latéral perpendiculaire à la cible
            if to_target.length_squared() > 0:
                perp = pygame.Vector2(-to_target.y, to_target.x).normalize()
                desired_move += perp * self.strafe_direction * 0.9

        elif self.state == AIState.CHASE:
            if to_target.length_squared() > 0:
                desired_move = to_target.normalize()

        elif self.state == AIState.SEEK_POWERUP and nearest_powerup:
            to_pw = nearest_powerup.position - self.tank.position
            if to_pw.length_squared() > 0:
                desired_move = to_pw.normalize()

        elif self.state == AIState.RETREAT:
            # S'éloigner du joueur
            if to_target.length_squared() > 0:
                desired_move = -to_target.normalize()
            # Si dos au mur, longer la paroi
            if self.tank.position.x < BORDER_THICKNESS + 90 or self.tank.position.x > SCREEN_WIDTH - BORDER_THICKNESS - 90:
                desired_move.y = 1.0 if self.tank.position.y < SCREEN_HEIGHT // 2 else -1.0

        elif self.state == AIState.PATROL:
            waypoint = self.patrol_waypoints[self.current_waypoint_idx]
            to_wp = waypoint - self.tank.position
            if to_wp.length() < 70:
                # Prochain waypoint
                self.current_waypoint_idx = (self.current_waypoint_idx + 1) % len(self.patrol_waypoints)
                waypoint = self.patrol_waypoints[self.current_waypoint_idx]
                to_wp = waypoint - self.tank.position

            if to_wp.length_squared() > 0:
                desired_move = to_wp.normalize()

        # Application du système anti-blocage
        evasion = self._update_anti_stuck(dt, desired_move)
        if evasion is not None:
            desired_move = evasion

        # Normalisation et alignement sur les 8 directions du jeu
        final_dir = pygame.Vector2(0.0, 0.0)
        if desired_move.length_squared() > 0:
            move_angle = math.degrees(math.atan2(desired_move.y, desired_move.x)) % 360.0
            _, final_dir = snap_to_8_directions(move_angle)
            final_dir *= self.speed_multiplier

        # =====================================================================
        # 3. ORIENTATION DE LA TOURELLE / VISÉE DU CHAR
        # =====================================================================
        # Calcul du point d'impact visé (prédictif en mode Hard)
        aim_target_pos = pygame.Vector2(self.target.position.x, self.target.position.y)
        if self.lead_shots and self.target.direction.length_squared() > 0:
            bullet_time = dist_target / max(100.0, BULLET_SPEED)
            target_velocity = self.target.direction * self.target.effective_speed
            aim_target_pos += target_velocity * bullet_time

        to_aim = aim_target_pos - self.tank.position
        if to_aim.length_squared() > 0:
            ideal_aim_angle = math.degrees(math.atan2(to_aim.y, to_aim.x)) % 360.0
        else:
            ideal_aim_angle = self.tank.rotation

        # Si en combat ou traque, le canon s'aligne vers le joueur
        # Sinon en patrouille pure, il s'aligne vers la direction de déplacement
        if self.state in (AIState.ATTACK, AIState.CHASE, AIState.RETREAT) or has_los:
            aim_snap_deg, _ = snap_to_8_directions(ideal_aim_angle)
        elif final_dir.length_squared() > 0:
            aim_snap_deg, _ = snap_to_8_directions(math.degrees(math.atan2(final_dir.y, final_dir.x)))
        else:
            aim_snap_deg = self.tank.rotation

        # Mise à jour de l'orientation du tank
        if aim_snap_deg != self.tank.rotation:
            self.tank.rotation = aim_snap_deg
            self.tank._update_rotation_sprite()

        # =====================================================================
        # 4. ARBITRAGE DU TIR DE CANON
        # =====================================================================
        should_shoot = False
        angle_diff = abs(self.tank.rotation - ideal_aim_angle)
        if angle_diff > 180.0:
            angle_diff = 360.0 - angle_diff

        # Conditions d'autorisation de tir :
        # - Alignement angulaire respecté
        # - Ligne de tir dégagée
        # - Cible à portée (< 650 px)
        # - Cible vulnérable (pas de bouclier)
        # - Cooldown canon disponible
        if (
            angle_diff <= self.aim_tolerance
            and has_los
            and dist_target <= 650.0
            and not target_invulnerable
            and self.tank.can_shoot()
        ):
            # En mode Easy, tir avec probabilité
            if self.difficulty == AIDifficulty.EASY:
                should_shoot = random.random() < 0.70
            else:
                should_shoot = True

        return final_dir, should_shoot
