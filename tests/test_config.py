"""Tests de la configuration globale."""

from src.core.config import GameConfig


def test_display_configuration():
    assert GameConfig.display.SCREEN_WIDTH == 1600
    assert GameConfig.display.SCREEN_HEIGHT == 900
    assert GameConfig.display.TARGET_FPS == 60


def test_network_configuration():
    assert GameConfig.network.MAX_PLAYERS == 2
    assert GameConfig.network.DEFAULT_PORT == 4242
    assert GameConfig.network.TICK_RATE == 60


def test_asset_paths_defined():
    assert GameConfig.BASE_DIR.exists()
    assert GameConfig.ASSETS_DIR.name == "assets"
    assert GameConfig.SPRITES_DIR.name == "sprites"

