"""Système de détection et résolution de collisions avancée pour Tank War.

Intègre :
- Échantillonnage continu par sous-pas (Anti-Tunneling / CCD) pour empêcher
  les traversées d'obstacles même à très haute vitesse ou lors de chutes de framerate.
- Glissement fluide le long des surfaces (séparation des axes X et Y).
- Confinement rigoureux dans les limites de l'arène.
"""

from typing import Optional, Sequence
import math
import pygame


class CollisionHandler:
    """Gestionnaire de détection et de résolution des collisions."""

    # Pas maximal en pixels par échantillon pour garantir l'absence de tunneling
    MAX_STEP_PIXELS = 5.0

    @staticmethod
    def is_colliding(
        test_rect: pygame.Rect,
        obstacle_rects: Sequence[pygame.Rect],
        other_tank_rect: Optional[pygame.Rect] = None
    ) -> bool:
        """Vérifie si le rectangle de test entre en collision avec un obstacle ou le second tank."""
        # 1. Collision avec le second tank
        if other_tank_rect is not None and test_rect.colliderect(other_tank_rect):
            return True

        # 2. Collision avec les obstacles physiques
        idx = test_rect.collidelist(obstacle_rects)
        return idx != -1

    @staticmethod
    def clamp_to_bounds(rect: pygame.Rect, bounds: pygame.Rect) -> None:
        """Contraint un rectangle à rester strictement à l'intérieur des limites de l'arène."""
        if rect.left < bounds.left:
            rect.left = bounds.left
        elif rect.right > bounds.right:
            rect.right = bounds.right

        if rect.top < bounds.top:
            rect.top = bounds.top
        elif rect.bottom > bounds.bottom:
            rect.bottom = bounds.bottom

    @classmethod
    def move_and_slide(
        cls,
        current_pos: pygame.Vector2,
        velocity: pygame.Vector2,
        hitbox_size: tuple[int, int],
        obstacle_rects: Sequence[pygame.Rect],
        bounds_rect: pygame.Rect,
        other_tank_rect: Optional[pygame.Rect] = None
    ) -> tuple[pygame.Vector2, pygame.Rect]:
        """Déplace l'entité avec échantillonnage continu (CCD) et séparation des axes X et Y.
        
        Empêche rigoureusement toute traversée d'obstacle (anti-tunneling) et assure un
        glissement parfait le long des murs et caisses.
        """
        hw = hitbox_size[0] // 2
        hh = hitbox_size[1] // 2
        new_x = float(current_pos.x)
        new_y = float(current_pos.y)

        # =========================================================================
        # 1. DÉPLACEMENT ET SOUS-PAS SUR L'AXE X (Anti-Tunneling)
        # =========================================================================
        if velocity.x != 0.0:
            total_x = velocity.x
            steps_x = max(1, math.ceil(abs(total_x) / cls.MAX_STEP_PIXELS))
            step_dx = total_x / steps_x

            for _ in range(steps_x):
                candidate_x = new_x + step_dx
                test_rect_x = pygame.Rect(int(candidate_x - hw), int(new_y - hh), hitbox_size[0], hitbox_size[1])

                # Limites de l'arène
                if test_rect_x.left < bounds_rect.left:
                    test_rect_x.left = bounds_rect.left
                    new_x = float(test_rect_x.centerx)
                    break
                elif test_rect_x.right > bounds_rect.right:
                    test_rect_x.right = bounds_rect.right
                    new_x = float(test_rect_x.centerx)
                    break

                # Collision avec obstacles ou adversaire
                if cls.is_colliding(test_rect_x, obstacle_rects, other_tank_rect):
                    # Blocage immédiat sur l'axe X (glissement préservé sur Y)
                    break

                new_x = candidate_x

        # =========================================================================
        # 2. DÉPLACEMENT ET SOUS-PAS SUR L'AXE Y (Anti-Tunneling)
        # =========================================================================
        if velocity.y != 0.0:
            total_y = velocity.y
            steps_y = max(1, math.ceil(abs(total_y) / cls.MAX_STEP_PIXELS))
            step_dy = total_y / steps_y

            for _ in range(steps_y):
                candidate_y = new_y + step_dy
                test_rect_y = pygame.Rect(int(new_x - hw), int(candidate_y - hh), hitbox_size[0], hitbox_size[1])

                # Limites de l'arène
                if test_rect_y.top < bounds_rect.top:
                    test_rect_y.top = bounds_rect.top
                    new_y = float(test_rect_y.centery)
                    break
                elif test_rect_y.bottom > bounds_rect.bottom:
                    test_rect_y.bottom = bounds_rect.bottom
                    new_y = float(test_rect_y.centery)
                    break

                # Collision avec obstacles ou adversaire
                if cls.is_colliding(test_rect_y, obstacle_rects, other_tank_rect):
                    # Blocage immédiat sur l'axe Y (glissement préservé sur X)
                    break

                new_y = candidate_y

        final_pos = pygame.Vector2(new_x, new_y)
        final_rect = pygame.Rect(int(new_x - hw), int(new_y - hh), hitbox_size[0], hitbox_size[1])
        return final_pos, final_rect
