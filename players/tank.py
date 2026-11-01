"""Modèle de Tank jouable pour Tank War (Arena Duel).

Gère la position vectorielle, la vitesse, la rotation 8-directions,
les 3 vies, les effets de power-ups (bouclier, vitesse, tir rapide),
les collisions physiques et le rendu à l'écran.
"""

from __future__ import annotations
import math
from pathlib import Path
from typing import Optional, Sequence
import pygame

from settings import (
    BASE_DIR,
    ASSETS_DIR,
    BORDER_THICKNESS,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    COLOR_SHADOW,
)
from players.controls import TankControls
from game.collision import CollisionHandler
from game.projectile import Projectile
from game.asset_manager import asset_manager


class Tank:
    """Représentation d'un char de combat contrôlé par un joueur."""

    # Dimensions physiques du châssis pour la hitbox de collision
    HITBOX_WIDTH = 50
    HITBOX_HEIGHT = 50

    def __init__(
        self,
        player_id: int,
        color_name: str,
        initial_position: tuple[float, float],
        initial_rotation: float = 0.0,
        controls: Optional[TankControls] = None,
        speed: float = 220.0,
        max_health: int = 3,
        fire_cooldown: float = 0.45,
        bullet_speed: float = 650.0,
        bullet_damage: int = 1
    ) -> None:
        self.player_id = player_id
        self.color_name = color_name.lower()
        self.base_speed = float(speed)
        self.vitesse = float(speed)
        self.vie = int(max_health)
        self.max_vie = int(max_health)

        # Balistique et cadence de tir
        self.fire_cooldown = float(fire_cooldown)
        self.current_cooldown = 0.0
        self.bullet_speed = float(bullet_speed)
        self.bullet_damage = int(bullet_damage)

        # Minuteurs d'effets de Power-Ups
        self.shield_timer = 0.0
        self.speed_timer = 0.0
        self.rapid_fire_timer = 0.0
        self.invulnerable_timer = 0.0

        # Position vectorielle précise (sub-pixel)
        self.position = pygame.Vector2(initial_position[0], initial_position[1])
        self.direction = pygame.Vector2(0.0, 0.0)
        self.rotation = float(initial_rotation)  # Degrés : 0 = Est, 90 = Sud, 180 = Ouest, 270 = Nord

        # Contrôleur assigné
        self.controls = controls

        # Chargement et conservation du sprite source original
        self.original_sprite = self._load_tank_sprite()
        self.sprite = self.original_sprite
        self.image = self.original_sprite.copy()

        # Hitbox de collision centrée
        self.hitbox = pygame.Rect(
            int(self.position.x - self.HITBOX_WIDTH // 2),
            int(self.position.y - self.HITBOX_HEIGHT // 2),
            self.HITBOX_WIDTH,
            self.HITBOX_HEIGHT
        )
        self.rect = self.image.get_rect(center=(int(self.position.x), int(self.position.y)))

        # Ombre portée
        self._shadow_surface = self._create_shadow_surface()

        # Applique l'orientation initiale
        self._update_rotation_sprite()

    @property
    def has_shield(self) -> bool:
        """Indique si un bouclier ou une invulnérabilité temporaire protège le char."""
        return self.shield_timer > 0.0 or self.invulnerable_timer > 0.0

    @property
    def effective_speed(self) -> float:
        """Vitesse réelle prenant en compte l'effet du power-up Vitesse Accrue."""
        return self.base_speed * (1.5 if self.speed_timer > 0.0 else 1.0)

    @property
    def effective_cooldown(self) -> float:
        """Délai de rechargement prenant en compte l'effet du power-up Tir Rapide."""
        return self.fire_cooldown * (0.5 if self.rapid_fire_timer > 0.0 else 1.0)

    def apply_powerup(self, powerup_type: str, duration: float) -> None:
        """Applique l'effet d'un bonus ramassé sur le tank."""
        ptype = str(powerup_type).lower()
        if "shield" in ptype:
            self.shield_timer = float(duration)
        elif "speed" in ptype:
            self.speed_timer = float(duration)
        elif "rapid" in ptype:
            self.rapid_fire_timer = float(duration)

    def respawn(self, position: tuple[float, float], rotation: float) -> None:
        """Réinitialise le char à sa base avec invulnérabilité temporaire."""
        self.position = pygame.Vector2(position[0], position[1])
        self.rotation = float(rotation)
        self.direction = pygame.Vector2(0.0, 0.0)
        self.vie = self.max_vie
        self.current_cooldown = 0.0
        self.invulnerable_timer = 1.0  # 1 seconde d'invulnérabilité au spawn
        self.shield_timer = 0.0
        self.speed_timer = 0.0
        self.rapid_fire_timer = 0.0
        self._update_rotation_sprite()
        self.hitbox.center = (int(self.position.x), int(self.position.y))
        self.rect.center = (int(self.position.x), int(self.position.y))

    def _load_tank_sprite(self) -> pygame.Surface:
        """Récupère le sprite pré-chargé en cache depuis l'AssetManager."""
        return asset_manager.get_image(f"tank_{self.color_name}")

    def _create_shadow_surface(self) -> pygame.Surface:
        """Crée une ombre portée ovale douce sous le char."""
        w, h = 64, 48
        shadow = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, COLOR_SHADOW, (0, 0, w, h))
        return shadow

    def _update_rotation_sprite(self) -> None:
        """Récupère le sprite pré-pivoté depuis le cache mémoire sans calcul redondant."""
        self.image = asset_manager.get_rotated_tank(self.color_name, self.rotation)
        self.rect = self.image.get_rect(center=(int(self.position.x), int(self.position.y)))

    def move(
        self,
        dt: float,
        obstacles: Sequence[pygame.Rect],
        bounds_rect: pygame.Rect,
        other_tank_rect: Optional[pygame.Rect] = None
    ) -> None:
        """Déplace le tank avec glissement fluide et mise à jour de la hitbox."""
        if self.direction.length_squared() == 0:
            return

        # Vitesse effective proportionnelle au delta-time
        self.vitesse = self.effective_speed
        velocity = self.direction * (self.vitesse * dt)

        # Résolution continue des collisions
        self.position, self.hitbox = CollisionHandler.move_and_slide(
            current_pos=self.position,
            velocity=velocity,
            hitbox_size=(self.HITBOX_WIDTH, self.HITBOX_HEIGHT),
            obstacle_rects=obstacles,
            bounds_rect=bounds_rect,
            other_tank_rect=other_tank_rect
        )

        self.rect.center = (int(self.position.x), int(self.position.y))

    def can_shoot(self) -> bool:
        """Vérifie si le tank est opérationnel et si le rechargement est terminé."""
        return self.is_alive and self.current_cooldown <= 0.0

    def get_cannon_tip_position(self) -> pygame.Vector2:
        """Calcule la position exacte de l'extrémité du canon (muzzle) selon l'orientation."""
        rad = math.radians(self.rotation)
        offset_distance = 38.0
        muzzle_x = self.position.x + (math.cos(rad) * offset_distance)
        muzzle_y = self.position.y + (math.sin(rad) * offset_distance)
        return pygame.Vector2(muzzle_x, muzzle_y)

    def shoot(self) -> Optional[Projectile]:
        """Génère un nouveau projectile à la bouche du canon s'il est prêt à tirer."""
        if not self.can_shoot():
            return None

        # Réinitialisation du délai de rechargement avec bonus éventuel
        self.current_cooldown = self.effective_cooldown

        muzzle_pos = self.get_cannon_tip_position()
        return Projectile(
            owner_id=self.player_id,
            start_position=(muzzle_pos.x, muzzle_pos.y),
            rotation=self.rotation,
            speed=self.bullet_speed,
            damage=self.bullet_damage
        )

    def update(
        self,
        dt: float,
        obstacles: Sequence[pygame.Rect],
        bounds_rect: Optional[pygame.Rect] = None,
        other_tank_rect: Optional[pygame.Rect] = None
    ) -> None:
        """Met à jour les entrées, l'orientation, le déplacement et les timers du tank."""
        if bounds_rect is None:
            bounds_rect = pygame.Rect(
                BORDER_THICKNESS,
                BORDER_THICKNESS,
                SCREEN_WIDTH - 2 * BORDER_THICKNESS,
                SCREEN_HEIGHT - 2 * BORDER_THICKNESS
            )

        # Décompte des minuteurs
        if self.current_cooldown > 0.0:
            self.current_cooldown = max(0.0, self.current_cooldown - dt)
        if self.shield_timer > 0.0:
            self.shield_timer = max(0.0, self.shield_timer - dt)
        if self.speed_timer > 0.0:
            self.speed_timer = max(0.0, self.speed_timer - dt)
        if self.rapid_fire_timer > 0.0:
            self.rapid_fire_timer = max(0.0, self.rapid_fire_timer - dt)
        if self.invulnerable_timer > 0.0:
            self.invulnerable_timer = max(0.0, self.invulnerable_timer - dt)

        # 1. Échantillonnage des contrôles pour obtenir la direction
        if self.controls:
            movement_vector = self.controls.get_movement_vector()
            if movement_vector.length_squared() > 0:
                self.direction = movement_vector
                
                angle_rad = math.atan2(self.direction.y, self.direction.x)
                angle_deg = math.degrees(angle_rad) % 360.0
                
                if angle_deg != self.rotation:
                    self.rotation = angle_deg
                    self._update_rotation_sprite()
            else:
                self.direction = pygame.Vector2(0.0, 0.0)

        # 2. Application du déplacement et des collisions
        self.move(dt, obstacles, bounds_rect, other_tank_rect)

    def draw(self, surface: pygame.Surface) -> None:
        """Dessine l'ombre, le sprite du tank, le bouclier énergétique et la jauge."""
        # 1. Ombre portée sous le tank
        shadow_rect = self._shadow_surface.get_rect(center=(int(self.position.x + 3), int(self.position.y + 4)))
        surface.blit(self._shadow_surface, shadow_rect)

        # 2. Effet visuel du boost de vitesse (traînées sous les chenilles)
        if self.speed_timer > 0.0 and self.direction.length_squared() > 0:
            trail_pos = self.position - (self.direction * 18.0)
            pygame.draw.circle(surface, (255, 230, 80, 150), (int(trail_pos.x), int(trail_pos.y)), 6)

        # 3. Sprite principal du char
        surface.blit(self.image, self.rect)

        # 4. Bulle de bouclier énergétique protectrice
        if self.has_shield:
            shield_radius = 38
            shield_surf = pygame.Surface((shield_radius * 2 + 4, shield_radius * 2 + 4), pygame.SRCALPHA)
            # Dôme énergétique translucide
            pygame.draw.circle(shield_surf, (80, 200, 255, 60), (shield_radius + 2, shield_radius + 2), shield_radius)
            # Anneau extérieur lumineux
            pygame.draw.circle(shield_surf, (150, 230, 255, 180), (shield_radius + 2, shield_radius + 2), shield_radius, 3)
            shield_rect = shield_surf.get_rect(center=(int(self.position.x), int(self.position.y)))
            surface.blit(shield_surf, shield_rect)

        # 5. Mini barre de santé et indicateur de rechargement
        self._draw_health_bar(surface)

    def _draw_health_bar(self, surface: pygame.Surface) -> None:
        """Dessine les 3 pips de vie au-dessus du tank."""
        pip_w = 14
        pip_h = 5
        spacing = 3
        total_w = (pip_w * self.max_vie) + (spacing * (self.max_vie - 1))
        start_x = int(self.position.x - total_w // 2)
        bar_y = int(self.position.y - 36)

        # 3 blocs de vie distincts
        for i in range(self.max_vie):
            pip_x = start_x + i * (pip_w + spacing)
            bg_rect = pygame.Rect(pip_x, bar_y, pip_w, pip_h)
            pygame.draw.rect(surface, (30, 30, 30), bg_rect, border_radius=2)
            if i < self.vie:
                fill_color = (231, 76, 60) if self.color_name == "red" else (46, 204, 113)
                pygame.draw.rect(surface, fill_color, bg_rect, border_radius=2)
            pygame.draw.rect(surface, (15, 15, 15), bg_rect, width=1, border_radius=2)

        # Indicateur discret de rechargement sous les vies
        if self.current_cooldown > 0.0:
            reload_ratio = 1.0 - (self.current_cooldown / self.effective_cooldown)
            reload_w = int(total_w * reload_ratio)
            pygame.draw.rect(surface, (255, 215, 0), (start_x, bar_y + pip_h + 2, reload_w, 2))

    def take_damage(self, amount: int = 1) -> bool:
        """Inflige des dégâts (retire 1 vie). Retourne True si les PV ont diminué."""
        if self.has_shield:
            # Le bouclier absorbe l'impact !
            return False

        self.vie = max(0, self.vie - amount)
        return True

    def heal(self, amount: int = 1) -> None:
        """Restaure des points de vie au tank."""
        self.vie = min(self.max_vie, self.vie + amount)

    @property
    def is_alive(self) -> bool:
        """Vérifie si le tank est toujours opérationnel."""
        return self.vie > 0
