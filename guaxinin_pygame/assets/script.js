// script.js - Refactored real-time raccoon environment simulator
// Architecture sections:
// CONFIG, STATE, DOM CACHE, UTILITIES, ASSET LOADER,
// ENVIRONMENT SYSTEM, RACCOON SYSTEM, RENDERER, UI CONTROLLER,
// STORAGE SYSTEM, INITIALIZATION

// ---------------------- CONFIG ----------------------
const CONFIG = {
  storageKeys: {
    centerTreeYOffset: 'centerTreeYOffset',
    sheetBottomNudge: 'sheetBottomNudge'
  },
  seasons: ['spring', 'summer', 'autumn', 'winter'],
  defaultPaths: {
    treeSheet: 'ässets/trees_sheet.png',
    raccoon: 'ässets/guaxinim_inteiro_transp.png',
    seasonFolder: 'ässets/', // allow files in repo root or uploaded
  }
};

// ---------------------- STATE ----------------------
const appState = {
  time: 12,
  manualTime: false,

  season: 'summer',
  manualSeason: false,

  weather: 'clear',
  manualWeather: false,

  city: 'São Paulo',

  showMoon: true,
  showClouds: true,

  raccoon: {
    state: 'idle', // idle | walking | hiding
    speed: 0.003,
    scale: 1,
    x: 50 // percent
  },

  positions: {
    tree1: 15,
    tree2: 80,
    bonfire: 65,
    centerTreeYOffset: parseInt(localStorage.getItem(CONFIG.storageKeys.centerTreeYOffset)) || 160,
    sheetBottomNudge: parseInt(localStorage.getItem(CONFIG.storageKeys.sheetBottomNudge)) || 0
  },

  assets: {
    raccoonImage: null,
    treeSheet: null,
    seasonImages: { spring: null, summer: null, autumn: null, winter: null },
    seasonImagesSmall: { spring: null, summer: null, autumn: null, winter: null }
  },

  debug: {
    fps: 0,
    lastFrameTime: performance.now()
  }
};

// ---------------------- DOM CACHE ----------------------
const DOM = (() => {
  const qs = (s) => document.getElementById(s);
  return {
    canvas: qs('gameCanvas'),
    uiToggle: qs('ui-toggle'),
    uiPanel: qs('ui-panel'),
    cityInput: qs('city-input'),
    overrideTime: qs('override-time'),
    timeSlider: qs('time-slider'),
    timeDisplay: qs('time-display'),
    overrideSeason: qs('override-season'),
    seasonSelect: qs('season-select'),
    overrideWeather: qs('override-weather'),
    weatherSelect: qs('weather-select'),
    showMoon: qs('show-moon'),
    showClouds: qs('show-clouds'),
    raccoonStateSelect: qs('raccoon-state-select'),
    raccoonSpeed: qs('raccoon-speed'),
    raccoonScale: qs('raccoon-scale'),
    raccoonX: qs('raccoon-x'),
    raccoonImageInput: qs('raccoon-image-input'),
    seasonSmallImagesInput: qs('season-small-images-input'),
    seasonCenterImagesInput: qs('season-center-images-input'),
    tree1X: qs('tree1-x'),
    tree2X: qs('tree2-x'),
    bonfireX: qs('bonfire-x'),
    centerTreeY: qs('center-tree-y'),
    centerTreeYVal: qs('center-tree-y-val'),
    saveCenterTree: qs('save-center-tree'),
    sheetBottomNudge: qs('sheet-bottom-nudge'),
    sheetBottomNudgeVal: qs('sheet-bottom-nudge-val'),
    saveSheetBottom: qs('save-sheet-bottom')
  };
})();

// local references
const ctx = DOM.canvas.getContext('2d', { alpha: false });

// ---------------------- UTILITIES ----------------------
const Utils = {
  clamp(v, a, b) { return Math.max(a, Math.min(b, v)); },
  lerp(a, b, t) { return a + (b - a) * t; },
  now() { return performance.now(); },
  readFileAsDataURL(file) {
    return new Promise((res, rej) => {
      const r = new FileReader();
      r.onerror = () => rej(new Error('FileReader failed'));
      r.onload = () => res(r.result);
      r.readAsDataURL(file);
    });
  },
  loadImage(src) {
    return new Promise((res, rej) => {
      const img = new Image();
      img.onload = () => res(img);
      img.onerror = (e) => rej(new Error('Image failed: ' + src));
      img.src = src;
    });
  }
};

// ---------------------- ASSET LOADER ----------------------
const AssetLoader = (() => {
  async function tryLoadDefaultAssets() {
    // attempt to load default images if available; failures are non-fatal
    const tries = [];
    tries.push(Utils.loadImage(CONFIG.defaultPaths.raccoon).then(img => { appState.assets.raccoonImage = img; }).catch(()=>{}));
    tries.push(Utils.loadImage(CONFIG.defaultPaths.treeSheet).then(img => { appState.assets.treeSheet = img; }).catch(()=>{}));
    // try season images (full size for center tree)
    for (const s of CONFIG.seasons) {
      tries.push(Utils.loadImage(`${CONFIG.defaultPaths.seasonFolder}${s}_in_out.png`).then(img => { if (!appState.assets.seasonImages[s]) appState.assets.seasonImages[s] = img; }).catch(()=>{}));
      tries.push(Utils.loadImage(`${CONFIG.defaultPaths.seasonFolder}${s}.png`).then(img => { if (!appState.assets.seasonImages[s]) appState.assets.seasonImages[s] = img; }).catch(()=>{}));
      // load small versions for side trees
      tries.push(Utils.loadImage(`${CONFIG.defaultPaths.seasonFolder}${s}_small.png`).then(img => { appState.assets.seasonImagesSmall[s] = img; }).catch(()=>{}));
    }
    await Promise.all(tries);
  }

  async function loadRaccoonFromFile(file) {
    const url = await Utils.readFileAsDataURL(file);
    const img = await Utils.loadImage(url);
    appState.assets.raccoonImage = img;
    console.log('Raccoon image loaded');
  }

  async function loadTreeSheetFromFile(file) {
    const url = await Utils.readFileAsDataURL(file);
    const img = await Utils.loadImage(url);
    appState.assets.treeSheet = img;
    await createTreeCropsAsync(img);
    console.log('Tree sheet loaded');
  }

  async function loadSeasonImagesFromFiles(files) {
    const seasons = CONFIG.seasons;
    for (let i = 0; i < files.length && i < seasons.length; i++) {
      try {
        const url = await Utils.readFileAsDataURL(files[i]);
        const img = await Utils.loadImage(url);
        appState.assets.seasonImages[seasons[i]] = img;
      } catch (e) {
        console.warn('season image load failed', e);
      }
    }
    console.log('Season images loaded');
  }

  async function loadSeasonSmallImagesFromFiles(files) {
    const seasons = CONFIG.seasons;
    for (let i = 0; i < files.length && i < seasons.length; i++) {
      try {
        const url = await Utils.readFileAsDataURL(files[i]);
        const img = await Utils.loadImage(url);
        appState.assets.seasonImagesSmall[seasons[i]] = img;
      } catch (e) {
        console.warn('season small image load failed', e);
      }
    }
    console.log('Season small images (side trees) loaded');
  }

  async function loadSeasonCenterImagesFromFiles(files) {
    const seasons = CONFIG.seasons;
    for (let i = 0; i < files.length && i < seasons.length; i++) {
      try {
        const url = await Utils.readFileAsDataURL(files[i]);
        const img = await Utils.loadImage(url);
        appState.assets.seasonImages[seasons[i]] = img;
      } catch (e) {
        console.warn('season center image load failed', e);
      }
    }
    console.log('Season center images loaded');
  }

  return { tryLoadDefaultAssets, loadRaccoonFromFile, loadSeasonSmallImagesFromFiles, loadSeasonCenterImagesFromFiles, loadSeasonImagesFromFiles };
})();

// ---------------------- ENVIRONMENT SYSTEM ----------------------
const Environment = (() => {
  // compute season from date when not manual
  function computeSeason(date) {
    if (appState.manualSeason) return appState.season;
    const month = date.getMonth() + 1;
    if ([12,1,2].includes(month)) return 'summer';
    if ([3,4,5].includes(month)) return 'spring';
    if ([6,7,8].includes(month)) return 'winter';
    return 'autumn';
  }

  function computeDayNight(hour) {
    return (hour >= 18 || hour < 6) ? 'night' : 'day';
  }

  // simplified weather placeholder (deterministic seed-based)
  function computeWeather(hour, season, date) {
    if (appState.manualWeather) return appState.weather;
    // deterministic seed using date and hour
    const seed = Math.abs(Math.sin((date.getDate()*7 + date.getMonth()*13 + Math.floor(hour)*17))) ;
    if (seed < 0.2) return 'clear';
    if (seed < 0.6) return 'cloudy';
    if (seed < 0.85) return (season === 'winter') ? 'snow' : 'rain';
    return 'storm';
  }

  // exposed API
  return { computeSeason, computeDayNight, computeWeather };
})();

// ---------------------- RACCOON SYSTEM ----------------------
class Raccoon {
  constructor(state) {
    this.state = state; // reference to appState.raccoon
    this.pixelX = 0;
    this.bounceOffset = 0;
    this.frame = 0;
    this.flip = false;
  }

  update(dt, centerTargetX, canvasWidth) {
    this.frame++;
    const targetPercent = (this.state.x);
    // if hiding, snap to centerTargetX percent
    if (this.state.state === 'hiding') {
      // convert centerTargetX px -> percent
      const targetP = (centerTargetX / canvasWidth) * 100;
      this.state.x = Utils.lerp(this.state.x, targetP, Utils.clamp(dt * 0.01 * (this.state.speed*100), 0, 1));
    } else if (this.state.state === 'walking') {
      // walking moves toward targetPercent (no external target here)
      // For UI-driven walking we respect state.x on user change
      this.state.x = Utils.clamp(this.state.x, 0, 100);
    }

    // compute pixelX for rendering
    this.pixelX = (this.state.x / 100) * canvasWidth;

    // bounce animation
    if (this.state.state === 'walking') {
      if (this.frame % 15 === 0) this.bounceOffset = this.bounceOffset === 0 ? -20 : 0;
    } else {
      if (this.frame % 45 === 0) this.bounceOffset = this.bounceOffset === 0 ? -8 : 0;
    }
  }

  draw(ctx, groundY, img) {
    if (!img) return;
    const spriteW = 260, spriteH = 260;
    ctx.save();
    ctx.translate(this.pixelX, groundY + this.bounceOffset);
    ctx.scale(this.state.scale, this.state.scale);
    if (this.flip) ctx.scale(-1,1);
    ctx.drawImage(img, -spriteW/2, -spriteH + 110, spriteW, spriteH);
    ctx.restore();
  }
}

// ---------------------- RENDERER ----------------------
const Renderer = (() => {
  let rafId = null;
  const metrics = { fps: 0, last: performance.now(), frames: 0 };
  let raccoonAgent = new Raccoon(appState.raccoon);

  // offscreen canvas for bottom pixel detection
  const off = document.createElement('canvas');
  const offCtx = off.getContext('2d');

  function resize() {
    DOM.canvas.width = window.innerWidth;
    DOM.canvas.height = window.innerHeight;
  }

  function getBottomInRegion(img, sx, sy, sw, sh) {
    // safe: if image not loaded, return sh-1
    if (!img || !img.naturalWidth) return Math.floor(sh) - 1;
    const sxI = Math.max(0, Math.floor(sx));
    const syI = Math.max(0, Math.floor(sy));
    const w = Math.max(1, Math.floor(sw));
    const h = Math.max(1, Math.floor(sh));
    off.width = w; off.height = h;
    try {
      offCtx.clearRect(0,0,w,h);
      offCtx.drawImage(img, sxI, syI, w, h, 0,0,w,h);
      const d = offCtx.getImageData(0,0,w,h).data;
      for (let y = h-1; y >= 0; y--) {
        for (let x = 0; x < w; x++) {
          const i = (y*w + x) * 4;
          if (d[i+3] > 10) return y;
        }
      }
    } catch (e) {
      // canvas tainted or other - fallback
    }
    return h-1;
  }

  // reuse existing drawSprite function (ASCII art) from old code (kept small)
  function drawSprite(sprite, startX, startY, scale, season) {
    for (let y = 0; y < sprite.length; y++) {
      const row = sprite[y];
      for (let x = 0; x < row.length; x++) {
        const char = row[x];
        if (char === 'T') continue;
        const drawX = x;
        ctx.fillStyle = getColor(char, season);
        ctx.fillRect(startX + drawX * scale, startY + y * scale, scale, scale);
      }
    }
  }

  // Bring in color tables from previous implementation (kept small)
  const SEASON_COLORS = {
    spring: { grass1: '#55efc4', grass2: '#00b894', leafM: '#fd79a8', leafN: '#e84393', leafE: '#d63031' },
    summer: { grass1: '#78e08f', grass2: '#38ada9', leafM: '#2ecc71', leafN: '#27ae60', leafE: '#1e8449' },
    autumn: { grass1: '#e58e26', grass2: '#b71540', leafM: '#f39c12', leafN: '#d35400', leafE: '#e67e22' },
    winter: { grass1: '#dfe6e9', grass2: '#b2bec3', leafM: '#ecf0f1', leafN: '#bdc3c7', leafE: '#95a5a6' }
  };

  const BASE_COLORS = { T:null, K:'#1e272e', B:'#834c32', D:'#5c3a21', S:'#f1c40f', O:'#e67e22', C:'#f5f6fa', Y:'#ffffff', V:'#dcdde1', I:'#7f8fa6', G:'#a5b1c2', A:'#485460', R:'#ff9ff3', P:'#f368e0', F:'#e74c3c' };
  function getColor(char, season){ if (BASE_COLORS[char]!==undefined) return BASE_COLORS[char]; const sc = SEASON_COLORS[season]; if (char==='M') return sc.leafM; if (char==='N') return sc.leafN; if (char==='E') return sc.leafE; return '#000'; }

  // Keep a small set of ASCII sprites (trimmed)
  const TREE = [ 'TTTTTTTTTTKKKKKKTTTTTTTTTT','TTTTTTTKKKMMMMMMKKKTTTTTTT','TTTTTKKMMMMMMMMMMMMKKTTTTT','TTTTKMMMMMMNNNNMMMMMMKTTTT','TTTKMMMMMNNNNNNNNMMMMMKTTT','TTKMMMMMNNNNNNNNNNMMMMMKTT','TKMMMMMNNNNNNNNNNNNMMMMKTT','TKMMMMNNNNNNNNNNNNNNMMMMKT','KMMMMNNNNNNNNNNNNNNNNMMMMK' ];

  // Main update and render separation
  function update(dt) {
    // time handling
    if (!appState.manualTime) {
      const now = new Date();
      appState.time = now.getHours() + now.getMinutes() / 60;
    } else {
      appState.time = parseFloat(DOM.timeSlider.value);
    }

    // season & weather
    const season = Environment.computeSeason(new Date());
    appState.season = season;
    appState.weather = Environment.computeWeather(appState.time, appState.season, new Date());

    // update raccoon
    // centerHoleX computed by render pass; approximate with center x for movement
    const centerPx = DOM.canvas.width/2;
    raccoonAgent.update(dt, centerPx, DOM.canvas.width);
  }

  function render() {
    const now = performance.now();
    metrics.frames++;
    if (now - metrics.last >= 1000) { metrics.fps = metrics.frames; metrics.frames = 0; metrics.last = now; appState.debug.fps = metrics.fps; }

    // clear
    ctx.clearRect(0,0,DOM.canvas.width, DOM.canvas.height);

    // draw sky
    const h = appState.time;
    const isNight = h >=18 || h < 6;
    const themeTop = isNight ? '#000' : '#0984e3';
    ctx.fillStyle = isNight ? '#0f1423' : '#74b9ff';
    ctx.fillRect(0,0,DOM.canvas.width, DOM.canvas.height);

    const groundY = DOM.canvas.height * 0.75;

    // grass
    ctx.fillStyle = SEASON_COLORS[appState.season].grass2;
    ctx.fillRect(0, groundY, DOM.canvas.width, DOM.canvas.height - groundY);

    // side trees - use small season images when available
    const sideImg = appState.assets.seasonImagesSmall[appState.season];
    if (sideImg) {
      const desiredSideWidth = Math.min(DOM.canvas.width * 0.12, 260);
      const sideScale = desiredSideWidth / sideImg.naturalWidth;
      const sideW = sideImg.naturalWidth * sideScale;
      const sideH = sideImg.naturalHeight * sideScale;
      const bottom = getBottomInRegion(sideImg, 0, 0, sideImg.naturalWidth, sideImg.naturalHeight);
      const nudge = appState.positions.sheetBottomNudge || 0;
      
      // left tree
      const lx = (appState.positions.tree1/100) * DOM.canvas.width - sideW/2;
      const ly = groundY - bottom * sideScale + nudge;
      ctx.drawImage(sideImg, lx, ly, sideW, sideH);
      
      // right tree
      const rx = (appState.positions.tree2/100) * DOM.canvas.width - sideW/2;
      const ry = groundY - bottom * sideScale + nudge;
      ctx.drawImage(sideImg, rx, ry, sideW, sideH);
    } else {
      drawSprite(TREE, (appState.positions.tree1/100)*DOM.canvas.width, groundY - 120, 8, appState.season);
      drawSprite(TREE, (appState.positions.tree2/100)*DOM.canvas.width, groundY - 120, 8, appState.season);
    }

    // center tree - use season images
    let centerHoleX = DOM.canvas.width/2;
    if (appState.assets.seasonImages[appState.season]) {
      const img = appState.assets.seasonImages[appState.season];
      const desiredWidth = Math.min(DOM.canvas.width * 0.28, 520);
      const scale = desiredWidth / img.naturalWidth;
      const imgW = img.naturalWidth * scale; 
      const imgH = img.naturalHeight * scale;
      const cx = DOM.canvas.width/2 - imgW/2;
      const bottom = getBottomInRegion(img, 0, 0, img.naturalWidth, img.naturalHeight);
      const cy = groundY - bottom * scale + appState.positions.centerTreeYOffset + (appState.positions.sheetBottomNudge || 0);
      ctx.drawImage(img, cx, cy, imgW, imgH);
      centerHoleX = cx + imgW * 0.5;
    } else {
      drawSprite(TREE, DOM.canvas.width/2 - 120, groundY - 160 + appState.positions.centerTreeYOffset, 9, appState.season);
    }

    // draw bonfire
    // simplified burn circle for night
    if (appState.time >= 18 || appState.time < 6) {
      ctx.fillStyle = 'rgba(230,126,34,0.2)';
      ctx.beginPath(); ctx.arc((appState.positions.bonfire/100)*DOM.canvas.width + 33, groundY - 10, 90, 0, Math.PI*2); ctx.fill();
    }

    // draw raccoon
    const raccoonImg = appState.assets.raccoonImage || appState.assets.seasonImages[appState.season];
    raccoonAgent.draw(ctx, groundY, raccoonImg);

    // debug overlays
    ctx.fillStyle = 'white'; ctx.font = '12px monospace'; ctx.fillText(`FPS: ${appState.debug.fps}`, 10, 20);
  }

  function loop(ts) {
    const dt = ts - (appState.debug.lastFrameTime || ts);
    appState.debug.lastFrameTime = ts;
    update(dt);
    render();
    rafId = requestAnimationFrame(loop);
  }

  function start() { resize(); window.addEventListener('resize', resize); rafId = requestAnimationFrame(loop); }
  function stop() { if (rafId) cancelAnimationFrame(rafId); }

  return { start, stop };
})();

// ---------------------- UI CONTROLLER ----------------------
const UI = (() => {
  function bindEvents() {
    // toggle panel
    DOM.uiToggle.addEventListener('click', () => DOM.uiPanel.classList.toggle('open'));

    // time controls
    DOM.overrideTime.addEventListener('change', (e) => { appState.manualTime = e.target.checked; DOM.timeSlider.classList.toggle('hidden', !e.target.checked); });
    DOM.timeSlider.addEventListener('input', (e) => { appState.time = parseFloat(e.target.value); DOM.timeDisplay.innerText = formatTime(appState.time); });

    // season
    DOM.overrideSeason.addEventListener('change', (e) => { appState.manualSeason = e.target.checked; DOM.seasonSelect.classList.toggle('hidden', !e.target.checked); });
    DOM.seasonSelect.addEventListener('change', (e) => { appState.season = e.target.value; });

    // weather
    DOM.overrideWeather.addEventListener('change', (e) => { appState.manualWeather = e.target.checked; DOM.weatherSelect.classList.toggle('hidden', !e.target.checked); });
    DOM.weatherSelect.addEventListener('change', (e) => { appState.weather = e.target.value; });

    // moon/clouds
    DOM.showMoon.addEventListener('change', (e) => { appState.showMoon = e.target.checked; });
    DOM.showClouds.addEventListener('change', (e) => { appState.showClouds = e.target.checked; });

    // raccoon controls
    DOM.raccoonStateSelect.addEventListener('change', (e) => { appState.raccoon.state = e.target.value; });
    DOM.raccoonSpeed.addEventListener('input', (e) => { appState.raccoon.speed = parseFloat(e.target.value); });
    DOM.raccoonScale.addEventListener('input', (e) => { appState.raccoon.scale = parseFloat(e.target.value); });
    DOM.raccoonX.addEventListener('input', (e) => { appState.raccoon.x = parseFloat(e.target.value); });

    // image uploads
    DOM.raccoonImageInput.addEventListener('change', async (e) => { if (e.target.files[0]) await AssetLoader.loadRaccoonFromFile(e.target.files[0]); });
    DOM.seasonSmallImagesInput.addEventListener('change', async (e) => { if (e.target.files.length) await AssetLoader.loadSeasonSmallImagesFromFiles(e.target.files); });
    DOM.seasonCenterImagesInput.addEventListener('change', async (e) => { if (e.target.files.length) await AssetLoader.loadSeasonCenterImagesFromFiles(e.target.files); });

    // positions
    DOM.tree1X.addEventListener('input', (e)=>{ appState.positions.tree1 = parseFloat(e.target.value); });
    DOM.tree2X.addEventListener('input', (e)=>{ appState.positions.tree2 = parseFloat(e.target.value); });
    DOM.bonfireX.addEventListener('input', (e)=>{ appState.positions.bonfire = parseFloat(e.target.value); });

    // center tree Y
    DOM.centerTreeY.addEventListener('input', (e)=>{ appState.positions.centerTreeYOffset = parseInt(e.target.value); DOM.centerTreeYVal.innerText = appState.positions.centerTreeYOffset + 'px'; });
    DOM.saveCenterTree.addEventListener('click', ()=>{ localStorage.setItem(CONFIG.storageKeys.centerTreeYOffset, String(appState.positions.centerTreeYOffset)); });

    // sheet bottom nudge
    DOM.sheetBottomNudge.addEventListener('input', (e)=>{ appState.positions.sheetBottomNudge = parseInt(e.target.value); DOM.sheetBottomNudgeVal.innerText = appState.positions.sheetBottomNudge + 'px'; });
    DOM.saveSheetBottom.addEventListener('click', ()=>{ localStorage.setItem(CONFIG.storageKeys.sheetBottomNudge, String(appState.positions.sheetBottomNudge)); });
  }

  function syncUI() {
    // initial values
    DOM.timeSlider.value = appState.time;
    DOM.timeDisplay.innerText = formatTime(appState.time);
    DOM.seasonSelect.value = appState.season;
    DOM.weatherSelect.value = appState.weather;
    DOM.showMoon.checked = appState.showMoon;
    DOM.showClouds.checked = appState.showClouds;
    DOM.raccoonStateSelect.value = appState.raccoon.state;
    DOM.raccoonSpeed.value = appState.raccoon.speed;
    DOM.raccoonScale.value = appState.raccoon.scale;
    DOM.raccoonX.value = appState.raccoon.x;
    DOM.tree1X.value = appState.positions.tree1;
    DOM.tree2X.value = appState.positions.tree2;
    DOM.bonfireX.value = appState.positions.bonfire;
    DOM.centerTreeY.value = appState.positions.centerTreeYOffset; DOM.centerTreeYVal.innerText = appState.positions.centerTreeYOffset + 'px';
    DOM.sheetBottomNudge.value = appState.positions.sheetBottomNudge; DOM.sheetBottomNudgeVal.innerText = appState.positions.sheetBottomNudge + 'px';
  }

  function formatTime(h) { const hrs = Math.floor(h); const mins = Math.floor((h-hrs)*60); return `${String(hrs).padStart(2,'0')}:${String(mins).padStart(2,'0')}`; }

  return { bindEvents, syncUI };
})();

// ---------------------- STORAGE SYSTEM ----------------------
const Storage = {
  save(key, val) { localStorage.setItem(key, JSON.stringify(val)); },
  load(key, fallback) { try { const v = JSON.parse(localStorage.getItem(key)); return v === null ? fallback : v; } catch(e) { return fallback; } }
};

// ---------------------- INITIALIZATION ----------------------
async function init() {
  // bind UI
  UI.bindEvents();
  UI.syncUI();
  // try load defaults
  await AssetLoader.tryLoadDefaultAssets();
  // start renderer
  Renderer.start();
  console.log('App initialized');
}

window.addEventListener('load', init);
