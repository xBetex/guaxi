import math
import sys
import traceback
import unicodedata
from datetime import datetime, timedelta, timezone
import pygame
from celestial import draw_sun, draw_moon, generate_stars, update_shooting_stars, draw_stars, compute_moon_phase, get_phase_name
from landscape import draw_sky, draw_landscape
from controls import Slider, Button, draw_debug_overlay, draw_panel, draw_help, draw_test_menu
from data import get_season, get_month_name
from sprites import Gfx
from calendar_ui import Calendar
from weather import WeatherSystem
from birds import Flock
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
    """Guess hemisphere from timezone offset, temperature, and month."""
    try:
        off = _timezone_offset(data)
        temp = data.get("temp_C", 20)
        month = datetime.now().month

        # Positive offset → Europe/Asia/Africa → mostly northern
        if off > 0:
            return False

        # Negative offset → could be Americas
        # Use temperature + month to distinguish north vs south
        # June-August: hot = northern summer, cold = southern winter
        if 6 <= month <= 8:
            if temp > 22: return False  # hot → northern summer
            if temp < 12: return True   # cold → southern winter
        # December-February: hot = southern summer, cold = northern winter
        if month >= 12 or month <= 2:
            if temp > 22: return True   # hot → southern summer
            if temp < 12: return False  # cold → northern winter
        # Shoulder months (Mar-May, Sep-Nov): use temp extremes
        if temp > 25: return True       # very warm → likely southern
        if temp < 10: return False      # very cold → likely northern

        # Fallback: keep current but strongly prefer southern for negative offsets
        # (most landmass at negative offsets is in South America)
        return True
    except Exception:
        return current_southern

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
    now_button = Button(110, HEIGHT - 98, 44, 32, "Now")
    speed_slider = Slider(165, HEIGHT - 89, 170, 14, 0.1, 20, 1.0)
    live_time_button = Button(345, HEIGHT - 98, 50, 32, "LIVE")
    fast_forward_button = Button(400, HEIGHT - 98, 50, 32, "FFWD")
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
                        n = datetime.now(timezone.utc)
                        nd = n.timetuple().tm_yday - 1
                        secs = n.hour * 3600 + n.minute * 60 + n.second + city_tz_offset * 3600
                        if secs < 0: secs += 86400; nd -= 1
                        elif secs >= 86400: secs -= 86400; nd += 1
                        slider.value = (nd % 365) + secs / 86400.0
                        playing = True
                        fast_forward_active = False
                    else:
                        playing = False
                elif event.key == pygame.K_f:
                    fast_forward_active = not fast_forward_active
                    if fast_forward_active:
                        live_time_mode = False

            elif event.type == pygame.MOUSEWHEEL:
                slider.value += event.y * 0.3
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
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
                if now_button.handle_event(event):
                    n = datetime.now()
                    nd = n.timetuple().tm_yday - 1
                    nh = n.hour + n.minute / 60.0 + n.second / 3600.0
                    slider.value = nd + nh / 24.0
                if live_time_button.handle_event(event):
                    live_time_mode = not live_time_mode
                    if live_time_mode:
                        n = datetime.now(timezone.utc)
                        nd = n.timetuple().tm_yday - 1
                        secs = n.hour * 3600 + n.minute * 60 + n.second + city_tz_offset * 3600
                        if secs < 0: secs += 86400; nd -= 1
                        elif secs >= 86400: secs -= 86400; nd += 1
                        slider.value = (nd % 365) + secs / 86400.0
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
            n = datetime.now(timezone.utc)
            nd = n.timetuple().tm_yday - 1
            secs = n.hour * 3600 + n.minute * 60 + n.second + city_tz_offset * 3600
            if secs < 0: secs += 86400; nd -= 1
            elif secs >= 86400: secs -= 86400; nd += 1
            slider.value = (nd % 365) + secs / 86400.0
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
            wind_px = live_weather_data["wind_speed"] * 1.5
            for c in weather.clouds:
                c.base_speed = wind_px
            # timezone offset — set slider to city's local time on first data arrival
            if not weather._tz_applied:
                off = _timezone_offset(live_weather_data)
                city_tz_offset = off
                if off != 0:
                    n = datetime.now(timezone.utc)
                    secs = n.hour * 3600 + n.minute * 60 + n.second + off * 3600
                    nd = n.timetuple().tm_yday - 1
                    if secs < 0: secs += 86400; nd -= 1
                    elif secs >= 86400: secs -= 86400; nd += 1
                    slider.value = (nd % 365) + secs / 86400.0
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
        sim_date = datetime(2026, 1, 1) + timedelta(days=day)
        moon_phase = compute_moon_phase(sim_date)
        phase_name = get_phase_name(moon_phase)
        year_pct = day / 364.99 * 100

        draw_sky(screen, WIDTH, HEIGHT, hour)
        draw_stars(screen, stars, shooting_stars, hour, WIDTH, HEIGHT, speed)
        draw_sun(screen, WIDTH, HEIGHT, hour)
        draw_moon(screen, WIDTH, HEIGHT, hour, moon_phase)
        weather.draw_clouds(screen, WIDTH, HEIGHT, hour, pygame.time.get_ticks() / 1000)
        flock.draw(screen)
        draw_landscape(screen, WIDTH, HEIGHT, season, hour, day, weather)
        weather.draw(screen, WIDTH, HEIGHT, hour)
        update_shooting_stars(shooting_stars, WIDTH, HEIGHT, speed)

        slider.rect.y = HEIGHT - 55
        slider.width = WIDTH - 80
        speed_slider.rect.y = HEIGHT - 89
        play_button.rect.y = HEIGHT - 98
        now_button.rect.y = HEIGHT - 98
        live_time_button.rect.y = HEIGHT - 98
        fast_forward_button.rect.y = HEIGHT - 98

        if show_controls:
            panel_rect = pygame.Rect(20, HEIGHT - 115, WIDTH - 40, 100)
            draw_panel(screen, panel_rect)
            slider.draw(screen)
            speed_slider.draw(screen)
            play_button.draw(screen)
            now_button.draw(screen)
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
        next_season_name = {80: "autumn", 172: "winter", 264: "spring", 355: "summer", 365: "summer"}[next_season_day]
        days_to_season = next_season_day - day
        cycle = 29.53058867
        days_to_full = ((0.5 - moon_phase) % 1.0) * cycle
        days_to_new = ((1.0 - moon_phase) % 1.0) * cycle

        moonrise_h = (6 + moon_phase * 24) % 24
        moonset_h = (moonrise_h + 12) % 24

        lines = [
            (f"{date_str}  {phase_name}", font, (220, 230, 255), "hud_header"),
            (f"{hh:02}:{mm:02}  ·  {season.title()}  ·  Day {day}", font_small, (190, 205, 235), "hud"),
            (f"Speed {speed:.1f}x{'  LIVE' if live_time_mode else ''}{'  FFWD' if fast_forward_active else ''}", font_small, (170, 190, 220), "hud"),
            (f"Sunrise 6:00  Sunset 18:00", font_small, (150, 175, 210), "hud"),
            (f"Moonrise {int(moonrise_h):02}:{int((moonrise_h%1)*60):02}  Moonset {int(moonset_h):02}:{int((moonset_h%1)*60):02}", font_small, (150, 175, 210), "hud"),
            (f"Next: {next_season_name} in {days_to_season}d", font_small, (130, 155, 190), "hud"),
            (f"Full {days_to_full:.1f}d  New {days_to_new:.1f}d", font_small, (130, 155, 190), "hud"),
            (f"Now: {datetime.now():%H:%M:%S}", font_small, (110, 135, 175), "hud"),
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
