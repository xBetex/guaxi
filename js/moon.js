// ============================================================
// js/moon.js — Moon phase logic & celestial drawing
// ============================================================

// Phase name → meta table
const PHASE_META = {
  "New Moon":       { waxing: true,  emoji: "🌑" },
  "Waxing Crescent":{ waxing: true,  emoji: "🌒" },
  "First Quarter":  { waxing: true,  emoji: "🌓" },
  "Waxing Gibbous": { waxing: true,  emoji: "🌔" },
  "Full Moon":      { waxing: false, emoji: "🌕" },
  "Waning Gibbous": { waxing: false, emoji: "🌖" },
  "Third Quarter":  { waxing: false, emoji: "🌗" },
  "Waning Crescent":{ waxing: false, emoji: "🌘" },
};

// Jean Meeus algorithm — accurate to ~1 day
function getMoonPhase() {
  const ref = new Date(Date.UTC(2000, 0, 6, 18, 14)); // known new moon
  const cycle = 29.53058770576;
  const days = (Date.now() - ref.getTime()) / 86400000;
  return (((days % cycle) + cycle) % cycle) / cycle; // 0=new … 0.5=full
}

async function fetchMoonPhase() {
  const CACHE_MS = 6 * 60 * 60 * 1000;
  try {
    const cached = JSON.parse(localStorage.getItem("guaxinim_moon") || "null");
    if (cached && cached.data && cached.data.illumination !== null && Date.now() - cached.at < CACHE_MS) {
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
      localStorage.setItem("guaxinim_moon", JSON.stringify({ data: moonData, at: moonFetchedAt }));
      updateWeatherBar();
    }
  } catch (e) {
    console.warn("Moon Phase API unavailable — using local Meeus calculation");
    const localPhase = getMoonPhase();
    const pn = localPhase < 0.03 || localPhase > 0.97 ? "Lua Nova"
      : localPhase < 0.24 ? "Crescente"
      : localPhase < 0.27 ? "Quarto Crescente"
      : localPhase < 0.49 ? "Gibosa Crescente"
      : localPhase < 0.51 ? "Lua Cheia"
      : localPhase < 0.74 ? "Gibosa Minguante"
      : localPhase < 0.77 ? "Quarto Minguante"
      : "Minguante";
    const pe = localPhase < 0.03 || localPhase > 0.97 ? "🌑"
      : localPhase < 0.25 ? "🌒"
      : localPhase < 0.27 ? "🌓"
      : localPhase < 0.49 ? "🌔"
      : localPhase < 0.51 ? "🌕"
      : localPhase < 0.74 ? "🌖"
      : localPhase < 0.77 ? "🌗"
      : "🌘";
    moonData = { phase: pn, illumination: localPhase * 100, emoji: pe };
    moonFetchedAt = Date.now();
  }
}

// ─── Off-screen celestial canvas ─────────────────────────────
const _celestialCanvas = document.createElement("canvas");
const _celestialCtx    = _celestialCanvas.getContext("2d");

function drawPixelatedCelestial(drawFn, cx, cy, r) {
  const low = 32;
  _celestialCanvas.width  = low;
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

// ─── Sun ─────────────────────────────────────────────────────
function drawSun(cx, cy, r, targetCtx = ctx) {
  const g = targetCtx;
  const t = Date.now() / 16000; // ultra-slow ray rotation
  g.save();
  g.translate(cx, cy);

  // Rays (alternating long/short)
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

  // Sun disk
  g.fillStyle = "#ffca28";
  g.beginPath();
  g.arc(0, 0, r, 0, Math.PI * 2);
  g.fill();
  g.restore();
}

// ─── Moon phase ───────────────────────────────────────────────
// FIX: New Moon now draws a dark disk with a faint luminous rim
// so it's clearly visible against the night sky, not invisible.
function drawMoonPhase(cx, cy, r, targetCtx = ctx) {
  const g = targetCtx;
  const localPhase = getMoonPhase();
  const illum = (1 - Math.cos(localPhase * Math.PI * 2)) / 2;
  const waxing = localPhase <= 0.5;

  const termScale = 1 - 2 * illum;
  const DEAD_BAND = 0.02;

  const moonLight  = "#ecf0f1";
  const moonShadow = "#04041a";

  g.save();

  // Base dark disk — always drawn
  g.fillStyle = moonShadow;
  g.beginPath();
  g.arc(cx, cy, r, 0, Math.PI * 2);
  g.fill();

  // FIX: New Moon — draw a subtle grey rim so it's visible against the sky
  if (illum < 0.01) {
    g.strokeStyle = "rgba(180,190,210,0.35)";
    g.lineWidth = Math.max(1, r * 0.08);
    g.beginPath();
    g.arc(cx, cy, r * 0.88, 0, Math.PI * 2);
    g.stroke();
    g.restore();
    return;
  }

  // Clip all lit drawing to the disk boundary
  g.save();
  g.beginPath();
  g.arc(cx, cy, r, 0, Math.PI * 2);
  g.clip();

  if (waxing) {
    // 🌒 🌓 🌔 Waxing: right half is the lit limb
    g.fillStyle = moonLight;
    g.fillRect(cx, cy - r, r + 2, r * 2);
    if (termScale > DEAD_BAND) {
      // Crescent — dark ellipse trims the right lit area
      g.fillStyle = moonShadow;
      g.save(); g.translate(cx, cy); g.scale(termScale, 1);
      g.fillRect(0, -r, r + 2, r * 2);
      g.restore();
    } else if (termScale < -DEAD_BAND) {
      // Gibbous — lit ellipse extends into the left dark area
      g.fillStyle = moonLight;
      g.save(); g.translate(cx, cy); g.scale(-termScale, 1);
      g.fillRect(-(r + 2), -r, r + 2, r * 2);
      g.restore();
    }
  } else {
    // 🌖 🌗 🌘 Waning: left half is the lit limb
    g.fillStyle = moonLight;
    g.fillRect(cx - r - 2, cy - r, r + 2, r * 2);
    const wts = -termScale;
    if (wts > DEAD_BAND) {
      g.fillStyle = moonLight;
      g.save(); g.translate(cx, cy); g.scale(wts, 1);
      g.fillRect(0, -r, r + 2, r * 2);
      g.restore();
    } else if (wts < -DEAD_BAND) {
      g.fillStyle = moonShadow;
      g.save(); g.translate(cx, cy); g.scale(-wts, 1);
      g.fillRect(-(r + 2), -r, r + 2, r * 2);
      g.restore();
    }
  }

  g.restore(); // remove clip
  g.restore();
}
