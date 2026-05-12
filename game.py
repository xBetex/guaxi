import pygame
import sys
import math
import random
import requests
import json
from datetime import datetime

# Local imports
from config import *
from sprites import *

class RaccoonGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Guaxinim Tempo Real")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # UI State
        self.ui_panel_open = False
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Controls
        self.auto_time = True
        self.manual_time = 12.0
        self.auto_season = True
        self.manual_season = 'summer'
        self.auto_weather = True
        self.manual_weather = 'clear'
        
        # Positions
        self.tree1_pct = 15
        self.tree2_pct = 80
        self.bonfire_pct = 65
        self.center_tree_y_offset = 160
        
        # Weather data
        self.external_weather = None
        self.external_weather_fetched_at = 0
        self.current_city = "São Paulo"
        self.city_input = "São Paulo"
        self.city_input_active = False
        
        # Raccoon state
        self.raccoon_x = SCREEN_WIDTH / 2
        self.raccoon_flip = False
        self.raccoon_scale = 1
        self.raccoon_bounce = 0
        self.raccoon_state = 'idle'
        self.raccoon_frame = 0
        self.random_hole_time = pygame.time.get_ticks() + random.randint(10000, 40000)
        
        # Particle effects
        self.lightning_flash = 0
        self.fireflies = []
        self.stars = []
        self.clouds = []
        self.snowflakes = []
        self.shooting_stars = []
        self.grass_blades = []
        
        self.raccoon_img = None
        self.tree_imgs = {}
        self.load_assets()
        self.init_effects()
        self.fetch_weather_for_city(self.current_city)
        
    def load_assets(self):
        """Create placeholder raccoon or load from file"""
        self.raccoon_img = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.ellipse(self.raccoon_img, (100, 100, 100), (15, 30, 70, 60))
        pygame.draw.ellipse(self.raccoon_img, (120, 120, 120), (25, 10, 50, 45))
        pygame.draw.circle(self.raccoon_img, (0, 0, 0), (40, 30), 5)
        pygame.draw.circle(self.raccoon_img, (0, 0, 0), (60, 30), 5)
        
        for season in ['spring', 'summer', 'autumn', 'winter']:
            self.tree_imgs[season] = None
            path = f'assets/{season}.png' if season != 'autumn' else 'assets/autum.png'
            try:
                self.tree_imgs[season] = pygame.image.load(path).convert_alpha()
            except:
                pass
    
    def init_effects(self):
        self.grass_blades = [{'x': random.random() * SCREEN_WIDTH, 'height': random.randint(5, 20), 'width': random.randint(2, 6), 'is_flower': random.random() > 0.95} for _ in range(300)]
        self.fireflies = [{'x': random.random() * SCREEN_WIDTH, 'y': random.random() * SCREEN_HEIGHT * 0.3 + SCREEN_HEIGHT * 0.6, 'phase': random.random() * math.pi * 2, 'speed_x': (random.random() - 0.5) * 0.8, 'speed_y': (random.random() - 0.5) * 0.5} for _ in range(25)]
        self.stars = [{'x': random.random(), 'y': random.random(), 'speed': random.random() * 0.05, 'twinkle': random.random() * math.pi * 2} for _ in range(150)]
        self.clouds = [{'x': random.randint(0, 100), 'y': random.randint(10, 40), 'speed': random.uniform(0.2, 0.8), 'scale': random.randint(4, 7)} for _ in range(4)]
        self.snowflakes = [{'x': random.random() * SCREEN_WIDTH, 'y': random.random() * SCREEN_HEIGHT, 'speed_y': random.random() + 0.5, 'speed_x': (random.random() - 0.5) * 0.5, 'size': random.random() * 3 + 1} for _ in range(200)]

    def fetch_weather_for_city(self, city):
        if not city: return
        try:
            geo_res = requests.get(f"https://nominatim.openstreetmap.org/search?format=json&limit=1&q={city}", headers={'User-Agent': 'RaccoonGame/1.0'}, timeout=3).json()
            if geo_res:
                w_res = requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={geo_res[0]['lat']}&longitude={geo_res[0]['lon']}&current_weather=true", timeout=3).json()
                if 'current_weather' in w_res:
                    code = w_res['current_weather']['weathercode']
                    self.external_weather = self.weather_code_to_category(code)
                    self.external_weather_fetched_at = pygame.time.get_ticks()
        except: pass
    
    def weather_code_to_category(self, code):
        if code == 0: return 'clear'
        if code in [1, 2, 3, 45, 48]: return 'cloudy'
        if (51 <= code <= 67) or (80 <= code <= 82): return 'rain'
        if 95 <= code <= 99: return 'storm'
        if 71 <= code <= 77: return 'snow'
        return 'cloudy'

    def get_active_time(self):
        if not self.auto_time: return self.manual_time
        now = datetime.now()
        return now.hour + now.minute / 60

    def draw_sprite(self, sprite, x, y, scale, season, flip=False):
        for row_idx, row in enumerate(sprite):
            for col_idx, char in enumerate(row):
                if char == 'T': continue
                draw_x = x + (col_idx * scale) if not flip else x + ((len(row) - 1 - col_idx) * scale)
                color = self.get_color(char, season)
                if color: pygame.draw.rect(self.screen, color, (draw_x, y + row_idx * scale, scale, scale))

    def get_color(self, char, season):
        if char in BASE_COLORS: return BASE_COLORS[char]
        sc = SEASON_COLORS[season]
        if char == 'M': return sc['leafM']
        if char == 'N': return sc['leafN']
        if char == 'E': return sc['leafE']
        return (0, 0, 0)

    def draw_mountain(self, center_x, ground_y, peak_height, base_width, color_shadow, color_light, has_snow):
        block_size = 16
        steps = max(1, int(peak_height / block_size))
        step_width = (base_width / 2) / steps
        for i in range(steps):
            current_y = ground_y - (i * block_size)
            current_half_width = (base_width / 2) - (i * step_width)
            lc = (223, 230, 233) if (has_snow and i > steps * 0.65) else color_shadow
            rc = (255, 255, 255) if (has_snow and i > steps * 0.65) else color_light
            pygame.draw.rect(self.screen, lc, (center_x - current_half_width, current_y - block_size, current_half_width, block_size))
            pygame.draw.rect(self.screen, rc, (center_x, current_y - block_size, current_half_width, block_size))

    def update(self, weather, hour):
        now = pygame.time.get_ticks()
        is_uncomfortable = weather in ['rain', 'storm', 'snow']
        is_randomly_hiding = self.random_hole_time < now < self.random_hole_time + 15000
        if self.random_hole_time + 15000 < now: self.random_hole_time = now + random.randint(10000, 40000)
        
        target_x = SCREEN_WIDTH / 2
        should_hide = is_uncomfortable or is_randomly_hiding
        
        speed = SCREEN_WIDTH * 0.003
        if abs(self.raccoon_x - target_x) > speed:
            self.raccoon_state = 'walking'
            if self.raccoon_x < target_x: self.raccoon_x += speed; self.raccoon_flip = False
            else: self.raccoon_x -= speed; self.raccoon_flip = True
            self.raccoon_scale = 1
        else:
            if should_hide: self.raccoon_state = 'hiding'; self.raccoon_scale = max(0, self.raccoon_scale - 0.05)
            else: self.raccoon_state = 'idle'; self.raccoon_scale = min(1, self.raccoon_scale + 0.05)
        
        self.raccoon_frame += 1
        if self.raccoon_state == 'walking':
            if self.raccoon_frame % 15 == 0: self.raccoon_bounce = -25 if self.raccoon_bounce == 0 else 0
        else:
            if self.raccoon_frame % 45 == 0: self.raccoon_bounce = -10 if self.raccoon_bounce == 0 else 0

        for cloud in self.clouds:
            cloud['x'] += cloud['speed']
            if cloud['x'] > 110: cloud['x'] = -20
        for fly in self.fireflies:
            fly['x'] += fly['speed_x']; fly['y'] += fly['speed_y']
            if fly['x'] < 0 or fly['x'] > SCREEN_WIDTH: fly['speed_x'] *= -1
            if fly['y'] < GROUND_Y - 50 or fly['y'] > SCREEN_HEIGHT: fly['speed_y'] *= -1
            fly['phase'] += 0.05
        for ss in self.shooting_stars[:]:
            ss['x'] += ss['speed']; ss['y'] += ss['speed']
            if ss['y'] > SCREEN_HEIGHT: self.shooting_stars.remove(ss)

    def draw(self, theme, season, weather, hour):
        self.screen.fill(theme['sky1'])
        # Simple sky gradient
        for i in range(0, SCREEN_HEIGHT, 4):
            t = i / SCREEN_HEIGHT
            c = theme['sky1'] if t < 0.5 else theme['sky2']
            pygame.draw.rect(self.screen, c, (0, i, SCREEN_WIDTH, 4))
        
        is_night = hour >= 18 or hour < 6
        if is_night:
            for s in self.stars:
                s['twinkle'] += s['speed']
                alpha = int((math.sin(s['twinkle']) + 1) * 127)
                pygame.draw.rect(self.screen, (255, 255, 255), (s['x'] * SCREEN_WIDTH, s['y'] * SCREEN_HEIGHT * 0.7, 4, 4))
        
        mtn_snow = season == 'winter' or weather == 'snow'
        self.draw_mountain(SCREEN_WIDTH * 0.25, GROUND_Y, SCREEN_HEIGHT * 0.45, SCREEN_WIDTH * 0.6, theme['mountain'], theme['mountainLight'], mtn_snow)
        self.draw_mountain(SCREEN_WIDTH * 0.75, GROUND_Y, SCREEN_HEIGHT * 0.35, SCREEN_WIDTH * 0.5, theme['mountain'], theme['mountainLight'], mtn_snow)
        
        pygame.draw.rect(self.screen, SEASON_COLORS[season]['grass2'], (0, GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT - GROUND_Y))
        for b in self.grass_blades:
            pygame.draw.rect(self.screen, SEASON_COLORS[season]['grass1'], (b['x'], GROUND_Y - b['height'], b['width'], b['height']))
        
        self.draw_sprite(TREE, self.tree1_pct * SCREEN_WIDTH / 100, GROUND_Y - 180, 8, season)
        self.draw_sprite(TREE, self.tree2_pct * SCREEN_WIDTH / 100, GROUND_Y - 180, 8, season)
        
        if self.raccoon_scale > 0:
            rx, ry = int(self.raccoon_x), GROUND_Y + self.raccoon_bounce
            self.screen.blit(pygame.transform.flip(pygame.transform.scale(self.raccoon_img, (int(100*self.raccoon_scale), int(100*self.raccoon_scale))), self.raccoon_flip, False), (rx-50, ry-80))

        # UI Overlay
        time_str = f"{int(hour):02d}:{int((hour % 1) * 60):02d}"
        self.screen.blit(self.font.render(time_str, True, (255, 255, 255)), (SCREEN_WIDTH // 2 - 40, 20))
        pygame.display.flip()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: self.running = False
            
            hour = self.get_active_time()
            season = self.auto_season and 'summer' or self.manual_season # Simplified
            weather = self.auto_weather and 'clear' or self.manual_weather
            theme = THEMES[hour >= 6 and hour < 9 and 'manha' or hour >= 9 and hour < 17 and 'dia' or hour >= 17 and hour < 18 and 'tarde' or 'noite']
            
            self.update(weather, hour)
            self.draw(theme, season, weather, hour)
            self.clock.tick(FPS)
        pygame.quit()

if __name__ == "__main__":
    RaccoonGame().run()