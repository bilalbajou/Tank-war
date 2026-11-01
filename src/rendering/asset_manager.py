"""Gestionnaire de chargement et de mise en cache des ressources visuelles (Sprites PNG).

Intègre un mécanisme de repli (fallback procédural) : si un sprite PNG
n'est pas encore présent sur le disque, une texture géométrique
appropriée est générée à la volée. Le jeu reste ainsi toujours exécutable.
"""

from pathlib import Path
from typing import Optional
import pygame

from src.core.config import GameConfig


class AssetManager:
    """Chargeur et cache des textures et polices."""

    _instance: Optional["AssetManager"] = None

    def __init__(self, assets_dir: Optional[Path] = None) -> None:
        self.assets_dir = assets_dir or GameConfig.ASSETS_DIR
        self.sprites_dir = self.assets_dir / "sprites"
        self._sprite_cache: dict[str, pygame.Surface] = {}
        self._font_cache: dict[str, pygame.font.Font] = {}

    @classmethod
    def get_instance(cls) -> "AssetManager":
        """Singleton accessor."""
        if cls._instance is None:
            cls._instance = AssetManager()
        return cls._instance

    def get_sprite(self, relative_path: str, fallback_size: tuple[int, int] = (64, 48), fallback_color: tuple[int, int, int] = (100, 100, 100)) -> pygame.Surface:
        """Récupère un sprite depuis le cache ou le charge depuis le disque."""
        if relative_path in self._sprite_cache:
            return self._sprite_cache[relative_path]

        full_path = self.sprites_dir / relative_path
        if full_path.exists() and full_path.is_file():
            try:
                surface = pygame.image.load(str(full_path)).convert_alpha()
                self._sprite_cache[relative_path] = surface
                return surface
            except pygame.error:
                pass

        # Génération d'une texture de substitution
        fallback_surface = self._create_procedural_fallback(fallback_size, fallback_color)
        self._sprite_cache[relative_path] = fallback_surface
        return fallback_surface

    def _create_procedural_fallback(self, size: tuple[int, int], color: tuple[int, int, int]) -> pygame.Surface:
        """Crée une surface de remplacement esthétique avec bordure."""
        surf = pygame.Surface(size, pygame.SRCALPHA)
        surf.fill(color)
        pygame.draw.rect(surf, (30, 30, 30), surf.get_rect(), width=2)
        return surf

    def get_font(self, size: int = 24, font_name: Optional[str] = None) -> pygame.font.Font:
        """Charge ou retourne une police de taille donnée."""
        key = f"{font_name}_{size}"
        if key in self._font_cache:
            return self._font_cache[key]

        font = pygame.font.SysFont("Segoe UI", size, bold=True)
        self._font_cache[key] = font
        return font

