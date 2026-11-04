"""Bridge de compatibilité vers assets.asset_manager.

Toutes les fonctionnalités de gestion centralisée des ressources ont été consolidées
dans assets/asset_manager.py pour garantir la portabilité multiplateforme et la compatibilité PyInstaller.
"""

from assets.asset_manager import (
    AssetManager,
    asset_manager,
    PROJECT_ROOT,
    ASSETS_DIR,
    MAPS_DIR,
    OBSTACLES_DIR,
    SPRITES_DIR,
    SOUNDS_DIR,
    FONTS_DIR,
    ICONS_DIR,
    POWERUPS_DIR,
    TANKS_DIR,
    PROJECTILES_DIR,
)

__all__ = [
    "AssetManager",
    "asset_manager",
    "PROJECT_ROOT",
    "ASSETS_DIR",
    "MAPS_DIR",
    "OBSTACLES_DIR",
    "SPRITES_DIR",
    "SOUNDS_DIR",
    "FONTS_DIR",
    "ICONS_DIR",
    "POWERUPS_DIR",
    "TANKS_DIR",
    "PROJECTILES_DIR",
]
