import pygame
import random
import math

def lerp_color(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def build_city(w, h):
    rng_b = random.Random(42)
    pattern = [.10,.18,.28,.22,.14,.20,.32,.16,.12,.26,.30,.20,.14,.24,.34,
               .18,.10,.22,.28,.16,.12,.26,.20,.30,.14,.18,.32,.10,.24,.22,
               .28,.16,.30,.12,.20,.26,.14,.18,.10]
    bldgs = []
    x = 0.0
    for ph in pattern:
        hv = ph + rng_b.uniform(-0.03, 0.03)
        hv = max(0.06, min(0.38, hv))
        bw = max(0.025, min(0.055, 0.025 + rng_b.uniform(-0.005, 0.015)))
        protr = []
        n = max(1, int(bw * w / 16))
        rng_r = random.Random(int(x * 10000 + hv * 100))
        for _ in range(n):
            px = rng_r.uniform(0.1, 0.9)
            ph2 = rng_r.randint(3, 10)
            pw = rng_r.randint(2, 5)
            protr.append((px, ph2, pw))
        bldgs.append((x, hv, bw, protr))
        x += bw + rng_b.uniform(0.005, 0.02)
    bldgs = [(bx, bh, bw, p) for bx, bh, bw, p in bldgs if bx < 0.98]
    far   = [(bx+.08, bh*.46, bw*.68, p) for bx,bh,bw,p in bldgs]
    mid   = [(bx+.04, bh*.70, bw*.82, p) for bx,bh,bw,p in bldgs]
    front = bldgs
    return front, mid, far


def win_lit(bx_px, wy, wx, hour, half_hour):
    seed = int(bx_px * 10000 + wy * 7 + wx * 13)
    rng = random.Random(seed)
    base = rng.random()
    is_day = 6 <= hour <= 18
    prob = 0.18 if is_day else 0.42
    if 17 < hour < 19:  prob = 0.18 + (hour - 17) * 0.12
    elif 4 < hour < 6:  prob = 0.42 - (hour - 4) * 0.12
    if base > prob + 0.06:
        return False
    if base > prob - 0.06:
        return (wy * 3 + wx * 7 + half_hour) % 2 == 0
    return True


def draw_city_layer(screen, w, h, ground_y, bldgs, col, hour,
                    draw_windows=False, draw_protr=False):
    is_dark = hour < 6 or hour >= 19
    half_hour = int(hour * 2)
    lr = 250 if is_dark else 190
    lg = 210
    lb = 90 if is_dark else 240

    for bx, bh, bw, protr in bldgs:
        bx_px = int(w * bx)
        bh_px = max(4, int(h * bh))
        bw_px = max(3, int(w * bw))
        bx_px = min(w - bw_px - 2, max(2, bx_px))
        top = ground_y - bh_px

        pygame.draw.rect(screen, col, (bx_px, top, bw_px, bh_px))
        hi = tuple(min(255, c + 18) for c in col)
        pygame.draw.line(screen, hi, (bx_px, top), (bx_px, ground_y - 1))

        if draw_protr and bw_px > 10:
            for px_frac, ph2, pw in protr:
                px = bx_px + int(px_frac * max(1, bw_px - pw))
                px = min(px, bx_px + bw_px - pw - 1)
                pygame.draw.rect(screen, col, (px, top - ph2, pw, ph2))

        if draw_windows and bh_px > 18:
            for wy in range(top + 6, ground_y - 3, 11):
                for wx in range(bx_px + 4, bx_px + bw_px - 3, 8):
                    if not win_lit(bx_px, wy, wx, hour, half_hour):
                        continue
                    if is_dark:
                        gsurf = pygame.Surface((14, 14), pygame.SRCALPHA)
                        pygame.draw.circle(gsurf, (lr, lg, lb, 45), (7, 7), 7)
                        screen.blit(gsurf, (wx - 3, wy - 3))
                    pygame.draw.rect(screen, (lr, lg, lb), (wx, wy, 4, 5))


def draw_streetlights(screen, w, ground_y, hour):
    is_dark = hour < 6 or hour >= 19
    pole_col = (130, 125, 110) if is_dark else (90, 88, 80)
    for lx in range(60, w, 130):
        pygame.draw.line(screen, pole_col, (lx, ground_y), (lx, ground_y - 48), 2)
        pygame.draw.line(screen, pole_col, (lx, ground_y - 48), (lx + 14, ground_y - 48), 2)
        if is_dark:
            glow = pygame.Surface((60, 60), pygame.SRCALPHA)
            for r, a in [(28, 14), (20, 30), (12, 60), (5, 160)]:
                pygame.draw.circle(glow, (255, 242, 180, a), (30, 30), r)
            screen.blit(glow, (lx + 14 - 30, ground_y - 48 - 30))
            pygame.draw.circle(screen, (255, 248, 210), (lx + 14, ground_y - 48), 3)


def draw_road(screen, w, ground_y, hour):
    is_dark = hour < 6 or hour >= 19
    road_y = ground_y + 4
    road_h = 16
    road_col = (30, 32, 42) if is_dark else (44, 46, 58)
    edge_col = (190, 180, 130, 90)
    dash_col = (215, 205, 148, 170) if is_dark else (195, 185, 128, 130)
    pygame.draw.rect(screen, road_col, (0, road_y, w, road_h))
    esurf = pygame.Surface((w, 1), pygame.SRCALPHA)
    esurf.fill(edge_col)
    screen.blit(esurf, (0, road_y))
    screen.blit(esurf, (0, road_y + road_h - 1))
    dsurf = pygame.Surface((16, 2), pygame.SRCALPHA)
    dsurf.fill(dash_col)
    for dx in range(0, w, 32):
        screen.blit(dsurf, (dx, road_y + road_h // 2 - 1))
