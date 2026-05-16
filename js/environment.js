// ============================================================
// js/environment.js — Particles, draw utilities, terrain drawing
// ============================================================

// ─── Particles ────────────────────────────────────────────────
let grassBlades = [];
function initGrass() {
  grassBlades = Array.from({ length: 300 }, () => ({
    x:        Math.random() * window.innerWidth * 2,
    height:   Math.random() * 15 + 5,
    width:    Math.random() * 4 + 2,
    isFlower: Math.random() > 0.95,
  }));
}

const fireflies = Array.from({ length: 25 }, () => ({
  x:      Math.random() * window.innerWidth,
  y:      Math.random() * window.innerHeight * 0.3 + window.innerHeight * 0.6,
  phase:  Math.random() * Math.PI * 2,
  speedX: (Math.random() - 0.5) * 0.5,
  speedY: (Math.random() - 0.5) * 0.5,
}));

const stars = Array.from({ length: 150 }, () => ({
  x:       Math.random(),
  y:       Math.random(),
  speed:   Math.random() * 0.05,
  twinkle: Math.random() * Math.PI * 2,
}));

const clouds = [
  { x: 10, y: 15, speed: 0.5, scale: 6 },
  { x: 50, y: 10, speed: 0.3, scale: 4 },
  { x: 80, y: 25, speed: 0.8, scale: 5 },
  { x: 20, y: 35, speed: 0.4, scale: 7 },
];

const snowflakes = Array.from({ length: 200 }, () => ({
  x:      Math.random() * window.innerWidth,
  y:      Math.random() * window.innerHeight,
  speedY: Math.random() * 1 + 0.5,
  speedX: (Math.random() - 0.5) * 0.5,
  size:   Math.random() * 3 + 1,
}));

const shootingStars = [];

// ─── Draw utilities ───────────────────────────────────────────
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

function drawBlockyMountain(centerX, groundY, peakHeight, baseWidth, colorShadow, colorLight, hasSnow) {
  const blockSize = 16;
  const steps     = Math.max(1, Math.floor(peakHeight / blockSize));
  const stepWidth = baseWidth / 2 / steps;
  for (let i = 0; i < steps; i++) {
    const cy  = groundY - i * blockSize;
    const chw = baseWidth / 2 - i * stepWidth;
    ctx.fillStyle = hasSnow && i > steps * 0.65 ? "#dfe6e9" : colorShadow;
    ctx.fillRect(centerX - chw, cy - blockSize, chw, blockSize);
    ctx.fillStyle = hasSnow && i > steps * 0.65 ? "#ffffff" : colorLight;
    ctx.fillRect(centerX, cy - blockSize, chw, blockSize);
  }
}

function drawRain(groundY, intensity) {
  const dropCount = Math.floor(100 + intensity * 200);
  ctx.strokeStyle = "rgba(255,255,255,0.12)"; ctx.lineWidth = 1;
  for (let i = 0; i < dropCount; i++) {
    const x = Math.random() * canvas.width, y = Math.random() * canvas.height;
    const len = 10 + Math.random() * 15;
    ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x - 4, y + len); ctx.stroke();
  }
  ctx.fillStyle = "rgba(255,255,255,0.05)";
  for (let i = 0; i < 15; i++) {
    const px = Math.random() * canvas.width, py = groundY + Math.random() * (canvas.height - groundY);
    ctx.beginPath(); ctx.arc(px, py, 6 + Math.random() * 10, 0, Math.PI * 2); ctx.fill();
  }
}

function drawSnow() {
  ctx.fillStyle = "rgba(255,255,255,0.8)";
  snowflakes.forEach((f) => {
    ctx.beginPath(); ctx.arc(f.x, f.y, f.size, 0, Math.PI * 2); ctx.fill();
    f.y += f.speedY * 0.45; f.x += f.speedX * 0.45;
    if (f.y > canvas.height) { f.y = -10; f.x = Math.random() * canvas.width; }
  });
}
