"""Gestionnaire d'icônes pour Tank War (Arena Duel).

Fournit :
- IconManager : Chargement, redimensionnement (smoothscale avec conservation de ratio),
  mise en cache multi-niveaux et gestion des états visuels (normal, hover, pressed, disabled).
- Module-level singleton `icon_manager` pour un accès universel sans rechargement disque.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, Optional, Tuple
import pygame

# Chemin de base des assets
BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_ICONS_DIR = BASE_DIR / "assets" / "icons"


class IconManager:
    """Gestionnaire et cache mémoire d'icônes 2D avec gestion d'états."""

    def __init__(self, icons_dir: Optional[Path] = None) -> None:
        self.icons_dir = Path(icons_dir) if icons_dir else DEFAULT_ICONS_DIR
        # Cache 1 : Images brutes originales chargées depuis le disque : {relative_key: pygame.Surface}
        self._raw_cache: Dict[str, pygame.Surface] = {}
        # Cache 2 : Images transformées par (clé, taille, état) : {(key, size, state): pygame.Surface}
        self._scaled_cache: Dict[Tuple[str, Tuple[int, int], str], pygame.Surface] = {}

        # Dictionnaire d'indexation rapide des fichiers disponibles
        self._indexed_files: Dict[str, Path] = {}
        self._scan_and_index()

    def _scan_and_index(self) -> None:
        """Parcourt récursivement le dossier assets/icons/ pour indexer les fichiers PNG."""
        if not self.icons_dir.exists():
            return

        for path in self.icons_dir.rglob("*.png"):
            # Clé relative e.g. "menu/play" ou "menu/play.png"
            rel_path = path.relative_to(self.icons_dir)
            rel_str = str(rel_path).replace("\\", "/")
            stem_rel = str(rel_path.with_suffix("")).replace("\\", "/")

            self._indexed_files[rel_str] = path
            self._indexed_files[stem_rel] = path

            # Indexation également par le nom seul e.g. "play"
            stem_name = path.stem.lower()
            if stem_name not in self._indexed_files:
                self._indexed_files[stem_name] = path

    def preload_all(self) -> int:
        """Précharge toutes les icônes indexées en mémoire pour éliminer les I/O en jeu."""
        count = 0
        for key in list(self._indexed_files.keys()):
            if "/" in key:  # Évite les doublons de chargement
                self._load_raw(key)
                count += 1
        return count

    def _find_path(self, icon_name: str) -> Optional[Path]:
        """Trouve le chemin absolu d'une icône par sa clé souple."""
        clean_name = icon_name.strip().replace("\\", "/")
        # Sans extension
        if clean_name.endswith(".png"):
            clean_name_no_ext = clean_name[:-4]
        else:
            clean_name_no_ext = clean_name

        # 1. Vérification dans l'index
        if clean_name in self._indexed_files:
            return self._indexed_files[clean_name]
        if clean_name_no_ext in self._indexed_files:
            return self._indexed_files[clean_name_no_ext]

        # 2. Test direct sur le disque
        direct = self.icons_dir / f"{clean_name_no_ext}.png"
        if direct.exists():
            return direct

        # 3. Test dans les sous-dossiers standards
        for cat in ("menu", "network", "hud", "pause", "results"):
            cat_path = self.icons_dir / cat / f"{clean_name_no_ext}.png"
            if cat_path.exists():
                return cat_path

        return None

    def _load_raw(self, icon_name: str) -> Optional[pygame.Surface]:
        """Charge ou récupère une surface brute 32-bit avec couche alpha."""
        if icon_name in self._raw_cache:
            return self._raw_cache[icon_name]

        path = self._find_path(icon_name)
        if not path or not path.exists():
            # Si le fichier n'existe pas encore sur disque, tentative de génération
            try:
                from generate_icons import generate_all_icons
                generate_all_icons(self.icons_dir)
                self._scan_and_index()
                path = self._find_path(icon_name)
            except Exception:
                pass

        if path and path.exists():
            try:
                surf = pygame.image.load(str(path)).convert_alpha()
                self._raw_cache[icon_name] = surf
                return surf
            except Exception:
                pass

        # Fallback procédural
        fallback = self._create_procedural_fallback(icon_name, 64)
        self._raw_cache[icon_name] = fallback
        return fallback

    def get_icon(
        self,
        icon_name: str,
        size: Tuple[int, int] = (24, 24),
        state: str = "normal",
        preserve_aspect_ratio: bool = True,
    ) -> pygame.Surface:
        """Récupère une icône mise en cache à la taille et dans l'état demandé.

        Paramètres :
        - icon_name : Identifiant e.g. "menu/play", "play", "wifi", "hud/health"...
        - size : Tuple (largeur, hauteur) cibles en pixels.
        - state : "normal", "hover", "pressed", ou "disabled".
        - preserve_aspect_ratio : Si True, conserve le ratio d'aspect dans le rectangle cible.
        """
        cache_key = (icon_name, (int(size[0]), int(size[1])), state)
        if cache_key in self._scaled_cache:
            return self._scaled_cache[cache_key]

        raw = self._load_raw(icon_name)
        if raw is None:
            raw = self._create_procedural_fallback(icon_name, size[0])

        target_w, target_h = max(1, int(size[0])), max(1, int(size[1]))

        # Redimensionnement avec conservation de ratio si nécessaire
        if preserve_aspect_ratio:
            orig_w, orig_h = raw.get_width(), raw.get_height()
            ratio = min(target_w / orig_w, target_h / orig_h)
            scaled_w = max(1, int(orig_w * ratio))
            scaled_h = max(1, int(orig_h * ratio))

            scaled_raw = pygame.transform.smoothscale(raw, (scaled_w, scaled_h))
            # Centrage sur une surface transparente de taille (target_w, target_h)
            base_surf = pygame.Surface((target_w, target_h), pygame.SRCALPHA)
            offset_x = (target_w - scaled_w) // 2
            offset_y = (target_h - scaled_h) // 2
            base_surf.blit(scaled_raw, (offset_x, offset_y))
        else:
            base_surf = pygame.transform.smoothscale(raw, (target_w, target_h))

        # Application de l'état visuel (Normal, Hover, Pressed, Disabled)
        styled_surf = self._apply_state(base_surf, state)
        self._scaled_cache[cache_key] = styled_surf
        return styled_surf

    def _apply_state(self, surf: pygame.Surface, state: str) -> pygame.Surface:
        """Applique des ajustements colorimétriques et de transparence selon l'état."""
        res = surf.copy()
        state = state.lower()

        if state == "hover":
            # Augmentation de la luminosité (lueur au survol)
            bright_overlay = pygame.Surface(res.get_size(), pygame.SRCALPHA)
            bright_overlay.fill((45, 45, 45, 0))
            res.blit(bright_overlay, (0, 0), special_flags=pygame.BLEND_RGB_ADD)

        elif state == "pressed":
            # Légère atténuation / assombrissement à l'enfoncement
            dark_overlay = pygame.Surface(res.get_size(), pygame.SRCALPHA)
            dark_overlay.fill((40, 40, 40, 0))
            res.blit(dark_overlay, (0, 0), special_flags=pygame.BLEND_RGB_SUB)

        elif state == "disabled":
            # Conversion monochrome / niveau de gris et réduction d'opacité à 45%
            w, h = res.get_size()
            gray_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            for x in range(w):
                for y in range(h):
                    r, g, b, a = res.get_at((x, y))
                    if a > 0:
                        gray = int(0.299 * r + 0.587 * g + 0.114 * b)
                        gray_surf.set_at((x, y), (gray, gray, gray, int(a * 0.45)))
            res = gray_surf

        return res

    def draw_icon(
        self,
        surface: pygame.Surface,
        icon_name: str,
        position: Tuple[int, int],
        size: Tuple[int, int] = (24, 24),
        state: str = "normal",
        anchor: str = "topleft",
    ) -> pygame.Rect:
        """Dessine une icône avec gestion automatique de l'ancrage et de l'état.

        Paramètres :
        - surface : Surface cible de dessin (ex: screen).
        - icon_name : Clé de l'icône (ex: "play", "wifi", "menu/play").
        - position : Coordonnées (x, y) de l'ancre.
        - size : Dimensions cibles (largeur, hauteur).
        - state : "normal", "hover", "pressed", "disabled".
        - anchor : "topleft", "center", "midleft", "midright", etc.
        """
        icon_surf = self.get_icon(icon_name, size=size, state=state)
        rect = icon_surf.get_rect()
        setattr(rect, anchor, position)
        surface.blit(icon_surf, rect)
        return rect

    def _create_procedural_fallback(self, name: str, size: int) -> pygame.Surface:
        """Génère un glyphe vectoriel de secours si le fichier PNG est introuvable."""
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        radius = max(2, size // 2 - 2)

        # Disque cartoon sombre
        pygame.draw.circle(surf, (40, 45, 55), center, radius)
        pygame.draw.circle(surf, (243, 156, 18), center, radius, width=max(1, size // 16))

        # Triangle ou cercle stylisé au centre
        inner_r = max(1, radius // 2)
        pygame.draw.circle(surf, (255, 255, 255), center, inner_r)
        return surf


# Singleton global pour importation directe : `from interface.icon_manager import icon_manager`
icon_manager = IconManager()

