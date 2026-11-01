"""Configuration globale du jeu Arena Duel (Tank War).

Centralise toutes les constantes géométriques, réseau, gameplay et de rendu.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DisplayConfig:
    """Paramètres d'affichage et de fenêtrage."""
    WINDOW_TITLE: str = "Tank War - Arena Duel"
    SCREEN_WIDTH: int = 1600
    SCREEN_HEIGHT: int = 900
    TARGET_FPS: int = 60
    VSYNC: bool = True


@dataclass(frozen=True)
class NetworkConfig:
    """Paramètres réseau (LAN Sockets TCP)."""
    DEFAULT_HOST: str = "127.0.0.1"
    DEFAULT_PORT: int = 4242
    MAX_PLAYERS: int = 2
    BUFFER_SIZE: int = 4096
    TICK_RATE: int = 60
    TIMEOUT_SECONDS: float = 5.0


@dataclass(frozen=True)
class TankConfig:
    """Caractéristiques physiques et mécaniques des tanks."""
    WIDTH: float = 64.0
    HEIGHT: float = 48.0
    MOVE_SPEED: float = 180.0         # Pixels par seconde
    ROTATION_SPEED: float = 120.0     # Degrés par seconde
    MAX_HEALTH: int = 100
    FIRE_COOLDOWN: float = 0.5        # Secondes entre deux tirs


@dataclass(frozen=True)
class ProjectileConfig:
    """Caractéristiques physiques des obus/projectiles."""
    RADIUS: float = 6.0
    SPEED: float = 450.0              # Pixels par seconde
    DAMAGE: int = 25
    MAX_LIFETIME: float = 3.0         # Secondes avant disparition


@dataclass(frozen=True)
class ArenaConfig:
    """Dimensions et propriétés de l'arène fixe."""
    WIDTH: int = 1600
    HEIGHT: int = 900
    BORDER_THICKNESS: int = 20


@dataclass(frozen=True)
class ColorPalette:
    """Palette de couleurs (thème désertique et HUD)."""
    # Environnement
    SAND: tuple[int, int, int] = (222, 198, 142)
    SAND_DARK: tuple[int, int, int] = (194, 168, 114)
    BORDER: tuple[int, int, int] = (90, 72, 48)
    
    # Éléments de décor
    CRATE: tuple[int, int, int] = (150, 105, 55)
    CRATE_OUTLINE: tuple[int, int, int] = (100, 70, 35)
    PLANT: tuple[int, int, int] = (68, 128, 62)
    BARRIER: tuple[int, int, int] = (140, 140, 140)
    
    # Joueurs & Projectiles
    PLAYER_ONE: tuple[int, int, int] = (52, 120, 246)    # Bleu
    PLAYER_TWO: tuple[int, int, int] = (235, 64, 52)     # Rouge
    PROJECTILE: tuple[int, int, int] = (25, 25, 25)
    
    # UI
    TEXT_WHITE: tuple[int, int, int] = (245, 245, 245)
    TEXT_MUTED: tuple[int, int, int] = (180, 180, 180)
    OVERLAY_BG: tuple[int, int, int] = (18, 18, 20)
    HEALTH_BAR_BG: tuple[int, int, int] = (60, 60, 60)
    HEALTH_BAR_FG: tuple[int, int, int] = (46, 204, 113)


class GameConfig:
    """Façade de configuration du jeu."""
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    ASSETS_DIR: Path = BASE_DIR / "assets"
    SPRITES_DIR: Path = ASSETS_DIR / "sprites"
    SOUNDS_DIR: Path = ASSETS_DIR / "sounds"
    FONTS_DIR: Path = ASSETS_DIR / "fonts"

    display: DisplayConfig = DisplayConfig()
    network: NetworkConfig = NetworkConfig()
    tank: TankConfig = TankConfig()
    projectile: ProjectileConfig = ProjectileConfig()
    arena: ArenaConfig = ArenaConfig()
    colors: ColorPalette = ColorPalette()

