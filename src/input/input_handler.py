"""Gestionnaire des événements de saisie Pygame.

Capture les frappes de touches (ZQSD / Flèches et Espace) et génère
un objet PlayerCommand neutre.
"""

import pygame
from src.input.command import PlayerCommand


class InputHandler:
    """Interprète les entrées matérielles pour produire des commandes de jeu."""

    def __init__(self, player_id: str = "player_1") -> None:
        self.player_id = player_id
        self._sequence_counter = 0

    def process_event(self, event: pygame.event.Event) -> None:
        """Permet de réagir à des événements unitaires si nécessaire."""
        pass

    def poll_command(self) -> PlayerCommand:
        """Échantillonne l'état du clavier et génère un instantané d'action."""
        self._sequence_counter += 1
        keys = pygame.key.get_pressed()

        move = 0.0
        if keys[pygame.K_z] or keys[pygame.K_UP]:
            move += 1.0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            move -= 1.0

        rot = 0.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            rot += 1.0
        if keys[pygame.K_q] or keys[pygame.K_LEFT]:
            rot -= 1.0

        fire = bool(keys[pygame.K_SPACE])

        return PlayerCommand(
            player_id=self.player_id,
            sequence_number=self._sequence_counter,
            move_forward=move,
            rotate=rot,
            fire=fire
        )

