"""Gestionnaire de projectiles (ProjectileManager) pour Tank War (Arena Duel).

Centralise l'apparition, la mise à jour, la détection des collisions
(murs, obstacles destructibles ou indestructibles, chars adverses)
et les effets visuels d'impact.
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Sequence
import random
import math
import pygame

from game.projectile import Projectile
from game.obstacle import Obstacle
from game.sound_manager import sound_manager
from game.effects import effects_manager

if TYPE_CHECKING:
    from players.tank import Tank
    from game.map import ArenaMap
    from game.game_state import MatchState


class ImpactParticle:
    """Particule d'étincelle ou d'éclat lors d'un impact de projectile."""

    def __init__(self, x: float, y: float, color: tuple[int, int, int]) -> None:
        self.position = pygame.Vector2(x, y)
        angle = random.uniform(0, math.tau)
        speed = random.uniform(60, 180)
        self.velocity = pygame.Vector2(math.cos(angle) * speed, math.sin(angle) * speed)
        self.lifetime = random.uniform(0.15, 0.25)
        self.age = 0.0
        self.color = color
        self.size = random.uniform(2.5, 4.5)

    def update(self, dt: float) -> bool:
        """Met à jour la particule. Retourne True si encore vivante."""
        self.age += dt
        self.position += self.velocity * dt
        self.size = max(0.5, self.size - (dt * 6.0))
        return self.age < self.lifetime

    def draw(self, surface: pygame.Surface) -> None:
        """Dessine l'éclat."""
        alpha_ratio = max(0.0, 1.0 - (self.age / self.lifetime))
        r, g, b = self.color
        pygame.draw.circle(
            surface,
            (r, g, b),
            (int(self.position.x), int(self.position.y)),
            int(self.size)
        )


class ProjectileManager:
    """Orchestrateur des tirs balistiques et de leurs conséquences physiques."""

    def __init__(self) -> None:
        self.projectiles: list[Projectile] = []
        self.particles: list[ImpactParticle] = []

    def spawn_projectile(self, tank: Tank) -> Optional[Projectile]:
        """Déclenche un tir depuis le canon du char si son rechargement le permet."""
        projectile = tank.shoot()
        if projectile:
            self.projectiles.append(projectile)
            # Effet sonore de tir et étincelle au bout du canon
            sound_manager.play_shoot()
            self._spawn_muzzle_flash(projectile.position, projectile.rotation)
        return projectile

    def _spawn_muzzle_flash(self, pos: pygame.Vector2, rotation_deg: float) -> None:
        """Génère un flash visuel à la sortie du canon."""
        flash_colors = [(255, 230, 100), (255, 120, 40)]
        for _ in range(4):
            col = random.choice(flash_colors)
            self.particles.append(ImpactParticle(pos.x, pos.y, col))

    def _spawn_impact_burst(self, pos: pygame.Vector2, is_tank: bool = False) -> None:
        """Génère une explosion d'éclats lors de l'impact."""
        colors = [(255, 80, 40), (255, 200, 60), (240, 240, 240)] if is_tank else [(200, 160, 90), (255, 210, 50)]
        count = 10 if is_tank else 6
        for _ in range(count):
            self.particles.append(ImpactParticle(pos.x, pos.y, random.choice(colors)))

    def update(
        self,
        dt: float,
        obstacles: Sequence[Obstacle],
        tanks: Sequence[Tank],
        bounds_rect: pygame.Rect,
        arena_map: Optional[ArenaMap] = None,
        match_state: Optional[MatchState] = None
    ) -> None:
        """Met à jour les trajectoires et résout les impacts."""
        # 1. Mise à jour des particules d'impact
        self.particles = [p for p in self.particles if p.update(dt)]

        # 2. Mise à jour et résolution des projectiles
        alive_projectiles: list[Projectile] = []

        for proj in self.projectiles:
            if not proj.is_alive:
                continue

            proj.update(dt)

            # A. Sortie des limites de l'arène
            if not bounds_rect.collidepoint(proj.position.x, proj.position.y):
                proj.is_alive = False
                effects_manager.spawn_impact(proj.position.x, proj.position.y, proj.rotation)
                sound_manager.play_collision()
                self._spawn_impact_burst(proj.position, is_tank=False)
                continue

            # B. Collision avec les obstacles physiques
            hit_obstacle = False
            for obs in obstacles:
                if obs.blocks_projectiles and obs.rect.colliderect(proj.hitbox):
                    proj.is_alive = False
                    hit_obstacle = True
                    effects_manager.spawn_impact(proj.position.x, proj.position.y, proj.rotation)
                    sound_manager.play_collision()
                    # Si l'obstacle est destructible (ex: caisse en bois), il encaisse les dégâts
                    if obs.destructible:
                        was_destroyed = obs.take_damage(proj.damage)
                        if was_destroyed:
                            sound_manager.play_crate_break()
                            if arena_map is not None:
                                arena_map.spawn_crate_debris(obs.rect.centerx, obs.rect.centery, count=16)
                    self._spawn_impact_burst(proj.position, is_tank=False)
                    break

            if hit_obstacle:
                continue

            # C. Collision avec les chars de combat (un tank ne peut PAS se toucher lui-même)
            hit_tank = False
            for tank in tanks:
                if tank.player_id == proj.owner_id:
                    # Règle absolue : immunité contre ses propres tirs
                    continue

                if tank.is_alive and tank.hitbox.colliderect(proj.hitbox):
                    proj.is_alive = False
                    hit_tank = True
                    effects_manager.spawn_impact(proj.position.x, proj.position.y, proj.rotation)
                    sound_manager.play_collision()
                    hit_registered = tank.take_damage(proj.damage)
                    if hit_registered:
                        if tank.vie <= 0:
                            sound_manager.play_explosion()
                            effects_manager.spawn_tank_explosion(tank.position.x, tank.position.y)
                        if match_state is not None:
                            match_state.register_hit(tank.player_id)
                    self._spawn_impact_burst(proj.position, is_tank=True)
                    break

            if proj.is_alive:
                alive_projectiles.append(proj)

        self.projectiles = alive_projectiles

    def draw(self, surface: pygame.Surface) -> None:
        """Dessine l'ensemble des projectiles en vol et les effets d'étincelles."""
        # Projectiles
        for proj in self.projectiles:
            proj.draw(surface)

        # Particules d'éclat
        for particle in self.particles:
            particle.draw(surface)

    def clear(self) -> None:
        """Supprime tous les projectiles et particules en cours."""
        self.projectiles.clear()
        self.particles.clear()
