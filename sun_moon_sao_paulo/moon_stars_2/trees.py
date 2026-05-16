"""
Tree placement using polygonal trees from poly_trees.py.

Call `draw_trees()` after drawing the sky/buildings, before HUD.
"""

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
# Forest treeline (behind ground)
# ─────────────────────────────────────────────────────────────────────────────

_DISTANCE_FOG = [0.55, 0.30, 0.05]


def draw_forest_treeline(screen, w, h, ground_y, season, day, base_scale, weather):
    trees = []
    variant = _SEASON_VARIANT.get(season, 1)

    bands = [
        (0,  0.020, 0.28, (28, 44)),
        (1,  0.006, 0.38, (22, 36)),
        (2, -0.008, 0.50, (16, 28)),
    ]

    for band_idx, (seed_off, y_frac, sz_frac, step_rng) in enumerate(bands):
        rng = random.Random(band_idx + seed_off)
        band_y = ground_y - int(h * y_frac)
        band_fog = _DISTANCE_FOG[band_idx]

        x = -rng.randint(0, 20)
        while x < w + 20:
            tx = x + rng.randint(-4, 4)
            fh = 0.55 + rng.random() * 0.45
            sz = int(72 * base_scale * sz_frac * fh)
            if sz >= 10:
                anchor_y = band_y - sz + 18
                trees.append((tx, anchor_y, sz, variant, band_fog))
            x += rng.randint(*step_rng)

    if trees:
        draw_tree_batch(screen, trees, season)


# ─────────────────────────────────────────────────────────────────────────────
# Foreground trees (on top of ground)
# ─────────────────────────────────────────────────────────────────────────────

def _generate_foreground_positions(w, h, day, base_scale, variant):
    rng = random.Random(0xA5F3)
    bands = [
        (0, 7,  0.92, 0.68, 0.14),
        (1, 8,  0.96, 0.86, 0.12),
        (2, 6,  1.00, 1.10, 0.16),
    ]

    trees = []
    for depth_z, count, y_depth, sz_base, x_spacing in bands:
        slot_w = 1.0 / count
        for i in range(count):
            slot_start = i * slot_w
            px = slot_start + rng.uniform(0.02, slot_w - 0.02)
            px = max(0.01, min(0.99, px))
            sz_mul = rng.uniform(0.82, 1.22)
            sz = int(100 * base_scale * sz_base * sz_mul * y_depth)
            tx = int(w * px)
            anchor_y = int(h * y_depth * 0.72)
            trees.append((depth_z, tx, anchor_y, sz, variant))
    trees.sort(key=lambda t: (t[0], t[2]))
    return trees


def draw_foreground_trees(screen, w, h, ground_y, season, day, base_scale, weather):
    variant = _SEASON_VARIANT.get(season, 1)
    raw = _generate_foreground_positions(w, h, day, base_scale, variant)
    trees = []
    for depth_z, tx, _, sz, _ in raw:
        if sz < 18:
            continue
        effective_fog = _DISTANCE_FOG[depth_z] * 0.6
        anchor_y = ground_y + int(sz * 0.15)
        trees.append((tx, anchor_y, sz, variant, effective_fog))
    if trees:
        draw_tree_batch(screen, trees, season)


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def draw_trees(screen, w, h, ground_y, season, day, base_scale, weather):
    draw_forest_treeline(screen, w, h, ground_y, season, day, base_scale, weather)
    draw_foreground_trees(screen, w, h, ground_y, season, day, base_scale, weather)
