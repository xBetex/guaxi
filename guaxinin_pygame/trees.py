"""
Tree placement using polygonal trees from poly_trees.py.

Call `draw_trees()` after drawing the sky/buildings, before HUD.
"""

import math
import random
import pygame
from tree_sheet import TreeSheet

_tree_sheet = None

def _get_tree_sheet():
    global _tree_sheet
    if _tree_sheet is None:
        _tree_sheet = TreeSheet()
    return _tree_sheet

# Variant selection is done dynamically.

# ─────────────────────────────────────────────────────────────────────────────
# Artistic Controls (Tweak these to change forest look!)
# ─────────────────────────────────────────────────────────────────────────────
TREE_SIZE_MULT = 1.0        # Global scale for all trees (lower this to make them smaller)
FG_SIZE_MAX = 1.5           # Max scale for massive foreground trees
FG_CLUSTER_MULT = 0.20      # Multiplier for the amount of foreground trees
BG_DENSITY_MULT = 0.40      # Multiplier for background forest density



# ─────────────────────────────────────────────────────────────────────────────
# Forest treeline (behind ground)
# ─────────────────────────────────────────────────────────────────────────────

_DISTANCE_FOG = [0.55, 0.30, 0.05]


def draw_forest_treeline(screen, w, h, ground_y, season, day, base_scale, weather):
    trees = []

    bands = [
        (0,  0.005, 0.60, 180),
        (1,  0.020, 0.85, 150),
    ]

    for band_idx, (seed_off, y_frac, sz_frac, spacing_base) in enumerate(bands):
        band_y_base = ground_y + int(h * y_frac)
        band_fog = _DISTANCE_FOG[band_idx]
        spacing = int(spacing_base / BG_DENSITY_MULT)

        x = (spacing // 2) * band_idx
        while x < w + 40:
            tx = x
            curve = math.sin(tx * 0.01 + band_idx) * 15
            band_y = int(band_y_base + curve)
            
            fh = 0.75
            sz = int(120 * base_scale * sz_frac * fh * TREE_SIZE_MULT)
            if sz >= 10:
                anchor_y = band_y
                variant = (x // spacing) % 2
                trees.append((tx, anchor_y, sz, variant, band_fog))
            x += spacing

    if trees:
        ts = _get_tree_sheet()
        for tx, anchor_y, sz, variant, band_fog in trees:
            img = ts.get(season, variant, sz)
            if img:
                rect = img.get_rect(midbottom=(tx, anchor_y))
                screen.blit(img, rect)


# ─────────────────────────────────────────────────────────────────────────────
# Foreground trees (on top of ground)
# ─────────────────────────────────────────────────────────────────────────────

def _generate_foreground_positions(w, h, day, base_scale):
    trees = []

    # ground_y is around 0.78. Put them right at the edge of the beach
    depth = 0.785
    num_trees = 6
    
    # Symmetrically spread them across the screen width
    spacing = w / max(1, num_trees - 1)
    
    for i in range(num_trees):
        x = i * spacing
        
        # Slight organic curve so they aren't perfectly flat
        curve = math.sin((x / w) * math.pi) * 4
        anchor_y = int(h * depth + curve)

        # Scale down the size so they aren't bigger than buildings
        sz = int(80 * base_scale * 1.5 * depth * TREE_SIZE_MULT)
        tx = int(x)
        
        depth_z = 0
        variant = i % 4
        trees.append((depth_z, tx, anchor_y, sz, variant))

    trees.sort(key=lambda t: (t[0], t[3]))
    return trees


def draw_foreground_trees(screen, w, h, ground_y, season, day, base_scale, weather):
    raw = _generate_foreground_positions(w, h, day, base_scale)
    trees = []
    for depth_z, tx, anchor_y, sz, variant in raw:
        if sz < 18:
            continue
        effective_fog = _DISTANCE_FOG[depth_z] * 0.6
        trees.append((tx, anchor_y, sz, variant, effective_fog))
    if trees:
        ts = _get_tree_sheet()
        for tx, anchor_y, sz, variant, band_fog in trees:
            img = ts.get(season, variant, sz)
            if img:
                rect = img.get_rect(midbottom=(tx, anchor_y))
                screen.blit(img, rect)


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def draw_trees(screen, w, h, ground_y, season, day, base_scale, weather):
    # draw_forest_treeline(screen, w, h, ground_y, season, day, base_scale, weather)
    
    t = pygame.time.get_ticks() / 1000.0
    for i in range(2):
        mist_y = ground_y - int(h * 0.05) + i * 30
        mist_h = int(h * 0.15)
        mist_surf = pygame.Surface((w, mist_h), pygame.SRCALPHA)
        alpha = 15 + int(math.sin(t * 0.5 + i) * 5)
        mist_surf.fill((180, 200, 255, alpha))
        screen.blit(mist_surf, (0, mist_y))
        
    draw_foreground_trees(screen, w, h, ground_y, season, day, base_scale, weather)
