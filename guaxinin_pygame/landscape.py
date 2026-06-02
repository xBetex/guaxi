# landscape.py
import pygame
import math
import random
from sprites import Gfx
from tree_sheet import TreeSheet, SEASONS
from cityscape import build_city, draw_city_layer, draw_streetlights, draw_road
from trees import draw_trees


_tree_sheet = None
_city_data = None


def _get_city(w, h):
    global _city_data
    if _city_data is None:
        _city_data = build_city(w, h)
    return _city_data

def _get_tree_sheet():
    global _tree_sheet
    if _tree_sheet is None:
        _tree_sheet = TreeSheet()
    return _tree_sheet

_sky_cache = {"elev": None, "surf": None, "w": 0, "h": 0}

KEY_ELEV = [0, 5, 10, 30, 90]
ZENITHS = [
    (108, 92, 231),   # 0: tarde (sunset/dusk)
    (90, 110, 230),   # 5: blend
    (116, 185, 255),  # 10: manha (morning)
    (9, 132, 227),    # 30: dia (day)
    (9, 132, 227)     # 90: dia (noon)
]
HORIZONS = [
    (253, 203, 110),  # 0: tarde
    (254, 220, 140),  # 5: blend
    (255, 234, 167),  # 10: manha
    (129, 236, 236),  # 30: dia
    (129, 236, 236)   # 90: dia
]
NIGHT_ZENITH = (0, 0, 0)
NIGHT_HORIZON = (15, 20, 35)


def sun_elevation(hour):
    t = (hour - 6) / 24 * math.pi * 2
    return math.sin(t) * 85


def get_sky_colors(elev):
    if elev < 0:
        f = min(1, max(0, (elev + 10) / 10))
        z = tuple(int(NIGHT_ZENITH[i] + (ZENITHS[0][i] - NIGHT_ZENITH[i]) * f) for i in range(3))
        h = tuple(int(NIGHT_HORIZON[i] + (HORIZONS[0][i] - NIGHT_HORIZON[i]) * f) for i in range(3))
        return z, h

    e = max(0, min(90, elev))
    for i in range(len(KEY_ELEV) - 1):
        if KEY_ELEV[i] <= e <= KEY_ELEV[i + 1]:
            t = (e - KEY_ELEV[i]) / (KEY_ELEV[i + 1] - KEY_ELEV[i])
            z = tuple(int(ZENITHS[i][j] + (ZENITHS[i + 1][j] - ZENITHS[i][j]) * t) for j in range(3))
            h = tuple(int(HORIZONS[i][j] + (HORIZONS[i + 1][j] - HORIZONS[i][j]) * t) for j in range(3))
            return z, h
    return ZENITHS[-1], HORIZONS[-1]


def draw_sky(screen, w, h, hour):
    global _sky_cache
    elev = sun_elevation(hour)

    if _sky_cache["surf"] is not None and abs(_sky_cache["elev"] - elev) < 0.3 and _sky_cache["w"] == w and _sky_cache["h"] == h:
        screen.blit(_sky_cache["surf"], (0, 0))
        return

    zenith, horizon = get_sky_colors(elev)
    surf = pygame.Surface((w, h))
    for y in range(h):
        t = (y / (h - 1)) ** 0.7 if h > 1 else 0
        r = int(zenith[0] + (horizon[0] - zenith[0]) * t)
        g = int(zenith[1] + (horizon[1] - zenith[1]) * t)
        b = int(zenith[2] + (horizon[2] - zenith[2]) * t)
        pygame.draw.line(surf, (r, g, b), (0, y), (w, y))

    _sky_cache = {"elev": elev, "surf": surf, "w": w, "h": h}
    screen.blit(surf, (0, 0))

def draw_landscape(screen, w, h, season, hour, day, weather=None):
    ground_y = int(h * 0.78)

    elev = sun_elevation(hour)
    if elev < 0:
        base_c = (10, 10, 15)
        light_c = (30, 39, 46)
    elif elev < 15:
        if hour < 12: # manha
            base_c = (130, 115, 151)
            light_c = (162, 155, 254)
        else: # tarde
            base_c = (27, 27, 47)
            light_c = (45, 52, 54)
    else: # dia
        base_c = (74, 91, 99)
        light_c = (99, 110, 114)
        
    mountain_colors = [
        tuple(int(base_c[i] + (light_c[i] - base_c[i]) * 0.1) for i in range(3)),
        tuple(int(base_c[i] + (light_c[i] - base_c[i]) * 0.4) for i in range(3)),
        tuple(int(base_c[i] + (light_c[i] - base_c[i]) * 0.7) for i in range(3)),
        light_c
    ]

    heights = [0.28, 0.22, 0.17, 0.12]
    peaks = [9, 7, 6, 5]

    for idx in range(4):
        pts = [(0, h)]

        for i in range(peaks[idx] + 1):
            x = i * w / peaks[idx]
            y = ground_y - math.sin(i * 1.2 + idx) * 40 - h * heights[idx]
            pts.append((x, y))

        pts.append((w, h))

        pygame.draw.polygon(screen, mountain_colors[idx], pts)

    is_dark = (hour < 6 or hour >= 19)
    front, mid, far = _get_city(w, h)
    cols = [(far, (22, 28, 44) if is_dark else (70, 85, 110), False, False),
            (mid, (30, 34, 54) if is_dark else (45, 55, 80), False, False),
            (front, (14, 16, 26) if is_dark else (25, 28, 42), True, True)]
    for bldgs, col, win, protr in cols:
        draw_city_layer(screen, w, h, ground_y, bldgs, col, hour, win, protr)
    draw_streetlights(screen, w, ground_y, hour)
    draw_road(screen, w, ground_y, hour)

    base_scale = min(w, h) / 800

    # Draw Sand Beach
    sand_c_top = (235, 213, 179)
    sand_c_bot = (194, 166, 126)
    
    if weather and weather.rain_intensity > 0.1:
        sand_c_top = tuple(max(0, int(c * 0.75)) for c in sand_c_top)
        sand_c_bot = tuple(max(0, int(c * 0.75)) for c in sand_c_bot)

    beach_h = h - ground_y
    if beach_h > 0:
        ground_surf = pygame.Surface((w, beach_h))
        for gy in range(beach_h):
            t = gy / beach_h
            r = int(sand_c_top[0] + (sand_c_bot[0] - sand_c_top[0]) * t)
            g = int(sand_c_top[1] + (sand_c_bot[1] - sand_c_top[1]) * t)
            b = int(sand_c_top[2] + (sand_c_bot[2] - sand_c_top[2]) * t)
            pygame.draw.line(ground_surf, (r, g, b), (0, gy), (w, gy))
            
        # Draw green strip for trees (promenade grass)
        grass_h = max(5, int(beach_h * 0.04))
        pygame.draw.rect(ground_surf, (76, 153, 76), (0, 0, w, grass_h))
        # Curb border
        pygame.draw.line(ground_surf, (170, 160, 140), (0, grass_h), (w, grass_h), 2)
            
        t_sec = pygame.time.get_ticks() / 1000.0
        
        base_shore_y = int(beach_h * 0.65) 
        surge_amp = int(beach_h * 0.20)
        max_reach_y = base_shore_y - surge_amp

        # Slower wave: 1 cycle every 10 seconds
        cycle_len = 10.0
        cycle_start = math.floor(t_sec / cycle_len) * cycle_len
        t_peak = cycle_start + 2.0  # Peak is at phase 0.2 (2 seconds in)
        
        phase = (t_sec / cycle_len) % 1.0
        if phase < 0.20:
            surge = math.sin((phase / 0.20) * (math.pi / 2)) # Fast surge
            t_wet = t_sec
            current_wet_y = base_shore_y - surge * surge_amp
            wet_alpha = 45
        else:
            surge = 1.0 - math.pow((phase - 0.20) / 0.80, 1.5) # Slow recede
            t_wet = t_peak
            current_wet_y = max_reach_y
            wet_alpha = int(45 * surge)

        # Wet sand layer (breathes by leaving a footprint that dries up)
        wet_sand_surf = pygame.Surface((w, beach_h), pygame.SRCALPHA)
        wet_points = []
        for wx in range(0, w + 20, 20):
            wavy = math.sin(wx * 0.012 + t_wet * 0.8) * 8 + math.sin(wx * 0.025 - t_wet * 1.2) * 5
            wet_points.append((wx, current_wet_y + wavy))
        wet_points.extend([(w + 20, beach_h), (0, beach_h)])
        pygame.draw.polygon(wet_sand_surf, (0, 0, 0, wet_alpha), wet_points)
        ground_surf.blit(wet_sand_surf, (0, 0))

        screen.blit(ground_surf, (0, ground_y))

        # Draw Ocean Wave
        water_surf = pygame.Surface((w, beach_h), pygame.SRCALPHA)
        
        sky_r, sky_g, sky_b = get_sky_colors(sun_elevation(hour))[1]
        base_r = max(0, min(255, int(sky_r * 0.2 + 20)))
        base_g = max(0, min(255, int(sky_g * 0.3 + 90)))
        base_b = max(0, min(255, int(sky_b * 0.4 + 150)))

        main_shore_y = base_shore_y - surge * surge_amp
        
        main_pts = []
        for wx in range(0, w + 20, 20):
            wavy = math.sin(wx * 0.012 + t_sec * 0.8) * 8 + math.sin(wx * 0.025 - t_sec * 1.2) * 5
            main_pts.append((wx, main_shore_y + wavy))
        main_pts.extend([(w + 20, beach_h), (0, beach_h)])
        
        pygame.draw.polygon(water_surf, (base_r, base_g, base_b, 230), main_pts)
        
        # Random foam drifting on the water
        for i in range(150):
            fx = (math.sin(i * 12.34) * 5000 + t_sec * 12) % w
            fy = (math.sin(i * 45.67) * 5000 + t_sec * 6) % beach_h
            
            wavy_offset = math.sin(fx * 0.012 + t_sec * 0.8) * 8 + math.sin(fx * 0.025 - t_sec * 1.2) * 5
            water_edge_y = main_shore_y + wavy_offset
            
            if fy > water_edge_y + 8:
                f_alpha = int((math.sin(t_sec * 1.5 + i) * 0.5 + 0.5) * 120)
                if f_alpha > 10:
                    f_size = 1 + int((math.sin(i * 78.9) * 0.5 + 0.5) * 4)
                    pygame.draw.ellipse(water_surf, (255, 255, 255, f_alpha), (int(fx), int(fy), f_size * 4, f_size))
        
        foam_pts = main_pts[:-2]
        if len(foam_pts) >= 2:
            foam_thick = int(2 + surge * 6)
            pygame.draw.lines(water_surf, (255, 255, 255, int(150 + 105*surge)), False, foam_pts, foam_thick)

        screen.blit(water_surf, (0, ground_y))

    draw_trees(screen, w, h, ground_y, season, day,
               base_scale, weather)

