"""
Tree placement using polygonal trees from poly_trees.py.

Call `draw_trees()` after drawing the sky/buildings, before HUD.
"""

import math
import random
import pygame
from poly_trees import draw_tree_batch, invalidate_cache

_SEASON_VARIANT = {
    "spring": 4,
    "summer": 1,
    "autumn": 1,
    "winter": 0,
}

# ─────────────────────────────────────────────────────────────────────────────
# Artistic Controls (Tweak these to change forest look!)
# ─────────────────────────────────────────────────────────────────────────────
TREE_SIZE_MULT = 0.65       # Global scale for all trees (lower this to make them smaller)
FG_SIZE_MAX = 1.4           # Max scale for massive foreground trees (was 3.8)
FG_CLUSTER_MULT = 1.3       # Multiplier for the amount of foreground trees
BG_DENSITY_MULT = 1.2       # Multiplier for background forest density



# ─────────────────────────────────────────────────────────────────────────────
# Forest treeline (behind ground)
# ─────────────────────────────────────────────────────────────────────────────

_DISTANCE_FOG = [0.55, 0.30, 0.05]


def draw_forest_treeline(screen, w, h, ground_y, season, day, base_scale, weather):
    trees = []
    variant = _SEASON_VARIANT.get(season, 1)

    bands = [
        (0,  0.005, 0.60, (140, 220)),
        (1,  0.020, 0.85, (120, 180)),
    ]

    for band_idx, (seed_off, y_frac, sz_frac, step_rng) in enumerate(bands):
        rng = random.Random(band_idx + seed_off)
        band_y_base = ground_y + int(h * y_frac)
        band_fog = _DISTANCE_FOG[band_idx]

        x = -rng.randint(0, 20)
        while x < w + 20:
            tx = x + rng.randint(-4, 4)
            curve = math.sin(tx * 0.01 + band_idx) * 15
            band_y = int(band_y_base + curve)
            
            fh = 0.55 + rng.random() * 0.45
            sz = int(120 * base_scale * sz_frac * fh * TREE_SIZE_MULT)
            if sz >= 10:
                anchor_y = band_y
                trees.append((tx, anchor_y, sz, variant, band_fog))
            x += rng.randint(int(step_rng[0] / BG_DENSITY_MULT), int(step_rng[1] / BG_DENSITY_MULT))

    if trees:
        draw_tree_batch(screen, trees, season)


# ─────────────────────────────────────────────────────────────────────────────
# Foreground trees (on top of ground)
# ─────────────────────────────────────────────────────────────────────────────

def _generate_foreground_positions(w, h, day, base_scale, variant):
    rng = random.Random(0xA5F3)

    trees = []

    clusters = [
        (0.18, 3),
        (0.52, 4),
        (0.82, 2),
    ]

    for cluster_x, amount in clusters:
        amount = max(1, int(amount * FG_CLUSTER_MULT))
        for _ in range(amount):
            px = cluster_x + rng.uniform(-0.12, 0.12)
            px = max(0.02, min(0.98, px))

            depth = rng.uniform(0.80, 1.05)
            curve = math.sin(px * math.pi * 2.0) * 30
            anchor_y = int(h * depth + curve)

            sz = int(120 * base_scale * rng.uniform(1.0, FG_SIZE_MAX) * depth * TREE_SIZE_MULT)
            tx = int(w * px)
            
            if depth < 0.88:
                depth_z = 0
            elif depth < 0.96:
                depth_z = 1
            else:
                depth_z = 2

            trees.append((depth_z, tx, anchor_y, sz, variant))

    trees.sort(key=lambda t: (t[0], t[3]))
    return trees


def draw_foreground_trees(screen, w, h, ground_y, season, day, base_scale, weather):
    variant = _SEASON_VARIANT.get(season, 1)
    raw = _generate_foreground_positions(w, h, day, base_scale, variant)
    trees = []
    for depth_z, tx, anchor_y, sz, _ in raw:
        if sz < 18:
            continue
        effective_fog = _DISTANCE_FOG[depth_z] * 0.6
        trees.append((tx, anchor_y, sz, variant, effective_fog))
    if trees:
        draw_tree_batch(screen, trees, season)


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def draw_trees(screen, w, h, ground_y, season, day, base_scale, weather):
    draw_forest_treeline(screen, w, h, ground_y, season, day, base_scale, weather)
    
    t = pygame.time.get_ticks() / 1000.0
    for i in range(2):
        mist_y = ground_y - int(h * 0.05) + i * 30
        mist_h = int(h * 0.15)
        mist_surf = pygame.Surface((w, mist_h), pygame.SRCALPHA)
        alpha = 15 + int(math.sin(t * 0.5 + i) * 5)
        mist_surf.fill((180, 200, 255, alpha))
        screen.blit(mist_surf, (0, mist_y))
        
    draw_foreground_trees(screen, w, h, ground_y, season, day, base_scale, weather)
