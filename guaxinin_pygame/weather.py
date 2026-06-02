import pygame
import random
import math

CLOUD_PIXELS = [
    "TTTTTTTTYYYYTTTTTTTT",
    "TTTTTTYYYYYYYYTTTTTT",
    "TTTTYYYYYYYYYYYYTTTT",
    "TTYYYYYYYYYYYYYYYYTT",
    "YYYYYYYYYYYYYYYYYYYY",
    "YYYYYYYYYYYYYYYYYYYY",
    "TYYYYYYYYYYYYYYYYYYT",
]
CLOUD_W = len(CLOUD_PIXELS[0])
CLOUD_H = len(CLOUD_PIXELS)
CLOUD_SPRITES = {}


def _make_cloud_surf(scale):
    key = scale
    if key in CLOUD_SPRITES:
        return CLOUD_SPRITES[key]
    pw = max(1, int(CLOUD_W * scale))
    ph = max(1, int(CLOUD_H * scale))
    small = pygame.Surface((CLOUD_W, CLOUD_H), pygame.SRCALPHA)
    for y, row in enumerate(CLOUD_PIXELS):
        for x, ch in enumerate(row):
            if ch == "Y":
                n = (x * 13 + y * 7) % 12
                v = 30 - n * 3
                small.set_at((x, y), (220 - v, 228 - v, 240 - v, 220))
            else:
                small.set_at((x, y), (0, 0, 0, 0))
    result = pygame.transform.scale(small, (pw, ph))
    CLOUD_SPRITES[key] = result
    return result


class Cloud:
    def __init__(self, w, h, base_speed=None):
        self.scale = random.uniform(5.0, 12.0)
        self.surf = _make_cloud_surf(self.scale)
        sw, sh = self.surf.get_size()
        self.x = random.randint(-sw, w + sw)
        self.y = random.randint(10, int(h * 0.32))
        self.base_speed = base_speed if base_speed is not None else random.uniform(15, 40)

    def update(self, dt, speed_mult, w):
        self.x += self.base_speed * speed_mult * dt


class WeatherSystem:
    def __init__(self):
        self.clouds = []
        self._flash = 0
        self._rainbow = 0
        self.moon_phase = 0.0
        self.rain_intensity = 0
        self.fog_intensity = 0
        self.humidity = 0.5
        self._is_winter = False
        self.rain_drops = []
        self.wind_speed = 0
        self._tz_applied = False
        self.cloud_cover = None

    def update(self, season, hour, day, speed=1.0, dt=0.016, w=1280, h=720):
        if self.cloud_cover is not None:
            target_clouds = int(self.cloud_cover * 35)
        else:
            target_clouds = {"summer": 5, "autumn": 10, "winter": 12, "spring": 8}.get(season, 5)

        while len(self.clouds) < target_clouds:
            self.clouds.append(Cloud(w, h))
        for c in self.clouds[:]:
            c.update(dt, speed, w)
            csw = c.surf.get_width()
            if c.x > w + csw:
                c.x = -csw
                c.y = random.randint(10, int(h * 0.32))
                c.base_speed = random.uniform(15, 40)
            if len(self.clouds) > target_clouds:
                self.clouds.remove(c)
        self._flash = max(0, self._flash - 0.02 * speed)
        self._rainbow = max(0, self._rainbow - 0.005 * speed)
        if self._rainbow <= 0 and self.rain_intensity > 0.3:
            self._rainbow = 2.0
        self.moon_phase = (day / 29.53058867) % 1.0

        # Maintain and move rain drops
        if self.rain_intensity > 0.01:
            target_drops = int(self.rain_intensity * (1000 if self._is_winter else 600))
            while len(self.rain_drops) < target_drops:
                self.rain_drops.append({
                    "x": random.randint(-w // 2, int(w * 1.5)),
                    "y": random.randint(-h, 0),
                    "len": random.randint(4, 12) if not self._is_winter else random.randint(1, 3),
                    "speed": random.uniform(700, 1100) if not self._is_winter else random.uniform(80, 180),
                    "_drift": random.uniform(0, 100)
                })
            for d in self.rain_drops:
                d["x"] += self.wind_speed * 12 * speed * dt
                d["y"] += d["speed"] * speed * dt
                if d["y"] > h:
                    d["y"] = random.randint(-200, -10)
                    d["x"] = random.randint(-w // 2, int(w * 1.5))
            if len(self.rain_drops) > target_drops:
                self.rain_drops = self.rain_drops[:target_drops]
        else:
            self.rain_drops.clear()

    def force_flash(self):
        self._flash = 1.0

    def force_rainbow(self):
        self._rainbow = 2.0

    def draw_clouds(self, screen, w, h, hour=12, t=0):
        if self._rainbow > 0.1 and 8 <= hour <= 16:
            rb = pygame.Surface((w, h), pygame.SRCALPHA)
            cx, cy = w // 2, int(h * 0.48) + 60
            colors = [(255, 60, 60), (255, 140, 40), (245, 230, 60), (60, 200, 80), (50, 130, 250)]
            bw = max(6, int(h * 0.014))
            pulse = 0.85 + 0.15 * math.sin(t * 0.5)
            a = int(self._rainbow * 80 * pulse)
            for i, col in enumerate(colors):
                r = int(h * 0.44) - i * bw
                pygame.draw.circle(rb, (*col, a), (cx, cy), r)
            inner_r = max(1, int(h * 0.44) - len(colors) * bw)
            hole = pygame.Surface((w, h), pygame.SRCALPHA)
            hole.fill((255, 255, 255, 255))
            pygame.draw.circle(hole, (0, 0, 0, 0), (cx, cy), inner_r)
            rb.blit(hole, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            mask = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, cy))
            rb.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(rb, (0, 0))

        if self.cloud_cover is not None and self.cloud_cover > 0.4:
            overcast = pygame.Surface((w, int(h * 0.8)), pygame.SRCALPHA)
            alpha_max = int((self.cloud_cover - 0.4) / 0.6 * 220)
            
            if hour < 5 or hour >= 19:
                color = (30, 35, 45)
            elif hour < 7 or hour >= 17:
                color = (120, 100, 110)
            else:
                color = (180, 190, 200)
                
            for y in range(0, int(h * 0.8), 8):
                a = int(alpha_max * (1 - (y / (h * 0.8)) ** 2))
                if a > 0:
                    pygame.draw.rect(overcast, (*color, a), (0, y, w, 8))
            screen.blit(overcast, (0, 0))

        for c in self.clouds:
            screen.blit(c.surf, (int(c.x), int(c.y)))

    def draw(self, screen, w, h, hour=12):
        if self._flash > 0.01:
            flash = pygame.Surface((w, h), pygame.SRCALPHA)
            flash.fill((255, 255, 255, int(self._flash * 200)))
            screen.blit(flash, (0, 0))

        # rain / snow
        if self.rain_intensity > 0.01:
            if self._is_winter:
                snow_surf = pygame.Surface((w, h), pygame.SRCALPHA)
                a = min(255, int(self.rain_intensity * 180))
                for d in self.rain_drops:
                    px, py = int(d["x"]), int(d["y"])
                    drift = math.sin(py * 0.05 + d.get("_drift", 0)) * 3
                    if 0 <= py < h:
                        snow_surf.set_at((px + int(drift), py), (240, 248, 255, a))
                screen.blit(snow_surf, (0, 0))
            else:
                rain_surf = pygame.Surface((w, h), pygame.SRCALPHA)
                a = min(255, int(self.rain_intensity * 150))
                for d in self.rain_drops:
                    for i in range(d["len"]):
                        y = int(d["y"] - i)
                        if 0 <= y < h:
                            rain_surf.set_at((int(d["x"]), y), (140, 165, 200, a))
                screen.blit(rain_surf, (0, 0))

        # fog
        if self.fog_intensity > 0.005:
            fog = pygame.Surface((w, h), pygame.SRCALPHA)
            bs = 20
            base_a = self.fog_intensity * 100
            for y in range(0, h, bs):
                ty = y / h
                vgrad = 0.3 + ty * 0.7
                for x in range(0, w, bs):
                    n = (math.sin(x * 0.003 + self.fog_intensity * 8) *
                         math.cos(y * 0.002 + self.fog_intensity * 5) *
                         math.sin((x + y) * 0.0015 + self.fog_intensity * 3))
                    fa = int(base_a * vgrad * (0.4 + n * 0.6))
                    if fa > 0:
                        c = 195 + int(n * 15)
                        fade = min(180, fa)
                        fog.set_at((x + bs // 2, y + bs // 2), (c, c + 8, c + 20, fade))
            fog = pygame.transform.smoothscale(fog, (w, h))
            screen.blit(fog, (0, 0))
            if self.fog_intensity > 0.3:
                fog2 = pygame.Surface((w, h), pygame.SRCALPHA)
                for y in range(0, h, bs * 2):
                    ty = y / h
                    fa2 = int(self.fog_intensity * 120 * ty * ty)
                    if fa2 > 0:
                        for x in range(0, w, bs * 2):
                            fog2.set_at((x + bs, y + bs), (200, 210, 225, min(100, fa2)))
                fog2 = pygame.transform.smoothscale(fog2, (w, h))
                screen.blit(fog2, (0, 0))
            if self.humidity > 0.8:
                haze = pygame.Surface((w, h), pygame.SRCALPHA)
                haze.fill((200, 210, 230, int((self.humidity - 0.8) * 25)))
                screen.blit(haze, (0, 0))


draw_weather_effects = WeatherSystem.draw
