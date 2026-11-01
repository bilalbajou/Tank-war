"""Gestionnaire d'état de match et de progression (GameState) pour Tank War.

Règles de jeu :
- 3 vies par joueur par manche.
- 1 coup au but = -1 vie.
- Élimination (0 vie) = +1 point pour l'adversaire et réapparition des deux chars.
- Premier à 5 points = Victoire.
- Durée max = 90 secondes. Si le temps expire : le meilleur score gagne.
- En cas d'égalité à 90s : déclenchement de la Mort Subite (le premier point marqué l'emporte).

La logique est entièrement découplée de l'affichage (testable en pur Python).
"""

from dataclasses import dataclass
from typing import Optional


class MatchState:
    """Arbitre logique et chronomètre d'une partie de Tank War."""

    DEFAULT_TARGET_SCORE = 5
    DEFAULT_MATCH_DURATION = 90.0
    DEFAULT_LIVES_PER_ROUND = 3

    def __init__(
        self,
        target_score: int = DEFAULT_TARGET_SCORE,
        match_duration: float = DEFAULT_MATCH_DURATION,
        lives_per_round: int = DEFAULT_LIVES_PER_ROUND
    ) -> None:
        self.target_score = target_score
        self.max_duration = float(match_duration)
        self.lives_per_round = lives_per_round

        # Scores des joueurs
        self.p1_score = 0
        self.p2_score = 0

        # Vies restantes pour la manche en cours
        self.p1_lives = self.lives_per_round
        self.p2_lives = self.lives_per_round

        # Chronomètre
        self.time_remaining = float(self.max_duration)
        self.is_sudden_death = False

        # Fin de partie
        self.is_game_over = False
        self.winner_id: Optional[int] = None
        self.win_reason: str = ""

        # Indicateur de réapparition
        self.respawn_needed = False

    def get_lives(self, player_id: int) -> int:
        """Retourne le nombre de vies restantes d'un joueur."""
        return self.p1_lives if player_id == 1 else self.p2_lives

    def get_score(self, player_id: int) -> int:
        """Retourne le score actuel d'un joueur."""
        return self.p1_score if player_id == 1 else self.p2_score

    def register_hit(self, victim_id: int) -> bool:
        """Enregistre un coup porté par un projectile adverse.
        
        Retourne True si le coup a entraîné l'élimination du joueur (perte de la manche).
        """
        if self.is_game_over:
            return False

        if victim_id == 1:
            self.p1_lives = max(0, self.p1_lives - 1)
            is_eliminated = (self.p1_lives == 0)
        else:
            self.p2_lives = max(0, self.p2_lives - 1)
            is_eliminated = (self.p2_lives == 0)

        if is_eliminated:
            # Attribution du point à l'adversaire
            killer_id = 2 if victim_id == 1 else 1
            if killer_id == 1:
                self.p1_score += 1
            else:
                self.p2_score += 1

            # Vérification des conditions de victoire
            killer_score = self.get_score(killer_id)
            if self.is_sudden_death:
                self.winner_id = killer_id
                self.is_game_over = True
                self.win_reason = "Victoire en Mort Subite !"
            elif killer_score >= self.target_score:
                self.winner_id = killer_id
                self.is_game_over = True
                self.win_reason = f"Premier à {self.target_score} points !"
            else:
                # Réapparition des deux chars pour la manche suivante
                self.respawn_needed = True
                self.p1_lives = self.lives_per_round
                self.p2_lives = self.lives_per_round

            return True

        return False

    def update(self, dt: float) -> None:
        """Fait défiler le chronomètre et surveille les limites de temps."""
        if self.is_game_over:
            return

        # Le temps ne s'écoule pas en mort subite (jusqu'à la première élimination)
        if not self.is_sudden_death:
            self.time_remaining = max(0.0, self.time_remaining - dt)

            if self.time_remaining <= 0.0:
                self._handle_time_expiration()

    def _handle_time_expiration(self) -> None:
        """Traite l'expiration des 90 secondes."""
        if self.p1_score > self.p2_score:
            self.winner_id = 1
            self.is_game_over = True
            self.win_reason = "Temps écoulé : Meilleur score !"
        elif self.p2_score > self.p1_score:
            self.winner_id = 2
            self.is_game_over = True
            self.win_reason = "Temps écoulé : Meilleur score !"
        else:
            # Égalité parfaite à la fin du temps réglementaire : Mort Subite !
            self.is_sudden_death = True
            self.p1_lives = 1  # 1 seule vie en mort subite pour un suspense maximal
            self.p2_lives = 1
            self.respawn_needed = True

    def acknowledge_respawn(self) -> None:
        """Confirme que la réapparition sur la carte a été effectuée."""
        self.respawn_needed = False

    def reset(self) -> None:
        """Réinitialise intégralement la partie."""
        self.p1_score = 0
        self.p2_score = 0
        self.p1_lives = self.lives_per_round
        self.p2_lives = self.lives_per_round
        self.time_remaining = float(self.max_duration)
        self.is_sudden_death = False
        self.is_game_over = False
        self.winner_id = None
        self.win_reason = ""
        self.respawn_needed = False

