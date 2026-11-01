"""Gestion des obstacles et décorations de la carte.

Fournit :
1. Barrières métalliques : bloquent les tanks et projectiles, indestructibles.
2. Caisses en bois : bloquent les déplacements, destructibles par projectiles, disparaissent à la destruction.
3. Décorations végétales : ne bloquent ni les déplacements ni les tirs.
4. Particules de débris pour l'animation de destruction des caisses.
"""

from enum import Enum, auto
from typing import Optional
import random
import math
import pygame

from settings import (
    OBSTACLES_DIR,
    COLOR_SHADOW,
    CRATE_SIZE,
    BARRIER_H_WIDTH,
    BARRIER_H_HEIGHT,
    BARRIER_V_WIDTH,
    BARRIER_V_HEIGHT,
    ROCK_LARGE_SIZE,
    ROCK_SMALL_SIZE,
    CACTUS_SIZE,
    BUSH_SIZE,
)
from game.asset_manager import asset_manager


class ObstacleType(Enum):
    """Types d'obstacles physiques."""
    CRATE = auto()
    BARRIER_HORIZONTAL = auto()
    BARRIER_VERTICAL = auto()
    ROCK_LARGE = auto()
    ROCK_SMALL = auto()
    BORDER_WALL = auto()


class DecorationType(Enum):
    """Types d'éléments décoratifs (non-bloquants)."""
    CACTUS = auto()
    BUSH = auto()


class DebrisParticle:
    """Particule d'éclat de bois / débris pour l'animation de destruction d'une caisse."""

    def __init__(self, x: float, y: float) -> None:
        self.position = pygame.Vector2(x, y)
        angle = random.uniform(0, math.tau)
        speed = random.uniform(80, 240)
        self.velocity = pygame.Vector2(math.cos(angle) * speed, math.sin(angle) * speed)
        
        # Dimensions de l'éclat de bois
        self.width = random.randint(6, 14)
        self.height = random.randint(3, 7)
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-360, 360)
        
        # Teintes de bois cartoon
        wood_tones = [
            (184, 125, 75),  # Chêne doré
            (138, 88, 48),   # Bois foncé
            (212, 152, 98),  # Latte claire
            (95, 60, 30),    # Écorce
        ]
        self.color = random.choice(wood_tones)
        self.lifetime = random.uniform(0.35, 0.55)
        self.age = 0.0

    def update(self, dt: float) -> bool:
        """Met à jour le débris avec frottement dans l'air. Retourne True si encore actif."""
        self.age += dt
        if self.age >= self.lifetime:
            return False

        # Ralentissement progressif (friction)
        self.velocity *= max(0.0, 1.0 - (dt * 3.5))
        self.position += self.velocity * dt
        self.rotation += self.rot_speed * dt
        return True

    def draw(self, surface: pygame.Surface) -> None:
        """Affiche le morceau de bois orienté."""
        if self.age >= self.lifetime:
            return

        # Surface du débris
        chunk_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        chunk_surf.fill(self.color)
        pygame.draw.rect(chunk_surf, (35, 20, 10), chunk_surf.get_rect(), width=1)

        # Rotation
        rotated_surf = pygame.transform.rotate(chunk_surf, self.rotation)
        new_rect = rotated_surf.get_rect(center=(int(self.position.x), int(self.position.y)))
        surface.blit(rotated_surf, new_rect)


class Obstacle:
    """Obstacle physique dans l'arène de combat."""

    def __init__(
        self,
        obstacle_type: ObstacleType,
        center_x: int,
        center_y: int,
        sprite_filename: Optional[str] = None,
        destructible: bool = False,
        blocks_movement: bool = True,
        blocks_projectiles: bool = True,
        health: int = 100
    ) -> None:
        self.obstacle_type = obstacle_type
        self.destructible = destructible
        self._blocks_movement = blocks_movement
        self._blocks_projectiles = blocks_projectiles
        self.health = health
        self.max_health = health
        self.is_alive = True

        # Résolution de la taille et du fichier sprite selon le type
        width, height, default_filename = self._resolve_dimensions_and_file(obstacle_type)
        self.width = width
        self.height = height
        self.sprite_filename = sprite_filename or default_filename

        # Rectangle Pygame centré pour la détection précise des collisions
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = (center_x, center_y)

        # Chargement de la texture PNG transparente
        self.image = self._load_sprite(self.sprite_filename, (width, height))
        self._shadow_surface = self._create_shadow_surface()

    @property
    def blocks_movement(self) -> bool:
        """Ne bloque les déplacements que tant que l'obstacle est intact."""
        return self._blocks_movement and self.is_alive

    @property
    def blocks_projectiles(self) -> bool:
        """Ne bloque les projectiles que tant que l'obstacle est intact."""
        return self._blocks_projectiles and self.is_alive

    def _resolve_dimensions_and_file(self, obs_type: ObstacleType) -> tuple[int, int, str]:
        """Détermine les dimensions et le sprite par défaut."""
        if obs_type == ObstacleType.CRATE:
            return (CRATE_SIZE, CRATE_SIZE, "crate.png")
        elif obs_type == ObstacleType.BARRIER_HORIZONTAL:
            return (BARRIER_H_WIDTH, BARRIER_H_HEIGHT, "barrier_horizontal.png")
        elif obs_type == ObstacleType.BARRIER_VERTICAL:
            return (BARRIER_V_WIDTH, BARRIER_V_HEIGHT, "barrier_vertical.png")
        elif obs_type == ObstacleType.ROCK_LARGE:
            return (ROCK_LARGE_SIZE, ROCK_LARGE_SIZE, "rock_large.png")
        elif obs_type == ObstacleType.ROCK_SMALL:
            return (ROCK_SMALL_SIZE, ROCK_SMALL_SIZE, "rock_small.png")
        else:
            return (32, 32, "crate.png")

    def _load_sprite(self, filename: str, size: tuple[int, int]) -> pygame.Surface:
        """Charge le sprite depuis l'AssetManager ou depuis le disque en cache."""
        key = filename.replace(".png", "")
        img = asset_manager.get_image(key)
        if img and img.get_size() == size:
            return img

        path = OBSTACLES_DIR / filename
        if path.exists() and path.is_file():
            try:
                loaded = pygame.image.load(str(path)).convert_alpha()
                if loaded.get_size() != size:
                    loaded = pygame.transform.smoothscale(loaded, size)
                return loaded
            except pygame.error:
                pass

        # Fallback de secours
        fallback = pygame.Surface(size, pygame.SRCALPHA)
        fallback.fill((160, 120, 80))
        pygame.draw.rect(fallback, (40, 30, 20), fallback.get_rect(), 2)
        return fallback

    def _create_shadow_surface(self) -> pygame.Surface:
        """Génère une ombre portée douce sous l'obstacle pour créer du volume."""
        shadow_w = self.width + 6
        shadow_h = self.height + 6
        shadow = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
        shadow_rect = pygame.Rect(4, 4, self.width - 2, self.height - 2)
        pygame.draw.rect(shadow, COLOR_SHADOW, shadow_rect, border_radius=6)
        return shadow

    def take_damage(self, amount: int) -> bool:
        """Applique des dégâts si destructible. Retourne True si détruit lors de ce tir."""
        if not self.destructible or not self.is_alive:
            return False

        self.health = max(0, self.health - amount)

        if self.health <= 0:
            self.is_alive = False
            return True

        # Remplacement par le sprite endommagé si la caisse est affaiblie
        if self.health <= self.max_health * 0.6:
            self.image = self._load_sprite("crate_damaged.png", (self.width, self.height))

        return False

    def draw(self, surface: pygame.Surface) -> None:
        """Dessine l'ombre puis le sprite transparent de l'obstacle si vivant."""
        if not self.is_alive:
            return
        # 1. Ombre portée légèrement décalée
        surface.blit(self._shadow_surface, (self.rect.left + 2, self.rect.top + 3))
        # 2. Sprite principal
        surface.blit(self.image, self.rect.topleft)


class Decoration:
    """Élément de décor végétal ou visuel qui NE bloque PAS les déplacements."""

    def __init__(
        self,
        decoration_type: DecorationType,
        center_x: int,
        center_y: int,
        sprite_filename: Optional[str] = None
    ) -> None:
        self.decoration_type = decoration_type
        self.blocks_movement = False
        self.blocks_projectiles = False

        if decoration_type == DecorationType.CACTUS:
            self.width, self.height = CACTUS_SIZE, CACTUS_SIZE
            filename = sprite_filename or "plant_cactus.png"
        else:
            self.width, self.height = BUSH_SIZE, BUSH_SIZE
            filename = sprite_filename or "plant_bush.png"

        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.rect.center = (center_x, center_y)

        self.image = self._load_sprite(filename, (self.width, self.height))
        self._shadow_surface = self._create_shadow_surface()

    def _load_sprite(self, filename: str, size: tuple[int, int]) -> pygame.Surface:
        """Charge le sprite de la plante depuis l'AssetManager ou depuis le disque."""
        key = filename.replace(".png", "")
        img = asset_manager.get_image(key)
        if img and img.get_size() == size:
            return img

        path = OBSTACLES_DIR / filename
        if path.exists() and path.is_file():
            try:
                loaded = pygame.image.load(str(path)).convert_alpha()
                if loaded.get_size() != size:
                    loaded = pygame.transform.smoothscale(loaded, size)
                return loaded
            except pygame.error:
                pass

        fallback = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.circle(fallback, (60, 180, 80), (size[0] // 2, size[1] // 2), size[0] // 3)
        return fallback

    def _create_shadow_surface(self) -> pygame.Surface:
        """Ombre circulaire douce pour la plante."""
        shadow = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        cx, cy = self.width // 2, self.height // 2
        pygame.draw.ellipse(shadow, COLOR_SHADOW, (cx - 16, cy + 4, 32, 14))
        return shadow

    def draw(self, surface: pygame.Surface) -> None:
        """Affiche la décoration sur la surface de jeu."""
        surface.blit(self._shadow_surface, self.rect.topleft)
        surface.blit(self.image, self.rect.topleft)
