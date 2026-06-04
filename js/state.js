// ============================================================
// js/state.js — Global mutable state
// ============================================================

let currentCity = "Julio de Castilhos";
let isAutoTime = true;
let manualTimeVal = 12;

let isAutoSeason = true;
let manualSeasonVal = "summer";

let isAutoWeather = true;
let manualWeatherVal = "clear";

let tree1Pct = 15, tree1YOff = 0;
let tree2Pct = 80, tree2YOff = 0;
let bonfirePct = 65, bonfireYOff = 0;

let centerTreeYOffset = parseInt(localStorage.getItem("centerTreeYOffset")) || 160;
let sheetBottomNudgeValNum = parseInt(localStorage.getItem("sheetBottomNudge")) || 0;

// raccoon runtime state
let raccoonState = "idle";
let raccoonScale = 1;
let raccoonX = window.innerWidth / 2;
let randomHoleTime = Date.now() + Math.random() * 30000;
let externalWeather = null;
let externalWeatherFetchedAt = 0;
let lightningFlash = 0;
let raccoon = { bounceOffset: 0, flip: false, frame: 0 };
let centerTreeUsingSheetTop = false;

// weather fetch state
let isFetchingWeather = false;
let lastWeatherSync = null; // HH:MM of last successful weather fetch
function updateWeatherSyncTime() {
  lastWeatherSync = new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

let _cityFetchDebounce = null;
let externalLat = null;
let externalLon = null;
let externalHemisphere = null; // 'north' or 'south'
let externalLocalDateParts = null; // { year, month, day, hour, minute }
let externalTimezone = null;
const EXTERNAL_STORAGE_KEY = "guaxinim_external";

// raccoon free roaming
let raccoonWanderTargetX = -1;
let raccoonWanderTimer = 0;
let raccoonSizeMultiplier = 1.0; // user-adjustable for OBS/streaming

// detailed weather state
let weatherInfo = {
  temp: null,
  feelsLike: null,
  humidity: null,
  windspeed: null,
  condition: null,
  sunrise: null,
  sunset: null,
};

// moon phase from API
let moonData = { phase: null, illumination: null, emoji: null };
let moonFetchedAt = 0;
