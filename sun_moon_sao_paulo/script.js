/* =========================================================
   Lunar-year scroll visualizer — Anália Franco • São Paulo
   ========================================================= */

"use strict";

// ── Canvas setup ──────────────────────────────────────────
const canvas = document.getElementById("scene");
const ctx = canvas.getContext("2d");

// Offscreen logical canvas (320×180 pixel-art grid)
const off = document.createElement("canvas");
off.width = 320;
off.height = 180;
const g = off.getContext("2d");

function resize() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}
window.addEventListener("resize", resize);
resize();

// ── Moon constants ────────────────────────────────────────
const MCX = 160; // moon centre X on 320-wide grid
const MCY = 68; // moon centre Y
const MR = 62; // moon radius
const MSZ = MR * 2 + 2; // 126 — bounding box side

// ── Pre-compute the lit-side texture (MOON_LIT) ───────────
const MOON_LIT = new Uint8ClampedArray(MSZ * MSZ * 4);

(function buildMoonTexture() {
  const MARES = [
    { x: 0.07, y: -0.16, r: 0.3 },
    { x: -0.22, y: 0.1, r: 0.24 },
    { x: 0.33, y: -0.04, r: 0.17 },
  ];
  const CRATERS = [
    { x: 0.2, y: -0.28, r: 0.16 },
    { x: -0.32, y: 0.22, r: 0.11 },
    { x: 0.48, y: 0.3, r: 0.09 },
    { x: -0.12, y: -0.5, r: 0.08 },
    { x: 0.15, y: 0.52, r: 0.07 },
    { x: -0.48, y: -0.08, r: 0.1 },
    { x: 0.05, y: 0.12, r: 0.05 },
  ];

  for (let py = 0; py < MSZ; py++) {
    for (let px = 0; px < MSZ; px++) {
      // Normalise to [-1, 1] relative to moon centre
      const dx = (px - MR) / MR;
      const dy = (py - MR) / MR;
      const dist2 = dx * dx + dy * dy;

      if (dist2 > 1.0) {
        // Outside circle — transparent
        const i = (py * MSZ + px) * 4;
        MOON_LIT[i + 3] = 0;
        continue;
      }

      let b = 0.92;

      // Mare (dark seas)
      for (const m of MARES) {
        const mdx = dx - m.x;
        const mdy = dy - m.y;
        const d = Math.sqrt(mdx * mdx + mdy * mdy);
        if (d < m.r) {
          const t = d / m.r;
          b -= (1 - t * t) * 0.14;
        }
      }

      // Craters
      for (const c of CRATERS) {
        const cdx = dx - c.x;
        const cdy = dy - c.y;
        const d = Math.sqrt(cdx * cdx + cdy * cdy);
        const t = d / c.r;
        if (t < 1.4) {
          // bright rim
          b += Math.exp(-((t - 0.88) * (t - 0.88)) / 0.015) * 0.07;
          // dark floor
          if (t < 1.0) b -= (1 - t) * 0.09;
        }
      }

      // Subtle texture
      b +=
        Math.sin(dx * 7.5 + dy * 5.2) * 0.015 +
        Math.cos(dx * 3.1 - dy * 4.8) * 0.01;

      // Limb darkening
      b *= 0.8 + 0.2 * Math.pow(1 - dist2, 0.3);

      // Clamp
      b = Math.max(0.55, Math.min(1.0, b));

      const i = (py * MSZ + px) * 4;
      MOON_LIT[i] = (b * 245) | 0;
      MOON_LIT[i + 1] = (b * 234) | 0;
      MOON_LIT[i + 2] = (b * 208) | 0;
      MOON_LIT[i + 3] = 255;
    }
  }
})();

// Persistent offscreen canvas for the moon ImageData
const moonOff = document.createElement("canvas");
moonOff.width = MSZ;
moonOff.height = MSZ;
const moonCtx = moonOff.getContext("2d");

// ── Stars ─────────────────────────────────────────────────
const STAR_COUNT = 200;
const stars = [];
(function buildStars() {
  for (let i = 0; i < STAR_COUNT; i++) {
    stars.push({
      x: (Math.random() * 320) | 0,
      y: (Math.random() * 105) | 0,
      s: Math.random() < 0.1 ? 2 : 1,
      p: Math.random() * Math.PI * 2,
      sp: 0.008 + Math.random() * 0.025,
      b: 0.45 + Math.random() * 0.45,
    });
  }
})();

// ── Mountains ─────────────────────────────────────────────
const MHORIZON = 130;

const MOUNTAINS = [
  {
    fill: "#1c2d42",
    pts: [
      0, 130, 32, 93, 62, 100, 97, 80, 132, 96, 164, 77, 200, 91, 234, 83, 267,
      95, 294, 89, 320, 109, 320, 180, 0, 180,
    ],
  },
  {
    fill: "#0d1b2d",
    pts: [
      0, 130, 26, 112, 58, 107, 93, 116, 126, 101, 161, 115, 196, 103, 230, 115,
      263, 107, 297, 115, 320, 122, 320, 180, 0, 180,
    ],
  },
  {
    fill: "#06101e",
    pts: [
      0, 130, 23, 122, 53, 119, 86, 124, 119, 116, 153, 124, 189, 118, 224, 124,
      259, 119, 293, 124, 320, 128, 320, 180, 0, 180,
    ],
  },
];

// ── Portuguese helpers ────────────────────────────────────
const MONTHS = [
  "Janeiro",
  "Fevereiro",
  "Março",
  "Abril",
  "Maio",
  "Junho",
  "Julho",
  "Agosto",
  "Setembro",
  "Outubro",
  "Novembro",
  "Dezembro",
];

function phaseName(phase) {
  if (phase < 0.025 || phase > 0.975) return "🌑\u2002Lua Nova";
  if (phase < 0.24) return "🌒\u2002Lua Crescente";
  if (phase < 0.27) return "🌓\u2002Quarto Crescente";
  if (phase < 0.49) return "🌔\u2002Gibosa Crescente";
  if (phase < 0.51) return "🌕\u2002Lua Cheia";
  if (phase < 0.74) return "🌖\u2002Gibosa Minguante";
  if (phase < 0.77) return "🌗\u2002Quarto Minguante";
  return "🌘\u2002Lua Minguante";
}

// ── Time state ────────────────────────────────────────────
const START = new Date(2025, 0, 1);
let targetDay = 0;
let displayDay = 0;
let hintOpacity = 1;
let scrolled = false;

// ── Draw helpers ─────────────────────────────────────────

function drawSky(fraction) {
  const mb = (fraction * 8) | 0;
  const grad = g.createLinearGradient(0, 0, 0, MHORIZON);
  grad.addColorStop(0, `rgb(${2 + mb},${5 + mb},${12 + mb * 2})`);
  grad.addColorStop(0.55, `rgb(${4 + mb},${10 + mb * 2},${22 + mb * 3})`);
  grad.addColorStop(1, `rgb(${8 + mb},${18 + mb * 2},${36 + mb * 4})`);
  g.fillStyle = grad;
  g.fillRect(0, 0, 320, MHORIZON);

  // Ground
  g.fillStyle = "rgb(3,7,14)";
  g.fillRect(0, MHORIZON, 320, 180 - MHORIZON);
}

function drawStars(fraction) {
  const vis = Math.max(0, 1 - fraction * 0.65);
  for (const star of stars) {
    star.p += star.sp;
    const a = vis * star.b * (0.5 + 0.5 * Math.sin(star.p));
    if (a > 0.05) {
      const v = (a * 255) | 0;
      g.fillStyle = `rgb(${v},${v},${(v * 0.95) | 0})`;
      g.fillRect(star.x, star.y, star.s, star.s);
    }
  }
}

/**
 * Returns true if the pixel at (dx, dy) [normalised –1..1] is on the lit side.
 * Southern Hemisphere orientation (São Paulo).
 */
function isPixelLit(dx, dy, fraction, phase) {
  if (fraction <= 0.015) return false;
  if (fraction >= 0.985) return true;
  const maxX = Math.sqrt(Math.max(0, 1 - dy * dy));
  const waxing = phase < 0.5;
  if (waxing) {
    // SH crescent on LEFT — grows from left
    return dx <= (2 * fraction - 1) * maxX;
  } else {
    // SH crescent on RIGHT — shrinks toward right
    return dx >= (1 - 2 * fraction) * maxX;
  }
}

function drawMoon(fraction, phase) {
  // Atmospheric glow (drawn on the offscreen BEFORE the moon body)
  const glowOuter = MR * (1.8 + fraction * 0.7);
  const glowGrad = g.createRadialGradient(
    MCX,
    MCY,
    MR * 0.7,
    MCX,
    MCY,
    glowOuter,
  );
  glowGrad.addColorStop(0, `rgba(220,205,170,${(fraction * 0.2).toFixed(3)})`);
  glowGrad.addColorStop(1, "rgba(220,205,170,0)");
  g.fillStyle = glowGrad;
  const gr = glowOuter + 2;
  g.fillRect(MCX - gr, MCY - gr, gr * 2, gr * 2);

  // Build pixel-art moon ImageData
  const imgData = moonCtx.createImageData(MSZ, MSZ);
  const data = imgData.data;

  const es = Math.max(0, 0.12 - fraction * 0.4) * 255;
  const darkR = (4 + es * 0.3) | 0;
  const darkG = (7 + es * 0.5) | 0;
  const darkB = (15 + es * 0.8) | 0;

  for (let py = 0; py < MSZ; py++) {
    for (let px = 0; px < MSZ; px++) {
      const i = (py * MSZ + px) * 4;
      const src = MOON_LIT[i + 3]; // alpha from precomputed texture

      if (src === 0) {
        // Outside circle — transparent
        data[i + 3] = 0;
        continue;
      }

      const dx = (px - MR) / MR;
      const dy = (py - MR) / MR;

      if (isPixelLit(dx, dy, fraction, phase)) {
        data[i] = MOON_LIT[i];
        data[i + 1] = MOON_LIT[i + 1];
        data[i + 2] = MOON_LIT[i + 2];
        data[i + 3] = 255;
      } else {
        data[i] = darkR;
        data[i + 1] = darkG;
        data[i + 2] = darkB;
        data[i + 3] = 255;
      }
    }
  }

  moonCtx.putImageData(imgData, 0, 0);
  g.drawImage(moonOff, MCX - MR, MCY - MR);
}

function drawMountains() {
  for (const layer of MOUNTAINS) {
    g.fillStyle = layer.fill;
    g.beginPath();
    g.moveTo(layer.pts[0], layer.pts[1]);
    for (let i = 2; i < layer.pts.length; i += 2) {
      g.lineTo(layer.pts[i], layer.pts[i + 1]);
    }
    g.closePath();
    g.fill();
  }
}

// ── HUD update ────────────────────────────────────────────
const elDate = document.getElementById("info-date");
const elPhase = document.getElementById("info-phase");
const elIllum = document.getElementById("info-illum");
const elFill = document.getElementById("progress-fill");
const elLabel = document.getElementById("progress-label");
const elHint = document.getElementById("scroll-hint");

function updateHUD(date, illum) {
  const { fraction, phase } = illum;
  const d = date.getDate();
  const m = MONTHS[date.getMonth()];
  const y = date.getFullYear();

  elDate.textContent = `${d} de ${m} de ${y}`;
  elPhase.textContent = phaseName(phase);
  elIllum.textContent = `${(fraction * 100).toFixed(0)}% iluminada`;

  elFill.style.width = `${phase * 100}%`;

  const dayInCycle = phase * 29.53059;
  const dayNum = (dayInCycle + 1) | 0;
  elLabel.textContent = `Dia ${dayNum} de 30 no ciclo lunar`;
}

// ── Main loop ─────────────────────────────────────────────
function loop() {
  requestAnimationFrame(loop);

  // Smooth scroll
  displayDay += (targetDay - displayDay) * 0.1;

  // Date at 22:00
  const dayFloor = Math.floor(displayDay);
  const date = new Date(START.getTime() + dayFloor * 86400000);
  date.setHours(22, 0, 0, 0);

  const illum = SunCalc.getMoonIllumination(date);
  const fraction = illum.fraction;
  const phase = illum.phase;

  // Draw offscreen
  drawSky(fraction);
  drawStars(fraction);
  drawMoon(fraction, phase);
  drawMountains();

  // Blit to main canvas (no smoothing = crisp pixels)
  ctx.imageSmoothingEnabled = false;
  ctx.drawImage(off, 0, 0, canvas.width, canvas.height);

  // HUD
  updateHUD(date, illum);

  // Scroll hint fade
  if (scrolled && hintOpacity > 0) {
    hintOpacity = Math.max(0, hintOpacity - 0.015);
    elHint.style.opacity = hintOpacity;
  }
}

// ── Input ─────────────────────────────────────────────────

// Mouse wheel
window.addEventListener(
  "wheel",
  (e) => {
    e.preventDefault();
    targetDay = Math.max(0, targetDay + e.deltaY / 80);
    if (!scrolled) scrolled = true;
  },
  { passive: false },
);

// Touch
let touchPrevY = 0;
window.addEventListener(
  "touchstart",
  (e) => {
    touchPrevY = e.touches[0].clientY;
  },
  { passive: true },
);
window.addEventListener(
  "touchmove",
  (e) => {
    e.preventDefault();
    const dy = touchPrevY - e.touches[0].clientY;
    targetDay = Math.max(0, targetDay + dy / 25);
    touchPrevY = e.touches[0].clientY;
    if (!scrolled) scrolled = true;
  },
  { passive: false },
);

// Keyboard
window.addEventListener("keydown", (e) => {
  if (e.key === "ArrowRight" || e.key === "ArrowDown") {
    targetDay += 1;
    if (!scrolled) scrolled = true;
  } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
    targetDay = Math.max(0, targetDay - 1);
    if (!scrolled) scrolled = true;
  }
});

// ── Kick off ──────────────────────────────────────────────
loop();
