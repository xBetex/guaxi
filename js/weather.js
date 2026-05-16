// ============================================================
// js/weather.js — API fetch, weather categorisation, time/season logic
// ============================================================

function weatherCodeToLabel(code) {
  if (code === 0) return "Céu limpo";
  if (code === 1) return "Quase limpo";
  if (code === 2) return "Parc. nublado";
  if (code === 3) return "Nublado";
  if (code === 45 || code === 48) return "Neblina";
  if (code >= 51 && code <= 55) return "Chuvisco";
  if (code >= 61 && code <= 65) return "Chuva";
  if (code >= 71 && code <= 77) return "Neve";
  if (code >= 80 && code <= 82) return "Pancadas";
  if (code >= 95) return "Tempestade";
  return "Variável";
}

function weatherCodeToCategory(code) {
  if (code === 0) return "clear";
  if ([1, 2, 3, 45, 48].includes(code)) return "cloudy";
  if ((code >= 51 && code <= 67) || (code >= 80 && code <= 82)) return "rain";
  if (code >= 95 && code <= 99) return "storm";
  if (code >= 71 && code <= 77) return "snow";
  return "cloudy";
}

function getActiveTime() {
  if (!isAutoTime) return manualTimeVal;
  try {
    if (externalTimezone) {
      const fmt = new Intl.DateTimeFormat("en-US", {
        hour: "2-digit", minute: "2-digit", hour12: false, timeZone: externalTimezone,
      });
      const parts = fmt.formatToParts(new Date());
      let hh = 0, mm = 0;
      for (const p of parts) {
        if (p.type === "hour")   hh = parseInt(p.value, 10);
        if (p.type === "minute") mm = parseInt(p.value, 10);
      }
      if (!isNaN(hh) && !isNaN(mm)) return hh + mm / 60;
    }
  } catch (e) {}
  if (externalLocalDateParts)
    return externalLocalDateParts.hour + externalLocalDateParts.minute / 60;
  const now = new Date();
  return now.getHours() + now.getMinutes() / 60;
}

function getTimeTheme(h) {
  if (h >= 6  && h < 9)  return "manha";
  if (h >= 9  && h < 17) return "dia";
  if (h >= 17 && h < 18) return "tarde";
  return "noite";
}

function getActiveSeason(date) {
  if (!isAutoSeason) return manualSeasonVal;
  const month = date.getMonth() + 1;
  const northSeason = (() => {
    if ([12, 1, 2].includes(month)) return "summer";
    if ([3, 4, 5].includes(month)) return "spring";
    if ([6, 7, 8].includes(month)) return "winter";
    return "autumn";
  })();
  if (externalHemisphere === "south") {
    if (northSeason === "summer") return "winter";
    if (northSeason === "winter") return "summer";
    if (northSeason === "spring") return "autumn";
    if (northSeason === "autumn") return "spring";
  }
  return northSeason;
}

function getActiveWeather(h, season, date) {
  if (!isAutoWeather) return manualWeatherVal;
  const nowTs = Date.now();
  const hasLive = externalWeather && nowTs - externalWeatherFetchedAt < 5 * 60 * 1000;
  if (hasLive) return externalWeather;
  const hasLocation = externalLat !== null && externalLon !== null;
  const allowPrecip = hasLive || !hasLocation;
  const month = date.getMonth() + 1;
  const day   = date.getDate();
  const seed  = Math.sin(day * 23 + month * 7 + Math.floor(h) * 17) * 10000;
  const v = seed - Math.floor(seed);
  let rain = 0.45;
  if (season === "summer") rain = 0.75;
  if (season === "spring") rain = 0.55;
  if (season === "winter") rain = 0.6;
  if (h >= 12 && h < 18) {
    if (v < rain && allowPrecip) { if (season === "winter") return "snow"; return v < rain * 0.6 ? "rain" : "storm"; }
    return v < 0.75 ? "cloudy" : "clear";
  }
  if (h >= 6 && h < 12) {
    if (v < 0.35) { if (season === "winter" && v < 0.15) return "snow"; return "cloudy"; }
    return "clear";
  }
  if (v < 0.4) { if (allowPrecip && season === "winter" && v < 0.2) return "snow"; return "cloudy"; }
  return "clear";
}

let geocodeAbortController = null;
let weatherAbortController = null;

async function fetchWeatherForCity(city) {
  if (!city || !city.trim()) return;
  weatherInfo.temp = null; weatherInfo.feelsLike = null;
  weatherInfo.humidity = null; weatherInfo.windspeed = null;
  weatherInfo.condition = null; weatherInfo.sunrise = null; weatherInfo.sunset = null;
  externalWeather = null; externalWeatherFetchedAt = 0;
  isFetchingWeather = true;
  updateWeatherBar();
  try {
    if (geocodeAbortController) geocodeAbortController.abort();
    geocodeAbortController = new AbortController();
    const geoRes  = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(city)}`,
      { signal: geocodeAbortController.signal }
    );
    const geoJson = await geoRes.json();
    if (!geoJson || !geoJson[0]) { externalWeather = null; externalWeatherFetchedAt = 0; return; }
    const lat = parseFloat(geoJson[0].lat);
    const lon = parseFloat(geoJson[0].lon);
    externalLat = lat; externalLon = lon;
    externalHemisphere = lat < 0 ? "south" : "north";
    if (weatherAbortController) weatherAbortController.abort();
    weatherAbortController = new AbortController();
    const url =
      `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}` +
      `&current_weather=true&hourly=temperature_2m,apparent_temperature,relativehumidity_2m,windspeed_10m,weathercode` +
      `&daily=sunrise,sunset&timezone=auto&forecast_days=1`;
    const wres  = await fetch(url, { signal: weatherAbortController.signal });
    const wj    = await wres.json();
    let cat = null, temp = null, feels = null, hum = null, wind = null, cond = null;
    if (wj && wj.current_weather) {
      const c = wj.current_weather;
      cat  = weatherCodeToCategory(c.weathercode);
      temp = typeof c.temperature === "number" ? Math.round(c.temperature) : null;
      wind = typeof c.windspeed   === "number" ? Math.round(c.windspeed)   : null;
      cond = weatherCodeToLabel(c.weathercode);
      if (wj.hourly && Array.isArray(wj.hourly.time)) {
        const match = (c.time || "").substring(0, 13) + ":00";
        const idx   = wj.hourly.time.indexOf(match);
        if (idx >= 0) {
          if (wj.hourly.temperature_2m?.[idx]   !== undefined) temp  = Math.round(wj.hourly.temperature_2m[idx]);
          if (wj.hourly.apparent_temperature?.[idx] !== undefined) feels = Math.round(wj.hourly.apparent_temperature[idx]);
          if (wj.hourly.relativehumidity_2m?.[idx]  !== undefined) hum   = Math.round(wj.hourly.relativehumidity_2m[idx]);
        }
      }
      try {
        const m = (c.time || "").match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/);
        if (m) externalLocalDateParts = { year: +m[1], month: +m[2], day: +m[3], hour: +m[4], minute: +m[5] };
      } catch (_) {}
    } else if (wj && wj.hourly) {
      const hd = wj.hourly;
      const nowStr = new Date().toISOString().substring(0, 13) + ":00";
      let last = hd.time.indexOf(nowStr);
      if (last < 0) last = hd.time.length ? hd.time.length - 1 : 0;
      if (hd.weathercode?.[last]          !== undefined) cat   = weatherCodeToCategory(hd.weathercode[last]);
      if (hd.temperature_2m?.[last]       !== undefined) temp  = Math.round(hd.temperature_2m[last]);
      if (hd.apparent_temperature?.[last] !== undefined) feels = Math.round(hd.apparent_temperature[last]);
      if (hd.relativehumidity_2m?.[last]  !== undefined) hum   = Math.round(hd.relativehumidity_2m[last]);
      if (hd.windspeed_10m?.[last]        !== undefined) wind  = Math.round(hd.windspeed_10m[last]);
      try {
        const m = (hd.time?.[last] || "").match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/);
        if (m) externalLocalDateParts = { year: +m[1], month: +m[2], day: +m[3], hour: +m[4], minute: +m[5] };
      } catch (_) {}
    }
    try { externalTimezone = wj.timezone || null; } catch (_) {}
    if (cat) {
      externalWeather = cat; externalWeatherFetchedAt = Date.now();
      try {
        localStorage.setItem(EXTERNAL_STORAGE_KEY, JSON.stringify({
          externalWeather, externalWeatherFetchedAt, externalLat, externalLon,
          externalHemisphere, externalLocalDateParts, externalTimezone, currentCity,
        }));
      } catch (_) {}
    } else { externalWeather = null; externalWeatherFetchedAt = 0; }
    if (temp  !== null) weatherInfo.temp      = temp;
    if (feels !== null) weatherInfo.feelsLike  = feels;
    if (hum   !== null) weatherInfo.humidity   = hum;
    if (wind  !== null) weatherInfo.windspeed  = wind;
    if (cond)           weatherInfo.condition  = cond;
    if (wj?.daily) {
      weatherInfo.sunrise = (wj.daily.sunrise[0] || "").split("T")[1] || null;
      weatherInfo.sunset  = (wj.daily.sunset[0]  || "").split("T")[1] || null;
    }
    updateWeatherBar();
  } catch (e) {
    externalWeather = null; externalWeatherFetchedAt = 0;
    console.warn("fetchWeatherForCity failed:", e && e.message);
  } finally {
    isFetchingWeather = false;
    updateWeatherBar();
  }
}

function loadExternalFromStorage() {
  try {
    const raw = localStorage.getItem(EXTERNAL_STORAGE_KEY);
    if (!raw) return;
    const obj = JSON.parse(raw);
    if (!obj) return;
    if (obj.externalWeather          !== undefined) externalWeather          = obj.externalWeather;
    if (obj.externalWeatherFetchedAt !== undefined) externalWeatherFetchedAt = obj.externalWeatherFetchedAt;
    if (obj.externalLat              !== undefined) externalLat              = obj.externalLat;
    if (obj.externalLon              !== undefined) externalLon              = obj.externalLon;
    if (obj.externalHemisphere       !== undefined) externalHemisphere       = obj.externalHemisphere;
    if (obj.externalLocalDateParts   !== undefined) externalLocalDateParts   = obj.externalLocalDateParts;
    if (obj.externalTimezone         !== undefined) externalTimezone         = obj.externalTimezone;
    if (obj.currentCity)                            currentCity              = obj.currentCity;
  } catch (e) {}
}
