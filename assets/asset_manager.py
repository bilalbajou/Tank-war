"""Gestionnaire centralisé des ressources (AssetManager) pour Tank War : Arena Duel.

Responsabilités :
1. Résolution portable et multiplateforme des chemins (pathlib.Path, compatible PyInstaller frozen et dev).
2. Pré-chargement, vérification d'intégrité et mise en cache mémoire de tous les sprites et icônes.
3. Préservation de la couche de transparence alpha (.convert_alpha()).
4. Génération de fallbacks procéduraux intelligents pour chaque type d'asset si un fichier manque.
5. Gestion des caches de rotation pour le rendu temps réel à 60 FPS constants.
"""

from __future__ import annotations
import math
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pygame

# =============================================================================
# 1. RÉSOLUTION UNIVERSELLE DES CHEMINS (INDEPENDANTE DU RÉPERTOIRE DE LANCEMENT)
# =============================================================================
def resolve_project_root() -> Path:
    """Détermine de façon fiable la racine du projet, même exécuté depuis un autre dossier ou gelé en PyInstaller."""
    # A. Mode exécutable PyInstaller gelé (onedir ou onefile)
    if getattr(sys, "frozen", False):
        if hasattr(sys, "_MEIPASS"):
            meipass_path = Path(sys._MEIPASS).resolve()
            if (meipass_path / "assets").exists():
                return meipass_path

        exe_dir = Path(sys.executable).resolve().parent
        if (exe_dir / "assets").exists():
            return exe_dir
        if (exe_dir / "_internal" / "assets").exists():
            return exe_dir / "_internal"

    # B. Mode développement standard (basé sur l'emplacement physique du script)
    here = Path(__file__).resolve().parent  # dossier assets/
    if (here.parent / "assets").exists():
        return here.parent
    if (here / "icons").exists():
        return here.parent

    # C. Repli sur le dossier de travail courant
    cwd = Path.cwd().resolve()
    if (cwd / "assets").exists():
        return cwd

    return here.parent


PROJECT_ROOT = resolve_project_root()
ASSETS_DIR = PROJECT_ROOT / "assets"
MAPS_DIR = ASSETS_DIR / "maps"
OBSTACLES_DIR = ASSETS_DIR / "obstacles"
SPRITES_DIR = ASSETS_DIR / "sprites"
SOUNDS_DIR = ASSETS_DIR / "sounds"
FONTS_DIR = ASSETS_DIR / "fonts"
ICONS_DIR = ASSETS_DIR / "icons"
POWERUPS_DIR = ASSETS_DIR / "powerups"
TANKS_DIR = ASSETS_DIR / "tanks"
PROJECTILES_DIR = ASSETS_DIR / "projectiles"


# =============================================================================
# 2. CLASSE CENTRALE ASSETMANAGER
# =============================================================================
class AssetManager:
    """Gestionnaire singleton de ressources graphiques avec indexation, cache et fallbacks."""

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
        self.project_root = PROJECT_ROOT
        self.assets_dir = ASSETS_DIR

        # Cache d'images principales : {clé_normalisée: Surface}
        self.images: Dict[str, pygame.Surface] = {}

        # Caches de rotation
        self._tank_rotation_cache: Dict[Tuple[str, int], pygame.Surface] = {}
        self._bullet_rotation_cache: Dict[int, pygame.Surface] = {}

        # Index des fichiers trouvés sur disque : {clé_relative: Path}
        self._file_index: Dict[str, Path] = {}
        self._scan_and_index_disk()

        # Pré-chargement des assets principaux
        self.preload_all()

    def _scan_and_index_disk(self) -> None:
        """Parcourt récursivement le dossier assets pour indexer tous les fichiers disponibles."""
        self._file_index.clear()
        if not self.assets_dir.exists():
            print(f"[AssetManager] [AVERTISSEMENT] Dossier assets introuvable : {self.assets_dir}")
            return

        for path in self.assets_dir.rglob("*"):
            if path.is_file():
                # 1. Chemin relatif par rapport à ASSETS_DIR
                try:
                    rel_to_assets = path.relative_to(self.assets_dir)
                    norm_key = str(rel_to_assets).replace("\\", "/").lower()
                    self._file_index[norm_key] = path

                    # Clé sans extension (ex: "icons/results/victory")
                    stem_key = str(rel_to_assets.with_suffix("")).replace("\\", "/").lower()
                    self._file_index[stem_key] = path

                    # Clé relative au sous-dossier (ex: "results/victory" si dans icons/)
                    if norm_key.startswith("icons/"):
                        sub_icon_key = norm_key[len("icons/"):]
                        self._file_index[sub_icon_key] = path
                        sub_stem = stem_key[len("icons/"):]
                        self._file_index[sub_stem] = path

                    # Nom de base du fichier (ex: "victory")
                    file_stem = path.stem.lower()
                    if file_stem not in self._file_index:
                        self._file_index[file_stem] = path

                except Exception as e:
                    print(f"[AssetManager] Erreur d'indexation pour {path}: {e}")

    def get_path(self, key: str) -> Optional[Path]:
        """Trouve le chemin physique d'un asset par sa clé relative ou son nom."""
        clean_key = key.strip().replace("\\", "/").lower()

        # 1. Recherche dans l'index pré-scanné
        if clean_key in self._file_index:
            return self._file_index[clean_key]

        # 2. Sans extension .png éventuelle
        if clean_key.endswith(".png"):
            no_ext = clean_key[:-4]
            if no_ext in self._file_index:
                return self._file_index[no_ext]

        # 3. Tentative d'accès direct relatif à ASSETS_DIR
        direct_path = self.assets_dir / clean_key
        if direct_path.exists() and direct_path.is_file():
            return direct_path

        # 4. Avec extension .png si omise
        if not clean_key.endswith(".png"):
            png_path = self.assets_dir / f"{clean_key}.png"
            if png_path.exists() and png_path.is_file():
                return png_path

        # 5. Recherche dans les sous-dossiers courants
        for sub in ("icons", "icons/results", "icons/hud", "icons/menu", "icons/network",
                    "icons/pause", "powerups", "sprites/powerups", "tanks", "obstacles", "maps", "projectiles"):
            candidate = self.assets_dir / sub / f"{Path(clean_key).name}.png"
            if candidate.exists() and candidate.is_file():
                return candidate

        return None

    def has_image(self, key: str) -> bool:
        """Vérifie si une image est déjà en cache ou disponible sur le disque."""
        norm_key = key.strip().replace("\\", "/").lower()
        if norm_key in self.images:
            return True
        return self.get_path(norm_key) is not None

    def load_image(
        self,
        candidate_paths: List[Path | str],
        is_alpha: bool = True,
        fallback_builder=None,
        explicit_name: str = ""
    ) -> pygame.Surface:
        """Charge une image depuis une liste de chemins candidats avec fallback sécurisé."""
        for p in candidate_paths:
            resolved_p: Optional[Path] = None
            if isinstance(p, Path):
                resolved_p = p
            elif isinstance(p, str):
                resolved_p = self.get_path(p) or (self.assets_dir / p)

            if resolved_p and resolved_p.exists() and resolved_p.is_file():
                try:
                    loaded = pygame.image.load(str(resolved_p))
                    if pygame.display.get_surface():
                        return loaded.convert_alpha() if is_alpha else loaded.convert()
                    return loaded
                except Exception as err:
                    print(f"[AssetManager] Erreur lors du chargement de {resolved_p}: {err}")

        # Si aucun chemin n'a fonctionné, avertissement explicite
        asset_label = explicit_name or (str(candidate_paths[0]) if candidate_paths else "inconnu")
        print(f"[AssetManager] [AVERTISSEMENT] Asset '{asset_label}' non trouvé sur disque -> Génération d'un fallback procédural.")

        if fallback_builder:
            return fallback_builder()

        # Fallback universel par défaut
        return self._create_generic_fallback(explicit_name or "asset", 64, is_alpha=is_alpha)

    # -------------------------------------------------------------------------
    # PRÉ-CHARGEMENT INTÉGRAL DES CATÉGORIES
    # -------------------------------------------------------------------------
    def preload_all(self) -> int:
        """Précharge en mémoire toutes les textures nécessaires pour un affichage instantané."""
        loaded_count = 0

        # 1. Chars de combat
        self.images["tank_red"] = self.load_image(
            [TANKS_DIR / "tank_red.png", SPRITES_DIR / "tanks" / "tank_red.png"],
            fallback_builder=lambda: self._create_tank_fallback("red"),
            explicit_name="tank_red"
        )
        self.images["tank_green"] = self.load_image(
            [TANKS_DIR / "tank_green.png", SPRITES_DIR / "tanks" / "tank_green.png"],
            fallback_builder=lambda: self._create_tank_fallback("green"),
            explicit_name="tank_green"
        )

        # 2. Obstacles
        obstacle_names = [
            "crate", "crate_damaged", "barrier_horizontal", "barrier_vertical",
            "rock_large", "rock_small", "plant_cactus", "plant_bush"
        ]
        for name in obstacle_names:
            self.images[name] = self.load_image(
                [OBSTACLES_DIR / f"{name}.png"],
                fallback_builder=lambda n=name: self._create_obstacle_fallback(n),
                explicit_name=name
            )

        # 3. Projectiles
        self.images["bullet"] = self.load_image(
            [PROJECTILES_DIR / "bullet.png", SPRITES_DIR / "projectiles" / "bullet.png"],
            fallback_builder=self._create_bullet_fallback,
            explicit_name="bullet"
        )

        # 4. Carte et bordures
        self.images["desert_background"] = self.load_image(
            [MAPS_DIR / "desert_background.png"],
            is_alpha=False,
            fallback_builder=self._create_desert_fallback,
            explicit_name="desert_background"
        )
        self.images["border_tile"] = self.load_image(
            [MAPS_DIR / "border_tile.png"],
            is_alpha=False,
            fallback_builder=self._create_border_fallback,
            explicit_name="border_tile"
        )

        # 5. Bonus / Power-ups
        for pup in ["shield", "speed", "rapid_fire"]:
            paths = [
                POWERUPS_DIR / f"{pup}.png",
                SPRITES_DIR / "powerups" / f"{pup}.png",
                ICONS_DIR / "hud" / f"{pup}.png",
            ]
            surf = self.load_image(
                paths,
                fallback_builder=lambda p=pup: self._create_powerup_fallback(p),
                explicit_name=f"powerup_{pup}"
            )
            self.images[f"powerup_{pup}"] = surf
            self.images[pup] = surf

        # 6. Icônes de récompenses et résultats (Victoire, Défaite, Trophée, Score)
        reward_icons = [
            ("results/victory", "victory"),
            ("results/defeat", "defeat"),
            ("results/replay", "replay"),
            ("results/home", "home"),
            ("hud/score", "score"),
            ("hud/health", "health"),
            ("hud/ammo", "ammo"),
            ("hud/timer", "timer"),
            ("hud/pause", "pause"),
            ("hud/shield", "shield_icon"),
            ("hud/speed", "speed_icon"),
        ]
        for rel_key, alias in reward_icons:
            paths = [
                ICONS_DIR / f"{rel_key}.png",
                ICONS_DIR / f"{alias}.png",
            ]
            surf = self.load_image(
                paths,
                fallback_builder=lambda a=alias: self._create_reward_icon_fallback(a),
                explicit_name=rel_key
            )
            self.images[rel_key] = surf
            self.images[alias] = surf

        loaded_count = len(self.images)
        return loaded_count

    # -------------------------------------------------------------------------
    # ACCÈS AUX IMAGES ET CACHES DE ROTATION
    # -------------------------------------------------------------------------
    def get_image(self, key: str) -> pygame.Surface:
        """Récupère une texture depuis le cache mémoire, ou la charge à la demande."""
        norm_key = key.strip().replace("\\", "/").lower()

        # 1. Vérification dans le cache principal
        if norm_key in self.images:
            return self.images[norm_key]

        # 2. Sans extension éventuelle
        if norm_key.endswith(".png"):
            no_ext = norm_key[:-4]
            if no_ext in self.images:
                return self.images[no_ext]

        # 3. Chargement à la demande depuis le disque
        path = self.get_path(norm_key)
        if path and path.exists() and path.is_file():
            try:
                loaded = pygame.image.load(str(path))
                surf = loaded.convert_alpha() if pygame.display.get_surface() else loaded
                self.images[norm_key] = surf
                return surf
            except Exception as e:
                print(f"[AssetManager] Erreur de chargement pour {path}: {e}")

        # 4. Fallback procédural dédié
        fallback = self._create_dedicated_fallback(norm_key)
        self.images[norm_key] = fallback
        return fallback

    def get_rotated_tank(self, color_name: str, angle_deg: float) -> pygame.Surface:
        """Retourne la surface pré-pivotée d'un char depuis le cache de rotations."""
        key_color = color_name.lower()
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

    def clear_cache(self) -> None:
        """Vide l'ensemble des caches mémoire."""
        self.images.clear()
        self._tank_rotation_cache.clear()
        self._bullet_rotation_cache.clear()

    # -------------------------------------------------------------------------
    # GÉNÉRATEURS DE FALLBACKS PROCÉDURAUX (GARANTIE DE RENDU SANS PLANTAGE)
    # -------------------------------------------------------------------------
    def _create_dedicated_fallback(self, key: str) -> pygame.Surface:
        """Génère un fallback contextuel selon le nom de l'asset manquant."""
        k = key.lower()
        if "victory" in k or "trophy" in k or "score" in k:
            return self._create_reward_icon_fallback("victory")
        elif "defeat" in k or "skull" in k:
            return self._create_reward_icon_fallback("defeat")
        elif "shield" in k:
            return self._create_powerup_fallback("shield")
        elif "speed" in k:
            return self._create_powerup_fallback("speed")
        elif "rapid_fire" in k or "ammo" in k:
            return self._create_powerup_fallback("rapid_fire")
        elif "tank" in k:
            color = "red" if "red" in k else "green"
            return self._create_tank_fallback(color)
        elif "bullet" in k:
            return self._create_bullet_fallback()
        elif "crate" in k:
            return self._create_obstacle_fallback("crate")
        return self._create_generic_fallback(key, 64)

    def _create_reward_icon_fallback(self, kind: str) -> pygame.Surface:
        """Crée une icône vectorielle pour la victoire, défaite ou le score."""
        surf = pygame.Surface((64, 64), pygame.SRCALPHA)
        center = (32, 32)

        if kind in ("victory", "score"):
            # Trophée doré cartoon
            # Base
            pygame.draw.rect(surf, (180, 110, 20), (20, 50, 24, 8), border_radius=3)
            pygame.draw.rect(surf, (243, 156, 18), (28, 42, 8, 10))
            # Coupe
            pygame.draw.ellipse(surf, (254, 211, 48), (16, 14, 32, 30))
            pygame.draw.circle(surf, (255, 235, 120), (32, 28), 10)
            # Anses du trophée
            pygame.draw.circle(surf, (243, 156, 18), (14, 26), 7, width=3)
            pygame.draw.circle(surf, (243, 156, 18), (50, 26), 7, width=3)

        elif kind == "defeat":
            # Crâne / explosion rouge de défaite
            pygame.draw.circle(surf, (231, 76, 60), center, 24)
            pygame.draw.circle(surf, (192, 57, 43), center, 24, width=3)
            # Yeux du crâne (croix)
            pygame.draw.circle(surf, (20, 24, 30), (24, 28), 5)
            pygame.draw.circle(surf, (20, 24, 30), (40, 28), 5)
            pygame.draw.rect(surf, (20, 24, 30), (28, 40, 8, 6), border_radius=2)

        else:
            # Médaille dorée générique
            pygame.draw.circle(surf, (243, 156, 18), center, 24)
            pygame.draw.circle(surf, (254, 211, 48), center, 20)
            pygame.draw.circle(surf, (255, 255, 255), center, 10)

        return surf

    def _create_powerup_fallback(self, kind: str) -> pygame.Surface:
        """Génère un sprite de power-up (bouclier, vitesse, cadence de tir)."""
        surf = pygame.Surface((36, 36), pygame.SRCALPHA)
        center = (18, 18)

        if kind == "shield":
            color = (52, 152, 219)
            border = (41, 128, 185)
            pygame.draw.circle(surf, color, center, 16)
            pygame.draw.circle(surf, border, center, 16, width=3)
            # Forme de bouclier interne
            pygame.draw.polygon(surf, (255, 255, 255), [(18, 8), (26, 12), (24, 22), (18, 28), (12, 22), (10, 12)])

        elif kind == "speed":
            color = (241, 196, 15)
            border = (211, 84, 0)
            pygame.draw.circle(surf, color, center, 16)
            pygame.draw.circle(surf, border, center, 16, width=3)
            # Éclair de vitesse
            pygame.draw.polygon(surf, (255, 255, 255), [(20, 7), (12, 19), (17, 19), (14, 29), (24, 16), (19, 16)])

        else:  # rapid_fire
            color = (231, 76, 60)
            border = (192, 57, 43)
            pygame.draw.circle(surf, color, center, 16)
            pygame.draw.circle(surf, border, center, 16, width=3)
            # Triple projectile / flamme
            pygame.draw.ellipse(surf, (255, 255, 255), (14, 8, 8, 20))

        return surf

    def _create_tank_fallback(self, color_name: str) -> pygame.Surface:
        """Génère un char cartoon vectoriel."""
        surf = pygame.Surface((68, 52), pygame.SRCALPHA)
        color = (220, 60, 50) if color_name == "red" else (46, 204, 113)
        # Chenilles
        pygame.draw.rect(surf, (40, 40, 45), (4, 4, 58, 10), border_radius=3)
        pygame.draw.rect(surf, (40, 40, 45), (4, 38, 58, 10), border_radius=3)
        # Châssis
        pygame.draw.rect(surf, color, (12, 10, 44, 32), border_radius=6)
        # Tourelle et canon
        pygame.draw.circle(surf, (30, 30, 30), (32, 26), 12)
        pygame.draw.rect(surf, (40, 40, 40), (32, 23, 28, 6), border_radius=2)
        return surf

    def _create_bullet_fallback(self) -> pygame.Surface:
        """Génère un obus vectoriel."""
        surf = pygame.Surface((18, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (255, 200, 30), (0, 1, 18, 8))
        pygame.draw.ellipse(surf, (240, 60, 30), (10, 1, 8, 8))
        return surf

    def _create_obstacle_fallback(self, name: str) -> pygame.Surface:
        """Génère une caisse ou barrière vectorielle."""
        if "crate" in name:
            surf = pygame.Surface((64, 64), pygame.SRCALPHA)
            pygame.draw.rect(surf, (184, 125, 75), (2, 2, 60, 60), border_radius=6)
            pygame.draw.rect(surf, (120, 75, 40), (2, 2, 60, 60), width=3, border_radius=6)
            pygame.draw.line(surf, (120, 75, 40), (6, 6), (58, 58), 3)
            pygame.draw.line(surf, (120, 75, 40), (6, 58), (58, 6), 3)
            return surf
        elif "barrier_horizontal" in name:
            surf = pygame.Surface((120, 40), pygame.SRCALPHA)
            pygame.draw.rect(surf, (245, 180, 0), (0, 0, 120, 40), border_radius=4)
            for x in range(0, 120, 24):
                pygame.draw.polygon(surf, (35, 38, 45), [(x, 40), (x + 12, 40), (x + 24, 0), (x + 12, 0)])
            return surf
        elif "barrier_vertical" in name:
            surf = pygame.Surface((40, 120), pygame.SRCALPHA)
            pygame.draw.rect(surf, (245, 180, 0), (0, 0, 40, 120), border_radius=4)
            for y in range(0, 120, 24):
                pygame.draw.polygon(surf, (35, 38, 45), [(0, y), (0, y + 12), (40, y + 24), (40, y + 12)])
            return surf

        surf = pygame.Surface((64, 64), pygame.SRCALPHA)
        pygame.draw.circle(surf, (140, 140, 145), (32, 32), 28)
        return surf

    def _create_desert_fallback(self) -> pygame.Surface:
        """Génère un fond sable désertique."""
        surf = pygame.Surface((64, 64))
        surf.fill((235, 209, 153))
        return surf

    def _create_border_fallback(self) -> pygame.Surface:
        """Génère une tuile de bordure murale."""
        surf = pygame.Surface((28, 28))
        surf.fill((82, 48, 22))
        pygame.draw.rect(surf, (140, 110, 75), (2, 2, 24, 24), width=2)
        return surf

    def _create_generic_fallback(self, name: str, size: int = 64, is_alpha: bool = True) -> pygame.Surface:
        """Génère une surface de secours générique propre."""
        surf = pygame.Surface((size, size), pygame.SRCALPHA if is_alpha else 0)
        surf.fill((45, 52, 64) if is_alpha else (200, 150, 100))
        if is_alpha:
            pygame.draw.circle(surf, (241, 196, 15), (size // 2, size // 2), size // 2 - 2, width=2)
        return surf


# =============================================================================
# 3. INSTANCE GLOBALE SINGLETON
# =============================================================================
asset_manager = AssetManager()

