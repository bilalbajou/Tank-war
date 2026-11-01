"""Carte 2D de combat en arène désertique (Arena Duel).

Gère le sol sablonneux, les bordures de l'arène, les obstacles physiques (Rects)
et les décorations végétales non-bloquantes.
"""

from typing import Optional
import pygame

from settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    BORDER_THICKNESS,
    MAPS_DIR,
    COLOR_BORDER_WALL,
    COLOR_BORDER_INNER,
    COLOR_SAND,
    PLAYER_1_SPAWN,
    PLAYER_2_SPAWN,
)
from game.obstacle import Obstacle, ObstacleType, Decoration, DecorationType, DebrisParticle
from game.asset_manager import asset_manager


class ArenaMap:
    """Gestionnaire de la carte désertique fixe et de ses éléments."""

    def __init__(self, width: int = SCREEN_WIDTH, height: int = SCREEN_HEIGHT) -> None:
        self.width = width
        self.height = height
        self.border_thickness = BORDER_THICKNESS

        # Listes d'entités de la carte
        self.obstacles: list[Obstacle] = []
        self.decorations: list[Decoration] = []
        self.border_rects: list[pygame.Rect] = []
        self.debris_particles: list[DebrisParticle] = []

        # Chargement des textures de fond et de bordure
        self.background_surface = self._load_background()
        self.border_tile = self._load_border_tile()

        # Construction des limites et de la disposition
        self._init_boundaries()
        self._build_balanced_desert_layout()

    def reset(self) -> None:
        """Réinitialise intégralement la disposition de la carte et restaure les caisses."""
        self.obstacles.clear()
        self.decorations.clear()
        self.debris_particles.clear()
        self._build_balanced_desert_layout()

    def spawn_crate_debris(self, center_x: float, center_y: float, count: int = 14) -> None:
        """Déclenche une animation de destruction avec dispersion d'éclats de bois."""
        for _ in range(count):
            self.debris_particles.append(DebrisParticle(center_x, center_y))

    def update(self, dt: float) -> None:
        """Met à jour les animations de débris et supprime définitivement les caisses détruites."""
        # 1. Mise à jour des particules d'éclats de bois
        self.debris_particles = [p for p in self.debris_particles if p.update(dt)]

        # 2. Nettoyage des obstacles détruits (mise à jour instantanée des hitboxes)
        self.obstacles = [obs for obs in self.obstacles if obs.is_alive]

    def get_spawn(self, player_number: int) -> tuple[tuple[float, float], float]:
        """Retourne la position de spawn (x, y) et l'angle initial d'un joueur."""
        if player_number == 1:
            return ((PLAYER_1_SPAWN[0], PLAYER_1_SPAWN[1]), PLAYER_1_SPAWN[2])
        else:
            return ((PLAYER_2_SPAWN[0], PLAYER_2_SPAWN[1]), PLAYER_2_SPAWN[2])

    def _load_background(self) -> pygame.Surface:
        """Charge l'image du terrain désertique pré-chargée depuis l'AssetManager."""
        bg = asset_manager.get_image("desert_background")
        if bg and bg.get_size() == (self.width, self.height):
            return bg
        elif bg:
            return pygame.transform.scale(bg, (self.width, self.height))

        fallback = pygame.Surface((self.width, self.height))
        fallback.fill(COLOR_SAND)
        return fallback

    def _load_border_tile(self) -> pygame.Surface:
        """Charge la texture de bordure pré-chargée depuis l'AssetManager."""
        tile = asset_manager.get_image("border_tile")
        if tile:
            return tile
        fallback = pygame.Surface((32, 32))
        fallback.fill(COLOR_BORDER_WALL)
        return fallback

    def _init_boundaries(self) -> None:
        """Crée les 4 Rects de collision pour les murs extérieurs délimitant l'arène."""
        t = self.border_thickness
        w, h = self.width, self.height

        self.border_rects = [
            pygame.Rect(0, 0, w, t),          # Mur Nord
            pygame.Rect(0, h - t, w, t),      # Mur Sud
            pygame.Rect(0, 0, t, h),          # Mur Ouest
            pygame.Rect(w - t, 0, t, h),      # Mur Est
        ]

    def _build_balanced_desert_layout(self) -> None:
        """Construit un agencement d'arène tactique et symétrique pour le duel à 2 joueurs."""
        # -------------------------------------------------------------
        # 1. ZONE CENTRALE (Bunker & Barrières de séparation)
        # -------------------------------------------------------------
        # Barrières jaunes/noires verticales au centre
        self.obstacles.append(Obstacle(ObstacleType.BARRIER_VERTICAL, 800, 240))
        self.obstacles.append(Obstacle(ObstacleType.BARRIER_VERTICAL, 800, 660))

        # Caisses centrales encadrant le passage médian
        self.obstacles.append(Obstacle(ObstacleType.CRATE, 740, 450, destructible=True))
        self.obstacles.append(Obstacle(ObstacleType.CRATE, 860, 450, destructible=True))

        # -------------------------------------------------------------
        # 2. FLANCS NORD ET SUD (Couloirs d'attaque alternatifs)
        # -------------------------------------------------------------
        # Flanc Nord : Rochers massifs et barrières horizontales
        self.obstacles.append(Obstacle(ObstacleType.ROCK_LARGE, 540, 180))
        self.obstacles.append(Obstacle(ObstacleType.BARRIER_HORIZONTAL, 670, 180))
        self.obstacles.append(Obstacle(ObstacleType.BARRIER_HORIZONTAL, 930, 180))
        self.obstacles.append(Obstacle(ObstacleType.ROCK_LARGE, 1060, 180))

        # Flanc Sud : Disposition symétrique avec rochers et barrières
        self.obstacles.append(Obstacle(ObstacleType.ROCK_LARGE, 540, 720))
        self.obstacles.append(Obstacle(ObstacleType.BARRIER_HORIZONTAL, 670, 720))
        self.obstacles.append(Obstacle(ObstacleType.BARRIER_HORIZONTAL, 930, 720))
        self.obstacles.append(Obstacle(ObstacleType.ROCK_LARGE, 1060, 720))

        # -------------------------------------------------------------
        # 3. ZONES DE PROTECTION PRÈS DES SPAWNS (Base P1 Ouest & Base P2 Est)
        # -------------------------------------------------------------
        # Couverture Joueur 1 (Ouest)
        self.obstacles.append(Obstacle(ObstacleType.CRATE, 340, 360, destructible=True))
        self.obstacles.append(Obstacle(ObstacleType.CRATE, 340, 540, destructible=True))
        self.obstacles.append(Obstacle(ObstacleType.ROCK_SMALL, 340, 450))
        self.obstacles.append(Obstacle(ObstacleType.ROCK_SMALL, 220, 260))
        self.obstacles.append(Obstacle(ObstacleType.ROCK_SMALL, 220, 640))

        # Couverture Joueur 2 (Est)
        self.obstacles.append(Obstacle(ObstacleType.CRATE, 1260, 360, destructible=True))
        self.obstacles.append(Obstacle(ObstacleType.CRATE, 1260, 540, destructible=True))
        self.obstacles.append(Obstacle(ObstacleType.ROCK_SMALL, 1260, 450))
        self.obstacles.append(Obstacle(ObstacleType.ROCK_SMALL, 1380, 260))
        self.obstacles.append(Obstacle(ObstacleType.ROCK_SMALL, 1380, 640))

        # -------------------------------------------------------------
        # 4. AMAS DE CAISSES DE COUVERTURE SECONDAIRES (Destructibles)
        # -------------------------------------------------------------
        self.obstacles.append(Obstacle(ObstacleType.CRATE, 580, 400, destructible=True))
        self.obstacles.append(Obstacle(ObstacleType.CRATE, 580, 500, destructible=True))
        self.obstacles.append(Obstacle(ObstacleType.CRATE, 1020, 400, destructible=True))
        self.obstacles.append(Obstacle(ObstacleType.CRATE, 1020, 500, destructible=True))

        # -------------------------------------------------------------
        # 5. DÉCORATIONS VÉGÉTALES NON-BLOQUANTES (Cactus & Buissons)
        # -------------------------------------------------------------
        # Cactus décoratifs (ne bloquent pas les mouvements !)
        cactus_positions = [
            (160, 140), (160, 760),
            (1440, 140), (1440, 760),
            (460, 300), (460, 600),
            (1140, 300), (1140, 600),
            (800, 100), (800, 800),
            (700, 450), (900, 450),
        ]
        for cx, cy in cactus_positions:
            self.decorations.append(Decoration(DecorationType.CACTUS, cx, cy))

        # Buissons succulents désertiques
        bush_positions = [
            (280, 180), (280, 720),
            (1320, 180), (1320, 720),
            (620, 280), (980, 280),
            (620, 620), (980, 620),
            (440, 450), (1160, 450),
        ]
        for bx, by in bush_positions:
            self.decorations.append(Decoration(DecorationType.BUSH, bx, by))

        # Référence fixe sur les caisses destructibles pour la synchronisation réseau
        self.all_initial_crates: list[Obstacle] = [obs for obs in self.obstacles if obs.destructible]

    def get_destroyed_crate_indices(self) -> list[int]:
        """Retourne la liste des indices de caisses détruites pour l'instantané réseau."""
        return [i for i, crate in enumerate(self.all_initial_crates) if crate not in self.obstacles or not crate.is_alive]

    def apply_destroyed_crate_indices(self, indices: list[int]) -> None:
        """Applique les caisses détruites reçues par le réseau côté client."""
        for idx in indices:
            if 0 <= idx < len(self.all_initial_crates):
                crate = self.all_initial_crates[idx]
                if crate in self.obstacles:
                    crate.is_alive = False
                    self.obstacles.remove(crate)
                    self.spawn_crate_debris(crate.rect.centerx, crate.rect.centery)

    def get_collision_rects(self) -> list[pygame.Rect]:
        """Retourne tous les rectangles Pygame bloquant les mouvements des tanks."""
        rects = [obs.rect for obs in self.obstacles if obs.blocks_movement]
        rects.extend(self.border_rects)
        return rects

    def get_projectile_collision_rects(self) -> list[pygame.Rect]:
        """Retourne tous les rectangles Pygame bloquant les tirs de projectiles."""
        rects = [obs.rect for obs in self.obstacles if obs.blocks_projectiles]
        rects.extend(self.border_rects)
        return rects

    def draw(self, surface: pygame.Surface) -> None:
        """Dessine l'ensemble des couches de la carte dans l'ordre de profondeur adéquat."""
        # 1. Sol désertique
        surface.blit(self.background_surface, (0, 0))

        # 2. Décorations végétales au sol (cactus et buissons sous les tanks)
        for dec in self.decorations:
            dec.draw(surface)

        # 3. Obstacles physiques (caisses, barrières, rochers avec ombres portées)
        for obs in self.obstacles:
            obs.draw(surface)

        # 4. Particules d'éclats de bois / débris de destruction
        for debris in self.debris_particles:
            debris.draw(surface)

        # 5. Bordures murales de l'arène
        self._draw_borders(surface)

    def _draw_borders(self, surface: pygame.Surface) -> None:
        """Dessine le mur d'enceinte en biseau/pierres avec finition stylisée."""
        t = self.border_thickness
        w, h = self.width, self.height

        # Cadre mural extérieur
        for rect in self.border_rects:
            pygame.draw.rect(surface, COLOR_BORDER_WALL, rect)

        # Ligne de biseau intérieur claire
        inner_rect = pygame.Rect(t - 1, t - 1, w - 2 * t + 2, h - 2 * t + 2)
        pygame.draw.rect(surface, COLOR_BORDER_INNER, inner_rect, width=2)
        # Ombre intérieure sur le sable
        pygame.draw.rect(surface, (50, 35, 20, 60), inner_rect.inflate(4, 4), width=2)

    def draw_debug(self, surface: pygame.Surface) -> None:
        """Affiche les Rects de collision en surimpression pour le débogage."""
        # Murs en rouge
        for rect in self.border_rects:
            pygame.draw.rect(surface, (255, 0, 0), rect, width=2)
        # Obstacles en vert
        for obs in self.obstacles:
            pygame.draw.rect(surface, (0, 255, 0), obs.rect, width=2)
        # Décorations en bleu (non bloquantes)
        for dec in self.decorations:
            pygame.draw.rect(surface, (0, 100, 255), dec.rect, width=1)
