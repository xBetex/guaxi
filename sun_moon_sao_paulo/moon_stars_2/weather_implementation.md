# Full Weather Implementation

## Files

| File | Path |
|------|------|
| `weather.py` | `weather_backup.py` |
| `live_weather.py` | `live_weather_backup.py` |
| `main.py` integration | `main_backup.py` |
| `trees.py` weather hook | `trees.py` (lines 28, 85, 92-93) |

---

## 1. `weather.py` — WeatherSystem class (245 lines)

### Key architecture

- `WeatherSystem` owns all state: rain, fog, humidity, clouds, lightning, rainbow
- `update()` runs seasonal simulation or respects `_manual` flag
- `draw()` renders rain/snow, fog, haze
- `draw_clouds()` renders rainbow arc + cloud sprites

### Core attributes

```python
class WeatherSystem:
    def __init__(self):
        self.clouds = []           # list of Cloud sprites
        self.rain_intensity = 0    # 0–1
        self.fog_intensity = 0     # 0–1
        self.humidity = 0.5        # 0–1
        self.rain_drops = []       # list of rain particle dicts
        self.target_clouds = 3     # desired cloud count
        self._flash = 0            # lightning flash alpha
        self._rainbow = 0          # rainbow intensity
        self._manual = False       # if True, update() skips seasonal overrides
        self._wind_speed = 0       # from live weather, affects cloud drift
```

### `update()` — called every frame

```python
def update(self, season, hour, day, speed=1.0, dt=0.016, w=1280, h=720):
    self._is_winter = (season == "winter")

    if not self._manual:
        self.target_clouds = {"summer": 5, "autumn": 10, "winter": 12, "spring": 8}.get(season, 5)

    while len(self.clouds) < self.target_clouds:
        self.clouds.append(Cloud(w, h, self._wind_speed if self._wind_speed > 0 else None))

    if not self._manual:
        # Seasonal parameter simulation — sin/cos waves over day index
        if season == "summer":
            self.humidity = 0.5 + math.sin(day * 0.05) * 0.3
            self.rain_intensity = max(0, math.sin(day * 0.1) * 0.7) if self.humidity > 0.7 else 0
            self.fog_intensity = max(0, math.sin(day * 0.06) * 0.3)
        elif season == "autumn":
            self.humidity = 0.6 + math.sin(day * 0.07) * 0.3
            self.rain_intensity = max(0, math.sin(day * 0.15) * 0.8)
            self.fog_intensity = max(0, math.sin(day * 0.03) * 0.6)
        elif season == "winter":
            self.humidity = 0.7 + math.cos(day * 0.05) * 0.25
            self.rain_intensity = max(0, math.sin(day * 0.12) * 0.6)
            self.fog_intensity = 0.4 + math.sin(day * 0.04) * 0.4
        elif season == "spring":
            self.humidity = 0.6 + math.sin(day * 0.08) * 0.3
            self.rain_intensity = max(0, math.sin(day * 0.2) * 0.9)
            self.fog_intensity = max(0, math.sin(day * 0.05) * 0.5)

    # Time-of-day fog adjustment (always runs)
    if 5 <= hour < 8:
        self.fog_intensity *= (1 - (hour - 5) / 3)
    elif 19 <= hour < 22:
        self.fog_intensity *= ((hour - 19) / 3)

    # Cloud movement + wrap-around
    for c in self.clouds[:]:
        c.update(dt, speed, w)
        if c.x > w + c.surf.get_width():
            c.x = -c.surf.get_width()
            c.y = random.randint(10, int(h * 0.32))
            c.base_speed = self._wind_speed * 1.5 if self._wind_speed > 0 else random.uniform(15, 40)
        if len(self.clouds) > self.target_clouds:
            self.clouds.remove(c)

    # Rain drop management
    target = int(self.rain_intensity * 200)
    while len(self.rain_drops) < target:
        self.rain_drops.append({"x": random.uniform(0, w), "y": random.uniform(-50, 0), "speed": random.uniform(200, 400), "len": random.randint(4, 10)})
    while len(self.rain_drops) > target and self.rain_drops:
        self.rain_drops.pop()

    # Rainbow & lightning
    self._flash = max(0, self._flash - 0.02 * speed)
    if self.rain_intensity > 0.3:
        self._rainbow = 2.0
    else:
        self._rainbow = max(0, self._rainbow - 0.005 * speed)
    if self.rain_intensity > 0.6 and random.random() < 0.002 * speed:
        self._flash = 1.0

    # Rain drop physics
    for d in self.rain_drops[:]:
        if self._is_winter:
            d["y"] += d["speed"] * dt
            d.setdefault("_drift", random.uniform(0, 10))
            d["x"] += math.sin(d["y"] * 0.05 + d["_drift"]) * 0.3
        else:
            d["y"] += d["speed"] * dt
        if d["y"] > h + 20:
            d["y"] = random.uniform(-20, -5)
            d["x"] = random.uniform(0, w)
```

### `draw()` — rain, fog, haze rendering

```python
def draw(self, screen, w, h, hour=12):
    # Lightning flash overlay
    if self._flash > 0.01:
        flash = pygame.Surface((w, h), pygame.SRCALPHA)
        flash.fill((255, 255, 255, int(self._flash * 200)))
        screen.blit(flash, (0, 0))

    # Rain / Snow streaks
    if self.rain_intensity > 0.01:
        if self._is_winter:
            # Snow: white dots with drift
            snow_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            a = min(255, int(self.rain_intensity * 180))
            for d in self.rain_drops:
                px, py = int(d["x"]), int(d["y"])
                drift = math.sin(py * 0.05 + d.get("_drift", 0)) * 3
                if 0 <= py < h:
                    snow_surf.set_at((px + int(drift), py), (240, 248, 255, a))
            screen.blit(snow_surf, (0, 0))
        else:
            # Rain: blue vertical streaks
            rain_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            a = min(255, int(self.rain_intensity * 150))
            for d in self.rain_drops:
                for i in range(d["len"]):
                    y = int(d["y"] - i)
                    if 0 <= y < h:
                        rain_surf.set_at((int(d["x"]), y), (140, 165, 200, a))
            screen.blit(rain_surf, (0, 0))

    # Fog: procedural noise blended over the scene
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
                    fog.set_at((x + bs // 2, y + bs // 2), (c, c + 8, c + 20, min(180, fa)))
        fog = pygame.transform.smoothscale(fog, (w, h))
        screen.blit(fog, (0, 0))

        # Second fog layer: dense ground fog
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

    # Haze: subtle blue wash at high humidity
    if self.humidity > 0.8:
        haze = pygame.Surface((w, h), pygame.SRCALPHA)
        haze.fill((200, 210, 230, int((self.humidity - 0.8) * 25)))
        screen.blit(haze, (0, 0))
```

### `draw_clouds()` — rainbow + cloud sprites

```python
def draw_clouds(self, screen, w, h, hour=12, t=0):
    if self._rainbow > 0.1 and 8 <= hour <= 16:
        # Rainbow: concentric colored arcs with center punched out
        rb = pygame.Surface((w, h), pygame.SRCALPHA)
        cx, cy = w // 2, int(h * 0.48) + 60
        colors = [(255, 60, 60), (255, 140, 40), (245, 230, 60), (60, 200, 80), (50, 130, 250)]
        bw = max(6, int(h * 0.014))
        pulse = 0.85 + 0.15 * math.sin(t * 0.5)
        a = int(self._rainbow * 80 * pulse)
        for i, col in enumerate(colors):
            r = int(h * 0.44) - i * bw
            pygame.draw.circle(rb, (*col, a), (cx, cy), r)
        # Punch out center
        inner_r = max(1, int(h * 0.44) - len(colors) * bw)
        hole = pygame.Surface((w, h), pygame.SRCALPHA)
        hole.fill((255, 255, 255, 255))
        pygame.draw.circle(hole, (0, 0, 0, 0), (cx, cy), inner_r)
        rb.blit(hole, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        # Clip bottom half
        mask = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, cy))
        rb.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(rb, (0, 0))

    # Clouds
    for c in self.clouds:
        screen.blit(c.surf, (int(c.x), int(c.y)))
```

---

## 2. `live_weather.py` — Real-time API bridge (168 lines)

### Architecture

- Threaded fetch from `wttr.in` (free, no API key)
- Per-city cache with 600s refresh
- Interpolation-free: sets values directly when data arrives
- Background thread never blocks the game loop

### URL construction

```python
def _fetch(city: str) -> dict | None:
    raw_slug = city.split(",")[0].strip().replace(" ", "+")
    city_slug = urllib.parse.quote(raw_slug, safe="+")
    url = f"https://wttr.in/{city_slug}?format=j1"
    # Returns parsed JSON or None
```

### Data parsing — maps wttr.in fields to sim params

| API field | Maps to | Formula |
|-----------|---------|--------|
| `temp_C` | `data["temp_C"]` | direct |
| `humidity` | `data["humidity"]` | / 100 |
| `cloudcover` | `data["cloud_cover"]` | / 100 |
| `precipMM` | `data["rain_intensity"]` | `min(1.0, precip / 10.0)`; boosted to 0.2 if desc contains rain keywords |
| `visibility` | `data["fog_intensity"]` | `1.0 - vis/20`; boosted to 0.3 if desc contains fog keywords |
| `windspeedKmph` | `data["wind_speed"]` | direct; also `_wind_speed` on WeatherSystem |
| `weatherDesc` | `data["desc"]` | used for keyword matching |
| `is_snow` | `data["is_snow"]` | keyword match on desc |

### `apply_live_weather()` — pushes API data into simulation

```python
def apply_live_weather(weather_system, data: dict):
    weather_system.humidity = data["humidity"]
    weather_system.rain_intensity = data["rain_intensity"]
    weather_system.fog_intensity = data["fog_intensity"]
    weather_system._is_winter = data["is_snow"]
    weather_system._manual = True

    cloud_factor = data["cloud_cover"] ** 1.4
    weather_system.target_clouds = max(0, int(cloud_factor * 18))

    wind_px = data["wind_speed"] * 1.5
    for c in weather_system.clouds:
        c.base_speed = wind_px
    weather_system._wind_speed = data["wind_speed"]

    if data["rain_intensity"] <= 0:
        weather_system.rain_drops.clear()
    elif data["rain_intensity"] > 0.5:
        weather_system._flash = min(1.0, weather_system._flash + 0.05)
```

### `get_weather()` — cache-aware fetch (threaded)

```python
def get_weather(city: str, force_refresh=False) -> dict | None:
    entry = _cache.get(city)
    if entry is not None and not force_refresh and now - entry["time"] < _REFRESH_INTERVAL:
        return entry["data"]
    if city not in _fetching:
        _fetching.add(city)
        t = threading.Thread(target=_do_fetch, args=(city,), daemon=True)
        t.start()
    return entry["data"] if entry else None
```

---

## 3. `main.py` — Integration points

### Initialization

```python
import live_weather

live_button = Button(345, HEIGHT - 98, 50, 32, "Live")
weather = WeatherSystem()
live_mode = False
live_weather_data = None
w_rain_slider = Slider(20, 310, 160, 12, 0, 1.0, 0)
w_fog_slider = Slider(20, 340, 160, 12, 0, 1.0, 0)
w_hum_slider = Slider(20, 370, 160, 12, 0, 1.0, 0.5)
```

### L key / Live button toggle

```python
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
```

### Main loop — weather update + live integration

```python
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

# Hard rain kill — safety net for live mode
if live_mode and weather.rain_intensity > 0:
    weather.rain_intensity = 0
    weather.rain_drops.clear()
# Re-apply cloud count from live data after update()
if live_mode and live_weather_data:
    cf = live_weather_data["cloud_cover"] ** 1.4
    weather.target_clouds = max(0, int(cf * 18))
```

### Draw order

```python
weather.draw_clouds(screen, WIDTH, HEIGHT, hour, pygame.time.get_ticks() / 1000)
flock.draw(screen)
draw_landscape(screen, WIDTH, HEIGHT, season, hour, day, weather)
weather.draw(screen, WIDTH, HEIGHT, hour)
```

### HUD display

```python
info = live_weather.format_weather(live_weather_data, city_name, font_small)
lines.extend(info)
```

### F2 Debug overlay

```python
# Shows: live_mode, playing, speed, _manual, rain_intensity, fog_intensity,
#        humidity, target_clouds, live_weather_data, _last_error, _fetching
```

### Test sliders (F5)

```python
if show_test:
    w_rain_slider.draw(screen)
    w_fog_slider.draw(screen)
    w_hum_slider.draw(screen)
    weather.rain_intensity = w_rain_slider.value
    weather.fog_intensity = w_fog_slider.value
    weather.humidity = w_hum_slider.value
    weather._manual = True
```

---

## 4. `trees.py` — Weather hook

```python
# draw_forest_treeline (line 28):
weather_fog = weather.fog_intensity if weather else 0.0

# draw_foreground_trees (line 85):
weather_fog = weather.fog_intensity if weather else 0.0

# Both use weather_fog to adjust tree distance-fog for atmospheric perspective.
# When weather has no fog_intensity attribute, this crashes — see fix below.
```

### Fix for safe fallback when weather is removed

Replace both occurrences of:

```python
weather_fog = weather.fog_intensity if weather else 0.0
```

with:

```python
weather_fog = getattr(weather, 'fog_intensity', 0) if weather else 0.0
```

---

## To restore weather

```
copy main_backup.py main.py
copy weather_backup.py weather.py
copy live_weather_backup.py live_weather.py
```
