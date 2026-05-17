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

    ground_colors = {
        "summer": (56, 173, 169),
        "autumn": (183, 21, 64),
        "winter": (178, 190, 195),
        "spring": (0, 184, 148),
    }
    gc = ground_colors.get(season, (40, 100, 50))
    # weather-responsive ground
    if weather:
        if getattr(weather, '_is_winter', False) and weather.rain_intensity > 0.01:
            gc = (180, 195, 210)  # snow cover
        elif weather.rain_intensity > 0.1:
            gc = tuple(max(0, int(c * 0.7)) for c in gc)  # wet ground (darker)
    ground_surf = pygame.Surface((w, h - ground_y))
    for gy in range(h - ground_y):
        t = gy / (h - ground_y)
        r = int(gc[0] * (1 - t * 0.3))
        g = int(gc[1] * (1 - t * 0.25))
        b = int(gc[2] * (1 - t * 0.2))
        pygame.draw.line(ground_surf, (r, g, b), (0, gy), (w, gy))
    screen.blit(ground_surf, (0, ground_y))

    path_x = w * 0.25
    path_w = int(w * 0.05)
    for py in range(ground_y, ground_y + int(h * 0.08)):
        t = (py - ground_y) / (h * 0.08)
        pw = int(path_w * (0.5 + t * 0.5))
        px = int(path_x + math.sin(t * 2) * 20)
        col = (100 + int(t * 40), 75 + int(t * 30), 50)
        pygame.draw.ellipse(screen, col, (px - pw // 2, py, pw, 2))

    lake_y = ground_y + int(h * 0.06)
    lake_h = int(h * 0.06)
    if season != "winter":
        lake_surf = pygame.Surface((w, lake_h), pygame.SRCALPHA)
        for ly in range(lake_h):
            t = ly / lake_h
            sky_r, sky_g, sky_b = get_sky_colors(sun_elevation(hour))[1]
            alpha = int(60 + 60 * (1 - t))
            col = (sky_r // 2, sky_g // 2, sky_b // 2, alpha)
            lake_surf.set_at((0, ly), col)
            for lx in range(0, w, 2):
                wv = math.sin(lx * 0.02 + ly * 0.1 + hour * 3) * 1.5
                lake_surf.set_at((lx, ly), (col[0] + int(wv), col[1] + int(wv), col[2] + int(wv), alpha))
        screen.blit(lake_surf, (0, lake_y))

    draw_trees(screen, w, h, ground_y, season, day,
               base_scale, weather)

