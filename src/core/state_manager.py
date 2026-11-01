"""Gestionnaire d'états du jeu (Finite State Machine).

Permet d'isoler la logique de chaque écran : Menu, Salon Réseau, Partie en cours, Fin de partie.
"""

from enum import Enum, auto
from typing import Callable, Optional


class GameState(Enum):
    """Énumération des états possibles de l'application."""
    MENU = auto()
    LOBBY = auto()
    PLAYING = auto()
    GAME_OVER = auto()


class StateManager:
    """Contrôleur de transitions d'état."""

    def __init__(self, initial_state: GameState = GameState.MENU) -> None:
        self._current_state: GameState = initial_state
        self._listeners: list[Callable[[GameState, GameState], None]] = []

    @property
    def current_state(self) -> GameState:
        """Retourne l'état actuel du jeu."""
        return self._current_state

    def subscribe(self, callback: Callable[[GameState, GameState], None]) -> None:
        """Enregistre un écouteur appelé lors des changements d'état (ancien_état, nouvel_état)."""
        self._listeners.append(callback)

    def change_state(self, new_state: GameState) -> None:
        """Bascule vers un nouvel état si différent de l'actuel."""
        if new_state == self._current_state:
            return

        old_state = self._current_state
        self._current_state = new_state

        for listener in self._listeners:
            listener(old_state, new_state)

    def is_in(self, state: GameState) -> bool:
        """Vérifie si le jeu se trouve dans un état donné."""
        return self._current_state == state

