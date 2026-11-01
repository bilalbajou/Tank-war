"""Système de bonus (Power-Ups) pour Tank War (Arena Duel).

Gère 3 types de power-ups :
1. Bouclier temporaire (absorbe les tirs adverses).
2. Vitesse accrue (+50% de vitesse de déplacement).
3. Tir rapide (cadence de tir doublée / cooldown divisé par deux).
"""

from enum import Enum
from pathlib import Path
from typing import Optional, Sequence
import random
import math
import pygame

from settings import ASSETS_DIR
from game.sound_manager import sound_manager


class PowerUpType(str, Enum):
    """Types de bonus disponibles dans l'arène."""
    SHIELD = "shield"
    SPEED = "speed"
    RAPID_FIRE = "rapid_fire"


class PowerUp:
    """Représentation d'un bonus ramassable au sol."""

    SIZE = 36

    def __init__(
        self,
        powerup_type: PowerUpType,
        position: tuple[float, float],
        duration: float = 8.0,
        lifetime: float = 18.0
    ) -> None:
        self.powerup_type = powerup_type
        self.position = pygame.Vector2(position[0], position[1])
        self.duration = float(duration)      # Durée du buff une fois ramassé
        self.lifetime = float(lifetime)      # Temps avant disparition s'il n'est pas ramassé
        self.age = 0.0
        self.is_collected = False

        # Hitbox de ramassage centrée
        self.rect = pygame.Rect(0, 0, self.SIZE, self.SIZE)
        self.rect.center = (int(self.position.x), int(self.position.y))

        # Chargement de la texture
        self.sprite = self._load_sprite()

    def _load_sprite(self) -> pygame.Surface:
        """Charge le sprite PNG transparent du bonus."""
        candidate_paths = [
            ASSETS_DIR / "sprites" / "powerups" / f"{self.powerup_type.value}.png",
            ASSETS_DIR / "powerups" / f"{self.powerup_type.value}.png",
        ]
        for path in candidate_paths:
            if path.exists() and path.is_file():
                try:
                    return pygame.image.load(str(path)).convert_alpha()
                except pygame.error:
                    pass

        # Fallback vectoriel
        surf = pygame.Surface((self.SIZE, self.SIZE), pygame.SRCALPHA)
        color = (52, 152, 219) if self.powerup_type == PowerUpType.SHIELD else (
            (241, 196, 15) if self.powerup_type == PowerUpType.SPEED else (231, 76, 60)
        )
        pygame.draw.circle(surf, color, (self.SIZE // 2, self.SIZE // 2), self.SIZE // 2 - 2)
        pygame.draw.circle(surf, (255, 255, 255), (self.SIZE // 2, self.SIZE // 2), self.SIZE // 2 - 2, 2)
        return surf

    def update(self, dt: float) -> bool:
        """Met à jour le temps de vie. Retourne True si encore actif."""
        self.age += dt
        return self.age < self.lifetime and not self.is_collected

    def draw(self, surface: pygame.Surface) -> None:
        """Dessine le power-up avec animation de flottement et halo d'énergie."""
        if self.is_collected:
            return

        # Flottement vertical sinusoïdal
        bobbing_y = math.sin(self.age * 4.0) * 4.0
        draw_pos = (self.rect.left, int(self.rect.top + bobbing_y))

        # Halo d'aura lumineux
        glow_size = int(self.SIZE + math.sin(self.age * 6.0) * 4.0)
        glow_surf = pygame.Surface((glow_size + 8, glow_size + 8), pygame.SRCALPHA)
        glow_color = (100, 200, 255, 50) if self.powerup_type == PowerUpType.SHIELD else (
            (255, 230, 100, 50) if self.powerup_type == PowerUpType.SPEED else (255, 120, 80, 50)
        )
        pygame.draw.circle(glow_surf, glow_color, (glow_surf.get_width() // 2, glow_surf.get_height() // 2), glow_size // 2)
        glow_rect = glow_surf.get_rect(center=(self.rect.centerx, int(self.rect.centery + bobbing_y)))
        surface.blit(glow_surf, glow_rect)

        # Sprite principal
        surface.blit(self.sprite, draw_pos)


class PowerUpManager:
    """Gestionnaire de l'apparition et du ramassage des power-ups dans l'arène."""

    # Emplacements tactiques stratégiques dégagés
    SPAWN_LOCATIONS = [
        (800, 180),   # Couloir Nord
        (800, 720),   # Couloir Sud
        (460, 450),   # Ouest (près de la base P1)
        (1140, 450),  # Est (près de la base P2)
        (800, 450),   # Centre exact de l'arène
    ]

    def __init__(self, spawn_interval: float = 12.0, max_active: int = 2) -> None:
        self.spawn_interval = float(spawn_interval)
        self.max_active = max_active
        self.spawn_timer = 2.0  # Premier bonus après 2 secondes de jeu
        self.active_powerups: list[PowerUp] = []

    def spawn_powerup(
        self,
        powerup_type: Optional[PowerUpType] = None,
        position: Optional[tuple[float, float]] = None
    ) -> PowerUp:
        """Génère un bonus sur la carte."""
        ptype = powerup_type or random.choice(list(PowerUpType))
        pos = position or random.choice(self.SPAWN_LOCATIONS)

        powerup = PowerUp(powerup_type=ptype, position=pos)
        self.active_powerups.append(powerup)
        return powerup

    def update(self, dt: float, tanks: Sequence) -> list[tuple[int, PowerUpType]]:
        """Met à jour les bonus et vérifie les collectes par les chars.
        
        Retourne la liste des événements de collecte (player_id, powerup_type).
        """
        collected_events: list[tuple[int, PowerUpType]] = []

        # 1. Gestion du cycle de spawn
        self.spawn_timer -= dt
        if self.spawn_timer <= 0.0:
            self.spawn_timer = self.spawn_interval
            if len(self.active_powerups) < self.max_active:
                # Trouve un spot inoccupé
                available_spots = [
                    spot for spot in self.SPAWN_LOCATIONS
                    if not any(p.position.distance_to(pygame.Vector2(spot)) < 40 for p in self.active_powerups)
                ]
                if available_spots:
                    self.spawn_powerup(position=random.choice(available_spots))

        # 2. Mise à jour et vérification du ramassage
        surviving_powerups: list[PowerUp] = []
        for p in self.active_powerups:
            if not p.update(dt):
                continue

            # Vérification de collision avec les chars vivants
            was_picked_up = False
            for tank in tanks:
                if tank.is_alive and tank.hitbox.colliderect(p.rect):
                    tank.apply_powerup(p.powerup_type, p.duration)
                    p.is_collected = True
                    was_picked_up = True
                    collected_events.append((tank.player_id, p.powerup_type))
                    sound_manager.play_powerup()
                    break

            if not was_picked_up and not p.is_collected:
                surviving_powerups.append(p)

        self.active_powerups = surviving_powerups
        return collected_events

    def draw(self, surface: pygame.Surface) -> None:
        """Affiche l'ensemble des bonus actifs."""
        for p in self.active_powerups:
            p.draw(surface)

    def clear(self) -> None:
        """Vide tous les power-ups lors d'une réinitialisation de partie."""
        self.active_powerups.clear()
        self.spawn_timer = 2.0

