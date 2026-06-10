import math
import sys
import traceback
import unicodedata
from datetime import datetime, timedelta, timezone
import pygame
from celestial import draw_sun, draw_moon, generate_stars, update_shooting_stars, draw_stars, draw_aurora, compute_moon_phase, get_phase_name
from landscape import draw_sky, draw_landscape
from controls import Slider, Button, draw_debug_overlay, draw_panel, draw_help, draw_test_menu
from data import get_season, get_month_name
from sprites import Gfx
from calendar_ui import Calendar
from weather import WeatherSystem
from birds import Flock
from fireflies import FireflySwarm
import live_weather

CRASH_LOG = "crash.log"
REALTIME_DAY_RATE = 1.0 / 86400.0

def _timezone_offset(data: dict) -> float:
    """Return UTC offset in hours from live weather data, or 0."""
    try:
        local = data.get("localObsDateTime", "")
        obs = data.get("observation_time", "")
        if not local or not obs:
            return 0
        lh = int(local.split()[1].split(":")[0])
        lp = local.split()[2].upper()
        if lp == "PM" and lh != 12: lh += 12
        if lp == "AM" and lh == 12: lh = 0
        oh = int(obs.split(":")[0])
        op = obs.split()[1].upper() if " " in obs else "AM"
        if op == "PM" and oh != 12: oh += 12
        if op == "AM" and oh == 12: oh = 0
        offset = lh - oh
        if offset > 12: offset -= 24
        elif offset < -12: offset += 24
        return offset
    except Exception:
        return 0

def _guess_hemisphere(data: dict, current_southern: bool) -> bool:
    """Guess hemisphere from timezone offset and temperature.

    Uses conservative thresholds to avoid misidentifying southern cities
    (e.g. São Paulo in a warm winter day) as northern hemisphere.
    Only flips hemisphere on extreme, unambiguous temperatures.
    """
    try:
        off = _timezone_offset(data)
        temp = data.get("temp_C", 20)
        month = datetime.now().month

        # Positive UTC offset → Europe/Asia/Africa → northern hemisphere
        if off > 0:
            return False

        # Negative UTC offset → Americas (mostly).
        # Only override if temperature is *extremely* unambiguous:
        #   June–Aug with scorching heat (>30°C) → must be northern summer
        #   June–Aug with freezing cold (<3°C)   → could be southern winter too,
        #                                           but that's also plausible in
        #                                           high-altitude S. America — keep current
        #   Dec–Feb with very hot (>30°C)        → southern summer
        #   Dec–Feb with genuinely freezing (<3°C) → northern winter
        if 6 <= month <= 8:
            if temp > 30: return False   # Unambiguously northern summer
            if temp < 3:  return False   # Deep freeze → probably Canada/US north
        if month >= 12 or month <= 2:
            if temp > 30: return True    # Unambiguously southern summer
            if temp < 3:  return False   # Very cold → northern winter

        # Not enough signal — preserve whatever the user/default currently has.
        # This prevents mild subtropical winters (~15–22°C) from being misread.
        return current_southern
    except Exception:
        return current_southern

def _snap_slider_to_now(slider, city_tz_offset: float) -> None:
    """Snap the timeline slider to the current real time.

    Uses the local machine clock when no city timezone offset is known (offset == 0),
    so the result is always coherent regardless of live-weather data availability.
    When a city UTC offset is set, converts from UTC to keep the city's local time.
    """
    if city_tz_offset == 0:
        n = datetime.now()
        nd = n.timetuple().tm_yday - 1
        secs = n.hour * 3600 + n.minute * 60 + n.second
    else:
        n = datetime.now(timezone.utc)
        nd = n.timetuple().tm_yday - 1
        secs = n.hour * 3600 + n.minute * 60 + n.second + city_tz_offset * 3600
        if secs < 0:
            secs += 86400
            nd -= 1
        elif secs >= 86400:
            secs -= 86400
            nd += 1
    slider.value = (nd % 365) + secs / 86400.0


def write_crash(err):
    with open(CRASH_LOG, "a") as f:
        f.write(f"\n=== CRASH {datetime.now().isoformat()} ===\n")
        traceback.print_exc(file=f)
        f.write("\n")

try:
    pygame.init()
    WIDTH, HEIGHT = 1280, 720
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Moon & Stars")

    clock = pygame.time.Clock()
    Gfx.init()

    try:
        font = pygame.font.Font("Outfit-Regular.ttf", 18)
        font_small = pygame.font.Font("Outfit-Regular.ttf", 14)
    except:
        font = pygame.font.SysFont("sans", 18)
        font_small = pygame.font.SysFont("sans", 14)

    now = datetime.now()
    start_day = now.timetuple().tm_yday - 1
    start_hour = now.hour + now.minute / 60.0
    start_value = start_day + start_hour / 24.0

    city_name = "São Paulo, Brazil"
    southern = True

    slider = Slider(40, HEIGHT - 55, WIDTH - 80, 16, 0, 364.99, start_value)
    play_button = Button(40, HEIGHT - 98, 65, 32, "Play")
    speed_slider = Slider(110, HEIGHT - 89, 210, 14, 0.1, 20, 1.0)
    live_time_button = Button(330, HEIGHT - 98, 50, 32, "Now")
    fast_forward_button = Button(385, HEIGHT - 98, 50, 32, "FFWD")
    calendar = Calendar(font, font_small)
    weather = WeatherSystem()
    flock = Flock(WIDTH, HEIGHT)
    go_button = Button(12, 8, 52, 22, "Go")

    star_count = WIDTH * HEIGHT // 4500
    stars = generate_stars(star_count, WIDTH, HEIGHT)
    shooting_stars = []

    playing = True
    live_time_mode = False
    fast_forward_active = False
    fast_forward_multiplier = 10.0
    live_weather_data = None
    city_tz_offset = 0
    city_editing = False
    city_input = ""
    city_input_selected = True
    city_rect = pygame.Rect(12, 8, 260, 22)
    show_controls = True
    show_debug = False
    show_test = False
    show_help = False
    fullscreen = False

    # ── Fun extras ──────────────────────────────────────────────────────────
    firefly_swarm = FireflySwarm()
    aurora_override = False   # A key toggles manual aurora
    total_time = 0.0          # elapsed wall-clock seconds (for aurora animation)
    meteor_shower_timer = 0.0 # seconds remaining in meteor shower burst
    camera_mode = 0

    running = True

    while running:
        dt = clock.tick(60) / 1000.0
        WIDTH, HEIGHT = screen.get_size()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                star_count = event.w * event.h // 4500
                stars = generate_stars(star_count, event.w, event.h)

            elif event.type == pygame.KEYDOWN:
                if city_editing:
                    if event.key == pygame.K_RETURN:
                        if city_input.strip():
                            city_name = city_input.strip()
                            live_weather.get_weather(city_name, force_refresh=True)
                            weather._tz_applied = False
                            live_weather_data = None
                            city_tz_offset = 0
                        city_editing = False
                        city_input = ""
                        live_time_mode = True
                        playing = True
                        fast_forward_active = False
                    elif event.key == pygame.K_ESCAPE:
                        city_editing = False
                        city_input = ""
                    elif event.key == pygame.K_BACKSPACE:
                        if city_input_selected:
                            city_input = ""
                        else:
                            city_input = city_input[:-1]
                        city_input_selected = False
                    elif event.unicode:
                        if city_input_selected:
                            city_input = ""
                        city_input += event.unicode
                        city_input = unicodedata.normalize('NFC', city_input)
                        city_input_selected = False
                elif event.key == pygame.K_SPACE:
                    playing = not playing
                elif event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                    speed_slider.value = min(20.0, speed_slider.value * 1.5)
                elif event.key == pygame.K_MINUS:
                    speed_slider.value = max(0.1, speed_slider.value / 1.5)
                elif event.key == pygame.K_s:
                    show_controls = not show_controls
                elif event.key == pygame.K_h:
                    show_help = not show_help
                elif event.key == pygame.K_F5:
                    show_test = not show_test
                elif event.key == pygame.K_F2:
                    show_debug = not show_debug
                elif event.key == pygame.K_F3:
                    calendar.toggle()
                    if calendar.visible:
                        calendar.go_to_day(day)
                elif event.key == pygame.K_F11:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
                    nw, nh = screen.get_size()
                    star_count = nw * nh // 4500
                    stars = generate_stars(star_count, nw, nh)
                elif event.key == pygame.K_t:
                    live_time_mode = not live_time_mode
                    if live_time_mode:
                        _snap_slider_to_now(slider, city_tz_offset)
                        playing = True
                        fast_forward_active = False
                    else:
                        playing = False
                elif event.key == pygame.K_f:
                    fast_forward_active = not fast_forward_active
                    if fast_forward_active:
                        live_time_mode = False
                # ── Fun shortcuts ──────────────────────────────────────────
                elif event.key == pygame.K_r:
                    # Toggle rain
                    if weather.rain_intensity > 0.05:
                        weather.rain_intensity = 0.0
                    else:
                        weather.rain_intensity = 0.6
                elif event.key == pygame.K_n:
                    # Trigger a 5-second meteor shower
                    meteor_shower_timer = 5.0
                elif event.key == pygame.K_a:
                    # Toggle aurora borealis
                    aurora_override = not aurora_override
                elif event.key == pygame.K_b:
                    # Lightning bolt
                    weather.force_flash()
                elif event.key == pygame.K_g:
                    # Jump forward 6 hours (skip to a different time of day)
                    slider.value = (slider.value + 6 / 24.0) % 365
                    live_time_mode = False
                elif event.key == pygame.K_v:
                    camera_mode = (camera_mode + 1) % 4

            elif event.type == pygame.MOUSEWHEEL:
                slider.value += event.y * 0.3
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                # Click on the night sky to launch a shooting star at cursor
                if my < int(HEIGHT * 0.72) and (hour < 6 or hour >= 18):
                    if not (city_editing and city_rect.collidepoint(mx, my)):
                        shooting_stars.append({
                            "x": mx + 60,
                            "y": max(0, my - 20),
                            "len": 80,
                            "speed": 7,
                        })
                if city_editing and go_button.rect.collidepoint(mx, my):
                    if city_input.strip():
                        city_name = city_input.strip()
                        live_weather.get_weather(city_name, force_refresh=True)
                        weather._tz_applied = False
                        live_weather_data = None
                        city_tz_offset = 0
                    city_editing = False
                    city_input = ""
                    live_time_mode = True
                    playing = True
                    fast_forward_active = False
                elif city_rect.collidepoint(mx, my):
                    if mx > city_rect.right - 40 and my < city_rect.top + 22:
                        southern = not southern
                    else:
                        city_editing = True
                        city_input = city_name
                        city_input_selected = True

            if calendar.handle_event(event, slider) == "date_selected":
                live_time_mode = False
            if show_test:
                pass
            if show_controls:
                slider.handle_event(event)
                speed_slider.handle_event(event)
                if play_button.handle_event(event):
                    playing = not playing
                if live_time_button.handle_event(event):
                    live_time_mode = not live_time_mode
                    if live_time_mode:
                        _snap_slider_to_now(slider, city_tz_offset)
                        playing = True
                        fast_forward_active = False
                    else:
                        playing = False
                if fast_forward_button.handle_event(event):
                    fast_forward_active = not fast_forward_active
                    if fast_forward_active:
                        live_time_mode = False

        slider.value %= 365
        speed = speed_slider.value

        if live_time_mode:
            _snap_slider_to_now(slider, city_tz_offset)
        else:
            effective_speed = speed
            if fast_forward_active:
                effective_speed *= fast_forward_multiplier
            if playing:
                slider.value += REALTIME_DAY_RATE * effective_speed * dt

        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT] or keys[pygame.K_DOWN]:
            slider.value += REALTIME_DAY_RATE * 2400 * speed * dt
        if keys[pygame.K_LEFT] or keys[pygame.K_UP]:
            slider.value -= REALTIME_DAY_RATE * 2400 * speed * dt

        day = int(slider.value)
        frac = slider.value - day
        hour = frac * 24

        season = get_season(day, southern)

        weather.update(season, hour, day, speed, dt, WIDTH, HEIGHT)

        live_weather_data = live_weather.get_weather(city_name)
        if live_weather_data:
            weather.humidity = live_weather_data["humidity"]
            weather.rain_intensity = live_weather_data["rain_intensity"]
            weather.fog_intensity = live_weather_data["fog_intensity"]
            weather._is_winter = live_weather_data["is_snow"]
            weather.wind_speed = live_weather_data["wind_speed"]
            weather.cloud_cover = live_weather_data["cloud_cover"]
            wind_px = live_weather_data["wind_speed"] * 1.5
            for c in weather.clouds:
                c.base_speed = wind_px
            # timezone offset — set slider to city's local time on first data arrival
            if not weather._tz_applied:
                city_tz_offset = _timezone_offset(live_weather_data)
                _snap_slider_to_now(slider, city_tz_offset)
                weather._tz_applied = True
                # guess hemisphere from timezone + temperature
                h = _guess_hemisphere(live_weather_data, southern)
                if h != southern:
                    southern = h
                # re-derive day/hour/season so all draw calls use the new time
                day = int(slider.value)
                frac = slider.value - day
                hour = frac * 24
                season = get_season(day, southern)

        flock.update(dt, hour, speed, WIDTH, HEIGHT)
        firefly_swarm.update(dt, hour, speed, WIDTH, HEIGHT)
        sim_date = datetime(2026, 1, 1) + timedelta(days=day)
        moon_phase = compute_moon_phase(sim_date)
        phase_name = get_phase_name(moon_phase)
        year_pct = day / 364.99 * 100

        total_time += dt

        # Meteor shower burst
        if meteor_shower_timer > 0:
            meteor_shower_timer -= dt
            if len(shooting_stars) < 12:
                import random as _rnd
                shooting_stars.append({
                    "x": _rnd.randint(0, WIDTH),
                    "y": _rnd.randint(0, int(HEIGHT * 0.25)),
                    "len": _rnd.randint(40, 120),
                    "speed": _rnd.uniform(5, 11),
                })

        # Aurora intensity: winter nights naturally, or manual override
        aurora_intensity = 0.0
        if aurora_override:
            aurora_intensity = 0.85
        elif season == "winter" and (hour < 5 or hour >= 19):
            aurora_intensity = 0.55

        draw_sky(screen, WIDTH, HEIGHT, hour)
        draw_stars(screen, stars, shooting_stars, hour, WIDTH, HEIGHT, speed)
        draw_aurora(screen, WIDTH, HEIGHT, hour, season, total_time, aurora_intensity)
        draw_sun(screen, WIDTH, HEIGHT, hour)
        draw_moon(screen, WIDTH, HEIGHT, hour, moon_phase)
        weather.draw_clouds(screen, WIDTH, HEIGHT, hour, pygame.time.get_ticks() / 1000)
        draw_landscape(screen, WIDTH, HEIGHT, season, hour, day, weather)
        flock.draw(screen)
        firefly_swarm.draw(screen, WIDTH, HEIGHT)
        weather.draw(screen, WIDTH, HEIGHT, hour)
        update_shooting_stars(shooting_stars, WIDTH, HEIGHT, speed)

        if camera_mode > 0:
            pip_w, pip_h = 320, 180
            pip_surf = pygame.Surface((pip_w, pip_h))
            
            if camera_mode == 3:  # Sky Telescope
                draw_sky(pip_surf, pip_w, pip_h, hour)
                pip_stars = [s for s in stars if s["x"] < pip_w and s["y"] < pip_h]
                pip_shooting = [s for s in shooting_stars if s["x"] < pip_w and s["y"] < pip_h]
                draw_stars(pip_surf, pip_stars, pip_shooting, hour, pip_w, pip_h, speed)
                draw_aurora(pip_surf, pip_w, pip_h, hour, season, total_time, aurora_intensity)
                draw_sun(pip_surf, pip_w, pip_h, hour)
                draw_moon(pip_surf, pip_w, pip_h, hour, moon_phase)
                lbl = "SKYCAM"
                
            elif camera_mode == 1:  # Inside City
                draw_sky(pip_surf, pip_w, pip_h, hour)
                from cityscape import draw_city_layer
                from landscape import _get_city
                cw, ch = pip_w * 6, pip_h * 4
                front, mid, far = _get_city(cw, ch)
                city_surf = pygame.Surface((cw, ch), pygame.SRCALPHA)
                is_dark = (hour < 6 or hour >= 19)
                cols = [(far, (22, 28, 44) if is_dark else (70, 85, 110), False, False),
                        (mid, (30, 34, 54) if is_dark else (45, 55, 80), False, False),
                        (front, (14, 16, 26) if is_dark else (25, 28, 42), True, True)]
                for bldgs, col, win, protr in cols:
                    draw_city_layer(city_surf, cw, ch, ch - 20, bldgs, col, hour, win, protr)
                pip_surf.blit(city_surf, (-pip_w * 2.5, -(ch - pip_h)))
                lbl = "CITYCAM"
                
            elif camera_mode == 2:  # Outside Forest
                draw_sky(pip_surf, pip_w, pip_h, hour)
                from trees import draw_trees
                fw, fh = pip_w * 3, pip_h * 3
                forest_surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
                draw_trees(forest_surf, fw, fh, fh - 20, season, day, 2.5, weather)
                pip_surf.blit(forest_surf, (-pip_w * 1.0, -(fh - pip_h)))
                lbl = "FORESTCAM"

            # Draw frame and label
            pygame.draw.rect(pip_surf, (80, 95, 130), pip_surf.get_rect(), width=2, border_radius=4)
            lbl_surf = font_small.render(lbl, True, (255, 255, 255))
            
            lbl_bg = pygame.Surface((lbl_surf.get_width() + 12, lbl_surf.get_height() + 6), pygame.SRCALPHA)
            lbl_bg.fill((0, 0, 0, 180))
            pip_surf.blit(lbl_bg, (4, 4))
            pip_surf.blit(lbl_surf, (10, 7))
            
            pip_x = WIDTH - pip_w - 20
            pip_y = HEIGHT - pip_h - 20
            screen.blit(pip_surf, (pip_x, pip_y))

        slider.rect.y = HEIGHT - 55
        slider.width = WIDTH - 80
        speed_slider.rect.y = HEIGHT - 89
        play_button.rect.y = HEIGHT - 98
        live_time_button.rect.y = HEIGHT - 98
        fast_forward_button.rect.y = HEIGHT - 98

        if show_controls:
            panel_rect = pygame.Rect(20, HEIGHT - 115, WIDTH - 40, 100)
            draw_panel(screen, panel_rect)
            slider.draw(screen)
            speed_slider.draw(screen)
            play_button.draw(screen)
            live_time_button.draw(screen)
            fast_forward_button.draw(screen)

        hh = int(hour)
        mm = int((hour - hh) * 60)

        # ── Weather info panel (Discord style) ──
        wpw = 280
        wpx = 12
        wpy = 8
        if city_editing:
            display_name = city_input + ("|" if int(pygame.time.get_ticks() / 500) % 2 == 0 else "")
        else:
            display_name = city_name
        hem = "S" if southern else "N"
        # Header row
        w_lines = [(f"{display_name}  [{hem}]", font, (220, 230, 255), "header")]
        # Weather data or fallback
        if live_weather_data:
            d = live_weather_data
            temp_str = f"{d['temp_C']:.0f}°C"
            desc_str = d['desc']
            # Main temp + description
            w_lines.append((f"{temp_str}  {desc_str}", font, (255, 235, 190), "big"))
            # Stats rows
            w_lines.append((f"Hum {d['humidity']*100:.0f}%  |  Wind {d['wind_speed']:.0f} km/h {d['wind_dir']}", font_small, (180, 205, 240), "stats"))
            w_lines.append((f"Clouds {d['cloud_cover']*100:.0f}%  |  Vis {d['visibility_km']:.0f} km", font_small, (180, 205, 240), "stats"))
            # Rain/fog with color coding
            rain_col = (120, 200, 255) if d['rain_intensity'] > 0.05 else (140, 160, 190)
            fog_col = (180, 200, 220) if d['fog_intensity'] > 0.05 else (140, 160, 190)
            w_lines.append((f"Rain {d['rain_intensity']*100:.0f}%  |  Fog {d['fog_intensity']*100:.0f}%", font_small, (rain_col, fog_col), "dual"))
        else:
            w_lines.append((f"{season.title()}  ·  {len(weather.clouds)} clouds", font_small, (160, 185, 220), "stats"))
            w_lines.append((f"{season.title()}  ·  {len(weather.clouds)} clouds", font_small, (160, 185, 220), "stats"))
            w_lines.append((f"Hum {weather.humidity*100:.0f}%", font_small, (160, 185, 220), "stats"))
            if weather._flash > 0.01:
                w_lines.append(("Lightning", font_small, (255, 220, 100), "stats"))
            if weather._rainbow > 0.1:
                w_lines.append(("Rainbow", font_small, (180, 220, 255), "stats"))

        # Draw the panel
        row_h = 24
        header_h = 32
        wp_h = header_h + (len(w_lines) - 1) * row_h + 16
        city_rect = pygame.Rect(wpx, wpy, wpw, wp_h)

        # Background — dark Discord-like surface
        wp_bg = pygame.Surface((wpw, wp_h), pygame.SRCALPHA)
        wp_bg.fill((24, 26, 32, 235))  # Discord dark background
        # Subtle border
        pygame.draw.rect(wp_bg, (50, 55, 70, 100), wp_bg.get_rect(), width=1, border_radius=8)
        # Accent line at top
        accent = pygame.Surface((wpw - 4, 2), pygame.SRCALPHA)
        accent.fill((88, 101, 242, 200))  # Discord blurple
        wp_bg.blit(accent, (2, 2))
        screen.blit(wp_bg, (wpx, wpy))

        y = wpy + 10
        for i, item in enumerate(w_lines):
            text, f, color, style = item
            if style == "dual":
                c1, c2 = color
                surf1 = f.render(text.split("  ")[0], True, c1)
                surf2 = f.render("  " + text.split("  ")[1], True, c2)
                screen.blit(surf1, (wpx + 14, y))
                screen.blit(surf2, (wpx + 14 + surf1.get_width(), y))
            else:
                col = color
                surf = f.render(text, True, col)
                screen.blit(surf, (wpx + 14, y))
            y += row_h if i > 0 else header_h

        if city_editing:
            go_button.rect.topleft = (wpx + wpw - 54, wpy + 8)
            go_button.draw(screen)
            hint = font_small.render("Enter = apply  ·  Esc = cancel", True, (100, 115, 145))
            screen.blit(hint, (wpx + 14, y + 4))

        date_str = sim_date.strftime("%b %d, %Y")
        season_ends = [80, 172, 264, 355]
        next_season_day = next((b for b in season_ends if day < b), 365)
        if southern:
            next_season_name = {80: "autumn", 172: "winter", 264: "spring", 355: "summer", 365: "summer"}[next_season_day]
        else:
            next_season_name = {80: "spring", 172: "summer", 264: "autumn", 355: "winter", 365: "winter"}[next_season_day]
        days_to_season = next_season_day - day
        cycle = 29.53058867
        days_to_full = ((0.5 - moon_phase) % 1.0) * cycle
        days_to_new = ((1.0 - moon_phase) % 1.0) * cycle

        moonrise_h = (6 + moon_phase * 24) % 24
        moonset_h = (moonrise_h + 12) % 24

        mode_tag = "  ◉ LIVE" if live_time_mode else ("  ⏩ FFWD" if fast_forward_active else "")
        lines = [
            (f"{date_str}  {phase_name}", font, (220, 230, 255), "hud_header"),
            (f"{hh:02}:{mm:02}  ·  {season.title()}  ·  Day {day}{mode_tag}", font_small, (190, 205, 235), "hud"),
            (f"Speed {speed:.1f}x", font_small, (170, 190, 220), "hud"),
            (f"Sunrise 6:00  Sunset 18:00", font_small, (150, 175, 210), "hud"),
            (f"Moonrise {int(moonrise_h):02}:{int((moonrise_h%1)*60):02}  Moonset {int(moonset_h):02}:{int((moonset_h%1)*60):02}", font_small, (150, 175, 210), "hud"),
            (f"Next: {next_season_name} in {days_to_season}d", font_small, (130, 155, 190), "hud"),
            (f"Full {days_to_full:.1f}d  New {days_to_new:.1f}d", font_small, (130, 155, 190), "hud"),
        ]

        tw = max(l[1].size(l[0])[0] for l in lines) + 28
        th = len(lines) * 22 + 18
        px = WIDTH - 20 - tw
        py = 8
        bg = pygame.Surface((tw, th), pygame.SRCALPHA)
        bg.fill((24, 26, 32, 235))
        pygame.draw.rect(bg, (50, 55, 70, 100), bg.get_rect(), width=1, border_radius=8)
        screen.blit(bg, (px, py))

        for i, (text, f, color, style) in enumerate(lines):
            if style == "hud_header":
                y = py + 12
            else:
                y = py + 12 + i * 22
            surf = f.render(text, True, color)
            screen.blit(surf, (px + 14, y))

        if show_debug:
            draw_debug_overlay(screen, font_small, clock.get_fps(), [])

        calendar.draw(screen)

        if show_help:
            draw_help(screen, font)

        if show_test:
            draw_test_menu(screen, font_small, weather, moon_phase, phase_name)

        pygame.display.flip()

    pygame.quit()

except SystemExit:
    raise
except:
    write_crash(sys.exc_info())
    print(f"Fatal error. See {CRASH_LOG}")
    raise
