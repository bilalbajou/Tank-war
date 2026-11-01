"""Moteur d'effets visuels et de particules pour Tank War : Arena Duel.

Fournit :
1. TankExplosionEffect : Déflagration spectaculaire avec boule de feu expansée, onde de choc, étincelles et fumée.
2. CrateBreakEffect : Projection de lattes de bois tournantes et nuage de sciure/poussière.
3. ImpactSparkEffect : Gerbe d'étincelles directionnelle et flash lumineux lors d'un impact balistique.
4. AnimatedPowerUp : Flottement sinusoïdal, aura lumineuse pulsante et particules de lueur.
5. VictoryCelebrationEffect : Pluie de confettis festifs et étoiles d'artifice dorées.
"""

from __future__ import annotations
import math
import random
from typing import Optional
import pygame


class SparkParticle:
    """Particule d'étincelle incandescente avec traînée et dissipation."""

    def __init__(
        self,
        x: float,
        y: float,
        velocity: pygame.Vector2,
        color: tuple[int, int, int],
        lifetime: float = 0.35,
        radius: float = 3.0,
    ) -> None:
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(velocity)
        self.color = color
        self.lifetime = lifetime
        self.age = 0.0
        self.radius = radius

    def update(self, dt: float) -> bool:
        """Met à jour la position et applique le frottement. Retourne False si expirée."""
        self.age += dt
        if self.age >= self.lifetime:
            return False
        # Frottement dans l'air
        self.velocity *= max(0.0, 1.0 - (dt * 4.0))
        self.position += self.velocity * dt
        return True

    def draw(self, surface: pygame.Surface) -> None:
        """Dessine l'étincelle avec fondu de transparence."""
        progress = self.age / self.lifetime
        current_r = max(1.0, self.radius * (1.0 - progress))
        alpha = int(255 * (1.0 - progress))

        spark_surf = pygame.Surface((int(current_r * 4) + 2, int(current_r * 4) + 2), pygame.SRCALPHA)
        pygame.draw.circle(
            spark_surf,
            (self.color[0], self.color[1], self.color[2], alpha),
            (spark_surf.get_width() // 2, spark_surf.get_height() // 2),
            int(current_r),
        )
        surface.blit(
            spark_surf,
            spark_surf.get_rect(center=(int(self.position.x), int(self.position.y))),
        )


class SmokePuff:
    """Particule de fumée volumétrique s'élevant et se dissipant."""

    def __init__(self, x: float, y: float, max_radius: float = 24.0, lifetime: float = 0.7) -> None:
        self.position = pygame.Vector2(x, y)
        angle = random.uniform(0, math.tau)
        speed = random.uniform(15, 60)
        self.velocity = pygame.Vector2(math.cos(angle) * speed, math.sin(angle) * speed - 20)  # Flottaison vers le haut
        self.max_radius = max_radius
        self.lifetime = lifetime
        self.age = 0.0
        tone = random.randint(35, 65)
        self.color = (tone, tone, tone)

    def update(self, dt: float) -> bool:
        self.age += dt
        if self.age >= self.lifetime:
            return False
        self.velocity *= max(0.0, 1.0 - (dt * 2.5))
        self.position += self.velocity * dt
        return True

    def draw(self, surface: pygame.Surface) -> None:
        progress = self.age / self.lifetime
        r = int(self.max_radius * (0.3 + 0.7 * math.sin(progress * math.pi * 0.5)))
        alpha = int(140 * (1.0 - progress))
        if r <= 0 or alpha <= 0:
            return

        smoke_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(smoke_surf, (self.color[0], self.color[1], self.color[2], alpha), (r + 1, r + 1), r)
        surface.blit(smoke_surf, smoke_surf.get_rect(center=(int(self.position.x), int(self.position.y))))


# =============================================================================
# 1. EXPLOSION DE TANK (SPECTACULAIRE)
# =============================================================================
class TankExplosionEffect:
    """Animation complète d'explosion lors de la destruction d'un char."""

    def __init__(self, center_x: float, center_y: float) -> None:
        self.center = pygame.Vector2(center_x, center_y)
        self.lifetime = 0.85
        self.age = 0.0

        # Particules internes
        self.sparks: list[SparkParticle] = []
        self.smoke_puffs: list[SmokePuff] = []

        # Gerbe de 24 étincelles flamboyantes dans toutes les directions
        spark_colors = [(255, 230, 80), (255, 140, 30), (240, 60, 20), (255, 255, 200)]
        for _ in range(26):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(120, 340)
            vel = pygame.Vector2(math.cos(angle) * speed, math.sin(angle) * speed)
            color = random.choice(spark_colors)
            self.sparks.append(SparkParticle(center_x, center_y, vel, color, lifetime=random.uniform(0.35, 0.65), radius=random.uniform(2.5, 4.5)))

        # Nuages de fumée
        for _ in range(12):
            ox = random.uniform(-14, 14)
            oy = random.uniform(-14, 14)
            self.smoke_puffs.append(SmokePuff(center_x + ox, center_y + oy, max_radius=random.uniform(20, 32), lifetime=random.uniform(0.55, 0.85)))

    def update(self, dt: float) -> bool:
        self.age += dt
        if self.age >= self.lifetime:
            return False

        self.sparks = [s for s in self.sparks if s.update(dt)]
        self.smoke_puffs = [p for p in self.smoke_puffs if p.update(dt)]
        return True

    def draw(self, surface: pygame.Surface) -> None:
        progress = self.age / self.lifetime

        # 1. Dessin des nuages de fumée
        for p in self.smoke_puffs:
            p.draw(surface)

        # 2. Onde de choc (Shockwave ring)
        if progress < 0.6:
            sw_ratio = progress / 0.6
            sw_radius = int(80 * sw_ratio)
            sw_alpha = int(220 * (1.0 - sw_ratio))
            sw_surf = pygame.Surface((sw_radius * 2 + 4, sw_radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(sw_surf, (255, 215, 100, sw_alpha), (sw_radius + 2, sw_radius + 2), sw_radius, width=3)
            surface.blit(sw_surf, sw_surf.get_rect(center=(int(self.center.x), int(self.center.y))))

        # 3. Boule de feu centrale (Fireball)
        if progress < 0.45:
            fb_ratio = progress / 0.45
            fb_radius = int(46 * math.sin(fb_ratio * math.pi))
            if fb_radius > 0:
                # Cœur blanc chaud
                pygame.draw.circle(surface, (255, 255, 220), (int(self.center.x), int(self.center.y)), max(1, int(fb_radius * 0.5)))
                # Halo orange/jaune
                fb_surf = pygame.Surface((fb_radius * 2 + 4, fb_radius * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(fb_surf, (255, 120, 30, 200), (fb_radius + 2, fb_radius + 2), fb_radius)
                surface.blit(fb_surf, fb_surf.get_rect(center=(int(self.center.x), int(self.center.y))))

        # 4. Étincelles
        for s in self.sparks:
            s.draw(surface)


# =============================================================================
# 2. IMPACT DE PROJECTILE (GERBE D'ÉTINCELLES & FLASH)
# =============================================================================
class ImpactEffect:
    """Flash lumineux et gerbe d'étincelles lors de l'impact d'un obus."""

    def __init__(self, x: float, y: float, impact_angle_deg: float = 0.0) -> None:
        self.center = pygame.Vector2(x, y)
        self.lifetime = 0.28
        self.age = 0.0
        self.sparks: list[SparkParticle] = []

        # Direction opposée au tir avec dispersion en cône
        base_rad = math.radians(impact_angle_deg + 180.0)
        for _ in range(8):
            spread = random.uniform(-0.6, 0.6)
            angle = base_rad + spread
            speed = random.uniform(90, 260)
            vel = pygame.Vector2(math.cos(angle) * speed, math.sin(angle) * speed)
            color = random.choice([(255, 240, 100), (255, 160, 40), (255, 80, 30)])
            self.sparks.append(SparkParticle(x, y, vel, color, lifetime=random.uniform(0.18, 0.26), radius=random.uniform(2.0, 3.2)))

    def update(self, dt: float) -> bool:
        self.age += dt
        if self.age >= self.lifetime:
            return False
        self.sparks = [s for s in self.sparks if s.update(dt)]
        return True

    def draw(self, surface: pygame.Surface) -> None:
        progress = self.age / self.lifetime
        # Flash initial blanc/doré ultra-bref
        if progress < 0.25:
            flash_r = int(12 * (1.0 - progress / 0.25))
            pygame.draw.circle(surface, (255, 255, 230), (int(self.center.x), int(self.center.y)), max(1, flash_r))

        for s in self.sparks:
            s.draw(surface)


# =============================================================================
# 3. CONFETTIS DE VICTOIRE
# =============================================================================
class ConfettiParticle:
    """Bout de papier festif multicolore tourbillonnant."""

    COLORS = [
        (241, 196, 15),  # Or
        (231, 76, 60),   # Rouge
        (46, 204, 113),  # Vert
        (52, 152, 219),  # Bleu
        (155, 89, 182),  # Violet
        (255, 255, 255), # Blanc
    ]

    def __init__(self, x: float, y: float) -> None:
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(random.uniform(-40, 40), random.uniform(80, 220))
        self.color = random.choice(self.COLORS)
        self.width = random.randint(6, 12)
        self.height = random.randint(4, 8)
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-280, 280)
        self.sway_phase = random.uniform(0, math.tau)

    def update(self, dt: float) -> None:
        self.sway_phase += dt * 4.0
        self.position.x += math.sin(self.sway_phase) * 45.0 * dt
        self.position.y += self.velocity.y * dt
        self.rotation += self.rot_speed * dt

    def draw(self, surface: pygame.Surface) -> None:
        conf_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        conf_surf.fill(self.color)
        rot_surf = pygame.transform.rotate(conf_surf, self.rotation)
        surface.blit(rot_surf, rot_surf.get_rect(center=(int(self.position.x), int(self.position.y))))


class VictoryCelebrationEffect:
    """Pluie de confettis et gerbe d'étoiles dorées célébrant la victoire."""

    def __init__(self, screen_width: int, screen_height: int) -> None:
        self.width = screen_width
        self.height = screen_height
        self.confettis: list[ConfettiParticle] = []
        self.spawn_timer = 0.0

        # Vague initiale
        for _ in range(80):
            x = random.uniform(50, screen_width - 50)
            y = random.uniform(-100, 200)
            self.confettis.append(ConfettiParticle(x, y))

    def update(self, dt: float) -> None:
        self.spawn_timer += dt
        if self.spawn_timer >= 0.08:
            self.spawn_timer = 0.0
            for _ in range(4):
                self.confettis.append(ConfettiParticle(random.uniform(50, self.width - 50), -20))

        for c in self.confettis:
            c.update(dt)

        # Nettoyage des confettis sortis de l'écran
        self.confettis = [c for c in self.confettis if c.position.y < self.height + 30]

    def draw(self, surface: pygame.Surface) -> None:
        for c in self.confettis:
            c.draw(surface)


# =============================================================================
# GESTIONNAIRE CENTRAL DES EFFETS (EFFECTS MANAGER)
# =============================================================================
class EffectsManager:
    """Coordinateur central de toutes les animations et particules en jeu."""

    _instance: Optional[EffectsManager] = None

    def __new__(cls) -> EffectsManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if getattr(self, "_initialized", False):
            return

        self._initialized = True
        self.tank_explosions: list[TankExplosionEffect] = []
        self.impacts: list[ImpactEffect] = []
        self.victory_effect: Optional[VictoryCelebrationEffect] = None

    def clear(self) -> None:
        """Réinitialise tous les effets visuels actifs."""
        self.tank_explosions.clear()
        self.impacts.clear()
        self.victory_effect = None

    def spawn_tank_explosion(self, x: float, y: float) -> None:
        """Déclenche une déflagration de char."""
        self.tank_explosions.append(TankExplosionEffect(x, y))

    def spawn_impact(self, x: float, y: float, angle_deg: float = 0.0) -> None:
        """Déclenche une gerbe d'étincelles lors d'un coup."""
        self.impacts.append(ImpactEffect(x, y, angle_deg))

    def trigger_victory(self, screen_width: int, screen_height: int) -> None:
        """Déclenche la pluie de confettis de victoire."""
        if self.victory_effect is None:
            self.victory_effect = VictoryCelebrationEffect(screen_width, screen_height)

    def stop_victory(self) -> None:
        self.victory_effect = None

    def update(self, dt: float) -> None:
        """Met à jour toutes les animations actives."""
        self.tank_explosions = [e for e in self.tank_explosions if e.update(dt)]
        self.impacts = [i for i in self.impacts if i.update(dt)]
        if self.victory_effect:
            self.victory_effect.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        """Dessine les effets dans l'ordre de profondeur approprié."""
        for imp in self.impacts:
            imp.draw(surface)

        for expl in self.tank_explosions:
            expl.draw(surface)

        if self.victory_effect:
            self.victory_effect.draw(surface)


# Instance globale partagée
effects_manager = EffectsManager()

