import pygame
import math
import random
import os

SPRITE_DIR = "sprites"


class Gfx:
    _cache = {}
    _pixel_cache = {}

    @classmethod
    def init(cls):
        os.makedirs(SPRITE_DIR, exist_ok=True)

    @classmethod
    def get(cls, name, size, variant=0):
        key = (name, size, variant)
        if key in cls._cache:
            return cls._cache[key]
        if name.startswith("tree_"):
            fname = f"{name}_v{variant}.png"
        else:
            fname = f"{name}.png"
        path = os.path.join(SPRITE_DIR, fname)
        if os.path.exists(path):
            img = pygame.image.load(path).convert_alpha()
            surf = pygame.transform.scale(img, (size, size))
        else:
            surf = cls._gen(name, size, variant)
        cls._cache[key] = surf
        return surf

    @classmethod
    def _pixel_grid(cls, name, grid_size, variant=0):
        key = ("_grid", name, grid_size, variant)
        if key in cls._pixel_cache:
            return cls._pixel_cache[key].copy()
        g = grid_size
        c = g // 2
        surf = pygame.Surface((g, g), pygame.SRCALPHA)

        if name == "sun":
            for y in range(g):
                for x in range(g):
                    dx, dy = x - c, y - c
                    d = math.sqrt(dx * dx + dy * dy)
                    if d > c:
                        continue
                    t = d / c
                    r = min(255, 255 - int(40 * t))
                    gv = min(255, 210 - int(50 * t))
                    b = min(255, 80 - int(30 * t))
                    surf.set_at((x, y), (r, gv, b))

        elif name == "moon":
            rng = random.Random(42)
            craters = [
                (c + int(0.10 * c), c - int(0.20 * c), int(0.30 * c)),
                (c - int(0.26 * c), c + int(0.14 * c), int(0.24 * c)),
                (c + int(0.38 * c), c - int(0.08 * c), int(0.18 * c)),
                (c + int(0.20 * c), c - int(0.32 * c), int(0.15 * c)),
                (c - int(0.37 * c), c + int(0.26 * c), int(0.11 * c)),
                (c + int(0.08 * c), c + int(0.12 * c), int(0.16 * c)),
            ]
            for y in range(g):
                for x in range(g):
                    dx, dy = x - c, y - c
                    d = math.sqrt(dx * dx + dy * dy)
                    if d > c:
                        continue
                    t = d / c
                    base = min(255, int(250 - t * 30))
                    rv, gv, bv = base, base - 4, base - 12
                    for cx2, cy2, cr in craters:
                        cd = math.sqrt((x - cx2) ** 2 + (y - cy2) ** 2)
                        if cd < cr:
                            if x > cx2:
                                rv = int(rv * 0.70)
                                gv = int(gv * 0.67)
                                bv = int(bv * 0.65)
                            if x < cx2 - 2:
                                rv = min(255, rv + 12)
                                gv = min(255, gv + 10)
                                bv = min(255, bv + 6)
                            if cd < cr * 0.5:
                                rv = int(rv * 0.82)
                                gv = int(gv * 0.80)
                                bv = int(bv * 0.78)
                            break
                    noise = (x * 197 + y * 313) % 25
                    if noise < 3:
                        rv = min(255, rv + 5)
                        gv = min(255, gv + 4)
                        bv = min(255, bv + 2)
                    surf.set_at((x, y), (min(255, rv), min(255, gv), min(255, bv)))

        elif name in ("tree_summer", "tree_autumn", "tree_winter", "tree_spring"):
            rng3 = random.Random(variant * 137 + 42)
            tw = max(2, g // 5)
            th = g * 2 // 5
            tx = c + rng3.randint(-1, 1)

            trunk_r, trunk_g, trunk_b = 82, 48, 28
            canopy = {"tree_summer": (42, 118, 48), "tree_autumn": (180, 95, 30),
                      "tree_winter": (130, 135, 145), "tree_spring": (70, 140, 60)}

            for y in range(g - th, g):
                for x in range(max(0, tx - tw // 2), min(g, tx + tw // 2 + 1)):
                    shade = ((x * 7 + y * 13) % 5 - 2) * 4
                    surf.set_at((x, y), (trunk_r + shade, trunk_g + shade, trunk_b + shade))

            cr = g * 2 // 5 + rng3.randint(-1, 1)
            cy3 = g - th - cr // 2 + rng3.randint(-2, 0)
            ox = c + rng3.randint(-2, 2)
            base_r, base_g, base_b = canopy[name]

            for y in range(g):
                for x in range(g):
                    dx, dy = x - ox, y - cy3
                    if dx * dx + dy * dy <= cr * cr:
                        n = (x * 53 + y * 97 + variant * 7) % 14
                        s = 0 if n < 5 else (6 if n < 9 else -6)
                        bloom = n % 4
                        rv = base_r + s + bloom * 3
                        gv = base_g + s + bloom * 5
                        bv = base_b + s + bloom * 2
                        if name == "tree_spring" and bloom > 2:
                            rv = min(255, rv + 15)
                            gv = max(0, gv - 8)
                        elif name == "tree_winter" and bloom > 1:
                            rv = min(255, rv + 8)
                            gv = min(255, gv + 10)
                            bv = min(255, bv + 12)
                        surf.set_at((x, y), (min(255, rv), min(255, gv), min(255, bv)))

        elif name == "star":
            c2 = g // 2
            r2 = max(1, g // 2)
            pygame.draw.circle(surf, (255, 255, 255), (c2, c2), r2)

        cls._pixel_cache[key] = surf.copy()
        return surf

    @classmethod
    def _gen(cls, name, size, variant=0):
        grid = max(8, min(48, size // 4))
        pix = cls._pixel_grid(name, grid, variant)
        result = pygame.transform.scale(pix, (size, size))
        cls._cache[(name, size, variant)] = result
        if name.startswith("tree_"):
            fname = f"{name}_v{variant}.png"
        else:
            fname = f"{name}.png"
        path = os.path.join(SPRITE_DIR, fname)
        if not os.path.exists(path):
            pygame.image.save(result, path)
        return result
