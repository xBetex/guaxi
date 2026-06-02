import pygame
import math
import random
import os
from constants import THEMES, get_time_theme, get_color, CLOUD_SPRITE, SEASON_COLORS

_cache = {}

def load_image(filename):
    if filename not in _cache:
        path = os.path.join("assets", filename)
        if os.path.exists(path):
            try:
                _cache[filename] = pygame.image.load(path).convert_alpha()
            except Exception as e:
                print(f"Error loading {path}: {e}")
                _cache[filename] = None
        else:
            _cache[filename] = None
    return _cache[filename]

def init_assets():
    seasons = ["spring", "summer", "autum", "winter"]
    for s in seasons:
        load_image(f"{s}_small.png")
        load_image(f"{s}_out.png")
        load_image(f"{s}_in.png")
    load_image("bonfire.png")
    load_image("guaxinim_inteiro_transp.png")

# Raccoon State
raccoon_x = 0
raccoon_state = "idle"
raccoon_scale = 1.0
raccoon_flip = False
raccoon_wander_target = -1
raccoon_wander_timer = 0
random_hole_time = 0
raccoon_frame = 0
raccoon_bounce = 0

def draw_sprite(screen, sprite, x, y, scale, season):
    for row_idx, row in enumerate(sprite):
        for col_idx, char in enumerate(row):
            if char == "T":
                continue
            color = get_color(char, season)
            if color:
                sz = math.ceil(scale)
                rx = int(x + col_idx * scale)
                ry = int(y + row_idx * scale)
                rect = pygame.Rect(rx, ry, sz, sz)
                pygame.draw.rect(screen, color, rect)
                
                # Faint grid lines to replicate Canvas subpixel gaps
                edge_color = tuple(max(0, c - 15) for c in color)
                pygame.draw.rect(screen, edge_color, rect, 1)

def draw_pixelated_sun(screen, cx, cy, radius):
    hi_res = 128
    surf_hi = pygame.Surface((hi_res, hi_res), pygame.SRCALPHA)
    surf_hi.fill((0,0,0,0))
    scx, scy = hi_res // 2, hi_res // 2
    r = hi_res // 2
    
    pygame.draw.circle(surf_hi, (255, 202, 40), (scx, scy), r)
    
    surf_32 = pygame.transform.smoothscale(surf_hi, (32, 32))
    scaled_surf = pygame.transform.scale(surf_32, (int(radius * 2), int(radius * 2)))
    screen.blit(scaled_surf, (int(cx - radius), int(cy - radius)))


# Craters defined as (norm_x, norm_y, norm_r) in [-1..1] space
_MOON_CRATERS = [
    (-0.30,  0.10, 0.14),
    ( 0.20, -0.25, 0.10),
    ( 0.40,  0.30, 0.08),
    (-0.10,  0.40, 0.07),
    ( 0.10,  0.05, 0.05),
    (-0.45, -0.20, 0.09),
    ( 0.30, -0.10, 0.06),
    (-0.20, -0.40, 0.06),
]


def draw_pixelated_moon(screen, cx, cy, radius, phase):
    """Draw pixel-art moon with visible pixel squares, craters, and phase shadow.
    Matches the cloud/sun pixelated aesthetic."""
    GRID = 20        # pixel grid resolution (cells across moon diameter)
    pixel_size = max(2, int(radius * 2 / GRID))   # rendered pixel size
    actual_diam = pixel_size * GRID
    half = actual_diam // 2

    surf = pygame.Surface((actual_diam, actual_diam), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))

    illum = (1 - math.cos(phase * 2 * math.pi)) / 2
    waxing = phase <= 0.5

    # Pre-compute which cells are in the lit circle and which are shadowed
    # terminator offset in cell units
    term_offset = (1.0 - 2.0 * illum) * (GRID / 2.0)

    for gy in range(GRID):
        for gx in range(GRID):
            # Cell centre in normalised coords [-1, 1]
            nx = (gx + 0.5 - GRID / 2.0) / (GRID / 2.0)
            ny = (gy + 0.5 - GRID / 2.0) / (GRID / 2.0)
            dist = math.sqrt(nx * nx + ny * ny)

            if dist > 1.0:
                continue   # outside circle

            # Phase clipping — is this cell lit?
            if waxing:
                # lit half is right side; terminator shifts left→right as phase 0→0.5
                lit = nx > -1.0 + (1.0 - illum) * 2.0 or dist <= 0.02
                # simpler: cell is lit if its x > terminator x
                x_term = (1.0 - 2.0 * illum)
                lit = nx > x_term
            else:
                x_term = -(1.0 - 2.0 * (1.0 - illum))
                lit = nx < x_term

            if not lit:
                # Dark side — very dark blue-grey
                r_, g_, b_ = 8, 10, 24
            else:
                # Lit side base colour varies with distance from centre
                t = dist
                if t < 0.15:   r_, g_, b_ = 245, 242, 235
                elif t < 0.35: r_, g_, b_ = 230, 226, 218
                elif t < 0.55: r_, g_, b_ = 210, 205, 198
                elif t < 0.75: r_, g_, b_ = 185, 178, 174
                elif t < 0.90: r_, g_, b_ = 155, 148, 150
                else:          r_, g_, b_ = 120, 112, 120

                # Craters
                for cnx, cny, cnr in _MOON_CRATERS:
                    cdist = math.sqrt((nx - cnx) ** 2 + (ny - cny) ** 2)
                    if cdist <= cnr:
                        # rim highlight on left, shadow on right
                        if cdist > cnr * 0.75:
                            rim = 1.0 if nx < cnx else 0.0
                            r_ = min(255, int(r_ * (0.7 + 0.5 * rim)))
                            g_ = min(255, int(g_ * (0.7 + 0.5 * rim)))
                            b_ = min(255, int(b_ * (0.7 + 0.5 * rim)))
                        else:
                            r_ = int(r_ * 0.72)
                            g_ = int(g_ * 0.70)
                            b_ = int(b_ * 0.68)
                        break

                # Subtle noise
                n = (gx * 17 + gy * 31) % 20
                r_ = min(255, r_ + n - 10)
                g_ = min(255, g_ + n - 10)
                b_ = min(255, b_ + n - 10)

            px = gx * pixel_size
            py = gy * pixel_size
            # Main pixel block
            pygame.draw.rect(surf, (r_, g_, b_), (px, py, pixel_size, pixel_size))
            # Subtle grid line to match cloud/sun pixel aesthetic
            edge = tuple(max(0, c - 18) for c in (r_, g_, b_))
            pygame.draw.rect(surf, edge, (px, py, pixel_size, pixel_size), 1)

    screen.blit(surf, (int(cx - half), int(cy - half)))

def draw_clouds_pixelated(screen, w, h, weather, season):
    cloud_list = [
        {"x": 10, "y": 15, "speed": 0.5, "scale": 6},
        {"x": 50, "y": 10, "speed": 0.3, "scale": 4},
        {"x": 80, "y": 25, "speed": 0.8, "scale": 5},
        {"x": 20, "y": 35, "speed": 0.4, "scale": 7},
    ]
    cc = getattr(weather, 'cloud_cover', 0) if weather else 0
    if cc is not None and cc > 0.4:
        cloud_list.extend([
            {"x": 35, "y": 18, "speed": 0.35, "scale": 5},
            {"x": 70, "y": 22, "speed": 0.45, "scale": 6},
            {"x": 15, "y": 28, "speed": 0.5, "scale": 7},
        ])
    
    wind_factor = 1.0
    if weather:
        ws = getattr(weather, 'wind_speed', 0)
        if ws is not None:
            wind_factor = max(0.4, min(2.0, ws / 20))
        
    for c in cloud_list:
        # We can't properly move them persistently without state, but we can fake it using ticks
        # Wait, the clouds need to be moved. I'll use pygame.time.get_ticks() to move them.
        tick = pygame.time.get_ticks() / 1000.0
        x_pos = ((c["x"] + tick * c["speed"] * 5 * wind_factor) % 130) - 20
        cx = (x_pos / 100) * w
        cy = (c["y"] / 100) * h
        draw_sprite(screen, CLOUD_SPRITE, int(cx), int(cy), int(c["scale"] * 2.4), season)

def draw_scenery(screen, w, h, season, hour, day, weather, moon_phase):
    global raccoon_x, raccoon_state, raccoon_scale, raccoon_flip
    global raccoon_wander_target, raccoon_wander_timer, random_hole_time
    global raccoon_frame, raccoon_bounce
    
    # Initialize some state once
    if random_hole_time == 0:
        random_hole_time = pygame.time.get_ticks() + random.randint(20000, 70000)
        raccoon_x = w / 2

    season_pfx = "autum" if season == "autumn" else season
    ground_y = int(h * 0.75)
    now = pygame.time.get_ticks()
    is_night = (hour < 6 or hour >= 18)
    
    # Celestial
    celestial_radius = min(w, h) * 0.15
    if not is_night:
        tp = (hour - 6) / 12
        sun_cx = w * 0.1 + w * 0.8 * tp
        sun_cy = h * 0.12 + math.sin(tp * math.pi) * -h * 0.06
        draw_pixelated_sun(screen, sun_cx, sun_cy, celestial_radius)
    else:
        night_hour = hour - 18 if hour >= 18 else hour + 6
        tp = night_hour / 12
        moon_cx = w * 0.1 + w * 0.8 * tp
        moon_cy = h * 0.16
        draw_pixelated_moon(screen, moon_cx, moon_cy, celestial_radius, moon_phase)

    # Clouds
    draw_clouds_pixelated(screen, w, h, weather, season)

    # Mountains
    def draw_mountain(cx, py, base_w, color_shadow, color_light, has_snow):
        block_size = 16
        steps = max(1, int(py / block_size))
        if steps == 0: return
        step_width = base_w / 2 / steps
        for i in range(steps):
            cy = ground_y - i * block_size
            chw = base_w / 2 - i * step_width
            sc = (223, 230, 233) if (has_snow and i > steps * 0.65) else color_shadow
            lc = (255, 255, 255) if (has_snow and i > steps * 0.65) else color_light
            
            # Use explicit int boundaries to avoid 1px gaps from float truncation
            left_x = int(cx - chw)
            center_x = int(cx)
            right_x = int(cx + chw)
            top_y = int(cy - block_size)
            h_val = int(block_size)
            
            pygame.draw.rect(screen, sc, (left_x, top_y, center_x - left_x, h_val))
            pygame.draw.rect(screen, lc, (center_x, top_y, right_x - center_x, h_val))

    theme_name = get_time_theme(int(hour))
    theme = THEMES[theme_name]
    theme_mtn = theme["mountain"]
    theme_mtnl = theme["mountain_light"]
    
    # Weather overrides
    mtn_snow = season == "winter" or (weather and getattr(weather, '_is_winter', False))
        
    draw_mountain(w * 0.25, h * 0.45, w * 0.6, theme_mtn, theme_mtnl, mtn_snow)
    draw_mountain(w * 0.75, h * 0.35, w * 0.5, theme_mtn, theme_mtnl, mtn_snow)
    draw_mountain(w * 0.5, h * 0.25, w * 0.4, theme_mtn, theme_mtnl, mtn_snow)
    
    # Ground
    grass1 = SEASON_COLORS[season]["grass1"]
    pygame.draw.rect(screen, grass1, (0, ground_y, w, h - ground_y))

    # Raccoon Logic
    is_uncomfortable = False
    if weather:
        is_uncomfortable = getattr(weather, 'rain_intensity', 0) > 0 or getattr(weather, '_is_winter', False)
        
    if now > random_hole_time + 15000:
        random_hole_time = now + random.randint(20000, 70000)
    
    is_randomly_hiding = (now > random_hole_time and now < random_hole_time + 15000)
    should_hide = is_uncomfortable or is_randomly_hiding
    
    center_hole_target = w / 2
    
    if should_hide:
        spd = w * 0.0015
        if abs(raccoon_x - center_hole_target) > spd:
            raccoon_state = "walking"
            if raccoon_x < center_hole_target:
                raccoon_x += spd
                raccoon_flip = False
            else:
                raccoon_x -= spd
                raccoon_flip = True
            raccoon_scale = 1.0
        else:
            raccoon_state = "hiding"
            raccoon_scale = max(0.0, raccoon_scale - 0.025)
    else:
        if raccoon_wander_target < 0 or now > raccoon_wander_timer:
            raccoon_wander_target = w * (0.07 + random.random() * 0.86)
            raccoon_wander_timer = now + random.randint(5000, 19000)
        
        spd = w * 0.0011
        raccoon_scale = min(1.0, raccoon_scale + 0.025)
        if abs(raccoon_x - raccoon_wander_target) > spd * 2:
            raccoon_state = "walking"
            if raccoon_x < raccoon_wander_target:
                raccoon_x += spd
                raccoon_flip = False
            else:
                raccoon_x -= spd
                raccoon_flip = True
        else:
            raccoon_state = "idle"
            
    raccoon_frame += 1
    if raccoon_state == "walking":
        if raccoon_frame % 30 == 0:
            raccoon_bounce = -25 if raccoon_bounce == 0 else 0
    else:
        if raccoon_frame % 90 == 0:
            if random.random() > 0.6:
                raccoon_flip = not raccoon_flip
            raccoon_bounce = -10 if raccoon_bounce == 0 else 0

    # Draw Side Trees
    img_small = load_image(f"{season_pfx}_small.png")
    if img_small:
        dsw = min(w * 0.18, 320)
        ss = dsw / img_small.get_width()
        sw, sh = int(img_small.get_width() * ss), int(img_small.get_height() * ss)
        scaled_small = pygame.transform.scale(img_small, (sw, sh))
        
        bot_offset = int(sh * 0.95)
        
        t1x = w * 0.15 - sw / 2
        screen.blit(scaled_small, (t1x, ground_y - bot_offset + 50))
        t2x = w * 0.80 - sw / 2
        screen.blit(scaled_small, (t2x, ground_y - bot_offset + 50))
        
    # Draw Center Tree
    use_in = (raccoon_state == "hiding")
    img_center = load_image(f"{season_pfx}_in.png") if use_in else load_image(f"{season_pfx}_out.png")
    if not img_center:
        img_center = load_image(f"{season_pfx}_out.png")
        
    center_img_w = 0
    if img_center:
        dw = min(w * 0.30, 520)
        sc = dw / img_center.get_width()
        cw, ch = int(img_center.get_width() * sc), int(img_center.get_height() * sc)
        scaled_center = pygame.transform.scale(img_center, (cw, ch))
        
        bot_offset = int(ch * 0.95)
        cx = w / 2 - cw / 2
        # Center tree should be higher (less Y offset)
        cy = ground_y - bot_offset + 50
        screen.blit(scaled_center, (cx, cy))
        center_img_w = cw

    # Draw Bonfire
    if is_night:
        bf_img = load_image("bonfire.png")
        bf_x = w / 2
        if bf_img:
            bf_sc = 80 / bf_img.get_height()
            bfw, bfh = int(bf_img.get_width() * bf_sc), int(bf_img.get_height() * bf_sc)
            scaled_bf = pygame.transform.scale(bf_img, (bfw, bfh))
            
            glow_alpha = int(((math.sin(now / 420.0) + 1) / 8 + 0.1) * 255)
            glow_surf = pygame.Surface((160, 160), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (230, 126, 34, glow_alpha), (80, 80), 80)
            screen.blit(glow_surf, (bf_x - 80, ground_y - 20 - 80 + 110))
            
            screen.blit(scaled_bf, (bf_x - bfw / 2, ground_y - bfh + 110))
            
    # Draw Raccoon
    rac_img = load_image("guaxinim_inteiro_transp.png")
    if rac_img and raccoon_scale > 0:
        spW, spH = 160, 160
        hiding_at_center = (raccoon_state == "hiding" and abs(raccoon_x - center_hole_target) < 160)
        
        if raccoon_scale > 0.3:
            shadow_w = int((60 if raccoon_bounce == 0 else 40) * raccoon_scale)
            shadow_h = int(8 * raccoon_scale)
            shadow_surf = pygame.Surface((shadow_w * 2, shadow_h * 2), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, 76), (0, 0, shadow_w * 2, shadow_h * 2))
            screen.blit(shadow_surf, (raccoon_x - shadow_w, ground_y - shadow_h))
            
        if hiding_at_center:
            if center_img_w > 0:
                bx = w / 2 + center_img_w / 2 - 48
                by = ground_y - 60
                pygame.draw.circle(screen, (0,0,0,150), (int(bx), int(by)), 18)
                font = pygame.font.SysFont("sans", 16)
                txt = font.render("Zzz", True, (255,255,255))
                screen.blit(txt, (bx - txt.get_width()//2, by - txt.get_height()//2))
        else:
            scale_x = raccoon_scale
            scale_y = raccoon_scale
            if raccoon_state == "walking":
                if raccoon_bounce != 0:
                    scale_x *= 0.95
                    scale_y *= 1.05
                else:
                    scale_x *= 1.05
                    scale_y *= 0.95
                    
            r_w = int(spW * scale_x)
            r_h = int(spH * scale_y)
            scaled_rac = pygame.transform.scale(rac_img, (r_w, r_h))
            if raccoon_flip:
                scaled_rac = pygame.transform.flip(scaled_rac, True, False)
            # Anchor raccoon feet to the ground line
            screen.blit(scaled_rac, (raccoon_x - r_w / 2, ground_y + raccoon_bounce - r_h + 75))
