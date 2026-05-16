import math
import sys
import traceback
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
    live_button = Button(345, HEIGHT - 98, 50, 32, "Live")
    calendar = Calendar(font, font_small)
    weather = WeatherSystem()
    flock = Flock(WIDTH, HEIGHT)
    w_rain_slider = Slider(20, 310, 160, 12, 0, 1.0, 0)
    w_fog_slider = Slider(20, 340, 160, 12, 0, 1.0, 0)
    w_hum_slider = Slider(20, 370, 160, 12, 0, 1.0, 0.5)

    star_count = WIDTH * HEIGHT // 4500
    stars = generate_stars(star_count, WIDTH, HEIGHT)
    shooting_stars = []

    playing = True
    live_mode = False
    live_weather_data = None
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
                if event.key == pygame.K_SPACE:
                    playing = not playing
                elif event.key in (pygame.K_EQUALS, pygame.K_PLUS):
                    speed_slider.value = min(20.0, speed_slider.value * 1.5)
                elif event.key == pygame.K_MINUS:
                    speed_slider.value = max(0.1, speed_slider.value / 1.5)
                elif event.key == pygame.K_w:
                    print(f"Weather - Rain: {weather.rain_intensity:.2f}, Fog: {weather.fog_intensity:.2f}")
                elif event.key == pygame.K_1:
                    weather.force_rain(0.8)
                elif event.key == pygame.K_2:
                    weather.force_fog(0.6)
                elif event.key == pygame.K_3:
                    weather.force_snow(True)
                elif event.key == pygame.K_4:
                    weather.force_flash()
                elif event.key == pygame.K_5:
                    weather.force_rainbow()
                elif event.key == pygame.K_6:
                    weather.rain_intensity = 0
                    weather.fog_intensity = 0
                    weather._is_winter = False
                    weather._rainbow = 0
                    weather._flash = 0
                    weather._manual = False
                elif event.key == pygame.K_s:
                    show_controls = not show_controls
                elif event.key == pygame.K_l:
                    live_mode = not live_mode
                    if live_mode:
                        n = datetime.now()
                        nd = n.timetuple().tm_yday - 1
                        nh = n.hour + n.minute / 60.0 + n.second / 3600.0
                        slider.value = nd + nh / 24.0
                        weather._manual = True
                        weather.rain_intensity = 0
                        weather.fog_intensity = 0
                        weather.target_clouds = 5
                        weather.rain_drops.clear()
                        live_weather.get_weather(city_name, force_refresh=True)
                    else:
                        weather._manual = False
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

            elif event.type == pygame.MOUSEWHEEL and show_controls:
                slider.value += event.y * 0.3

            if calendar.handle_event(event, slider):
                pass
            if show_test:
                w_rain_slider.handle_event(event)
                w_fog_slider.handle_event(event)
                w_hum_slider.handle_event(event)
            if show_controls:
                slider.handle_event(event)
                speed_slider.handle_event(event)
                if play_button.handle_event(event):
                    playing = not playing
                if live_button.handle_event(event):
                    live_mode = not live_mode
                    if live_mode:
                        n = datetime.now()
                        nd = n.timetuple().tm_yday - 1
                        nh = n.hour + n.minute / 60.0 + n.second / 3600.0
                        slider.value = nd + nh / 24.0
                        weather._manual = True
                        weather.rain_intensity = 0
                        weather.fog_intensity = 0
                        weather.target_clouds = 5
                        weather.rain_drops.clear()
                        live_weather.get_weather(city_name, force_refresh=True)
                    else:
                        weather._manual = False
                if now_button.handle_event(event):
                    n = datetime.now()
                    nd = n.timetuple().tm_yday - 1
                    nh = n.hour + n.minute / 60.0 + n.second / 3600.0
                    slider.value = nd + nh / 24.0

        slider.value %= 365
        speed = speed_slider.value

        if playing:
            slider.value += REALTIME_DAY_RATE * speed * dt

        keys = pygame.key.get_pressed()
        if keys[pygame.K_RIGHT] or keys[pygame.K_DOWN]:
            slider.value += REALTIME_DAY_RATE * 2400 * speed * dt
        if keys[pygame.K_LEFT] or keys[pygame.K_UP]:
            slider.value -= REALTIME_DAY_RATE * 2400 * speed * dt

        day = int(slider.value)
        frac = slider.value - day
        hour = frac * 24

        season = get_season(day, southern)

        live_weather_data = live_weather.get_weather(city_name)
        if live_mode:
            weather._manual = True
            if live_weather_data:
                live_weather.apply_live_weather(weather, live_weather_data)
            else:
                weather.rain_intensity = 0
                weather.fog_intensity = 0
                weather.rain_drops.clear()
                weather.target_clouds = 5
        else:
            weather._manual = False
        weather.update(season, hour, day, speed, dt, WIDTH, HEIGHT)

        # hard kill — override anything update() set for rain in live mode
        if live_mode and weather.rain_intensity > 0:
            print(f"[LIVE] rain kill: rain={weather.rain_intensity:.4f} drops={len(weather.rain_drops)}")
            weather.rain_intensity = 0
            weather.rain_drops.clear()
        if live_mode and weather.fog_intensity > 0.01:
            print(f"[LIVE] fog active: fog={weather.fog_intensity:.4f}")
        # keep cloud count from live data (update() may have set seasonal defaults when _manual was off)
        if live_mode and live_weather_data:
            cf = live_weather_data["cloud_cover"] ** 1.4
            weather.target_clouds = max(0, int(cf * 18))

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
        live_button.rect.y = HEIGHT - 98

        if show_controls:
            panel_rect = pygame.Rect(20, HEIGHT - 115, WIDTH - 40, 100)
            draw_panel(screen, panel_rect)
            slider.draw(screen)
            speed_slider.draw(screen)
            play_button.draw(screen)
            now_button.draw(screen)
            live_button.draw(screen)

        hh = int(hour)
        mm = int((hour - hh) * 60)

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
            (f"{date_str}  {phase_name}  {year_pct:.1f}%", font, (210, 220, 255)),
            (f"Day {day}  {get_month_name(day)}  {season.title()}  {hh:02}:{mm:02}", font, (230, 235, 245)),
            (city_name, font_small, (160, 175, 210)),
            (f"Speed {speed:.1f}x  {'LIVE' if live_mode else 'Simulated'}", font_small, (200, 210, 230)),
            (f"Sunrise 6:00  Sunset 18:00", font_small, (150, 170, 210)),
            (f"Moonrise {int(moonrise_h):02}:{int((moonrise_h%1)*60):02}  Moonset {int(moonset_h):02}:{int((moonset_h%1)*60):02}", font_small, (150, 170, 210)),
            (f"Next season: {next_season_name} in {days_to_season}d", font_small, (130, 150, 190)),
            (f"Full moon in {days_to_full:.1f}d  ·  New moon in {days_to_new:.1f}d", font_small, (130, 150, 190)),
            (f"Now: {datetime.now():%H:%M:%S}", font_small, (120, 140, 180)),
        ]
        info = live_weather.format_weather(live_weather_data, city_name, font_small)
        lines.extend(info)

        tw = max(l[1].size(l[0])[0] for l in lines) + 24
        th = len(lines) * 20 + 16
        px = WIDTH - 20 - tw
        py = 8
        bg = pygame.Surface((tw, th), pygame.SRCALPHA)
        bg.fill((6, 8, 16, 180))
        pygame.draw.rect(bg, (30, 36, 55, 100), bg.get_rect(), width=1, border_radius=4)
        screen.blit(bg, (px, py))

        for i, (text, f, color) in enumerate(lines):
            surf = f.render(text, True, color)
            screen.blit(surf, (px + 12, py + 10 + i * 20))

        if show_debug:
            elements = [
                ("Play", play_button.rect),
                ("Now", now_button.rect),
                ("Time Slider", slider.rect),
                ("Speed Slider", speed_slider.rect),
            ]
            draw_debug_overlay(screen, font_small, clock.get_fps(), elements)
            # live weather debug
            dw = font_small.render("LIVE WEATHER DEBUG", True, (255, 200, 100))
            screen.blit(dw, (10, 80))
            y = 104
            for lbl, val in [
                ("live_mode", live_mode),
                ("playing", playing),
                ("speed", f"{speed:.3f}"),
                ("_manual", weather._manual),
                ("rain_intensity", f"{weather.rain_intensity:.3f}"),
                ("fog_intensity", f"{weather.fog_intensity:.3f}"),
                ("humidity", f"{weather.humidity:.3f}"),
                ("target_clouds", weather.target_clouds),
                ("live_weather_data", "None" if live_weather_data is None else "OK"),
                ("_last_error", live_weather.latest_error() or "none"),
                ("_fetching", str(live_weather._fetching)),
            ]:
                t = font_small.render(f"  {lbl}: {val}", True, (200, 210, 230))
                screen.blit(t, (10, y))
                y += 18

        calendar.draw(screen)

        if show_help:
            draw_help(screen, font)

        if show_test:
            w_rain_slider.draw(screen)
            w_fog_slider.draw(screen)
            w_hum_slider.draw(screen)
            for i, (lbl, val) in enumerate([("Rain", weather.rain_intensity), ("Fog", weather.fog_intensity), ("Hum", weather.humidity)]):
                t = font_small.render(f"{lbl}: {val:.2f}", True, (180, 200, 230))
                screen.blit(t, (185, 308 + i * 30))
            draw_test_menu(screen, font_small, weather, moon_phase, phase_name)
            weather.rain_intensity = w_rain_slider.value
            weather.fog_intensity = w_fog_slider.value
            weather.humidity = w_hum_slider.value
            weather._manual = True

        pygame.display.flip()

    pygame.quit()

except SystemExit:
    raise
except:
    write_crash(sys.exc_info())
    print(f"Fatal error. See {CRASH_LOG}")
    raise
