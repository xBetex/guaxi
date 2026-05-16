"""
poly_trees.py — Simple polygonal trees that don't look simple.

The shapes are still just polygons and ellipses.
What sells them:
  - per-tree micro-jitter on every point (no two trees identical)
  - 2-3 paint layers per shape (dark base → mid → highlight sliver)
  - trunk texture via thin vertical rects with random brightness offsets
  - ambient occlusion darkening where trunk meets canopy
  - size-driven detail: large trees get more layers; tiny far trees get one flat fill
  - fog tint that also desaturates (not just alpha-fades)
"""

import math, random, pygame
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# Palettes  [shadow, base, highlight, trunk_dark, trunk_light]
# ─────────────────────────────────────────────────────────────────────────────
_PAL = {
    "summer": [(22,58,18),(38,88,28),(68,130,48),(36,26,16),(60,44,26)],
    "autumn": [(130,44,10),(185,82,16),(215,135,28),(48,30,16),(70,48,26)],
    "winter": [(48,62,80),(72,95,118),(105,135,158),(42,38,36),(64,58,52)],
    "spring": [(48,105,44),(82,148,60),(120,195,85),(38,28,16),(58,44,26)],
}

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
    c = _desaturate(col, fog*0.55)
    return _lerp(c, fog_tint, fog*0.45)

def _jitter_pts(pts, rng, amt):
    """Nudge every point by ±amt pixels — breaks the 'perfect polygon' read."""
    return [(x + rng.uniform(-amt, amt), y + rng.uniform(-amt*0.7, amt*0.7))
            for x, y in pts]

def _rng(season, variant, size):
    return random.Random(hash((season, variant, size)) & 0xFFFFFFFF)

# ─────────────────────────────────────────────────────────────────────────────
# Draw primitives  (all accept float coords, round internally)
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

    # base rect
    pygame.draw.rect(surf, pal[3],
                     (cx - trunk_w//2, top_y, trunk_w, trunk_h))

    if detail < 1:
        return top_y

    # light side
    pygame.draw.rect(surf, pal[4],
                     (cx, top_y, max(1, trunk_w//2), trunk_h))

    # bark texture: random vertical brightness stripes
    if detail >= 2:
        stripe_w = max(1, trunk_w // 5)
        for _ in range(4):
            sx = cx - trunk_w//2 + rng.randint(0, max(1, trunk_w - stripe_w))
            sh = rng.randint(trunk_h//4, trunk_h)
            sy = top_y + rng.randint(0, trunk_h - sh)
            bright = rng.choice([-1, 1])
            sc = _lerp(pal[3], pal[4] if bright>0 else (0,0,0), 0.22)
            pygame.draw.rect(surf, sc, (sx, sy, stripe_w, sh))

    # ambient occlusion blob at trunk/canopy join
    ao = pygame.Surface((trunk_w*4, trunk_w*2), pygame.SRCALPHA)
    pygame.draw.ellipse(ao, (0,0,0,55), (0, 0, trunk_w*4, trunk_w*2))
    surf.blit(ao, (cx - trunk_w*2, top_y - trunk_w))

    return top_y


# ─────────────────────────────────────────────────────────────────────────────
# Conifer
# ─────────────────────────────────────────────────────────────────────────────
def _draw_conifer(surf, cx, base_y, size, pal, rng, detail, season):
    top_y   = _draw_trunk(surf, cx, base_y, size, pal, rng, detail)
    layers  = max(2, int(size / 20))
    lean    = rng.uniform(-size*0.025, size*0.025)
    ch      = int(size * 0.82)                    # total canopy height

    for i in range(layers):
        prog   = i / max(layers-1, 1)
        t_y    = top_y - ch * 0.08 + (i / layers) * ch * 0.70
        b_y    = t_y + (ch / layers) * 1.15
        hw     = size * (0.18 + 0.40 * prog)
        jit    = hw * 0.06 * detail

        # shadow side
        shadow_pts = _jitter_pts(
            [(cx+lean, t_y), (cx-hw+lean*.3, b_y), (cx+lean, b_y)], rng, jit)
        _poly(surf, _lerp(pal[0], pal[1], 1-prog*0.5), shadow_pts)

        # light side
        light_pts = _jitter_pts(
            [(cx+lean, t_y), (cx+lean, b_y), (cx+hw+lean*.3, b_y)], rng, jit)
        _poly(surf, _lerp(pal[1], pal[2], 1-prog*0.45), light_pts)

        # highlight sliver on light side (only when big enough)
        if detail >= 2 and hw > 14:
            sliver_pts = _jitter_pts(
                [(cx+lean, t_y),
                 (cx+lean, t_y + (b_y-t_y)*0.45),
                 (cx+hw*.38+lean*.3, t_y + (b_y-t_y)*0.55)], rng, jit*0.5)
            _poly(surf, _lerp(pal[2], (255,255,255), 0.12), sliver_pts)

        # snow ledge
        if season == "winter" and i < max(1, layers//3):
            sw = hw * 0.48
            snow_pts = _jitter_pts(
                [(cx+lean, t_y),
                 (cx-sw+lean*.3, t_y+(b_y-t_y)*0.38),
                 (cx+sw+lean*.3, t_y+(b_y-t_y)*0.38)], rng, jit*0.4)
            _poly(surf, (225,233,242), snow_pts)


# ─────────────────────────────────────────────────────────────────────────────
# Deciduous
# ─────────────────────────────────────────────────────────────────────────────
def _draw_deciduous(surf, cx, base_y, size, pal, rng, detail, season):
    top_y  = _draw_trunk(surf, cx, base_y, size, pal, rng, detail)
    cr     = size * 0.40
    ccy    = top_y - cr * 0.52

    if season == "winter":
        # bare: just branch lines, no fill
        for b in range(max(4, int(size/22))):
            angle = 0.12*math.pi + (b/max(4,int(size/22)))*math.pi*0.76
            L     = cr * rng.uniform(0.52, 0.92)
            ex    = cx + int(math.cos(angle)*L)
            ey    = int(ccy - math.sin(angle)*L*0.78)
            w     = max(1, int(size*0.016))
            _line(surf, pal[4], cx, ccy, ex, ey, w)
            # secondary twigs
            if detail >= 1:
                for _ in range(2):
                    ta = angle + rng.uniform(-0.4, 0.4)
                    tl = L * rng.uniform(0.25, 0.45)
                    _line(surf, pal[4], ex, ey,
                          ex+int(math.cos(ta)*tl), ey-int(math.sin(ta)*tl*0.78),
                          max(1, w-1))
        return

    # blob count scales with size
    n = max(3, int(size / 16))

    # layer 1: dark shadow blobs
    for b in range(n):
        a  = (b/n)*math.tau + rng.uniform(-0.35, 0.35)
        d  = rng.uniform(cr*0.05, cr*0.42)
        bw = cr * rng.uniform(0.58, 0.95)
        bh = bw * rng.uniform(0.72, 0.92)
        jit = bw * 0.07 * detail
        ox = cx + math.cos(a)*d + rng.uniform(-jit, jit)
        oy = ccy + math.sin(a)*d*0.70 + rng.uniform(-jit, jit)
        _elli(surf, pal[0], ox, oy, bw, bh)

    # layer 2: mid blobs, offset toward light (upper-left)
    for b in range(max(2, n-1)):
        a  = (b/(n-1))*math.tau + rng.uniform(-0.25, 0.25)
        d  = rng.uniform(0, cr*0.30)
        bw = cr * rng.uniform(0.42, 0.80)
        bh = bw * rng.uniform(0.70, 0.90)
        ox = cx + math.cos(a)*d - cr*0.10
        oy = ccy + math.sin(a)*d*0.70 - cr*0.08
        _elli(surf, pal[1], ox, oy, bw*0.9, bh*0.9)

    # layer 3: highlight slivers — light source upper-left
    if detail >= 1:
        for _ in range(max(1, n//3)):
            bw = cr * rng.uniform(0.22, 0.42)
            bh = bw * rng.uniform(0.55, 0.78)
            ox = cx - cr*rng.uniform(0.05, 0.35)
            oy = ccy - cr*rng.uniform(0.10, 0.40)
            _elli(surf, pal[2], ox, oy, bw, bh)

    # autumn leaf scatter
    if season == "autumn" and detail >= 1:
        for _ in range(max(2, int(size/30))):
            lx = cx + rng.randint(-int(cr), int(cr))
            ly = int(ccy) + rng.randint(-int(cr*.5), int(cr*0.9))
            pygame.draw.circle(surf, pal[1],
                               (lx, ly), max(1, int(size*0.022)))


# ─────────────────────────────────────────────────────────────────────────────
# Cache  {(season, variant, size): Surface}
# ─────────────────────────────────────────────────────────────────────────────
_CACHE: dict = {}

_BUILDERS = {0: _draw_conifer, 1: _draw_deciduous}


def invalidate_cache():
    _CACHE.clear()


def _get_surface(season, variant, size):
    key = (season, variant, size)
    if key in _CACHE:
        return _CACHE[key]

    pal    = _PAL.get(season, _PAL["summer"])
    rng    = _rng(season, variant, size)
    detail = 2 if size >= 50 else (1 if size >= 24 else 0)

    # canvas: transparent, tree centred horizontally, trunk base at bottom centre
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
    """
    Draw one tree.  cx/base_y = trunk base centre.  fog in [0,1].
    """
    if size < 6:
        return
    surf = _get_surface(season, variant, size)

    if fog > 0.01:
        # fog: tint + desaturate pixel data (done once then re-cached under fog key)
        fog_key = (season, variant, size, round(fog, 2))
        if fog_key not in _CACHE:
            fs = surf.copy()
            arr = pygame.surfarray.pixels3d(fs)
            grey = (arr[:,:,0]*.299 + arr[:,:,1]*.587 + arr[:,:,2]*.114).astype(arr.dtype)
            for ch in range(3):
                arr[:,:,ch] = (arr[:,:,ch]*(1-fog*.55) + grey*(fog*.55)).astype(arr.dtype)
            ft = fog_tint
            for ch in range(3):
                arr[:,:,ch] = (arr[:,:,ch]*(1-fog*.40) + ft[ch]*(fog*.40)).astype(arr.dtype)
            del arr
            _CACHE[fog_key] = fs
        surf = _CACHE[fog_key]

    pad  = max(4, int(size*0.12))
    screen.blit(surf, (cx - surf.get_width()//2, base_y - surf.get_height() + pad))


def draw_tree_batch(screen, trees, season: str = "summer"):
    """
    trees: iterable of (cx, base_y, size, variant)
                     or (cx, base_y, size, variant, fog)
    """
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

        # forest row (far, small)
        rng_row = random.Random(season+str(sz))
        for x in range(30, W, 26):
            v = rng_row.randint(0,1)
            s = int(sz*0.38) + rng_row.randint(-4,4)
            draw_tree(screen, x, gnd_y-8, max(12,s), season, v, fog*0.6)

        # mid row
        rng_row2 = random.Random("mid"+season)
        for x in range(50, W, 50):
            v = rng_row2.randint(0,1)
            s = int(sz*0.65) + rng_row2.randint(-8,8)
            draw_tree(screen, x, gnd_y+4, max(20,s), season, v, fog*0.8)

        # foreground row (large)
        rng_row3 = random.Random("fg"+season+str(sz))
        for x in range(80, W, 90):
            v = rng_row3.randint(0,1)
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
