"""Gestionnaire central d'assets (AssetManager) pour Tank War : Arena Duel.

Optimise les performances graphiques :
- Pré-chargement de toutes les textures au démarrage (.convert_alpha() / .convert()).
- Cache en mémoire pour éliminer tout accès disque durant la boucle de jeu à 60 FPS.
- Mise en cache intelligente des surfaces pivotées pour les chars et projectiles.
- Fallback procédural autonome si un fichier est absent.
"""

from __future__ import annotations
import math
from pathlib import Path
from typing import Optional
import pygame

from settings import ASSETS_DIR, MAPS_DIR, OBSTACLES_DIR


class AssetManager:
    """Gestionnaire singleton de ressources graphiques avec mise en cache."""

    _instance: Optional[AssetManager] = None

    def __new__(cls) -> AssetManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return

        self._initialized = True
        self.images: dict[str, pygame.Surface] = {}
        # Caches de rotations pour éviter les calculs trigonométriques redondants
        self._tank_rotation_cache: dict[tuple[str, int], pygame.Surface] = {}
        self._bullet_rotation_cache: dict[int, pygame.Surface] = {}

        self.preload_all()

    def preload_all(self) -> None:
        """Pré-charge l'ensemble des textures dans le cache mémoire."""
        # 1. Chars de combat
        self.images["tank_red"] = self._load_or_fallback(
            [ASSETS_DIR / "tanks" / "tank_red.png", ASSETS_DIR / "sprites" / "tanks" / "tank_red.png"],
            fallback_builder=lambda: self._create_tank_fallback("red")
        )
        self.images["tank_green"] = self._load_or_fallback(
            [ASSETS_DIR / "tanks" / "tank_green.png", ASSETS_DIR / "sprites" / "tanks" / "tank_green.png"],
            fallback_builder=lambda: self._create_tank_fallback("green")
        )

        # 2. Obstacles
        self.images["crate"] = self._load_or_fallback([OBSTACLES_DIR / "crate.png"])
        self.images["crate_damaged"] = self._load_or_fallback([OBSTACLES_DIR / "crate_damaged.png"])
        self.images["barrier_horizontal"] = self._load_or_fallback([OBSTACLES_DIR / "barrier_horizontal.png"])
        self.images["barrier_vertical"] = self._load_or_fallback([OBSTACLES_DIR / "barrier_vertical.png"])
        self.images["rock_large"] = self._load_or_fallback([OBSTACLES_DIR / "rock_large.png"])
        self.images["rock_small"] = self._load_or_fallback([OBSTACLES_DIR / "rock_small.png"])
        self.images["plant_cactus"] = self._load_or_fallback([OBSTACLES_DIR / "plant_cactus.png"])
        self.images["plant_bush"] = self._load_or_fallback([OBSTACLES_DIR / "plant_bush.png"])

        # 3. Projectiles
        self.images["bullet"] = self._load_or_fallback(
            [ASSETS_DIR / "projectiles" / "bullet.png", ASSETS_DIR / "sprites" / "projectiles" / "bullet.png"],
            fallback_builder=self._create_bullet_fallback
        )

        # 4. Carte et bordures
        self.images["desert_background"] = self._load_or_fallback([MAPS_DIR / "desert_background.png"], is_alpha=False)
        self.images["border_tile"] = self._load_or_fallback([MAPS_DIR / "border_tile.png"], is_alpha=False)

        # 5. Power-ups
        for pup in ["shield", "speed", "rapid_fire"]:
            paths = [
                ASSETS_DIR / "powerups" / f"{pup}.png",
                ASSETS_DIR / "sprites" / "powerups" / f"{pup}.png",
            ]
            self.images[f"powerup_{pup}"] = self._load_or_fallback(paths)

    def _load_or_fallback(
        self,
        candidate_paths: list[Path],
        fallback_builder=None,
        is_alpha: bool = True
    ) -> pygame.Surface:
        """Charge une image depuis les chemins possibles ou génère un fallback."""
        for p in candidate_paths:
            if p.exists() and p.is_file():
                try:
                    loaded = pygame.image.load(str(p))
                    if pygame.display.get_surface():
                        return loaded.convert_alpha() if is_alpha else loaded.convert()
                    return loaded
                except Exception:
                    pass

        if fallback_builder:
            return fallback_builder()

        surf = pygame.Surface((64, 64), pygame.SRCALPHA if is_alpha else 0)
        surf.fill((200, 150, 100))
        return surf

    def _create_tank_fallback(self, color_name: str) -> pygame.Surface:
        """Génère un fallback visuel pour un char."""
        surf = pygame.Surface((68, 52), pygame.SRCALPHA)
        color = (220, 60, 50) if color_name == "red" else (46, 204, 113)
        pygame.draw.rect(surf, (40, 40, 45), (4, 4, 58, 10), border_radius=3)
        pygame.draw.rect(surf, (40, 40, 45), (4, 38, 58, 10), border_radius=3)
        pygame.draw.rect(surf, color, (12, 10, 44, 32), border_radius=6)
        pygame.draw.circle(surf, (30, 30, 30), (32, 26), 12)
        pygame.draw.rect(surf, (40, 40, 40), (32, 23, 28, 6), border_radius=2)
        return surf

    def _create_bullet_fallback(self) -> pygame.Surface:
        """Génère un fallback visuel pour un obus."""
        surf = pygame.Surface((18, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (255, 200, 30), (0, 1, 18, 8))
        pygame.draw.ellipse(surf, (240, 60, 30), (10, 1, 8, 8))
        return surf

    def get_image(self, key: str) -> pygame.Surface:
        """Récupère une texture depuis le cache mémoire."""
        if key not in self.images:
            self.preload_all()
        return self.images.get(key, pygame.Surface((32, 32)))

    def get_rotated_tank(self, color_name: str, angle_deg: float) -> pygame.Surface:
        """Retourne la surface pré-pivotée d'un char depuis le cache de rotations."""
        key_color = color_name.lower()
        # Arrondi de l'angle au degré entier pour limiter le cache
        angle_key = int(round(angle_deg)) % 360
        cache_key = (key_color, angle_key)

        cached = self._tank_rotation_cache.get(cache_key)
        if cached is not None:
            return cached

        base_sprite = self.get_image(f"tank_{key_color}")
        rotated = pygame.transform.rotate(base_sprite, -angle_key)
        self._tank_rotation_cache[cache_key] = rotated
        return rotated

    def get_rotated_bullet(self, angle_deg: float) -> pygame.Surface:
        """Retourne la surface pré-pivotée d'un obus depuis le cache."""
        angle_key = int(round(angle_deg)) % 360
        cached = self._bullet_rotation_cache.get(angle_key)
        if cached is not None:
            return cached

        base_bullet = self.get_image("bullet")
        rotated = pygame.transform.rotate(base_bullet, -angle_key)
        self._bullet_rotation_cache[angle_key] = rotated
        return rotated


# Instance globale partagée
asset_manager = AssetManager()

