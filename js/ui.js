// ============================================================
// js/ui.js — UI references, event listeners, save/load settings,
//            weather bar update, time display
// ============================================================

// ─── Canvas ──────────────────────────────────────────────────
const canvas = document.getElementById("gameCanvas");
const ctx    = canvas.getContext("2d", { alpha: false });

// ─── UI element references ────────────────────────────────────
const uiToggle  = document.getElementById("ui-toggle");
const uiPanel   = document.getElementById("ui-panel");
const cityInput = document.getElementById("city-input");

const overrideTime  = document.getElementById("override-time");
const timeSlider    = document.getElementById("time-slider");
const timeDisplay   = document.getElementById("time-display");

const overrideSeason = document.getElementById("override-season");
const seasonSelect   = document.getElementById("season-select");

const overrideWeather = document.getElementById("override-weather");
const weatherSelect   = document.getElementById("weather-select");

const tree1Slider  = document.getElementById("tree1-x");
const tree1YSlider = document.getElementById("tree1-y");
const tree1XValEl  = document.getElementById("tree1-x-val");
const tree1YValEl  = document.getElementById("tree1-y-val");

const tree2Slider  = document.getElementById("tree2-x");
const tree2YSlider = document.getElementById("tree2-y");
const tree2XValEl  = document.getElementById("tree2-x-val");
const tree2YValEl  = document.getElementById("tree2-y-val");

const bonfireSlider  = document.getElementById("bonfire-x");
const bonfireYSlider = document.getElementById("bonfire-y");
const bonfireXValEl  = document.getElementById("bonfire-x-val");
const bonfireYValEl  = document.getElementById("bonfire-y-val");

const centerTreeYSlider  = document.getElementById("center-tree-y");
const centerTreeYValDisp = document.getElementById("center-tree-y-val");
const saveCenterTreeBtn  = document.getElementById("save-center-tree");

const sheetBottomNudgeSlider  = document.getElementById("sheet-bottom-nudge");
const sheetBottomNudgeValDisp = document.getElementById("sheet-bottom-nudge-val");
const saveSheetBottomBtn      = document.getElementById("save-sheet-bottom");

const raccoonScaleSlider = document.getElementById("raccoon-scale-input");
const raccoonScaleValEl  = document.getElementById("raccoon-scale-val");
const saveAllBtn         = document.getElementById("save-all-btn");

const raccoonImageInput = document.getElementById("raccoon-image-input");
const bonfireImageInput = document.getElementById("bonfire-image-input");
const treeInputs        = document.querySelectorAll(".tree-input");

// ─── Event listeners ─────────────────────────────────────────
if (uiToggle) uiToggle.addEventListener("click", () => uiPanel.classList.toggle("open"));

if (overrideTime)
  overrideTime.addEventListener("change", (e) => {
    isAutoTime = !e.target.checked;
    timeSlider.classList.toggle("hidden", isAutoTime);
    if (isAutoTime) {
      if (currentCity && currentCity.trim()) { fetchMoonPhase(); fetchWeatherForCity(currentCity.trim()); }
      updateTimeDisplay(getActiveTime());
    }
  });
if (timeSlider) timeSlider.addEventListener("input", (e) => { manualTimeVal = parseFloat(e.target.value); });

if (overrideSeason)
  overrideSeason.addEventListener("change", (e) => {
    isAutoSeason = !e.target.checked;
    seasonSelect.classList.toggle("hidden", isAutoSeason);
  });
if (seasonSelect) seasonSelect.addEventListener("change", (e) => { manualSeasonVal = e.target.value; });

if (overrideWeather)
  overrideWeather.addEventListener("change", (e) => {
    isAutoWeather = !e.target.checked;
    weatherSelect.classList.toggle("hidden", isAutoWeather);
    if (isAutoWeather) { fetchMoonPhase(); fetchWeatherForCity(currentCity); }
  });
if (weatherSelect) weatherSelect.addEventListener("change", (e) => { manualWeatherVal = e.target.value; });

// Position sliders X
if (tree1Slider)   tree1Slider.addEventListener("input",   (e) => { tree1Pct  = parseFloat(e.target.value); if (tree1XValEl)  tree1XValEl.innerText  = tree1Pct.toFixed(0)  + "%"; });
if (tree2Slider)   tree2Slider.addEventListener("input",   (e) => { tree2Pct  = parseFloat(e.target.value); if (tree2XValEl)  tree2XValEl.innerText  = tree2Pct.toFixed(0)  + "%"; });
if (bonfireSlider) bonfireSlider.addEventListener("input", (e) => { bonfirePct = parseFloat(e.target.value); if (bonfireXValEl) bonfireXValEl.innerText = bonfirePct.toFixed(0) + "%"; });

// Position sliders Y
if (tree1YSlider)   tree1YSlider.addEventListener("input",   (e) => { tree1YOff  = parseInt(e.target.value); if (tree1YValEl)  tree1YValEl.innerText  = tree1YOff  + "px"; });
if (tree2YSlider)   tree2YSlider.addEventListener("input",   (e) => { tree2YOff  = parseInt(e.target.value); if (tree2YValEl)  tree2YValEl.innerText  = tree2YOff  + "px"; });
if (bonfireYSlider) bonfireYSlider.addEventListener("input", (e) => { bonfireYOff = parseInt(e.target.value); if (bonfireYValEl) bonfireYValEl.innerText = bonfireYOff + "px"; });

if (centerTreeYSlider) {
  centerTreeYSlider.value = centerTreeYOffset;
  if (centerTreeYValDisp) centerTreeYValDisp.innerText = centerTreeYOffset + "px";
  centerTreeYSlider.addEventListener("input", (e) => {
    centerTreeYOffset = parseInt(e.target.value);
    if (centerTreeYValDisp) centerTreeYValDisp.innerText = centerTreeYOffset + "px";
  });
}
if (sheetBottomNudgeSlider) {
  sheetBottomNudgeSlider.value = sheetBottomNudgeValNum;
  if (sheetBottomNudgeValDisp) sheetBottomNudgeValDisp.innerText = sheetBottomNudgeValNum + "px";
  sheetBottomNudgeSlider.addEventListener("input", (e) => {
    sheetBottomNudgeValNum = parseInt(e.target.value);
    if (sheetBottomNudgeValDisp) sheetBottomNudgeValDisp.innerText = sheetBottomNudgeValNum + "px";
  });
}
if (raccoonScaleSlider) {
  raccoonScaleSlider.value = raccoonSizeMultiplier;
  if (raccoonScaleValEl) raccoonScaleValEl.innerText = raccoonSizeMultiplier.toFixed(2) + "×";
  raccoonScaleSlider.addEventListener("input", (e) => {
    raccoonSizeMultiplier = parseFloat(e.target.value);
    if (raccoonScaleValEl) raccoonScaleValEl.innerText = raccoonSizeMultiplier.toFixed(2) + "×";
  });
}

// ─── Save / Load All Settings ─────────────────────────────────
function saveAllSettings() {
  localStorage.setItem("guaxinim_all", JSON.stringify({
    tree1Pct, tree1YOff, tree2Pct, tree2YOff,
    bonfirePct, bonfireYOff, centerTreeYOffset,
    sheetBottomNudgeValNum, raccoonSizeMultiplier,
  }));
}

function loadAllSettings() {
  try {
    const raw = localStorage.getItem("guaxinim_all");
    if (!raw) return;
    const s = JSON.parse(raw);
    const apply = (val, slider, disp, fmt) => { if (slider) slider.value = val; if (disp) disp.innerText = fmt(val); };
    if (s.tree1Pct           !== undefined) { tree1Pct           = s.tree1Pct;           apply(tree1Pct,           tree1Slider,           tree1XValEl,           (v) => Math.round(v) + "%"); }
    if (s.tree1YOff          !== undefined) { tree1YOff          = s.tree1YOff;           apply(tree1YOff,          tree1YSlider,          tree1YValEl,           (v) => v + "px"); }
    if (s.tree2Pct           !== undefined) { tree2Pct           = s.tree2Pct;           apply(tree2Pct,           tree2Slider,           tree2XValEl,           (v) => Math.round(v) + "%"); }
    if (s.tree2YOff          !== undefined) { tree2YOff          = s.tree2YOff;           apply(tree2YOff,          tree2YSlider,          tree2YValEl,           (v) => v + "px"); }
    if (s.bonfirePct         !== undefined) { bonfirePct         = s.bonfirePct;          apply(bonfirePct,         bonfireSlider,         bonfireXValEl,         (v) => Math.round(v) + "%"); }
    if (s.bonfireYOff        !== undefined) { bonfireYOff        = s.bonfireYOff;          apply(bonfireYOff,        bonfireYSlider,        bonfireYValEl,         (v) => v + "px"); }
    if (s.centerTreeYOffset  !== undefined) { centerTreeYOffset  = s.centerTreeYOffset;   apply(centerTreeYOffset,  centerTreeYSlider,     centerTreeYValDisp,    (v) => v + "px"); }
    if (s.sheetBottomNudgeValNum !== undefined) { sheetBottomNudgeValNum = s.sheetBottomNudgeValNum; apply(sheetBottomNudgeValNum, sheetBottomNudgeSlider, sheetBottomNudgeValDisp, (v) => v + "px"); }
    if (s.raccoonSizeMultiplier  !== undefined) { raccoonSizeMultiplier  = s.raccoonSizeMultiplier;  apply(raccoonSizeMultiplier,  raccoonScaleSlider,    raccoonScaleValEl,      (v) => v.toFixed(2) + "×"); }
  } catch (e) {}
}

if (saveAllBtn)
  saveAllBtn.addEventListener("click", () => {
    saveAllSettings();
    saveAllBtn.innerText = "✅ Salvo!";
    setTimeout(() => { saveAllBtn.innerText = "💾 Salvar Tudo"; }, 2000);
  });

// File inputs
if (raccoonImageInput)
  raccoonImageInput.addEventListener("change", (e) => {
    if (!e.target.files[0]) return;
    const reader = new FileReader();
    reader.onload = (evt) => { raccoonImg.src = evt.target.result; };
    reader.readAsDataURL(e.target.files[0]);
  });

if (bonfireImageInput)
  bonfireImageInput.addEventListener("change", (e) => {
    if (!e.target.files[0]) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      bonfireImgLoaded = false;
      bonfireImg.src = evt.target.result;
      bonfireImg.onload = () => { bonfireImgLoaded = true; };
    };
    reader.readAsDataURL(e.target.files[0]);
  });

treeInputs.forEach((input) => {
  input.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const season = input.dataset.season;
    const type   = input.dataset.type;
    const btn    = document.getElementById(`${season}-${type}-btn`);
    const reader = new FileReader();
    reader.onload = (evt) => {
      const img = new Image();
      img.src = evt.target.result;
      img.onload = () => {
        if (!treeImgs[season]) treeImgs[season] = {};
        treeImgs[season][type] = img;
        getBottomYFromRegion(img, 0, 0, img.naturalWidth, img.naturalHeight, _bottomCacheImg, img.src);
        if (btn) { btn.classList.add("loaded"); btn.innerText = "OK"; }
      };
    };
    reader.readAsDataURL(file);
  });
});

// City input
if (cityInput) {
  cityInput.addEventListener("input", (e) => {
    currentCity = e.target.value;
    if (isAutoWeather) {
      if (_cityFetchDebounce) clearTimeout(_cityFetchDebounce);
      _cityFetchDebounce = setTimeout(() => {
        const val = currentCity ? currentCity.trim() : "";
        if (val) { fetchMoonPhase(); fetchWeatherForCity(val); }
      }, 700);
    }
  });
}

const cityUpdateBtn = document.getElementById("city-update-btn");
if (cityUpdateBtn)
  cityUpdateBtn.addEventListener("click", () => {
    currentCity = cityInput ? cityInput.value.trim() : currentCity;
    if (!currentCity) return;
    cityUpdateBtn.innerText = "⏳";
    cityUpdateBtn.disabled = true;
    updateWeatherBar();
    fetchMoonPhase();
    fetchWeatherForCity(currentCity).then(() => { updateWeatherSyncTime(); }).finally(() => {
      cityUpdateBtn.innerText = "🔍";
      cityUpdateBtn.disabled = false;
    });
  });

// ─── Time display & weather bar ───────────────────────────────
function updateTimeDisplay(h) {
  if (!timeDisplay) return;
  const hours   = Math.floor(h);
  const minutes = Math.floor((h - hours) * 60);
  const str = `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
  timeDisplay.innerText = str;
  const el = document.getElementById("wb-time");
  if (el) el.innerText = str;
}

function updateWeatherBar() {
  const set = (id, val) => { const e = document.getElementById(id); if (e) e.innerText = val; };
  set("wb-city",    currentCity);
  set("wb-temp",    weatherInfo.temp      !== null ? weatherInfo.temp      + "°C" : "--°C");
  set("wb-feels",   weatherInfo.feelsLike !== null ? weatherInfo.feelsLike + "°C" : "--°C");
  set("wb-hum",     weatherInfo.humidity  !== null ? weatherInfo.humidity  + "%"  : "--%");
  set("wb-wind",    weatherInfo.windspeed !== null ? weatherInfo.windspeed + " km/h" : "-- km/h");
  set("wb-cond",    weatherInfo.condition || "--");
  set("wb-sunrise", weatherInfo.sunrise   || "--:--");
  set("wb-sunset",  weatherInfo.sunset    || "--:--");

  // Moon phase label in weather bar
  const mp = getMoonPhase();
  const mn = mp < 0.03 || mp > 0.97 ? "Lua Nova"
      : mp < 0.24 ? "Crescente" : mp < 0.27 ? "Quarto Crescente"
      : mp < 0.49 ? "Gibosa Crescente" : mp < 0.51 ? "Lua Cheia"
      : mp < 0.74 ? "Gibosa Minguante" : mp < 0.77 ? "Quarto Minguante" : "Minguante";
  const mi = (1 - Math.cos(mp * Math.PI * 2)) / 2;
  const me = mi < 0.03 ? "🌑" : mi > 0.97 ? "🌕"
      : mi < 0.25 ? (mp < 0.5 ? "🌒" : "🌘") : mi < 0.27 ? (mp < 0.5 ? "🌓" : "🌗")
      : mi < 0.49 ? (mp < 0.5 ? "🌔" : "🌖") : mi < 0.51 ? "🌕"
      : mi < 0.74 ? (mp < 0.5 ? "🌔" : "🌖") : mi < 0.77 ? (mp < 0.5 ? "🌓" : "🌗")
      : (mp < 0.5 ? "🌒" : "🌘");
  set("wb-moon", `${me} ${mn}`);

  // Sync badge
  try {
    const row = document.getElementById("wb-city-row");
    if (row) {
      const existing = document.getElementById("wb-source-badge");
      if (existing) existing.remove();
      const badge = document.createElement("span");
      badge.id = "wb-source-badge";
      badge.style.cssText = "margin-left:8px;font-size:11px;opacity:0.7;";
      if (isFetchingWeather) {
        badge.innerText = "(sincronizando...)"; badge.style.color = "#f1c40f";
      } else if (externalWeather && (Date.now() - externalWeatherFetchedAt < 30 * 60 * 1000)) {
        badge.innerText = `(sincronizado \u2022 ${lastWeatherSync || "--:--"})`; badge.style.color = "#2ecc71";
      } else {
        badge.innerText = "(modo simula\u00e7\u00e3o)"; badge.style.color = "#a29bfe";
      }
      try { const t = document.getElementById("wb-tz"); if (t) t.remove(); } catch (_) {}
      if (externalTimezone) {
        const tz = document.createElement("span");
        tz.id = "wb-tz"; tz.style.cssText = "margin-left:6px;font-size:11px;opacity:0.6;";
        tz.innerText = externalTimezone;
        row.appendChild(tz);
      }
      row.appendChild(badge);
    }
  } catch (e) {}
}

function drawWeatherText() { /* replaced by HTML bar */ }
