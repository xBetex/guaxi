// ============================================================
// Guaxinim Tempo Real — Main Script
// ============================================================

// ─── STATE ──────────────────────────────────────────────────
let currentCity = "São Paulo";
let isAutoTime = true;
let manualTimeVal = 12;

let isAutoSeason = true;
let manualSeasonVal = "summer";

let isAutoWeather = true;
let manualWeatherVal = "clear";

let tree1Pct = 15,
  tree1YOff = 0;
let tree2Pct = 80,
  tree2YOff = 0;
let bonfirePct = 65,
  bonfireYOff = 0;

let centerTreeYOffset =
  parseInt(localStorage.getItem("centerTreeYOffset")) || 160;
let sheetBottomNudgeValNum =
  parseInt(localStorage.getItem("sheetBottomNudge")) || 0;

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
// persisted external info key
const EXTERNAL_STORAGE_KEY = 'guaxinim_external';

// Restore last-known external location/timezone/hemisphere from localStorage
function loadExternalFromStorage() {
  try {
    const raw = localStorage.getItem(EXTERNAL_STORAGE_KEY);
    if (!raw) return;
    const obj = JSON.parse(raw);
    if (!obj) return;
    if (obj.externalWeather !== undefined) externalWeather = obj.externalWeather;
    if (obj.externalWeatherFetchedAt !== undefined)
      externalWeatherFetchedAt = obj.externalWeatherFetchedAt;
    if (obj.externalLat !== undefined) externalLat = obj.externalLat;
    if (obj.externalLon !== undefined) externalLon = obj.externalLon;
    if (obj.externalHemisphere !== undefined)
      externalHemisphere = obj.externalHemisphere;
    if (obj.externalLocalDateParts !== undefined)
      externalLocalDateParts = obj.externalLocalDateParts;
    if (obj.externalTimezone !== undefined) externalTimezone = obj.externalTimezone;
    if (obj.currentCity) currentCity = obj.currentCity;
  } catch (e) {}
}

loadExternalFromStorage();
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

// ─── UI REFERENCES ───────────────────────────────────────────
const uiToggle = document.getElementById("ui-toggle");
const uiPanel = document.getElementById("ui-panel");
const cityInput = document.getElementById("city-input");

const overrideTime = document.getElementById("override-time");
const timeSlider = document.getElementById("time-slider");
const timeDisplay = document.getElementById("time-display");

const overrideSeason = document.getElementById("override-season");
const seasonSelect = document.getElementById("season-select");

const overrideWeather = document.getElementById("override-weather");
const weatherSelect = document.getElementById("weather-select");

const tree1Slider = document.getElementById("tree1-x");
const tree1YSlider = document.getElementById("tree1-y");
const tree1XValEl = document.getElementById("tree1-x-val");
const tree1YValEl = document.getElementById("tree1-y-val");

const tree2Slider = document.getElementById("tree2-x");
const tree2YSlider = document.getElementById("tree2-y");
const tree2XValEl = document.getElementById("tree2-x-val");
const tree2YValEl = document.getElementById("tree2-y-val");

const bonfireSlider = document.getElementById("bonfire-x");
const bonfireYSlider = document.getElementById("bonfire-y");
const bonfireXValEl = document.getElementById("bonfire-x-val");
const bonfireYValEl = document.getElementById("bonfire-y-val");

const centerTreeYSlider = document.getElementById("center-tree-y");
const centerTreeYValDisp = document.getElementById("center-tree-y-val");
const saveCenterTreeBtn = document.getElementById("save-center-tree");

const sheetBottomNudgeSlider = document.getElementById("sheet-bottom-nudge");
const sheetBottomNudgeValDisp = document.getElementById(
  "sheet-bottom-nudge-val",
);
const saveSheetBottomBtn = document.getElementById("save-sheet-bottom");
const raccoonScaleSlider = document.getElementById("raccoon-scale-input");
const raccoonScaleValEl = document.getElementById("raccoon-scale-val");
const saveAllBtn = document.getElementById("save-all-btn");

const raccoonImageInput = document.getElementById("raccoon-image-input");
const bonfireImageInput = document.getElementById("bonfire-image-input");
const treeInputs = document.querySelectorAll(".tree-input");

// ─── UI EVENT LISTENERS ──────────────────────────────────────
if (uiToggle)
  uiToggle.addEventListener("click", () => uiPanel.classList.toggle("open"));

if (overrideTime)
  overrideTime.addEventListener("change", (e) => {
    isAutoTime = !e.target.checked;
    timeSlider.classList.toggle("hidden", isAutoTime);
  });
if (timeSlider)
  timeSlider.addEventListener("input", (e) => {
    manualTimeVal = parseFloat(e.target.value);
  });

if (overrideSeason)
  overrideSeason.addEventListener("change", (e) => {
    isAutoSeason = !e.target.checked;
    seasonSelect.classList.toggle("hidden", isAutoSeason);
  });
if (seasonSelect)
  seasonSelect.addEventListener("change", (e) => {
    manualSeasonVal = e.target.value;
  });

if (overrideWeather)
  overrideWeather.addEventListener("change", (e) => {
    isAutoWeather = !e.target.checked;
    weatherSelect.classList.toggle("hidden", isAutoWeather);
    if (isAutoWeather) fetchWeatherForCity(currentCity);
  });
if (weatherSelect)
  weatherSelect.addEventListener("change", (e) => {
    manualWeatherVal = e.target.value;
  });

// Position sliders – X
if (tree1Slider)
  tree1Slider.addEventListener("input", (e) => {
    tree1Pct = parseFloat(e.target.value);
    if (tree1XValEl) tree1XValEl.innerText = tree1Pct.toFixed(0) + "%";
  });
if (tree2Slider)
  tree2Slider.addEventListener("input", (e) => {
    tree2Pct = parseFloat(e.target.value);
    if (tree2XValEl) tree2XValEl.innerText = tree2Pct.toFixed(0) + "%";
  });
if (bonfireSlider)
  bonfireSlider.addEventListener("input", (e) => {
    bonfirePct = parseFloat(e.target.value);
    if (bonfireXValEl) bonfireXValEl.innerText = bonfirePct.toFixed(0) + "%";
  });

// Position sliders – Y
if (tree1YSlider)
  tree1YSlider.addEventListener("input", (e) => {
    tree1YOff = parseInt(e.target.value);
    if (tree1YValEl) tree1YValEl.innerText = tree1YOff + "px";
  });
if (tree2YSlider)
  tree2YSlider.addEventListener("input", (e) => {
    tree2YOff = parseInt(e.target.value);
    if (tree2YValEl) tree2YValEl.innerText = tree2YOff + "px";
  });
if (bonfireYSlider)
  bonfireYSlider.addEventListener("input", (e) => {
    bonfireYOff = parseInt(e.target.value);
    if (bonfireYValEl) bonfireYValEl.innerText = bonfireYOff + "px";
  });

if (centerTreeYSlider) {
  centerTreeYSlider.value = centerTreeYOffset;
  if (centerTreeYValDisp)
    centerTreeYValDisp.innerText = centerTreeYOffset + "px";
  centerTreeYSlider.addEventListener("input", (e) => {
    centerTreeYOffset = parseInt(e.target.value);
    if (centerTreeYValDisp)
      centerTreeYValDisp.innerText = centerTreeYOffset + "px";
  });
}
// Sheet bottom nudge slider (no individual save — use Save All)
if (sheetBottomNudgeSlider) {
  sheetBottomNudgeSlider.value = sheetBottomNudgeValNum;
  if (sheetBottomNudgeValDisp)
    sheetBottomNudgeValDisp.innerText = sheetBottomNudgeValNum + "px";
  sheetBottomNudgeSlider.addEventListener("input", (e) => {
    sheetBottomNudgeValNum = parseInt(e.target.value);
    if (sheetBottomNudgeValDisp)
      sheetBottomNudgeValDisp.innerText = sheetBottomNudgeValNum + "px";
  });
}

// Raccoon scale slider
if (raccoonScaleSlider) {
  raccoonScaleSlider.value = raccoonSizeMultiplier;
  if (raccoonScaleValEl)
    raccoonScaleValEl.innerText = raccoonSizeMultiplier.toFixed(2) + "×";
  raccoonScaleSlider.addEventListener("input", (e) => {
    raccoonSizeMultiplier = parseFloat(e.target.value);
    if (raccoonScaleValEl)
      raccoonScaleValEl.innerText = raccoonSizeMultiplier.toFixed(2) + "×";
  });
}

// ─── Save / Load All Settings ────────────────────────────────────────────
function saveAllSettings() {
  localStorage.setItem(
    "guaxinim_all",
    JSON.stringify({
      tree1Pct,
      tree1YOff,
      tree2Pct,
      tree2YOff,
      bonfirePct,
      bonfireYOff,
      centerTreeYOffset,
      sheetBottomNudgeValNum,
      raccoonSizeMultiplier,
    }),
  );
}

function loadAllSettings() {
  try {
    const raw = localStorage.getItem("guaxinim_all");
    if (!raw) return;
    const s = JSON.parse(raw);
    const applySlider = (val, slider, dispEl, fmt) => {
      if (slider) slider.value = val;
      if (dispEl) dispEl.innerText = fmt(val);
    };
    if (s.tree1Pct !== undefined) {
      tree1Pct = s.tree1Pct;
      applySlider(
        tree1Pct,
        tree1Slider,
        tree1XValEl,
        (v) => Math.round(v) + "%",
      );
    }
    if (s.tree1YOff !== undefined) {
      tree1YOff = s.tree1YOff;
      applySlider(tree1YOff, tree1YSlider, tree1YValEl, (v) => v + "px");
    }
    if (s.tree2Pct !== undefined) {
      tree2Pct = s.tree2Pct;
      applySlider(
        tree2Pct,
        tree2Slider,
        tree2XValEl,
        (v) => Math.round(v) + "%",
      );
    }
    if (s.tree2YOff !== undefined) {
      tree2YOff = s.tree2YOff;
      applySlider(tree2YOff, tree2YSlider, tree2YValEl, (v) => v + "px");
    }
    if (s.bonfirePct !== undefined) {
      bonfirePct = s.bonfirePct;
      applySlider(
        bonfirePct,
        bonfireSlider,
        bonfireXValEl,
        (v) => Math.round(v) + "%",
      );
    }
    if (s.bonfireYOff !== undefined) {
      bonfireYOff = s.bonfireYOff;
      applySlider(bonfireYOff, bonfireYSlider, bonfireYValEl, (v) => v + "px");
    }
    if (s.centerTreeYOffset !== undefined) {
      centerTreeYOffset = s.centerTreeYOffset;
      applySlider(
        centerTreeYOffset,
        centerTreeYSlider,
        centerTreeYValDisp,
        (v) => v + "px",
      );
    }
    if (s.sheetBottomNudgeValNum !== undefined) {
      sheetBottomNudgeValNum = s.sheetBottomNudgeValNum;
      applySlider(
        sheetBottomNudgeValNum,
        sheetBottomNudgeSlider,
        sheetBottomNudgeValDisp,
        (v) => v + "px",
      );
    }
    if (s.raccoonSizeMultiplier !== undefined) {
      raccoonSizeMultiplier = s.raccoonSizeMultiplier;
      applySlider(
        raccoonSizeMultiplier,
        raccoonScaleSlider,
        raccoonScaleValEl,
        (v) => v.toFixed(2) + "×",
      );
    }
  } catch (e) {}
}

if (saveAllBtn)
  saveAllBtn.addEventListener("click", () => {
    saveAllSettings();
    saveAllBtn.innerText = "✅ Salvo!";
    setTimeout(() => {
      saveAllBtn.innerText = "💾 Salvar Tudo";
    }, 2000);
  });

// File inputs
if (raccoonImageInput)
  raccoonImageInput.addEventListener("change", (e) => {
    if (!e.target.files[0]) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      raccoonImg.src = evt.target.result;
    };
    reader.readAsDataURL(e.target.files[0]);
  });

if (bonfireImageInput)
  bonfireImageInput.addEventListener("change", (e) => {
    if (!e.target.files[0]) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      bonfireImgLoaded = false;
      bonfireImg.src = evt.target.result;
      bonfireImg.onload = () => {
        bonfireImgLoaded = true;
      };
    };
    reader.readAsDataURL(e.target.files[0]);
  });

treeInputs.forEach((input) => {
  input.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const season = input.dataset.season;
    const type = input.dataset.type; // 'small' or 'center'
    const btn = document.getElementById(`${season}-${type}-btn`);
    const reader = new FileReader();
    reader.onload = (evt) => {
      const img = new Image();
      img.src = evt.target.result;
      img.onload = () => {
        if (!treeImgs[season]) treeImgs[season] = {};
        treeImgs[season][type] = img;
        getBottomYFromRegion(
          img,
          0,
          0,
          img.naturalWidth,
          img.naturalHeight,
          _bottomCacheImg,
          img.src,
        );
        if (btn) {
          btn.classList.add("loaded");
          btn.innerText = "OK";
        }
      };
    };
    reader.readAsDataURL(file);
  });
});

// City input — update state only, button triggers fetch
if (cityInput)
  cityInput.addEventListener("input", (e) => {
    currentCity = e.target.value;
  });

const cityUpdateBtn = document.getElementById("city-update-btn");
if (cityUpdateBtn)
  cityUpdateBtn.addEventListener("click", () => {
    currentCity = cityInput ? cityInput.value.trim() : currentCity;
    if (!currentCity) return;
    cityUpdateBtn.innerText = "⏳";
    cityUpdateBtn.disabled = true;
    updateWeatherBar();
    fetchWeatherForCity(currentCity).finally(() => {
      cityUpdateBtn.innerText = "🔍";
      cityUpdateBtn.disabled = false;
    });
  });

// ─── CANVAS ──────────────────────────────────────────────────
const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d", { alpha: false });

// ─── THEMES & COLORS ─────────────────────────────────────────
const THEMES = {
  manha: {
    sky1: "#74b9ff",
    sky2: "#81ecec",
    sky3: "#ffeaa7",
    mountain: "#827397",
    mountainLight: "#a29bfe",
  },
  dia: {
    sky1: "#0984e3",
    sky2: "#74b9ff",
    sky3: "#81ecec",
    mountain: "#4a5b63",
    mountainLight: "#636e72",
  },
  tarde: {
    sky1: "#6c5ce7",
    sky2: "#e84393",
    sky3: "#fdcb6e",
    mountain: "#1b1b2f",
    mountainLight: "#2d3436",
  },
  noite: {
    sky1: "#000000",
    sky2: "#1e272e",
    sky3: "#0f1423",
    mountain: "#0a0a0f",
    mountainLight: "#1e272e",
  },
};

const SEASON_COLORS = {
  spring: {
    grass1: "#55efc4",
    grass2: "#00b894",
    leafM: "#fd79a8",
    leafN: "#e84393",
    leafE: "#d63031",
  },
  summer: {
    grass1: "#78e08f",
    grass2: "#38ada9",
    leafM: "#2ecc71",
    leafN: "#27ae60",
    leafE: "#1e8449",
  },
  autumn: {
    grass1: "#e58e26",
    grass2: "#b71540",
    leafM: "#f39c12",
    leafN: "#d35400",
    leafE: "#e67e22",
  },
  winter: {
    grass1: "#dfe6e9",
    grass2: "#b2bec3",
    leafM: "#ecf0f1",
    leafN: "#bdc3c7",
    leafE: "#95a5a6",
  },
};

const BASE_COLORS = {
  T: null,
  K: "#1e272e",
  B: "#834c32",
  D: "#5c3a21",
  S: "#f1c40f",
  O: "#e67e22",
  C: "#f5f6fa",
  Y: "#ffffff",
  V: "#dcdde1",
  I: "#7f8fa6",
  G: "#a5b1c2",
  A: "#485460",
  R: "#ff9ff3",
  P: "#f368e0",
  F: "#e74c3c",
};

function getColor(char, season) {
  if (BASE_COLORS[char] !== undefined) return BASE_COLORS[char];
  const sc = SEASON_COLORS[season];
  if (char === "M") return sc.leafM;
  if (char === "N") return sc.leafN;
  if (char === "E") return sc.leafE;
  return "#000";
}

// ─── SPRITE DEFINITIONS ──────────────────────────────────────
const TREE = [
  "TTTTTTTTTTKKKKKKTTTTTTTTTT",
  "TTTTTTTKKKMMMMMMKKKTTTTTTT",
  "TTTTTKKMMMMMMMMMMMMKKTTTTT",
  "TTTTKMMMMMMNNNNMMMMMMKTTTT",
  "TTTKMMMMMNNNNNNNNMMMMMKTTT",
  "TTKMMMMMNNNNNNNNNNMMMMMKTT",
  "TKMMMMMNNNNNNNNNNNNMMMMKTT",
  "TKMMMMNNNNNNNNNNNNNNMMMMKT",
  "KMMMMNNNNNNNNNNNNNNNNMMMMK",
  "KMMMNNNNNNNEEEENNNNNNNMMMK",
  "KMMMNNNNNNEEEEEEENNNNNMMMK",
  "KMMNNNNNNNEEEEEEEENNNNNMMK",
  "TKNNNNNNNNEEEEEEEENNNNNNKT",
  "TKNNNNNNNNEEEEEEEENNNNNNKT",
  "TTKNNNNNNNEEEEEEEENNNNNKTT",
  "TTTKKNNNNNEEEEEEENNNNKKTTT",
  "TTTTTKKNNNEEEEEENNNKKTTTTT",
  "TTTTTTTKKNEEEEEENKKTTTTTTT",
  "TTTTTTTTTKKEEEEKKTTTTTTTTT",
  "TTTTTTTTTTTKBBKTTTTTTTTTTT",
  "TTTTTTTTTTTKBDBKTTTTTTTTTT",
  "TTTTTTTTTTTKBDBKTTTTTTTTTT",
  "TTTTTTTTTTTKKKKKTTTTTTTTTT",
  "TTTTTTTTTTTKKKKKTTTTTTTTTT",
  "TTTTTTTTTTKKKKKKKTTTTTTTTT",
  "TTTTTTTTTKKKKKKKKKTTTTTTTT",
  "TTTTTTTTTKKKKKKKKKTTTTTTTT",
];

const BONFIRE_1 = [
  "TTTTTFTTTTT",
  "TTTTFOFTTTT",
  "TTTOOOFTTTT",
  "TTFOOSOFTTT",
  "TFOOSSOOFTT",
  "TFOOSSSOFTT",
  "FOOSSSSSOFT",
  "KDKKBBKKDKT",
  "TKDBKKBDKTT",
  "TTKKKKKTTTT",
];
const BONFIRE_2 = [
  "TTTTTTFTTTT",
  "TTTTTFOFTTT",
  "TTTTOOFTTTT",
  "TTTOOSOFTTT",
  "TTFOOSOOFTT",
  "TFOOSSSOFTT",
  "FOOSSSSSOFT",
  "KDKKBBKKDKT",
  "TKDBKKBDKTT",
  "TTKKKKKTTTT",
];

const BUSH = [
  "TTTTTTMMMMMNTTTTTT",
  "TTTTMMMMMMNNNNTTTT",
  "TTTMMMMMMNNNNNETTT",
  "TTMMMMMMMNNNNNEETT",
  "TMMMMMMNNNNNEEEEET",
  "MMMMMNNNNNEEEEEEEE",
  "MMMMNNNNNNEEEEEEEE",
];

const FLOWER = ["TRT", "RPR", "TRT", "TNT", "MNN"];

const ROCK = ["TTGGTT", "TGGGGT", "GDDGGA", "DAAADA"];

const SUN = [
  "TTTTTTTSTTTTTTT",
  "TTTTTTTSTTTTTTT",
  "TTSTTTTSTTTTSTT",
  "TTTSTOOSSOOSTTT",
  "TTTTOOSSSSOOTTT",
  "TTTOSSSYYSSSOTT",
  "TTOSSYYYYYYSSOT",
  "SSOSYYYYYYYYOSS",
  "TTOSSYYYYYYSSOT",
  "TTTOSSSYYSSSOTT",
  "TTTTOOSSSSOOTTT",
  "TTTSTOOSSOOSTTT",
  "TTSTTTTSTTTTSTT",
  "TTTTTTTSTTTTTTT",
  "TTTTTTTSTTTTTTT",
];

const MOON = [
  "TTTTTCCCCCCCTTTT",
  "TTTCCVVVVCCCCCCT",
  "TTCVVVVVVVVCCCCT",
  "TCCVVVVVCCCVVVCT",
  "TCCCVVVCCCCVVVCT",
  "TCCCCCCCCCCVVVCT",
  "CCCVCCCCCCCCCCCC",
  "CCVVVCCCCCCCCCCC",
  "CCVVVCCCCCVVVCCC",
  "CCCVCCCCCVVVVVCC",
  "TCCCCCCCCCVVVVCT",
  "TCCCCCCCCCCVVVCT",
  "TTCCCCCVVVCCCCTT",
  "TTTCCCCCVCCCCCTT",
  "TTTTTCCCCCCCTTTT",
  "TTTTTTTTTTTTTTTT",
];

const CLOUD = [
  "TTTTTTTTYYYYTTTTTTTT",
  "TTTTTTYYYYYYYYTTTTTT",
  "TTTTYYYYYYYYYYYYTTTT",
  "TTYYYYYYYYYYYYYYYYTT",
  "YYYYYYYYYYYYYYYYYYYY",
  "YYYYYYYYYYYYYYYYYYYY",
  "TYYYYYYYYYYYYYYYYYYT",
];

// ─── IMAGES ──────────────────────────────────────────────────
const raccoonImg = new Image();
raccoonImg.src = "../ässets/guaxinim_inteiro_transp.png";

const bonfireImg = new Image();
let bonfireImgLoaded = false;
bonfireImg.onload = () => {
  bonfireImgLoaded = true;
};
bonfireImg.onerror = () => {
  bonfireImgLoaded = false;
};
bonfireImg.src = "../ässets/bonfire.png";

const treesSheet = new Image();
let treesSheetLoaded = false;
treesSheet.onload = () => {
  treesSheetLoaded = true;
  try {
    const shW = treesSheet.naturalWidth,
      shH = treesSheet.naturalHeight;
    const tW = shW / 4,
      tH = shH / 2;
    for (let col = 0; col < 4; col++) {
      for (let row = 0; row < 2; row++) {
        try {
          getBottomYFromRegion(
            treesSheet,
            col * tW,
            row * tH,
            tW,
            tH,
            _bottomCacheSheet,
            `${col}_${row}`,
          );
        } catch (e) {}
      }
    }
  } catch (e) {}
};
treesSheet.onerror = () => {
  treesSheetLoaded = false;
};
treesSheet.src = "../ässets/trees_sheet.png";

const treeImgs = {
  spring: { center: new Image(), centerIn: new Image(), small: new Image() },
  summer: { center: new Image(), centerIn: new Image(), small: new Image() },
  autumn: { center: new Image(), centerIn: new Image(), small: new Image() },
  winter: { center: new Image(), centerIn: new Image(), small: new Image() },
};

function loadTreeImages() {
  // Center trees — "_out" variant (tree without raccoon)
  treeImgs.spring.center.src = "../ässets/spring_out.png";
  treeImgs.summer.center.src = "../ässets/summer_out.png";
  treeImgs.autumn.center.src = "../ässets/autum_out.png";
  treeImgs.winter.center.src = "../ässets/winter_out.png";

  // Center trees — "_in" variant (raccoon baked inside)
  treeImgs.spring.centerIn.src = "../ässets/spring_in.png";
  treeImgs.summer.centerIn.src = "../ässets/summer_in.png";
  treeImgs.autumn.centerIn.src = "../ässets/autum_in.png";
  treeImgs.winter.centerIn.src = "../ässets/winter_in.png";

  // Small side trees
  treeImgs.spring.small.src = "../ässets/spring_small.png";
  treeImgs.summer.small.src = "../ässets/summer_small.png";
  treeImgs.autumn.small.src = "../ässets/autum_small.png";
  treeImgs.winter.small.src = "../ässets/winter_small.png";

  Object.entries(treeImgs).forEach(([season, seasonImgs]) => {
    Object.entries(seasonImgs).forEach(([type, img]) => {
      img.onload = () => {
        try {
          if (img.complete && img.naturalWidth) {
            getBottomYFromRegion(
              img,
              0,
              0,
              img.naturalWidth,
              img.naturalHeight,
              _bottomCacheImg,
              img.src,
            );
          }
        } catch (e) {}
        const btn = document.getElementById(`${season}-${type}-btn`);
        if (btn) {
          btn.classList.add("loaded");
          btn.innerText = "OK";
        }
      };
      img.onerror = () => {
        const btn = document.getElementById(`${season}-${type}-btn`);
        if (btn) {
          btn.innerText = "—";
          btn.style.opacity = "0.5";
        }
      };
    });
  });
}

// hole placement as fraction of image (for raccoon hiding)
const holeFrac = { x: 0.5, y: 0.76, r: 0.11 };

// ─── PARTICLES & ENVIRONMENT ─────────────────────────────────
let grassBlades = [];
function initGrass() {
  grassBlades = Array.from({ length: 300 }, () => ({
    x: Math.random() * window.innerWidth * 2,
    height: Math.random() * 15 + 5,
    width: Math.random() * 4 + 2,
    isFlower: Math.random() > 0.95,
  }));
}

const _bottomCacheSheet = {};
const _bottomCacheImg = {};
const _offscreen = document.createElement("canvas");
const _offCtx = _offscreen.getContext("2d");
const _celestialCanvas = document.createElement("canvas");
const _celestialCtx = _celestialCanvas.getContext("2d");

function getBottomYFromRegion(img, sx, sy, sw, sh, cache, cacheKey) {
  if (cache[cacheKey] !== undefined) return cache[cacheKey];
  const sxI = Math.max(0, Math.floor(sx));
  const syI = Math.max(0, Math.floor(sy));
  const w = Math.max(1, Math.floor(sw));
  const h = Math.max(1, Math.floor(sh));
  _offscreen.width = w;
  _offscreen.height = h;
  try {
    _offCtx.clearRect(0, 0, w, h);
    _offCtx.drawImage(img, sxI, syI, w, h, 0, 0, w, h);
    const data = _offCtx.getImageData(0, 0, w, h).data;
    function px(ix, iy) {
      const idx = (iy * w + ix) * 4;
      return [data[idx], data[idx + 1], data[idx + 2], data[idx + 3]];
    }
    const [bgR, bgG, bgB] = px(0, 0);
    const threshold = 30;
    for (let y = h - 1; y >= 0; y--) {
      const rowBase = y * w * 4;
      for (let x = 0; x < w; x++) {
        const b = rowBase + x * 4;
        const r = data[b],
          g = data[b + 1],
          bl = data[b + 2],
          a = data[b + 3];
        const dist = Math.sqrt(
          (r - bgR) ** 2 + (g - bgG) ** 2 + (bl - bgB) ** 2,
        );
        if (a > 10 || dist > threshold) {
          cache[cacheKey] = y;
          return y;
        }
      }
    }
  } catch (e) {
    console.warn("getBottomYFromRegion failed:", e && e.message);
  }
  cache[cacheKey] = h - 1;
  return h - 1;
}

const fireflies = Array.from({ length: 25 }, () => ({
  x: Math.random() * window.innerWidth,
  y: Math.random() * window.innerHeight * 0.3 + window.innerHeight * 0.6,
  phase: Math.random() * Math.PI * 2,
  speedX: (Math.random() - 0.5) * 0.5,
  speedY: (Math.random() - 0.5) * 0.5,
}));

const stars = Array.from({ length: 150 }, () => ({
  x: Math.random(),
  y: Math.random(),
  speed: Math.random() * 0.05,
  twinkle: Math.random() * Math.PI * 2,
}));

const clouds = [
  { x: 10, y: 15, speed: 0.5, scale: 6 },
  { x: 50, y: 10, speed: 0.3, scale: 4 },
  { x: 80, y: 25, speed: 0.8, scale: 5 },
  { x: 20, y: 35, speed: 0.4, scale: 7 },
];

const snowflakes = Array.from({ length: 200 }, () => ({
  x: Math.random() * window.innerWidth,
  y: Math.random() * window.innerHeight,
  speedY: Math.random() * 1 + 0.5,
  speedX: (Math.random() - 0.5) * 0.5,
  size: Math.random() * 3 + 1,
}));

const shootingStars = [];

// ─── DRAW UTILITIES ──────────────────────────────────────────
function drawSprite(sprite, startX, startY, scale, season, flip = false) {
  for (let y = 0; y < sprite.length; y++) {
    const row = sprite[y];
    for (let x = 0; x < row.length; x++) {
      const char = row[x];
      if (char === "T") continue;
      const drawX = flip ? row.length - 1 - x : x;
      ctx.fillStyle = getColor(char, season);
      ctx.fillRect(startX + drawX * scale, startY + y * scale, scale, scale);
    }
  }
}

function drawBlockyMountain(
  centerX,
  groundY,
  peakHeight,
  baseWidth,
  colorShadow,
  colorLight,
  hasSnow,
) {
  const blockSize = 16;
  const steps = Math.max(1, Math.floor(peakHeight / blockSize));
  const stepWidth = baseWidth / 2 / steps;
  for (let i = 0; i < steps; i++) {
    const currentY = groundY - i * blockSize;
    const currentHalfWidth = baseWidth / 2 - i * stepWidth;
    ctx.fillStyle = hasSnow && i > steps * 0.65 ? "#dfe6e9" : colorShadow;
    ctx.fillRect(
      centerX - currentHalfWidth,
      currentY - blockSize,
      currentHalfWidth,
      blockSize,
    );
    ctx.fillStyle = hasSnow && i > steps * 0.65 ? "#ffffff" : colorLight;
    ctx.fillRect(centerX, currentY - blockSize, currentHalfWidth, blockSize);
  }
}

function drawRain(groundY, intensity) {
  const dropCount = Math.floor(100 + intensity * 200);
  ctx.strokeStyle = "rgba(255,255,255,0.12)";
  ctx.lineWidth = 1;
  for (let i = 0; i < dropCount; i++) {
    const x = Math.random() * canvas.width;
    const y = Math.random() * canvas.height;
    const len = 10 + Math.random() * 15;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x - 4, y + len);
    ctx.stroke();
  }
  ctx.fillStyle = "rgba(255,255,255,0.05)";
  for (let i = 0; i < 15; i++) {
    const px = Math.random() * canvas.width;
    const py = groundY + Math.random() * (canvas.height - groundY);
    ctx.beginPath();
    ctx.arc(px, py, 6 + Math.random() * 10, 0, Math.PI * 2);
    ctx.fill();
  }
}

// ─── MOON PHASE ─────────────────────────────────────────────
// ─── STYLISH SUN ───────────────────────────────────────────
function drawSun(cx, cy, r, targetCtx = ctx) {
  const g = targetCtx;
  const t = Date.now() / 16000; // ultra-slow ray rotation
  g.save();
  g.translate(cx, cy);

  // 1. Rays (alternating long/short, slowly rotating)
  g.save();
  g.rotate(t);
  const nRays = 16;
  for (let i = 0; i < nRays; i++) {
    const a = (i / nRays) * Math.PI * 2;
    const isLong = i % 2 === 0;
    const len = r * (isLong ? 0.58 : 0.32);
    g.strokeStyle = isLong ? "rgba(255,235,110,0.75)" : "rgba(255,200,60,0.40)";
    g.lineWidth = isLong ? r * 0.09 : r * 0.045;
    g.lineCap = "round";
    g.beginPath();
    g.moveTo(Math.cos(a) * r * 1.2, Math.sin(a) * r * 1.2);
    g.lineTo(Math.cos(a) * (r * 1.2 + len), Math.sin(a) * (r * 1.2 + len));
    g.stroke();
  }
  g.restore();

  // 2. Sun disk (solid fill to avoid border artifacts)
  g.fillStyle = "#ffca28";
  g.beginPath();
  g.arc(0, 0, r, 0, Math.PI * 2);
  g.fill();

  g.restore();
}

// ─── MOON PHASE API ──────────────────────────────────────────────
// Phase-name → waxing? table (used as fallback labels too)
const PHASE_META = {
  "New Moon": { waxing: true, emoji: "🌑" },
  "Waxing Crescent": { waxing: true, emoji: "🌒" },
  "First Quarter": { waxing: true, emoji: "🌓" },
  "Waxing Gibbous": { waxing: true, emoji: "🌔" },
  "Full Moon": { waxing: false, emoji: "🌕" },
  "Waning Gibbous": { waxing: false, emoji: "🌖" },
  "Third Quarter": { waxing: false, emoji: "🌗" },
  "Waning Crescent": { waxing: false, emoji: "🌘" },
};

async function fetchMoonPhase() {
  const CACHE_MS = 6 * 60 * 60 * 1000; // re-fetch every 6 h
  // Try localStorage cache first
  try {
    const cached = JSON.parse(localStorage.getItem("guaxinim_moon") || "null");
    if (
      cached &&
      cached.data &&
      cached.data.illumination !== null &&
      Date.now() - cached.at < CACHE_MS
    ) {
      moonData = cached.data;
      moonFetchedAt = cached.at;
      updateWeatherBar();
      return;
    }
  } catch (e) {}

  try {
    const res = await fetch("https://api.phaseofthemoontoday.com/v1/current");
    const data = await res.json();
    if (typeof data.illumination === "number") {
      moonData = {
        phase: data.phase,
        illumination: data.illumination,
        emoji: data.emoji || (PHASE_META[data.phase] || {}).emoji || "🌕",
      };
      moonFetchedAt = Date.now();
      localStorage.setItem(
        "guaxinim_moon",
        JSON.stringify({ data: moonData, at: moonFetchedAt }),
      );
      updateWeatherBar();
    }
  } catch (e) {
    console.warn("Moon Phase API unavailable — using local Meeus calculation");
  }
}

// Local fallback: Jean Meeus algorithm (accurate to ~1 day)
// Pixelate helper for celestial bodies
function drawPixelatedCelestial(drawFn, cx, cy, r) {
  const low = 16; // low-res buffer size (ultra chunky pixels)
  _celestialCanvas.width = low;
  _celestialCanvas.height = low;
  const g = _celestialCtx;
  g.imageSmoothingEnabled = false;
  g.clearRect(0, 0, low, low);
  const rOff = low / 2;
  drawFn(rOff, rOff, rOff, g);
  ctx.save();
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(_celestialCanvas, cx - r, cy - r, r * 2, r * 2);
  ctx.restore();
}

function getMoonPhase() {
  const ref = new Date(Date.UTC(2000, 0, 6, 18, 14)); // known new moon
  const cycle = 29.53058770576;
  const days = (Date.now() - ref.getTime()) / 86400000;
  return (((days % cycle) + cycle) % cycle) / cycle; // 0=new … 0.5=full
}

function drawMoonPhase(cx, cy, r, targetCtx = ctx) {
  const g = targetCtx;
  // ── Source: API when fresh, else local calculation ──
  let illum, waxing;
  if (moonData.illumination !== null) {
    illum = moonData.illumination / 100; // 0–1
    const p = (moonData.phase || "").toLowerCase();
    waxing = !(p.includes("waning") || p.includes("third")); // false = lit-left
  } else {
    const localPhase = getMoonPhase(); // 0=new … 1=new
    illum = (1 - Math.cos(localPhase * Math.PI * 2)) / 2;
    waxing = localPhase <= 0.5;
  }

  // terminator x-scale:
  //   +1 → new moon  (dark covers the lit sliver)
  //    0 → quarter   (vertical terminator)
  //   -1 → full moon (lit fills the other half)
  const termScale = 1 - 2 * illum;
  const DEAD_BAND = 0.02; // avoid pixel-thin ellipses right at quarter

  const moonLight = "#ecf0f1";
  const moonShadow = "#04041a";

  g.save();
  // Base dark disk (always drawn; new moon stays this way)
  g.fillStyle = moonShadow;
  g.beginPath();
  g.arc(cx, cy, r, 0, Math.PI * 2);
  g.fill();

  if (illum < 0.01) {
    g.restore();
    return;
  } // 🌑 New Moon

  // Clip all drawing to the disk boundary
  g.save();
  g.beginPath();
  g.arc(cx, cy, r, 0, Math.PI * 2);
  g.clip();

  if (waxing) {
    // 🌒 🌓 🌔 Waxing: right half is the lit limb
    g.fillStyle = moonLight;
    g.fillRect(cx, cy - r, r + 2, r * 2);
    if (termScale > DEAD_BAND) {
      // Crescent — dark ellipse shrinks the right lit area
      g.fillStyle = moonShadow;
      g.save();
      g.translate(cx, cy);
      g.scale(termScale, 1);
      g.fillRect(0, -r, r + 2, r * 2);
      g.restore();
    } else if (termScale < -DEAD_BAND) {
      // Gibbous — lit ellipse extends into the left dark area
      g.fillStyle = moonLight;
      g.save();
      g.translate(cx, cy);
      g.scale(-termScale, 1);
      g.fillRect(-(r + 2), -r, r + 2, r * 2);
      g.restore();
    }
    // termScale ≈0 → First Quarter (right half only, no extra ellipse)
  } else {
    // 🌖 🌗 🌘 Waning: left half is the lit limb
    g.fillStyle = moonLight;
    g.fillRect(cx - r - 2, cy - r, r + 2, r * 2);
    const wts = -termScale; // +1 at full, 0 at last quarter, -1 at new
    if (wts > DEAD_BAND) {
      // Gibbous — lit ellipse extends into the right dark area
      g.fillStyle = moonLight;
      g.save();
      g.translate(cx, cy);
      g.scale(wts, 1);
      g.fillRect(0, -r, r + 2, r * 2);
      g.restore();
    } else if (wts < -DEAD_BAND) {
      // Crescent — dark ellipse shrinks the left lit area
      g.fillStyle = moonShadow;
      g.save();
      g.translate(cx, cy);
      g.scale(-wts, 1);
      g.fillRect(-(r + 2), -r, r + 2, r * 2);
      g.restore();
    }
    // wts ≈0 → Third Quarter (left half only, no extra ellipse)
  }

  g.restore(); // remove clip
  g.restore();
}

function drawSnow() {
  ctx.fillStyle = "rgba(255,255,255,0.8)";
  snowflakes.forEach((f) => {
    ctx.beginPath();
    ctx.arc(f.x, f.y, f.size, 0, Math.PI * 2);
    ctx.fill();
    f.y += f.speedY * 0.45;
    f.x += f.speedX * 0.45;
    if (f.y > canvas.height) {
      f.y = -10;
      f.x = Math.random() * canvas.width;
    }
  });
}

// ─── TIME / SEASON / WEATHER ─────────────────────────────────
function getActiveTime() {
  if (!isAutoTime) return manualTimeVal;
  const now = new Date();
  return now.getHours() + now.getMinutes() / 60;
}

function getTimeTheme(h) {
  if (h >= 6 && h < 9) return "manha";
  if (h >= 9 && h < 17) return "dia";
  if (h >= 17 && h < 18) return "tarde";
  return "noite";
}

function getActiveSeason(date) {
  if (!isAutoSeason) return manualSeasonVal;
  const month = date.getMonth() + 1;
  if ([12, 1, 2, 3].includes(month)) return "summer";
  if ([9, 10, 11].includes(month)) return "spring";
  if ([6, 7, 8].includes(month)) return "winter";
  return "autumn";
}

function getActiveWeather(h, season, date) {
  if (!isAutoWeather) return manualWeatherVal;
  const nowTs = Date.now();
  const hasLiveExternal = externalWeather && nowTs - externalWeatherFetchedAt < 5 * 60 * 1000;
  if (hasLiveExternal) return externalWeather;
  const hasSelectedLocation = externalLat !== null && externalLon !== null;
  const allowPrecipitation = hasLiveExternal || !hasSelectedLocation;
  const month = date.getMonth() + 1;
  const day = date.getDate();
  const seed = Math.sin(day * 23 + month * 7 + Math.floor(h) * 17) * 10000;
  const v = seed - Math.floor(seed);
  let rainChance = 0.45;
  if (season === "summer") rainChance = 0.75;
  if (season === "spring") rainChance = 0.55;
  if (season === "winter") rainChance = 0.6;
  if (h >= 12 && h < 18) {
    if (v < rainChance && allowPrecipitation) {
      if (season === "winter") return "snow";
      return v < rainChance * 0.6 ? "rain" : "storm";
    }
    return v < 0.75 ? "cloudy" : "clear";
  }
  if (h >= 6 && h < 12) {
    if (v < 0.35) {
      if (season === "winter" && v < 0.15 && allowPrecipitation) return "snow";
      return "cloudy";
    }
    return "clear";
  }
  if (v < 0.4) {
    if (allowPrecipitation && season === "winter" && v < 0.2) return "snow";
    return "cloudy";
  }
  return "clear";
}

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

let geocodeAbortController = null;
let weatherAbortController = null;

async function fetchWeatherForCity(city) {
  if (!city || !city.trim()) return;
  try {
    if (geocodeAbortController) geocodeAbortController.abort();
    geocodeAbortController = new AbortController();
    const geoRes = await fetch(
      `https://nominatim.openstreetmap.org/search?format=json&limit=1&q=${encodeURIComponent(city)}`,
      { signal: geocodeAbortController.signal },
    );
    const geoJson = await geoRes.json();
    if (!geoJson || !geoJson[0]) return;
    const lat = parseFloat(geoJson[0].lat);
    const lon = parseFloat(geoJson[0].lon);
    if (weatherAbortController) weatherAbortController.abort();
    weatherAbortController = new AbortController();
    const wres = await fetch(
      `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}` +
        `&current=temperature_2m,apparent_temperature,relative_humidity_2m,windspeed_10m,weathercode` +
        `&daily=sunrise,sunset&timezone=auto&forecast_days=1`,
      { signal: weatherAbortController.signal },
    );
    const wjson = await wres.json();
    if (wjson && wjson.current) {
      const c = wjson.current;
      externalWeather = weatherCodeToCategory(c.weathercode);
      externalWeatherFetchedAt = Date.now();
      weatherInfo.temp = Math.round(c.temperature_2m);
      weatherInfo.feelsLike = Math.round(c.apparent_temperature);
      weatherInfo.humidity = Math.round(c.relative_humidity_2m);
      weatherInfo.windspeed = Math.round(c.windspeed_10m);
      weatherInfo.condition = weatherCodeToLabel(c.weathercode);
      // persist external info
      try {
        localStorage.setItem(
          EXTERNAL_STORAGE_KEY,
          JSON.stringify({
            externalWeather,
            externalWeatherFetchedAt,
            externalLat: lat,
            externalLon: lon,
            externalHemisphere: lat < 0 ? 'south' : 'north',
            externalLocalDateParts,
            externalTimezone,
            currentCity: city,
          }),
        );
      } catch (e) {}
    }
    if (wjson && wjson.daily) {
      weatherInfo.sunrise =
        (wjson.daily.sunrise[0] || "").split("T")[1] || null;
      weatherInfo.sunset = (wjson.daily.sunset[0] || "").split("T")[1] || null;
    }
    updateWeatherBar();
  } catch (e) {
    /* ignore abort / network errors */
  }
}

function updateTimeDisplay(h) {
  if (!timeDisplay) return;
  const hours = Math.floor(h);
  const minutes = Math.floor((h - hours) * 60);
  const str = `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
  timeDisplay.innerText = str;
  const el = document.getElementById("wb-time");
  if (el) el.innerText = str;
}

function updateWeatherBar() {
  const set = (id, val) => {
    const e = document.getElementById(id);
    if (e) e.innerText = val;
  };
  set("wb-city", currentCity);
  set("wb-temp", weatherInfo.temp !== null ? weatherInfo.temp + "°C" : "--°C");
  set(
    "wb-feels",
    weatherInfo.feelsLike !== null ? weatherInfo.feelsLike + "°C" : "--°C",
  );
  set(
    "wb-hum",
    weatherInfo.humidity !== null ? weatherInfo.humidity + "%" : "--%",
  );
  set(
    "wb-wind",
    weatherInfo.windspeed !== null
      ? weatherInfo.windspeed + " km/h"
      : "-- km/h",
  );
  set("wb-cond", weatherInfo.condition || "--");
  set("wb-sunrise", weatherInfo.sunrise || "--:--");
  set("wb-sunset", weatherInfo.sunset || "--:--");
  // Moon phase
  if (moonData.phase) {
    set("wb-moon", `${moonData.emoji || ""} ${moonData.phase}`);
  }
}

function drawWeatherText() {
  /* replaced by HTML bar */
}

// ─── RESIZE ──────────────────────────────────────────────────
function resize() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  raccoonX = canvas.width / 2;
  initGrass();
}

// ─── MAIN LOOP ───────────────────────────────────────────────
function loop() {
  const now = new Date();
  const h = getActiveTime();
  updateTimeDisplay(h);

  const themeName = getTimeTheme(h);
  const theme = THEMES[themeName];
  const season = getActiveSeason(now);
  const weather = getActiveWeather(h, season, now);

  const isNight = h >= 18 || h < 6;
  const groundY = canvas.height * 0.75;

  // approximate hole target (refined after drawing center tree)
  let centerHoleTarget = canvas.width / 2;
  const centerTreeX = canvas.width / 2 - 40;

  // ── Raccoon AI ──────────────────────────────────────────────
  const isUncomfortable =
    weather === "rain" || weather === "storm" || weather === "snow";
  if (Date.now() > randomHoleTime + 15000)
    randomHoleTime = Date.now() + Math.random() * 50000 + 20000;
  const isRandomlyHiding =
    Date.now() > randomHoleTime && Date.now() < randomHoleTime + 15000;
  const shouldHide = isUncomfortable || isRandomlyHiding;

  if (shouldHide) {
    // Head to center tree hole
    const spd = canvas.width * 0.0015;
    if (Math.abs(raccoonX - centerHoleTarget) > spd) {
      raccoonState = "walking";
      if (raccoonX < centerHoleTarget) {
        raccoonX += spd;
        raccoon.flip = false;
      } else {
        raccoonX -= spd;
        raccoon.flip = true;
      }
      raccoonScale = 1;
    } else {
      raccoonState = "hiding";
      raccoonScale = Math.max(0, raccoonScale - 0.025);
    }
  } else {
    // Free roaming — pick a new wander target periodically
    if (raccoonWanderTargetX < 0 || Date.now() > raccoonWanderTimer) {
      raccoonWanderTargetX = canvas.width * (0.07 + Math.random() * 0.86);
      raccoonWanderTimer = Date.now() + 5000 + Math.random() * 14000;
    }
    const spd = canvas.width * 0.0011;
    raccoonScale = Math.min(1, raccoonScale + 0.025);
    if (Math.abs(raccoonX - raccoonWanderTargetX) > spd * 2) {
      raccoonState = "walking";
      if (raccoonX < raccoonWanderTargetX) {
        raccoonX += spd;
        raccoon.flip = false;
      } else {
        raccoonX -= spd;
        raccoon.flip = true;
      }
    } else {
      raccoonState = "idle";
    }
  }

  // ── 1. SKY ──────────────────────────────────────────────────
  const skyGrad = ctx.createLinearGradient(0, 0, 0, canvas.height * 0.8);
  skyGrad.addColorStop(0, theme.sky1);
  skyGrad.addColorStop(0.4, theme.sky2);
  skyGrad.addColorStop(1, theme.sky3);
  ctx.fillStyle = skyGrad;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // ── 2. Weather darkness overlay ─────────────────────────────
  if (weather === "cloudy" || weather === "snow") {
    ctx.fillStyle = "rgba(0,0,0,0.12)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  } else if (weather === "rain") {
    ctx.fillStyle = "rgba(0,0,20,0.15)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  } else if (weather === "storm") {
    ctx.fillStyle = "rgba(0,0,30,0.25)";
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    if (Math.random() < 0.02) lightningFlash = 8;
  }

  // ── 3. Stars & shooting stars (night) ───────────────────────
  if (isNight) {
    stars.forEach((s) => {
      s.twinkle += s.speed * 0.4;
      ctx.fillStyle = `rgba(255,255,255,${(Math.sin(s.twinkle) + 1) / 2})`;
      ctx.fillRect(s.x * canvas.width, s.y * canvas.height * 0.7, 4, 4);
    });
    if (Math.random() < 0.005 && weather === "clear") {
      shootingStars.push({
        x: Math.random() * canvas.width,
        y: 0,
        len: Math.random() * 50 + 20,
        speed: Math.random() * 2.5 + 4,
      });
    }
    shootingStars.forEach((ss, i) => {
      ctx.strokeStyle = "rgba(255,255,255,0.8)";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(ss.x, ss.y);
      ctx.lineTo(ss.x - ss.len, ss.y - ss.len);
      ctx.stroke();
      ss.x += ss.speed * 0.5;
      ss.y += ss.speed * 0.5;
      if (ss.y > canvas.height) shootingStars.splice(i, 1);
    });
  }

  // ── 4. Sun or Moon ──────────────────────────────────────────
  const celestialR = Math.min(canvas.width, canvas.height) * 0.085;
  if (!isNight) {
    const tp = (h - 6) / 12;
    const sunCx = canvas.width * 0.1 + canvas.width * 0.8 * tp;
    const sunCy =
      canvas.height * 0.12 + Math.sin(tp * Math.PI) * -canvas.height * 0.06;
    drawPixelatedCelestial(drawSun, sunCx, sunCy, celestialR);
  } else {
    const nightH = h >= 18 ? h - 18 : h + 6;
    const tp = nightH / 12;
    const moonCx = canvas.width * 0.1 + canvas.width * 0.8 * tp;
    const moonCy = canvas.height * 0.16;
    drawPixelatedCelestial(drawMoonPhase, moonCx, moonCy, celestialR);
  }

  // ── 5. Clouds ───────────────────────────────────────────────
  const windKmh =
    typeof weatherInfo.windspeed === "number" ? weatherInfo.windspeed : 8;
  const windFactor = Math.min(2.0, Math.max(0.4, windKmh / 20)); // 0.4x .. 2.0x
  const cloudList =
    weather !== "rain" && weather !== "storm" && weather !== "snow"
      ? clouds
      : clouds.concat([
          { x: 35, y: 18, speed: 0.35, scale: 5 },
          { x: 70, y: 22, speed: 0.45, scale: 6 },
        ]);
  cloudList.forEach((c) => {
    c.x += c.speed * 0.2 * windFactor;
    if (c.x > 110) c.x = -20;
    drawSprite(
      CLOUD,
      (c.x / 100) * canvas.width,
      (c.y / 100) * canvas.height,
      c.scale * 2.4,
      season,
    );
  });

  // ── 6. Mountains ────────────────────────────────────────────
  const mtnSnow = season === "winter" || weather === "snow";
  drawBlockyMountain(
    canvas.width * 0.25,
    groundY,
    canvas.height * 0.45,
    canvas.width * 0.6,
    theme.mountain,
    theme.mountainLight,
    mtnSnow,
  );
  drawBlockyMountain(
    canvas.width * 0.75,
    groundY,
    canvas.height * 0.35,
    canvas.width * 0.5,
    theme.mountain,
    theme.mountainLight,
    mtnSnow,
  );
  drawBlockyMountain(
    canvas.width * 0.5,
    groundY,
    canvas.height * 0.25,
    canvas.width * 0.4,
    theme.mountain,
    theme.mountainLight,
    season === "winter",
  );

  // ── 7. Ground ───────────────────────────────────────────────
  ctx.fillStyle = SEASON_COLORS[season].grass2;
  ctx.fillRect(0, groundY, canvas.width, canvas.height - groundY);
  ctx.fillStyle = SEASON_COLORS[season].grass1;
  grassBlades.forEach((b) => {
    if (b.x < canvas.width)
      ctx.fillRect(b.x, groundY - b.height, b.width, b.height);
  });
  ctx.fillRect(0, groundY, canvas.width, canvas.height - groundY);

  // ── 8. Rocks, bushes, flowers ───────────────────────────────
  drawSprite(ROCK, canvas.width * 0.3, groundY - 15, 4, season);
  drawSprite(ROCK, canvas.width * 0.65, groundY - 10, 3, season);
  drawSprite(
    BUSH,
    canvas.width * 0.2,
    groundY - BUSH.length * 6 + 10,
    6,
    season,
  );
  drawSprite(
    BUSH,
    canvas.width * 0.85,
    groundY - BUSH.length * 5 + 5,
    5,
    season,
  );
  drawSprite(
    BUSH,
    canvas.width * 0.1,
    groundY - BUSH.length * 4 + 15,
    4,
    season,
  );
  if (season === "spring" || season === "summer") {
    grassBlades.forEach((b) => {
      if (b.isFlower && b.x < canvas.width)
        drawSprite(FLOWER, b.x, groundY + b.height * 2, 3, season);
    });
  }

  // ── 9. Side trees ───────────────────────────────────────────
  const seasonTrees = treeImgs[season];
  if (
    seasonTrees &&
    seasonTrees.small.complete &&
    seasonTrees.small.naturalWidth
  ) {
    const si = seasonTrees.small;
    const dsw = Math.min(canvas.width * 0.12, 260);
    const ss = dsw / si.naturalWidth;
    const sW = si.naturalWidth * ss;
    const sH = si.naturalHeight * ss;
    const bot = getBottomYFromRegion(
      si,
      0,
      0,
      si.naturalWidth,
      si.naturalHeight,
      _bottomCacheImg,
      si.src,
    );
    const nudge = sheetBottomNudgeValNum;
    ctx.drawImage(
      si,
      (tree1Pct / 100) * canvas.width - sW / 2,
      groundY - bot * ss + nudge + tree1YOff,
      sW,
      sH,
    );
    ctx.drawImage(
      si,
      (tree2Pct / 100) * canvas.width - sW / 2,
      groundY - bot * ss + nudge + tree2YOff,
      sW,
      sH,
    );
  } else if (treesSheetLoaded && treesSheet.naturalWidth) {
    const shW = treesSheet.naturalWidth,
      shH = treesSheet.naturalHeight;
    const tW = shW / 4,
      tH = shH / 2;
    const col = { winter: 0, spring: 1, summer: 2, autumn: 3 }[season] ?? 1;
    const dsw = Math.min(canvas.width * 0.12, 260);
    const ss = dsw / tW;
    const sW = tW * ss,
      sH = tH * ss;
    const botS = getBottomYFromRegion(
      treesSheet,
      col * tW,
      tH,
      tW,
      tH,
      _bottomCacheSheet,
      `${col}_1`,
    );
    ctx.drawImage(
      treesSheet,
      col * tW,
      tH,
      tW,
      tH,
      (tree1Pct / 100) * canvas.width - sW / 2,
      groundY - botS * ss + sheetBottomNudgeValNum + tree1YOff,
      sW,
      sH,
    );
    ctx.drawImage(
      treesSheet,
      col * tW,
      tH,
      tW,
      tH,
      (tree2Pct / 100) * canvas.width - sW / 2,
      groundY - botS * ss + sheetBottomNudgeValNum + tree2YOff,
      sW,
      sH,
    );
  } else {
    drawSprite(
      TREE,
      (tree1Pct / 100) * canvas.width,
      groundY - TREE.length * 8 + 15 + tree1YOff,
      8,
      season,
    );
    drawSprite(
      TREE,
      (tree2Pct / 100) * canvas.width,
      groundY - TREE.length * 8 + 15 + tree2YOff,
      8,
      season,
    );
  }

  // ── 10. Center tree ─────────────────────────────────────────
  let centerTreeImgX = centerTreeX;
  let centerTreeImgY = groundY - TREE.length * 8 + 25;
  let centerTreeImgW = 0,
    centerTreeImgH = 0;
  let centerHoleX = centerTreeX,
    centerHoleY = groundY,
    centerHoleR = 40;
  centerTreeUsingSheetTop = false;

  if (seasonTrees) {
    // Switch to _in only once raccoon has fully arrived (state='hiding'),
    // so the tree never changes before the raccoon reaches the hole.
    const useIn =
      raccoonState === "hiding" &&
      seasonTrees.centerIn.complete &&
      seasonTrees.centerIn.naturalWidth;
    const ciBase =
      seasonTrees.center.complete && seasonTrees.center.naturalWidth
        ? seasonTrees.center
        : null;
    const ci = useIn ? seasonTrees.centerIn : ciBase;
    if (ci) {
      // ── Stable layout: ALWAYS anchor size & bottom to the '_out' reference.
      // This means switching between _out and _in never shifts the tree position,
      // even if the two images have slightly different raw dimensions or padding.
      const layoutRef = ciBase || ci; // prefer _out; fall back to whatever loaded
      const dw = Math.min(canvas.width * 0.28, 520);
      const sc = dw / layoutRef.naturalWidth; // scale fixed by _out width
      centerTreeImgW = layoutRef.naturalWidth * sc; // stable W
      centerTreeImgH = layoutRef.naturalHeight * sc; // stable H
      const imgBot = getBottomYFromRegion(
        // stable bottom anchor
        layoutRef,
        0,
        0,
        layoutRef.naturalWidth,
        layoutRef.naturalHeight,
        _bottomCacheImg,
        layoutRef.src,
      );
      centerTreeImgX = canvas.width / 2 - centerTreeImgW / 2;
      centerTreeImgY =
        groundY - imgBot * sc + centerTreeYOffset + sheetBottomNudgeValNum;
      // Draw the active variant (ci) at the stable rect — ctx stretches it to fit
      ctx.drawImage(
        ci,
        centerTreeImgX,
        centerTreeImgY,
        centerTreeImgW,
        centerTreeImgH,
      );
      centerHoleX = centerTreeImgX + centerTreeImgW * holeFrac.x;
      centerHoleY = centerTreeImgY + centerTreeImgH * holeFrac.y;
      centerHoleR = centerTreeImgW * holeFrac.r;
      centerHoleTarget = centerHoleX;
      centerTreeUsingSheetTop = useIn; // _in has raccoon baked, skip extra draw
    } else if (treesSheetLoaded && treesSheet.naturalWidth) {
      const shW = treesSheet.naturalWidth,
        shH = treesSheet.naturalHeight;
      const tW = shW / 4,
        tH = shH / 2;
      const col = { winter: 0, spring: 1, summer: 2, autumn: 3 }[season] ?? 1;
      const row = shouldHide ? 0 : 1;
      const dw = Math.min(canvas.width * 0.28, 520);
      const sc = dw / tW;
      centerTreeImgW = tW * sc;
      centerTreeImgH = tH * sc;
      const sx = col * tW,
        sy = row * tH;
      const botTile = getBottomYFromRegion(
        treesSheet,
        sx,
        sy,
        tW,
        tH,
        _bottomCacheSheet,
        `${col}_${row}`,
      );
      centerTreeImgX = canvas.width / 2 - centerTreeImgW / 2;
      centerTreeImgY =
        groundY - botTile * sc + centerTreeYOffset + sheetBottomNudgeValNum;
      ctx.drawImage(
        treesSheet,
        sx,
        sy,
        tW,
        tH,
        centerTreeImgX,
        centerTreeImgY,
        centerTreeImgW,
        centerTreeImgH,
      );
      centerHoleX = centerTreeImgX + centerTreeImgW * holeFrac.x;
      centerHoleY = centerTreeImgY + centerTreeImgH * holeFrac.y;
      centerHoleR = centerTreeImgW * holeFrac.r;
      centerHoleTarget = centerHoleX;
      centerTreeUsingSheetTop = row === 0;
    } else {
      const fallbackY = groundY - TREE.length * 8 + 25 + centerTreeYOffset;
      drawSprite(TREE, centerTreeX, fallbackY, 9, season);
      centerHoleX = canvas.width / 2;
      centerHoleY = fallbackY + 220;
      centerHoleTarget = centerHoleX;
    }
  } // end seasonTrees block

  // ── 11. Hiding badge ────────────────────────────────────────
  if (
    raccoonState === "hiding" &&
    Math.abs(raccoonX - centerHoleTarget) < 160 &&
    centerTreeImgW > 0
  ) {
    const bx = centerTreeImgX + centerTreeImgW - 48;
    const by = centerTreeImgY + 24;
    ctx.fillStyle = "rgba(0,0,0,0.6)";
    ctx.beginPath();
    ctx.arc(bx, by, 18, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "rgba(255,255,255,0.95)";
    ctx.font = '16px "Outfit", sans-serif';
    ctx.textAlign = "center";
    ctx.fillText("😴", bx, by + 6);
  }

  // ── 12. Bonfire + fireflies (night) ─────────────────────────
  if (isNight) {
    const bfX = (bonfirePct / 100) * canvas.width;

    if (bonfireImgLoaded && bonfireImg.naturalWidth) {
      const bfSc = 80 / bonfireImg.naturalHeight;
      const bfW = bonfireImg.naturalWidth * bfSc;
      const bfH = bonfireImg.naturalHeight * bfSc;
      // glow
      ctx.save();
      ctx.globalAlpha = (Math.sin(Date.now() / 420) + 1) / 8 + 0.1;
      ctx.fillStyle = "#e67e22";
      ctx.beginPath();
      ctx.arc(bfX, groundY - 20, 80, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
      ctx.drawImage(
        bonfireImg,
        bfX - bfW / 2,
        groundY - bfH + bonfireYOff,
        bfW,
        bfH,
      );
    } else {
      const bfSprite =
        Math.floor(Date.now() / 320) % 2 === 0 ? BONFIRE_1 : BONFIRE_2;
      drawSprite(
        bfSprite,
        bfX,
        groundY - BONFIRE_1.length * 6 + 15 + bonfireYOff,
        6,
        season,
      );
      ctx.fillStyle = `rgba(230,126,34,${(Math.sin(Date.now() / 420) + 1) / 8 + 0.1})`;
      ctx.beginPath();
      ctx.arc(bfX + 33, groundY - 10, 90, 0, Math.PI * 2);
      ctx.fill();
    }

    if (weather === "clear" && (season === "summer" || season === "spring")) {
      fireflies.forEach((fly) => {
        fly.x += fly.speedX * 0.45;
        fly.y += fly.speedY * 0.45;
        if (fly.x < 0 || fly.x > canvas.width) fly.speedX *= -1;
        if (fly.y < groundY - 50 || fly.y > canvas.height) fly.speedY *= -1;
        fly.phase += 0.05;
        const glow = (Math.sin(fly.phase) + 1) / 2;
        ctx.fillStyle = `rgba(241,196,15,${glow})`;
        ctx.beginPath();
        ctx.arc(fly.x, fly.y, 3, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = `rgba(241,196,15,${glow * 0.3})`;
        ctx.beginPath();
        ctx.arc(fly.x, fly.y, 8, 0, Math.PI * 2);
        ctx.fill();
      });
    }
  }

  // ── 13. Raccoon ─────────────────────────────────────────────
  raccoon.frame++;
  if (raccoonState === "walking") {
    if (raccoon.frame % 30 === 0)
      raccoon.bounceOffset = raccoon.bounceOffset === 0 ? -25 : 0;
  } else {
    if (raccoon.frame % 90 === 0) {
      if (Math.random() > 0.6) raccoon.flip = !raccoon.flip;
      raccoon.bounceOffset = raccoon.bounceOffset === 0 ? -10 : 0;
    }
  }

  if (
    raccoonImg.complete &&
    raccoonImg.naturalHeight !== 0 &&
    raccoonScale > 0
  ) {
    const spW = 260,
      spH = 260;
    const hidingAtCenter =
      raccoonState === "hiding" && Math.abs(raccoonX - centerHoleTarget) < 160;

    // shadow
    if (raccoonScale > 0.3) {
      ctx.fillStyle = "rgba(0,0,0,0.3)";
      ctx.beginPath();
      ctx.ellipse(
        raccoonX,
        groundY,
        (raccoon.bounceOffset === 0 ? 60 : 40) *
          raccoonScale *
          raccoonSizeMultiplier,
        8 * raccoonScale * raccoonSizeMultiplier,
        0,
        0,
        Math.PI * 2,
      );
      ctx.fill();
    }

    if (hidingAtCenter) {
      raccoonX = centerHoleTarget;
      if (!centerTreeUsingSheetTop) {
        const iW = spW * 0.6 * raccoonScale * raccoonSizeMultiplier,
          iH = spH * 0.6 * raccoonScale * raccoonSizeMultiplier;
        ctx.save();
        ctx.translate(centerHoleX, centerHoleY + iH * 0.08);
        ctx.rotate(-0.08);
        ctx.drawImage(raccoonImg, -iW / 2, -iH / 2, iW, iH);
        // closed eyes
        ctx.strokeStyle = "rgba(20,20,20,0.95)";
        ctx.lineWidth = Math.max(2, iW * 0.02);
        ctx.lineCap = "round";
        const eyeY = -iH * 0.12,
          eyeLX = -iW * 0.12,
          eyeRX = iW * 0.12;
        ctx.beginPath();
        ctx.moveTo(eyeLX - iW * 0.04, eyeY);
        ctx.quadraticCurveTo(eyeLX, eyeY + iH * 0.03, eyeLX + iW * 0.04, eyeY);
        ctx.stroke();
        ctx.beginPath();
        ctx.moveTo(eyeRX - iW * 0.04, eyeY);
        ctx.quadraticCurveTo(eyeRX, eyeY + iH * 0.03, eyeRX + iW * 0.04, eyeY);
        ctx.stroke();
        // Zs
        ctx.fillStyle = "rgba(255,255,255,0.9)";
        ctx.font = `${Math.max(12, Math.floor(iW * 0.08))}px "Outfit", sans-serif`;
        ctx.textAlign = "center";
        for (let i = 0; i < 3; i++) {
          ctx.globalAlpha = 1 - i * 0.28;
          ctx.fillText(
            "Z",
            iW * 0.18 + i * iW * 0.06,
            -iH * 0.6 - i * iH * 0.12,
          );
        }
        ctx.globalAlpha = 1;
        ctx.restore();
      }
    } else {
      ctx.save();
      ctx.translate(raccoonX, groundY + raccoon.bounceOffset);
      ctx.scale(
        raccoonScale * raccoonSizeMultiplier,
        raccoonScale * raccoonSizeMultiplier,
      );
      if (raccoonState === "walking") {
        if (raccoon.bounceOffset !== 0) ctx.scale(0.95, 1.05);
        else ctx.scale(1.05, 0.95);
      } else {
        if (raccoon.bounceOffset !== 0) ctx.scale(1.02, 0.98);
      }
      if (raccoon.flip) ctx.scale(-1, 1);
      ctx.drawImage(raccoonImg, -spW / 2, -spH + 110, spW, spH);
      ctx.restore();
    }
  }

  // ── 14. Rain / Snow ─────────────────────────────────────────
  if (weather === "rain" || weather === "storm")
    drawRain(groundY, weather === "storm" ? 1 : 0.6);
  else if (weather === "snow") drawSnow();

  // ── 15. Lightning ───────────────────────────────────────────
  if (lightningFlash > 0) {
    ctx.fillStyle = `rgba(255,255,255,${lightningFlash / 20})`;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    lightningFlash -= 1;
  }

  // ── 16. Weather bar update ───────────────────────────────────
  updateTimeDisplay(h);

  requestAnimationFrame(loop);
}

// ─── INIT ────────────────────────────────────────────────────
window.addEventListener("resize", resize);
window.addEventListener("load", () => {
  resize();
  loadAllSettings();
  loadTreeImages();
  fetchWeatherForCity(currentCity);
  fetchMoonPhase();
  setInterval(fetchMoonPhase, 6 * 60 * 60 * 1000); // refresh every 6 h
  loop();
});
