# celestial.py
import pygame
import math
import random
from datetime import datetime
from data import CRATERS

PIXEL_GRID = 64
_pixel_cache = {}

def compute_moon_phase(dt):
    known = datetime(2000, 1, 6, 18, 14, 0)
    days = (dt - known).total_seconds() / 86400.0
    cycle = 29.53058867
    return (days % cycle) / cycle

def get_phase_name(phase):
    names = [
        "New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
        "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent"
    ]
    idx = int((phase + 0.0625) * 8) % 8
    return names[idx]

def _build_pixel_celestial(name, size, **kwargs):
    """Build pixel art for celestial bodies using same grid system"""
    key = (name, size, tuple(sorted(kwargs.items())))
    if key in _pixel_cache:
        return _pixel_cache[key].copy()
    
    grid = PIXEL_GRID
    target = max(4, size)
    cx = cy = grid // 2
    radius = grid // 2 - 2
    
    grid_surf = pygame.Surface((grid, grid), pygame.SRCALPHA)
    
    if name == "sun":
        hour = kwargs.get("hour", 12)
        progress = kwargs.get("progress", 0.5)
        
        for y in range(grid):
            for x in range(grid):
                dx = x - cx
                dy = y - cy
                d = math.sqrt(dx*dx + dy*dy)
                
                if d > radius:
                    continue
                
                t = d / radius
                
                # Solar gradient
                r = min(255, 255 - int(30 * t))
                g = min(255, 200 - int(40 * t))
                b = min(255, 80 - int(50 * t))
                
                # Add sunspot noise
                noise = (x * 131 + y * 253) % 100
                if noise < 5 and t > 0.3:
                    r = int(r * 0.7)
                    g = int(g * 0.6)
                    b = int(b * 0.5)
                elif noise > 95 and t < 0.6:
                    r = min(255, r + 20)
                    g = min(255, g + 15)
                    b = min(255, b + 10)
                
                grid_surf.set_at((x, y), (r, g, b))
    
    elif name == "sun_glow":
        for i in range(6):
            gr = int(radius * (1.0 + i * 0.3))
            alpha = max(1, int(15 / (i + 1) * kwargs.get("vis", 1)))
            for y in range(grid):
                for x in range(grid):
                    dx = x - cx
                    dy = y - cy
                    d = math.sqrt(dx*dx + dy*dy)
                    if abs(d - gr) < 2:
                        color = (255, 200, 100, alpha)
                        existing = grid_surf.get_at((x, y))
                        if existing[3] < alpha:
                            grid_surf.set_at((x, y), color)
    
    elif name == "moon":
        mr = int(radius * 0.85)
        
        def base_color(t):
            if t < 0.12: return (250, 245, 237)
            if t < 0.30: return (238, 230, 222)
            if t < 0.50: return (218, 208, 202)
            if t < 0.70: return (185, 175, 172)
            if t < 0.85: return (140, 130, 132)
            if t < 0.95: return (85, 75, 82)
            return (45, 38, 52)
        
        gcr = [(cx + int(dx * mr), cy + int(dy * mr), max(2, int(size * mr * 0.8))) 
               for dx, dy, size in CRATERS]
        
        for y in range(grid):
            for x in range(grid):
                dx = x - cx
                dy = y - cy
                d = math.sqrt(dx*dx + dy*dy)
                
                if d > mr + 0.5:
                    continue
                
                t = d / mr if mr > 0 else 0
                r_, g_, b_ = base_color(t)
                
                for gx, gy, gr in gcr:
                    cdx = x - gx
                    cdy = y - gy
                    cd = math.sqrt(cdx*cdx + cdy*cdy)
                    if cd <= gr:
                        if cdx > 0:
                            r_ = int(r_ * 0.70)
                            g_ = int(g_ * 0.67)
                            b_ = int(b_ * 0.65)
                        if cdx < -2:
                            r_ = min(255, r_ + 14)
                            g_ = min(255, g_ + 10)
                            b_ = min(255, b_ + 6)
                        if cd / gr < 0.5:
                            r_ = int(r_ * 0.82)
                            g_ = int(g_ * 0.80)
                            b_ = int(b_ * 0.78)
                        break
                
                n = (x * 197 + y * 313 + 42) % 101
                if n < 8:
                    r_ = min(255, r_ + 6)
                    g_ = min(255, g_ + 5)
                    b_ = min(255, b_ + 3)
                elif n > 92:
                    r_ = int(r_ * 0.94)
                    g_ = int(g_ * 0.93)
                    b_ = int(b_ * 0.92)
                
                grid_surf.set_at((x, y), (min(255, r_), min(255, g_), min(255, b_)))
    
    elif name == "moon_glow":
        mr = int(radius * 0.85)
        for i in range(4):
            gr = int(mr * (1.2 + i * 0.3))
            alpha = max(1, int(20 / (i + 1) * kwargs.get("vis", 1)))
            for y in range(grid):
                for x in range(grid):
                    dx = x - cx
                    dy = y - cy
                    d = math.sqrt(dx*dx + dy*dy)
                    if abs(d - gr) < 2:
                        color = (180, 160, 210, alpha)
                        existing = grid_surf.get_at((x, y))
                        if existing[3] < alpha:
                            grid_surf.set_at((x, y), color)
    
    elif name == "star":
        size_val = kwargs.get("star_size", 1)
        brightness = kwargs.get("brightness", 255)
        for y in range(grid):
            for x in range(grid):
                dx = x - cx
                dy = y - cy
                if abs(dx) <= size_val and abs(dy) <= size_val:
                    grid_surf.set_at((x, y), (brightness, brightness, brightness, 255))
    
    result = pygame.transform.scale(grid_surf, (target, target))
    _pixel_cache[key] = result.copy()
    return result

def draw_sun(screen, w, h, hour):
    if not (6 <= hour < 18):
        return
    
    if hour < 7:
        vis = hour - 6
    elif hour > 17:
        vis = 18 - hour
    else:
        vis = 1
    vis = max(0, min(1, vis))
    
    r = int(0.11 * min(w, h))
    progress = max(0, min(1, (hour - 6) / 12))
    angle = progress * math.pi
    cx = w * (0.02 + 0.96 * progress)
    cy = h * 0.40 - math.sin(angle) * h * 0.22
    
    total_size = r * 3
    surf = pygame.Surface((total_size, total_size), pygame.SRCALPHA)
    center = total_size // 2
    
    # Pixelated glow
    glow = _build_pixel_celestial("sun_glow", total_size, vis=vis)
    surf.blit(glow, (0, 0))
    
    # Sun body
    sun = _build_pixel_celestial("sun", total_size, hour=hour, progress=progress)
    surf.blit(sun, (0, 0))
    
    surf.set_alpha(int(vis * 255))
    screen.blit(surf, (cx - center, cy - center))

def draw_moon(screen, w, h, hour, moon_phase):
    if not (hour >= 18 or hour < 6):
        return
    
    if 18 <= hour < 19:
        vis = hour - 18
    elif 5 <= hour < 6:
        vis = 6 - hour
    else:
        vis = 1
    vis = max(0, min(1, vis))
    
    r = int(0.10 * min(w, h))
    if r < 6:
        return
    
    if hour >= 18:
        night_progress = (hour - 18) / 12
    else:
        night_progress = (hour + 6) / 12
    cx = w * (0.05 + 0.90 * night_progress)
    cy = h * 0.42 - math.sin(night_progress * math.pi) * h * 0.18
    
    total_size = r * 3
    surf = pygame.Surface((total_size, total_size), pygame.SRCALPHA)
    center = total_size // 2
    
    # Pixelated moon glow
    glow = _build_pixel_celestial("moon_glow", total_size, vis=vis)
    surf.blit(glow, (0, 0))
    
    # Moon texture
    moon = _build_pixel_celestial("moon", total_size)
    surf.blit(moon, (0, 0))
    
    # Shadow for phase (using pixel grid for consistency)
    shadow_size = total_size
    shadow_surf = pygame.Surface((shadow_size, shadow_size), pygame.SRCALPHA)
    shadow_center = shadow_size // 2
    moon_r = r
    
    if moon_phase <= 0.5:
        soff = int(4 * r * moon_phase)
    else:
        soff = int(4 * r * (1 - moon_phase))
    
    # Pixelated shadow circle
    grid = PIXEL_GRID
    grid_shadow = pygame.Surface((grid, grid), pygame.SRCALPHA)
    gcx = gcy = grid // 2
    gr = int((moon_r / total_size) * grid)
    gsoff = int((soff / total_size) * grid)
    
    for y in range(grid):
        for x in range(grid):
            dx = x - (gcx + gsoff)
            dy = y - gcy
            d = math.sqrt(dx*dx + dy*dy)
            if d <= gr:
                alpha = 230 if d < gr * 0.9 else int(230 * (1 - (d - gr * 0.9) / (gr * 0.1)))
                grid_shadow.set_at((x, y), (0, 0, 0, alpha))
    
    shadow_surf.blit(pygame.transform.scale(grid_shadow, (shadow_size, shadow_size)), (0, 0))
    surf.blit(shadow_surf, (0, 0))
    
    # Earthshine for crescent moons
    es = 1 - abs(moon_phase - 0.5) * 2
    if es > 0.01:
        es_surf = pygame.Surface((total_size, total_size), pygame.SRCALPHA)
        grid_es = pygame.Surface((grid, grid), pygame.SRCALPHA)
        for y in range(grid):
            for x in range(grid):
                dx = x - (gcx - gsoff)
                dy = y - gcy
                d = math.sqrt(dx*dx + dy*dy)
                if d <= gr:
                    alpha = int(45 * es * vis)
                    grid_es.set_at((x, y), (55, 40, 25, alpha))
        es_surf.blit(pygame.transform.scale(grid_es, (total_size, total_size)), (0, 0))
        surf.blit(es_surf, (0, 0))
    
    surf.set_alpha(int(vis * 255))
    screen.blit(surf, (cx - center, cy - center))

def generate_stars(count, w, h):
    stars = []
    for _ in range(count):
        stars.append({
            "x": random.randint(0, w),
            "y": random.randint(0, int(h * 0.72)),
            "size": random.choice([1, 1, 2, 2, 3]) if random.random() < 0.12 else 1,
            "p": random.random() * math.pi * 2,
            "sp": random.uniform(0.5, 2),
            "b": random.uniform(0.4, 1),
        })
    return stars

def draw_stars(screen, stars, shooting, hour, w, h, speed=1.0):
    if 6 <= hour < 18:
        return

    if hour >= 18 and hour < 20:
        vis = (hour - 18) / 2
    elif hour >= 5 and hour < 6:
        vis = 1 - (hour - 5)
    else:
        vis = 1

    for s in stars:
        s["p"] += s["sp"] * 0.01 * speed
        a = vis * s["b"] * (0.5 + 0.5 * math.sin(s["p"]))
        alpha = max(0, min(255, int(a * 255)))
        if alpha < 8:
            continue
        sx, sy = s["x"], s["y"]
        sz = s["size"]
        if sz == 1:
            screen.set_at((int(sx), int(sy)), (alpha, alpha, alpha))
        else:
            star_surf = pygame.Surface((sz * 2 + 1, sz * 2 + 1), pygame.SRCALPHA)
            pygame.draw.circle(star_surf, (alpha, alpha, max(0, alpha - 20), alpha),
                               (sz, sz), sz)
            screen.blit(star_surf, (int(sx) - sz, int(sy) - sz))

    if random.random() < 0.004 * speed:
        shooting.append({
            "x": random.randint(0, w),
            "y": random.randint(0, int(h * 0.3)),
            "len": random.randint(20, 70),
            "speed": random.uniform(4, 9)
        })

    for s in shooting:
        steps = max(3, s["len"] // 6)
        for i in range(steps):
            t = i / steps
            x = s["x"] - t * s["len"]
            y = s["y"] + t * s["len"] * 0.5
            alpha = int(255 * (1 - t) * vis)
            size = 3 if i < 2 else 1
            if alpha > 10:
                star = _build_pixel_celestial("star", size * 3, star_size=size, brightness=255)
                star.set_alpha(alpha)
                screen.blit(star, (int(x) - size, int(y) - size))


def draw_aurora(screen, w, h, hour, season, t=0.0, intensity=1.0):
    """Draw dancing aurora borealis bands in the upper sky.

    Uses a low-resolution surface to draw horizontal pygame.draw.line strips,
    then smoothscales up. This achieves a massive performance improvement 
    (~100x fewer draw calls) and produces a beautiful natural blur effect.
    """
    if intensity <= 0.01:
        return
    # Night visibility fade
    if hour >= 19:
        night_vis = min(1.0, (hour - 19) / 1.5)
    elif hour < 4:
        night_vis = 1.0
    elif hour < 6:
        night_vis = max(0.0, 1.0 - (hour - 4) / 2.0)
    else:
        return  # daytime

    alpha_scale = night_vis * intensity
    if alpha_scale < 0.02:
        return

    # Render at 1/8th resolution
    SCALE = 8
    sw = max(1, w // SCALE)
    sh = max(1, h // SCALE)

    aurora_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)

    # Aurora bands
    bands = [
        # (base_y_frac, color_a, color_b, wave_freq, wave_amp, phase_offset, thickness)
        (0.08, (0, 255, 120),   (80, 200, 255),  0.8,  0.04,  0.0,  0.07),
        (0.14, (80, 200, 255),  (180, 80, 255),  1.1,  0.035, 1.2,  0.06),
        (0.19, (0, 255, 160),   (0, 200, 255),   0.6,  0.028, 2.5,  0.05),
        (0.05, (200, 80, 255),  (0, 255, 140),   1.4,  0.045, 0.7,  0.04),
    ]

    # Step size on the small surface
    X_STEP = 2

    for base_frac, col_a, col_b, freq, amp, phase_off, thick_frac in bands:
        band_h = max(2, int(sh * thick_frac))
        drift = math.sin(t * 0.12 + phase_off) * sh * 0.02
        base_y = int(sh * base_frac + drift)

        for x in range(0, sw, X_STEP):
            # Scale x back up to maintain the same frequency visual
            orig_x = x * SCALE
            wave = math.sin(orig_x * freq * 0.012 + t * 0.4 + phase_off)
            shimmer = 0.5 + 0.5 * math.sin(orig_x * 0.05 + t * 1.1 + phase_off * 2)
            y_off = int(wave * sh * amp)

            cx_frac = (math.sin(orig_x * 0.007 + t * 0.2) + 1) / 2
            r = int(col_a[0] + (col_b[0] - col_a[0]) * cx_frac)
            g = int(col_a[1] + (col_b[1] - col_a[1]) * cx_frac)
            b = int(col_a[2] + (col_b[2] - col_a[2]) * cx_frac)
            x2 = min(sw - 1, x + X_STEP - 1)

            for dy in range(band_h):
                fy = dy / band_h
                fade = math.exp(-((fy - 0.5) ** 2) * 8)
                a = int(alpha_scale * shimmer * fade * 110)
                if a < 3:
                    continue
                py = base_y + y_off + dy
                if 0 <= py < sh:
                    pygame.draw.line(aurora_surf, (r, g, b, a), (x, py), (x2, py))

    # Scale up for beautiful soft blur
    if sw < w or sh < h:
        aurora_surf = pygame.transform.smoothscale(aurora_surf, (w, h))

    screen.blit(aurora_surf, (0, 0))

def update_shooting_stars(stars, w, h, speed=1.0):
    for s in stars[:]:
        s["x"] -= s["speed"] * speed
        s["y"] += s["speed"] * 0.5 * speed
        if s["y"] > h * 0.7:
            stars.remove(s)