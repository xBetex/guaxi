"""
fireflies.py — Glowing firefly particles for the Moon & Stars scene.

Fireflies appear near the ground at dusk and night, drifting lazily
with organic sinusoidal movement and pulsing glow.
"""
import pygame
import math
import random


class Firefly:
    _GLOW_CACHE = {}

    @classmethod
    def get_glow_surf(cls, color, size, brightness_level):
        """Returns a cached glow surface for a given color, size, and quantized brightness."""
        key = (color, size, brightness_level)
        if key in cls._GLOW_CACHE:
            return cls._GLOW_CACHE[key]

        brightness = brightness_level / 10.0
        glow_r = size + 5
        glow_surf = pygame.Surface((glow_r * 2 + 2, glow_r * 2 + 2), pygame.SRCALPHA)
        
        for r in range(glow_r, 0, -1):
            a = int(brightness * 60 * (1 - r / glow_r) ** 1.5)
            if a > 0:
                pygame.draw.circle(
                    glow_surf,
                    (*color, a),
                    (glow_r + 1, glow_r + 1),
                    r,
                )
        
        cls._GLOW_CACHE[key] = glow_surf
        return glow_surf

    def __init__(self, w, h, ground_y):
        self.x = random.uniform(0, w)
        # Place fireflies at the tree level (around ground_y and foreground)
        # Trees span from ground_y to bottom of screen (h * 1.05)
        # So fireflies should be between ground_y - h * 0.05 and h
        self.y = random.uniform(ground_y - h * 0.05, h)
        self.vx = random.uniform(-18, 18)
        self.vy = random.uniform(-8, 8)
        self.phase = random.uniform(0, math.pi * 2)
        self.glow_phase = random.uniform(0, math.pi * 2)
        self.glow_speed = random.uniform(1.2, 3.5)
        self.drift_x = random.uniform(0.3, 1.2)
        self.drift_y = random.uniform(0.2, 0.8)
        self.size = random.choice([2, 2, 2, 3, 3])
        # Colour — mostly warm yellow-green, occasional blue-white
        if random.random() < 0.12:
            self.color = (120, 220, 255)   # rare blue
        elif random.random() < 0.08:
            self.color = (255, 200, 80)    # warm amber
        else:
            self.color = (180, 255, 100)   # typical green-yellow
        self.alpha = 0.0
        self.fade_in = True
        self.life = random.uniform(4.0, 14.0)
        self._age = 0.0
        self.w = w
        self.h = h
        self.ground_y = ground_y

    def update(self, dt, speed):
        s = max(0.05, speed)
        self._age += dt * s
        self.phase += dt * self.drift_x * s
        self.glow_phase += self.glow_speed * dt * s

        # Lazy sinusoidal drift
        self.x += (self.vx + math.sin(self.phase * 1.3) * 12) * dt * s
        self.y += (self.vy + math.cos(self.phase * 0.9) * 6) * dt * s

        # Fade in/out
        if self._age < 0.6:
            self.alpha = self._age / 0.6
        elif self._age > self.life - 0.8:
            self.alpha = max(0, (self.life - self._age) / 0.8)
        else:
            self.alpha = 1.0

        # Wrap horizontally, drift within vertical zone
        if self.x < -20:
            self.x = self.w + 10
        elif self.x > self.w + 20:
            self.x = -10
        self.y = max(self.ground_y - self.h * 0.08, min(self.h + 10, self.y))

    def is_dead(self):
        return self._age >= self.life

    def draw(self, surf):
        pulse = 0.55 + 0.45 * math.sin(self.glow_phase)
        brightness = self.alpha * pulse
        if brightness < 0.02:
            return

        brightness_level = int(brightness * 10)
        if brightness_level <= 0:
            return

        # Outer soft glow (cached)
        glow_surf = self.get_glow_surf(self.color, self.size, brightness_level)
        glow_r = self.size + 5
        surf.blit(glow_surf, (int(self.x) - glow_r - 1, int(self.y) - glow_r - 1),
                  special_flags=pygame.BLEND_RGBA_ADD)

        # Bright core
        core_a = int(brightness * 230)
        pygame.draw.circle(surf, (*self.color, core_a),
                           (int(self.x), int(self.y)), self.size)


class FireflySwarm:
    """Manages a pool of fireflies that appear at dusk and night."""

    def __init__(self):
        self.fireflies: list[Firefly] = []
        self._spawn_timer = 0.0

    def update(self, dt, hour, speed, w, h):
        # Fireflies active from dusk (hour 18) to dawn (hour 6)
        if 6.5 <= hour < 18.5:
            # Daytime — fade out and stop spawning
            for f in self.fireflies[:]:
                f._age = max(f.life - 0.5, f._age)  # force fade
                f.update(dt, speed)
                if f.is_dead():
                    self.fireflies.remove(f)
            return

        # Density ramps up at dusk and dawn
        if hour >= 18:
            intensity = min(1.0, (hour - 18) / 1.5)
        elif hour < 6:
            intensity = max(0.0, 1.0 - (hour - 4.5) / 1.5)
        else:
            intensity = 0.0

        ground_y = int(h * 0.78)
        target = int(intensity * 38)

        self._spawn_timer += dt * max(0.3, speed)
        if self._spawn_timer > 0.35 and len(self.fireflies) < target:
            self._spawn_timer = 0.0
            count = random.randint(1, 3)
            for _ in range(count):
                if len(self.fireflies) < target:
                    self.fireflies.append(Firefly(w, h, ground_y))

        for f in self.fireflies[:]:
            f.update(dt, speed)
            if f.is_dead():
                self.fireflies.remove(f)

    def draw(self, screen, w, h):
        if not self.fireflies:
            return
        for f in self.fireflies:
            f.draw(screen)

