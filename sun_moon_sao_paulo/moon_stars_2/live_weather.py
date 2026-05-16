"""
live_weather.py — Fetches real weather for a city and maps it to simulation params.

Uses wttr.in (no API key). Threaded fetch to avoid freezing.
Smoothly interpolates all weather transitions for cinematic feel.
"""

import json
import ssl
import threading
import time
import urllib.parse
import urllib.request
import urllib.error

_REFRESH_INTERVAL = 600
_SSL_CTX = ssl._create_unverified_context()
_RAIN_WORDS = {"rain", "drizzle", "shower", "storm", "thunder", "squall", "downpour"}
_FOG_WORDS = {"fog", "mist", "haze"}
_CLEAR_WORDS = {"clear", "sunny"}
_SNOW_WORDS = {"snow", "sleet", "blizzard"}

_cache: dict[str, dict] = {}
_last_error: str | None = None
_fetching: set[str] = set()


def _fetch(city: str) -> dict | None:
    # use just the city name before comma, spaces → +, URL-encode accents
    raw_slug = city.split(",")[0].strip().replace(" ", "+")
    city_slug = urllib.parse.quote(raw_slug, safe="+")
    url = f"https://wttr.in/{city_slug}?format=j1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10, context=_SSL_CTX) as resp:
            body = resp.read().decode("utf-8")
            # wttr.in returns HTML on bad city — check first char is '{'
            if not body.lstrip().startswith("{"):
                return None
            return json.loads(body)
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, OSError, UnicodeEncodeError):
        return None


def _parse(raw: dict) -> dict:
    cc = raw.get("current_condition", [{}])[0]

    desc = cc.get("weatherDesc", [{}])[0].get("value", "")
    desc_lower = desc.lower()

    temp_C = float(cc.get("temp_C", 25))
    humidity = float(cc.get("humidity", 50)) / 100.0
    cloud_cover = float(cc.get("cloudcover", 0)) / 100.0
    precip = float(cc.get("precipMM", 0))
    visibility_km = float(cc.get("visibility", 10))
    wind_speed = float(cc.get("windspeedKmph", 0))
    wind_dir = cc.get("winddir16Point", "N")

    is_day = str(cc.get("isdaytime", "yes")).lower() in ("yes", "1", "true")

    try:
        obs_hour = int(cc.get("observation_time", "00:00").split(":")[0])
    except (ValueError, IndexError):
        obs_hour = 0

    is_rain = any(w in desc_lower for w in _RAIN_WORDS)
    is_snow = any(w in desc_lower for w in _SNOW_WORDS)
    is_fog = any(w in desc_lower for w in _FOG_WORDS)
    is_clear = any(w in desc_lower for w in _CLEAR_WORDS)

    rain_intensity = min(1.0, precip / 10.0)
    if is_rain and rain_intensity < 0.2:
        rain_intensity = 0.2
    elif is_clear:
        rain_intensity = 0.0

    fog_intensity = max(0.0, min(1.0, 1.0 - visibility_km / 20.0))
    if is_fog and fog_intensity < 0.3:
        fog_intensity = 0.3
    elif is_clear:
        fog_intensity = 0.0

    return {
        "temp_C": temp_C,
        "humidity": min(1.0, max(0.0, humidity)),
        "cloud_cover": min(1.0, max(0.0, cloud_cover)),
        "rain_intensity": min(1.0, max(0.0, rain_intensity)),
        "fog_intensity": min(1.0, max(0.0, fog_intensity)),
        "is_snow": is_snow,
        "desc": desc,
        "wind_speed": wind_speed,
        "wind_dir": wind_dir,
        "obs_hour": obs_hour,
        "is_day": is_day,
        "visibility_km": visibility_km,
        "localObsDateTime": cc.get("localObsDateTime", ""),
        "observation_time": cc.get("observation_time", ""),
    }


def _do_fetch(city: str):
    try:
        raw = _fetch(city)
        now = time.time()
        if raw is not None:
            parsed = _parse(raw)
            _cache[city] = {"time": now, "data": parsed}
            global _last_error
            _last_error = None
        else:
            _last_error = f"Could not find weather for {city}"
    except Exception:
        pass  # daemon thread must never throw during interp shutdown
    finally:
        _fetching.discard(city)


def get_weather(city: str, force_refresh=False) -> dict | None:
    now = time.time()
    entry = _cache.get(city)

    if entry is not None and not force_refresh and now - entry["time"] < _REFRESH_INTERVAL:
        return entry["data"]

    if city not in _fetching:
        _fetching.add(city)
        t = threading.Thread(target=_do_fetch, args=(city,), daemon=True)
        t.start()

    return entry["data"] if entry else None


def apply_live_weather(weather_system, data: dict):
    weather_system.humidity = data["humidity"]
    weather_system.rain_intensity = data["rain_intensity"]
    weather_system.fog_intensity = data["fog_intensity"]
    weather_system._is_winter = data["is_snow"]
    weather_system._manual = True

    cloud_factor = data["cloud_cover"] ** 1.4
    weather_system.target_clouds = max(0, int(cloud_factor * 18))

    # wind speed → cloud drift speed (km/h → px/s)
    wind_px = data["wind_speed"] * 1.5
    for c in weather_system.clouds:
        c.base_speed = wind_px
    weather_system._wind_speed = data["wind_speed"]

    if data["rain_intensity"] <= 0:
        weather_system.rain_drops.clear()
    elif data["rain_intensity"] > 0.5:
        weather_system._flash = min(1.0, weather_system._flash + 0.05)


def format_weather(data: dict | None, city: str="", font=None) -> list[tuple[str, object, tuple[int, int, int]]]:
    if data is None:
        if city and city in _fetching:
            return [("Fetching weather for " + city + "…", font, (140, 170, 210))]
        err = _last_error or "No weather data"
        return [(err, font, (180, 120, 120))]
    colour = (170, 210, 255)
    return [
        (f"Live: {data['temp_C']:.0f}°C  {data['desc']}  {data['humidity']*100:.0f}%RH", font, colour),
        (f"Clouds {data['cloud_cover']*100:.0f}%  Wind {data['wind_speed']:.0f} km/h {data['wind_dir']}  Vis {data['visibility_km']:.0f}km", font, colour),
        (f"Rain {data['rain_intensity']*100:.0f}%  Fog {data['fog_intensity']*100:.0f}%", font, colour),
    ]


def latest_error() -> str | None:
    return _last_error
