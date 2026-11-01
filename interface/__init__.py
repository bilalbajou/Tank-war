"""Package interface : Menus, écrans, composants, HUD et Lobby pour Tank War."""

from interface.hud import HUD
from interface.scoreboard import Scoreboard
from interface.components import UIButton, UITextInput, draw_cartoon_panel
from interface.menu import MainMenu
from interface.lobby import LobbyScreen
from interface.screens import HostScreen, JoinScreen, PauseOverlay, GameOverOverlay

__all__ = [
    "HUD",
    "Scoreboard",
    "UIButton",
    "UITextInput",
    "draw_cartoon_panel",
    "MainMenu",
    "LobbyScreen",
    "HostScreen",
    "JoinScreen",
    "PauseOverlay",
    "GameOverOverlay",
]
