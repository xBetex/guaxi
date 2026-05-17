"""
poly_trees.py — Simple polygonal trees that don't look simple (quieter version)

Changes:
- Jitter reduced by ~60% globally
- Detail thresholds raised: size>=80 for full detail (was 50)
- Fewer paint layers (shadow+mid+highlight often just 2 layers)
- Trunk stripes reduced and AO opacity halved
- Special variants (weeping, sakura, mystic, bonsai) slimmed down
- Fog desaturation softened a bit
- Winter snow only on largest trees
"""

import math, random, pygame
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# Palettes  [shadow, base, highlight, trunk_dark, trunk_light]
# ─────────────────────────────────────────────────────────────────────────────
_PAL = {
    "summer": [(30, 132, 73), (39, 174, 96), (46, 204, 113), (92, 58, 33), (131, 76, 50)],
    "autumn": [(211, 84, 0), (230, 126, 34), (243, 156, 18), (92, 58, 33), (131, 76, 50)],
    "winter": [(149, 165, 166), (189, 195, 199), (236, 240, 241), (92, 58, 33), (131, 76, 50)],
    "spring": [(214, 48, 49), (232, 67, 147), (253, 121, 168), (92, 58, 33), (131, 76, 50)],
}

_SNOW = (225, 233, 242)
_SNOW_SHADOW = (185, 200, 220)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _lerp(a, b, t):
    return tuple(max(0, min(255, int(a[i] + (b[i]-a[i])*t))) for i in range(3))

def _desaturate(col, amt):
    grey = int(col[0]*.299 + col[1]*.587 + col[2]*.114)
    return _lerp(col, (grey,grey,grey), amt)

def _fog_col(col, fog, fog_tint=(200,210,220)):
    if fog <= 0: return col
    c = _desaturate(col, fog*0.35)
    return _lerp(c, fog_tint, fog*0.30)

def _jitter_pts(pts, rng, amt):
    return [(x + rng.uniform(-amt, amt), y + rng.uniform(-amt*0.5, amt*0.5))
            for x, y in pts]

def _rng(season, variant, size):
    return random.Random(hash((season, variant, size)) & 0xFFFFFFFF)

# ─────────────────────────────────────────────────────────────────────────────
# Draw primitives
# ─────────────────────────────────────────────────────────────────────────────
def _poly(surf, col, pts):
    ipts = [(int(round(x)), int(round(y))) for x, y in pts]
    if len(ipts) >= 3:
        pygame.draw.polygon(surf, col, ipts)

def _elli(surf, col, cx, cy, rw, rh):
    rw, rh = max(1, int(rw)), max(1, int(rh))
    pygame.draw.ellipse(surf, col, (int(cx-rw), int(cy-rh), rw*2, rh*2))

def _line(surf, col, x0, y0, x1, y1, w=1):
    pygame.draw.line(surf, col,
                     (int(round(x0)), int(round(y0))),
                     (int(round(x1)), int(round(y1))), max(1, w))

# ─────────────────────────────────────────────────────────────────────────────
# Trunk
# ─────────────────────────────────────────────────────────────────────────────
def _draw_trunk(surf, cx, base_y, size, pal, rng, detail):
    trunk_h = max(4, int(size * 0.22))
    trunk_w = max(2, int(size * 0.09))
    top_y   = base_y - trunk_h

    segments = max(2, trunk_h // 8)
    seg_h = trunk_h / segments
    
    pts_l, pts_r, pts_mid = [], [], []
    twist_seed = rng.uniform(0, 100)
    for i in range(segments + 1):
        y = base_y - i * seg_h
        frac = i / segments
        twist = math.sin(frac * 4.0 + twist_seed) * size * 0.02
        w = trunk_w * (1.0 - frac * 0.2)
        pts_l.append((cx + twist - w/2, y))
        pts_mid.append((cx + twist, y))
        pts_r.append((cx + twist + w/2, y))
        
    _poly(surf, pal[3], pts_l + pts_r[::-1])

    if detail < 1:
        return top_y

    _poly(surf, pal[4], pts_mid + pts_r[::-1])
    
    # Ground integration
    for _ in range(max(2, int(size / 15))):
        gx = cx + rng.uniform(-size*0.12, size*0.12)
        gy = base_y + rng.uniform(-2, 4)
        gw = rng.uniform(2, size*0.06)
        gh = rng.uniform(1, size*0.03)
        _elli(surf, pal[0], gx, gy, gw, gh)

    if detail >= 2:
        stripe_w = max(1, trunk_w // 6)
        for _ in range(2):
            sx = cx - trunk_w//2 + rng.randint(0, max(1, trunk_w - stripe_w))
            sh = rng.randint(trunk_h//4, trunk_h)
            sy = top_y + rng.randint(0, trunk_h - sh)
            bright = rng.choice([-1, 1])
            sc = _lerp(pal[3], pal[4] if bright>0 else (0,0,0), 0.22)
            pygame.draw.rect(surf, sc, (sx, sy, stripe_w, sh))

    ao = pygame.Surface((trunk_w*3, trunk_w*2), pygame.SRCALPHA)
    pygame.draw.ellipse(ao, (0,0,0,28), (0, 0, trunk_w*3, trunk_w*2))
    surf.blit(ao, (cx - trunk_w*1.5, top_y - trunk_w))

    return top_y


# ─────────────────────────────────────────────────────────────────────────────
# Conifer
# ─────────────────────────────────────────────────────────────────────────────
def _draw_conifer(surf, cx, base_y, size, pal, rng, detail, season):
    top_y   = _draw_trunk(surf, cx, base_y, size, pal, rng, detail)
    layers  = max(2, int(size / 28))
    lean    = rng.uniform(-size*0.018, size*0.018)
    ch      = int(size * 0.82)

    for i in range(layers):
        prog   = i / max(layers-1, 1)
        tip_frac = i / layers
        base_frac = min((i + 1.15) / layers, 1.0)
        t_y    = top_y - ch * (1.0 - tip_frac)
        b_y    = top_y - ch * (1.0 - base_frac)
        
        # Stronger silhouette asymmetry
        left_scale = rng.uniform(0.75, 1.15)
        right_scale = rng.uniform(0.75, 1.15)
        base_hw = size * (0.08 + 0.34 * prog)
        l_hw = base_hw * left_scale
        r_hw = base_hw * right_scale
        jit = base_hw * 0.03 * detail

        shadow_pts = _jitter_pts(
            [(cx+lean, t_y), (cx-l_hw+lean*.3, b_y), (cx+lean, b_y)], rng, jit)
        _poly(surf, _lerp(pal[0], pal[1], 1-prog*0.5), shadow_pts)

        light_pts = _jitter_pts(
            [(cx+lean, t_y), (cx+lean, b_y), (cx+r_hw+lean*.3, b_y)], rng, jit)
        _poly(surf, _lerp(pal[1], pal[2], 1-prog*0.45), light_pts)

        if detail >= 2 and base_hw > 20 and i == layers-1:
            sliver_pts = _jitter_pts(
                [(cx+lean, t_y),
                 (cx+lean, t_y + (b_y-t_y)*0.45),
                 (cx+r_hw*.38+lean*.3, t_y + (b_y-t_y)*0.55)], rng, jit*0.5)
            _poly(surf, _lerp(pal[2], (255,255,255), 0.12), sliver_pts)

        if season == "winter" and i < 1 and size > 60:
            sw = base_hw * 0.38
            snow_pts = _jitter_pts(
                [(cx+lean, t_y),
                 (cx-sw+lean*.3, t_y+(b_y-t_y)*0.38),
                 (cx+sw+lean*.3, t_y+(b_y-t_y)*0.38)], rng, jit*0.4)
            _poly(surf, _SNOW, snow_pts)


# ─────────────────────────────────────────────────────────────────────────────
# Deciduous
# ─────────────────────────────────────────────────────────────────────────────
def _draw_deciduous(surf, cx, base_y, size, pal, rng, detail, season):
    top_y  = _draw_trunk(surf, cx, base_y, size, pal, rng, detail)
    
    cr = size * 0.40
    if season == "summer":
        cr = size * 0.48
    elif season == "spring":
        cr = size * 0.42
    elif season == "autumn":
        cr = size * 0.38
        
    ccy    = top_y - cr * 0.52

    if season == "winter":
        for b in range(max(3, int(size/28))):
            angle = 0.12*math.pi + (b/max(3,int(size/28)))*math.pi*0.76
            L     = cr * rng.uniform(0.52, 0.92)
            ex    = cx + int(math.cos(angle)*L)
            ey    = int(ccy - math.sin(angle)*L*0.78)
            w     = max(1, int(size*0.012))
            _line(surf, pal[4], cx, ccy, ex, ey, w)
            if detail >= 2:
                for _ in range(1):
                    ta = angle + rng.uniform(-0.3, 0.3)
                    tl = L * rng.uniform(0.25, 0.45)
                    _line(surf, pal[4], ex, ey,
                          ex+int(math.cos(ta)*tl), ey-int(math.sin(ta)*tl*0.78),
                          max(1, w-1))
        return

    n = max(3, int(size / 24))

    for b in range(n):
        a  = (b/n)*math.tau + rng.uniform(-0.25, 0.25)
        d  = rng.uniform(cr*0.02, cr*0.62)
        bw = cr * rng.uniform(0.58, 0.95)
        bh = bw * rng.uniform(0.72, 0.92)
        jit = bw * 0.04 * detail
        ox = cx + math.cos(a)*d + rng.uniform(-jit, jit)
        oy = ccy + math.sin(a)*d*0.70 + rng.uniform(-jit, jit)
        _elli(surf, pal[0], ox, oy, bw, bh)

    for b in range(max(2, n-1)):
        a  = (b/(n-1))*math.tau + rng.uniform(-0.15, 0.15)
        d  = rng.uniform(0, cr*0.25)
        bw = cr * rng.uniform(0.42, 0.80)
        bh = bw * rng.uniform(0.70, 0.90)
        ox = cx + math.cos(a)*d - cr*0.10
        oy = ccy + math.sin(a)*d*0.70 - cr*0.08
        _elli(surf, pal[1], ox, oy, bw*0.9, bh*0.9)

    if detail >= 2:
        for _ in range(max(1, n//4)):
            bw = cr * rng.uniform(0.22, 0.42)
            bh = bw * rng.uniform(0.55, 0.78)
            ox = cx - cr*rng.uniform(0.05, 0.35)
            oy = ccy - cr*rng.uniform(0.10, 0.40)
            _elli(surf, pal[2], ox, oy, bw, bh)

    if season == "autumn" and detail >= 2:
        for _ in range(max(1, int(size/50))):
            lx = cx + rng.randint(-int(cr), int(cr))
            ly = int(ccy) + rng.randint(-int(cr*.5), int(cr*0.9))
            pygame.draw.circle(surf, pal[1],
                               (lx, ly), max(1, int(size*0.018)))


# ─────────────────────────────────────────────────────────────────────────────
# Weeping Willow
# ─────────────────────────────────────────────────────────────────────────────
def _draw_weeping(surf, cx, base_y, size, pal, rng, detail, season):
    trunk_h = max(6, int(size * 0.28))
    trunk_w = max(2, int(size * 0.06))
    top_y = base_y - trunk_h

    pygame.draw.rect(surf, pal[3], (cx - trunk_w//2, top_y, trunk_w, trunk_h))
    pygame.draw.rect(surf, pal[4], (cx, top_y, max(1, trunk_w//2), trunk_h))

    if detail >= 2:
        stripe_w = max(1, trunk_w // 5)
        for _ in range(2):
            sx = cx - trunk_w//2 + rng.randint(0, max(1, trunk_w - stripe_w))
            sh = rng.randint(trunk_h//3, trunk_h)
            sy = top_y + rng.randint(0, trunk_h - sh)
            sc = _lerp(pal[3], pal[4], 0.25)
            pygame.draw.rect(surf, sc, (sx, sy, stripe_w, sh))

    cr = size * 0.38
    ccy = top_y - cr * 0.25
    jit = cr * 0.03 * detail

    willow_mid = (65, 98, 48)
    willow_light = (95, 125, 65)

    for _ in range(max(4, int(size / 16))):
        angle = rng.uniform(-0.6, 0.6)
        length = cr * rng.uniform(0.5, 1.0)
        droop = rng.uniform(0.4, 0.7)
        ex = cx + math.cos(angle) * length * 0.35 + rng.uniform(-jit, jit)
        ey = ccy + length * droop + rng.uniform(jit, jit*1.5)
        w = max(1, int(size * 0.014))
        _line(surf, willow_mid, cx + rng.uniform(-jit, jit), ccy, ex, ey, w)

    if detail >= 2:
        for _ in range(max(1, int(size / 24))):
            angle = rng.uniform(-0.4, 0.4)
            length = cr * rng.uniform(0.3, 0.6)
            droop = rng.uniform(0.5, 0.75)
            ex = cx + math.cos(angle) * length * 0.3
            ey = ccy + length * droop + rng.uniform(jit, jit*1.2)
            w = max(1, int(size * 0.010))
            _line(surf, willow_light, cx, ccy, ex, ey, w)


# ─────────────────────────────────────────────────────────────────────────────
# Bonsai
# ─────────────────────────────────────────────────────────────────────────────
def _draw_bonsai(surf, cx, base_y, size, pal, rng, detail, season):
    trunk_h = max(12, int(size * 0.42))
    trunk_w = max(2, int(size * 0.055))
    top_y = base_y - trunk_h

    for i in range(trunk_h):
        frac = i / trunk_h
        twist = int(math.sin(frac * math.pi * 2.2) * size * 0.04)
        tw = max(1, int(trunk_w * (1 - frac * 0.35)))
        col = _lerp(pal[3], pal[4], frac * 0.5 + 0.25)
        pygame.draw.rect(surf, col, (cx + twist - tw // 2, top_y + i, tw, 1))

    if detail >= 1:
        for _ in range(2):
            angle = rng.uniform(-math.pi * 0.3, math.pi * 0.3)
            length = size * rng.uniform(0.22, 0.42)
            ex = cx + int(math.cos(angle) * length)
            ey = top_y + int(-math.sin(angle) * length * 0.75)
            w = max(1, int(size * 0.012))
            _line(surf, pal[4], cx + rng.randint(-1, 1), top_y + rng.randint(0, trunk_h//3), ex, ey, w)

    cr = size * 0.28
    ccy = top_y - cr * 0.35
    jit = cr * 0.05 * detail

    for _ in range(max(2, int(size / 18))):
        bx = cx + rng.randint(-int(cr * 0.5), int(cr * 0.5))
        by = ccy + rng.randint(-int(cr * 0.4), int(cr * 0.25))
        bw = cr * rng.uniform(0.45, 0.85)
        bh = cr * rng.uniform(0.35, 0.65)
        ox = bx + rng.uniform(-jit, jit)
        oy = by + rng.uniform(-jit, jit)
        col = pal[1] if rng.random() > 0.5 else pal[2]
        _elli(surf, col, ox, oy, bw, bh)


# ─────────────────────────────────────────────────────────────────────────────
# Sakura
# ─────────────────────────────────────────────────────────────────────────────
def _draw_sakura(surf, cx, base_y, size, pal, rng, detail, season):
    trunk_h = max(6, int(size * 0.30))
    trunk_w = max(2, int(size * 0.065))
    top_y = base_y - trunk_h

    # Sweeping curved trunk
    segments = max(2, trunk_h // 8)
    seg_h = trunk_h / segments
    pts_l, pts_r, pts_mid = [], [], []
    twist_seed = rng.uniform(0, 100)
    for i in range(segments + 1):
        y = base_y - i * seg_h
        frac = i / segments
        twist = math.sin(frac * 3.0 + twist_seed) * size * 0.03 + (frac * size * 0.05) # slight lean right
        w = trunk_w * (1.0 - frac * 0.2)
        pts_l.append((cx + twist - w/2, y))
        pts_mid.append((cx + twist, y))
        pts_r.append((cx + twist + w/2, y))
        
    _poly(surf, pal[3], pts_l + pts_r[::-1])
    if detail >= 1:
        _poly(surf, pal[4], pts_mid + pts_r[::-1])

    cr = size * 0.42
    ccy = top_y - cr * 0.45
    jit = cr * 0.04 * detail

    pink_light = (255, 195, 210)
    pink_mid = (240, 155, 175)
    pink_dark = (210, 120, 145)

    n = max(5, int(size / 14))
    for b in range(n):
        # Sweeping angles
        angle = (b / n) * math.tau + rng.uniform(-0.3, 0.3)
        dist = rng.uniform(0, cr * 0.45)
        # Make them longer horizontally for wind-swept look
        bw = cr * rng.uniform(0.65, 1.2)
        bh = bw * rng.uniform(0.45, 0.7)
        ox = cx + math.cos(angle) * dist + rng.uniform(-jit, jit) + (cr * 0.2) # push right
        oy = ccy + math.sin(angle) * dist * 0.65 + rng.uniform(-jit, jit)
        col = pink_light if b % 3 == 0 else (pink_mid if b % 2 == 0 else pink_dark)
        _elli(surf, col, ox, oy, bw, bh)

    if detail >= 2:
        for _ in range(max(2, int(size / 22))):
            px = cx + rng.randint(-int(cr * 0.25), int(cr * 0.65))
            py = ccy + rng.randint(-int(cr * 0.35), int(cr * 0.2))
            pygame.draw.circle(surf, (255, 255, 255),
                               (px + rng.randint(-1, 1), py), max(1, int(size * 0.022)))

    # Drifting blossom particles!
    if detail >= 1:
        for _ in range(max(5, int(size / 5))):
            px = cx + rng.uniform(0, cr * 1.8) # drift to the right
            py = ccy + rng.uniform(-cr * 0.5, cr * 1.2) # drift down/across
            particle_sz = max(1, int(size * rng.uniform(0.01, 0.025)))
            # Add a slight transparency for depth
            col = pink_light if rng.random() > 0.5 else pink_mid
            pygame.draw.circle(surf, col, (int(px), int(py)), particle_sz)


# ─────────────────────────────────────────────────────────────────────────────
# Silhouette
# ─────────────────────────────────────────────────────────────────────────────
def _draw_silhouette(surf, cx, base_y, size, pal, rng, detail, season):
    is_conifer = rng.random() > 0.5
    dark = (18, 12, 8)
    light_dark = (32, 24, 18)

    if is_conifer:
        trunk_h = max(3, int(size * 0.14))
        trunk_w = max(2, int(size * 0.055))
        top_y = base_y - trunk_h

        layers = max(2, int(size / 28))
        lean = rng.uniform(-size * 0.015, size * 0.015)
        ch = int(size * 0.80)

        for i in range(layers):
            prog = i / max(layers - 1, 1)
            tip_frac = i / layers
            base_frac = min((i + 1.15) / layers, 1.0)
            t_y = top_y - ch * (1.0 - tip_frac)
            b_y = top_y - ch * (1.0 - base_frac)
            hw = size * (0.12 + 0.46 * prog)
            jit = hw * 0.03 * detail

            pts = _jitter_pts(
                [(cx + lean, t_y), (cx - hw + lean * 0.3, b_y), (cx + lean, b_y)], rng, jit)
            _poly(surf, dark, pts)
            light_pts = _jitter_pts(
                [(cx + lean, t_y), (cx + lean, b_y), (cx + hw + lean * 0.3, b_y)], rng, jit)
            _poly(surf, light_dark, light_pts)

        pygame.draw.rect(surf, dark, (cx - trunk_w//2, top_y, trunk_w, trunk_h))
    else:
        trunk_h = max(5, int(size * 0.26))
        trunk_w = max(2, int(size * 0.065))
        top_y = base_y - trunk_h
        pygame.draw.rect(surf, dark, (cx - trunk_w//2, top_y, trunk_w, trunk_h))

        cr = size * 0.36
        ccy = top_y - cr * 0.45
        jit = cr * 0.03 * detail

        for b in range(max(3, int(size / 20))):
            angle = (b / max(3, int(size / 20))) * math.tau + rng.uniform(-0.2, 0.2)
            dist = rng.uniform(0, cr * 0.45)
            bw = cr * rng.uniform(0.55, 0.95)
            bh = bw * rng.uniform(0.65, 0.9)
            ox = cx + math.cos(angle) * dist + rng.uniform(-jit, jit)
            oy = ccy + math.sin(angle) * dist * 0.7 + rng.uniform(-jit, jit)
            _elli(surf, dark, ox, oy, bw, bh)

        if detail >= 2:
            for b in range(max(1, int(size / 30))):
                angle = 0.15 * math.pi + (b / max(1, int(size / 30))) * math.pi * 0.7
                L = cr * rng.uniform(0.4, 0.75)
                ex = cx + int(math.cos(angle) * L)
                ey = int(ccy - math.sin(angle) * L * 0.75)
                w = max(1, int(size * 0.010))
                _line(surf, dark, cx, ccy, ex, ey, w)


# ─────────────────────────────────────────────────────────────────────────────
# Mystic
# ─────────────────────────────────────────────────────────────────────────────
def _draw_mystic(surf, cx, base_y, size, pal, rng, detail, season):
    trunk_h = max(4, int(size * 0.15))
    trunk_w = max(2, int(size * 0.045))
    top_y = base_y - trunk_h

    trunk_col = (45, 30, 50)
    pygame.draw.rect(surf, trunk_col, (cx - trunk_w//2, top_y, trunk_w, trunk_h))
    pygame.draw.rect(surf, (65, 45, 70), (cx, top_y, max(1, trunk_w//2), trunk_h))

    layers = max(2, int(size / 24))
    lean = rng.uniform(-size * 0.012, size * 0.012)
    ch = int(size * 0.82)

    glow_colors = [(120, 180, 255), (170, 130, 255), (140, 220, 180), (255, 200, 100)]
    inner_colors = [(150, 210, 255), (200, 160, 255), (170, 240, 200), (255, 220, 130)]

    for i in range(layers):
        prog = i / max(layers - 1, 1)
        tip_frac = i / layers
        base_frac = min((i + 1.15) / layers, 1.0)
        t_y = top_y - ch * (1.0 - tip_frac)
        b_y = top_y - ch * (1.0 - base_frac)
        hw = size * (0.12 + 0.30 * prog)
        jit = hw * 0.03 * detail

        col_idx = i % len(glow_colors)
        col = glow_colors[col_idx]
        inner_col = inner_colors[col_idx]
        shadow_col = tuple(max(0, c - 45) for c in col)

        shadow_pts = _jitter_pts(
            [(cx + lean, t_y), (cx - hw + lean * 0.3, b_y), (cx + lean, b_y)], rng, jit)
        _poly(surf, shadow_col, shadow_pts)

        light_pts = _jitter_pts(
            [(cx + lean, t_y), (cx + lean, b_y), (cx + hw + lean * 0.3, b_y)], rng, jit)
        _poly(surf, col, light_pts)

        if detail >= 2 and i == layers-1:
            inner_hw = hw * 0.45
            inner_pts = _jitter_pts(
                [(cx + lean, t_y + size * 0.03),
                 (cx - inner_hw + lean * 0.3, b_y - size * 0.04),
                 (cx + inner_hw + lean * 0.3, b_y - size * 0.04)], rng, jit * 0.4)
            _poly(surf, inner_col, inner_pts)

        if rng.random() > 0.7 and detail >= 2:
            sparkle_x = cx + lean + rng.randint(-int(hw * 0.3), int(hw * 0.3))
            sparkle_y = t_y + rng.randint(0, int(size * 0.08))
            pygame.draw.circle(surf, (255, 255, 255),
                               (int(sparkle_x), int(sparkle_y)), max(1, int(size * 0.016)))

    if detail >= 2 and rng.random() > 0.8:
        aura_surf = pygame.Surface((size * 1.4, size * 1.4), pygame.SRCALPHA)
        aura_col = glow_colors[rng.randint(0, len(glow_colors) - 1)]
        pygame.draw.circle(aura_surf, (*aura_col, 25),
                           (aura_surf.get_width() // 2, aura_surf.get_height() // 2),
                           size * 0.5)
        surf.blit(aura_surf, (cx - aura_surf.get_width() // 2, top_y - size * 0.3))


# ─────────────────────────────────────────────────────────────────────────────
# Cache
# ─────────────────────────────────────────────────────────────────────────────
_CACHE: dict = {}

_BUILDERS = {
    0: _draw_conifer,
    1: _draw_deciduous,
    2: _draw_weeping,
    3: _draw_bonsai,
    4: _draw_sakura,
    5: _draw_silhouette,
    6: _draw_mystic,
}

def invalidate_cache():
    _CACHE.clear()

def _get_surface(season, variant, size):
    key = (season, variant, size)
    if key in _CACHE:
        return _CACHE[key]

    pal    = _PAL.get(season, _PAL["summer"])
    rng    = _rng(season, variant, size)
    detail = 2 if size >= 80 else (1 if size >= 35 else 0)

    pad = max(4, int(size*0.12))
    sw  = size + pad*2
    sh  = size + pad*2
    surf = pygame.Surface((sw, sh), pygame.SRCALPHA)

    cx     = sw // 2
    base_y = sh - pad

    builder = _BUILDERS.get(variant % len(_BUILDERS), _draw_conifer)
    builder(surf, cx, base_y, size, pal, rng, detail, season)

    _CACHE[key] = surf
    return surf


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────
def draw_tree(screen, cx: int, base_y: int, size: int,
              season: str = "summer", variant: int = 0,
              fog: float = 0.0, fog_tint=(200,210,220)):
    if size < 6:
        return
    surf = _get_surface(season, variant, size)

    if fog > 0.01:
        fog_key = (season, variant, size, round(fog, 2))
        if fog_key not in _CACHE:
            fs = surf.copy()
            arr = pygame.surfarray.pixels3d(fs)
            grey = (arr[:,:,0]*.299 + arr[:,:,1]*.587 + arr[:,:,2]*.114).astype(arr.dtype)
            for ch in range(3):
                arr[:,:,ch] = (arr[:,:,ch]*(1-fog*.35) + grey*(fog*.35)).astype(arr.dtype)
            ft = fog_tint
            for ch in range(3):
                arr[:,:,ch] = (arr[:,:,ch]*(1-fog*.25) + ft[ch]*(fog*.25)).astype(arr.dtype)
            del arr
            _CACHE[fog_key] = fs
        surf = _CACHE[fog_key]

    pad  = max(4, int(size*0.12))
    screen.blit(surf, (cx - surf.get_width()//2, base_y - surf.get_height() + pad))


def draw_tree_batch(screen, trees, season: str = "summer"):
    for item in trees:
        cx, base_y, size, variant = item[:4]
        fog = item[4] if len(item) > 4 else 0.0
        draw_tree(screen, cx, base_y, size, season, variant, fog)


# ─────────────────────────────────────────────────────────────────────────────
# Demo
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    pygame.init()
    W, H = 900, 520
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("poly_trees  |  ←→ season  ↑↓ size  F fog")
    clock  = pygame.font.SysFont("monospace", 13)
    font   = clock
    clock  = pygame.time.Clock()

    seasons = ["summer","autumn","winter","spring"]
    si, sz, fog = 0, 80, 0.0

    SKY  = {"summer":(88,150,205),"autumn":(158,118,78),"winter":(168,182,205),"spring":(125,180,218)}
    GND  = {"summer":(50,88,35),"autumn":(75,60,28),"winter":(192,205,220),"spring":(65,112,50)}

    running = True
    while running:
        for e in pygame.event.get():
            if e.type == pygame.QUIT: running = False
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RIGHT: si=(si+1)%4; invalidate_cache()
                if e.key == pygame.K_LEFT:  si=(si-1)%4; invalidate_cache()
                if e.key == pygame.K_UP:    sz=min(200,sz+8)
                if e.key == pygame.K_DOWN:  sz=max(16,sz-8)
                if e.key == pygame.K_f:     fog=0.0 if fog>0 else 0.55

        season = seasons[si]
        screen.fill(SKY[season])
        gnd_y = int(H*0.68)
        pygame.draw.rect(screen, GND[season], (0, gnd_y, W, H-gnd_y))

        rng_row = random.Random(season+str(sz))
        for x in range(30, W, 26):
            v = rng_row.randint(0, 6)
            s = int(sz*0.38) + rng_row.randint(-4,4)
            draw_tree(screen, x, gnd_y-8, max(12,s), season, v, fog*0.6)

        rng_row2 = random.Random("mid"+season)
        for x in range(50, W, 50):
            v = rng_row2.randint(0, 6)
            s = int(sz*0.65) + rng_row2.randint(-8,8)
            draw_tree(screen, x, gnd_y+4, max(20,s), season, v, fog*0.8)

        rng_row3 = random.Random("fg"+season+str(sz))
        for x in range(80, W, 90):
            v = rng_row3.randint(0, 6)
            s = sz + rng_row3.randint(-12,12)
            draw_tree(screen, x, gnd_y+18, max(30,s), season, v, fog)

        hud = font.render(
            f"season:{season}  size:{sz}  fog:{fog:.2f}  "
            f"cache:{len(_CACHE)}  |  ←→ season  ↑↓ size  F fog",
            True, (235,230,220))
        screen.blit(hud, (10,10))
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()