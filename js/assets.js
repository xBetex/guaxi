// ============================================================
// js/assets.js — Image loading, sprite-sheet helpers, bottom-pixel detection
// ============================================================

// ─── Off-screen canvas for pixel inspection ──────────────────
const _bottomCacheSheet = {};
const _bottomCacheImg   = {};
const _offscreen  = document.createElement("canvas");
const _offCtx     = _offscreen.getContext("2d");

function getBottomYFromRegion(img, sx, sy, sw, sh, cache, cacheKey) {
  if (cache[cacheKey] !== undefined) return cache[cacheKey];
  const sxI = Math.max(0, Math.floor(sx));
  const syI = Math.max(0, Math.floor(sy));
  const w   = Math.max(1, Math.floor(sw));
  const h   = Math.max(1, Math.floor(sh));
  _offscreen.width  = w;
  _offscreen.height = h;
  try {
    _offCtx.clearRect(0, 0, w, h);
    _offCtx.drawImage(img, sxI, syI, w, h, 0, 0, w, h);
    const data = _offCtx.getImageData(0, 0, w, h).data;
    const [bgR, bgG, bgB] = [data[0], data[1], data[2]];
    const threshold = 30;
    for (let y = h - 1; y >= 0; y--) {
      const base = y * w * 4;
      for (let x = 0; x < w; x++) {
        const b  = base + x * 4;
        const dr = data[b] - bgR, dg = data[b+1] - bgG, db2 = data[b+2] - bgB;
        if (data[b+3] > 10 || Math.sqrt(dr*dr + dg*dg + db2*db2) > threshold) {
          cache[cacheKey] = y; return y;
        }
      }
    }
  } catch (e) { console.warn("getBottomYFromRegion failed:", e && e.message); }
  cache[cacheKey] = h - 1;
  return h - 1;
}

// ─── Raccoon image ────────────────────────────────────────────
const raccoonImg = new Image();
raccoonImg.src = "assets/guaxinim_inteiro_transp.png";

// ─── Bonfire image ────────────────────────────────────────────
const bonfireImg = new Image();
let bonfireImgLoaded = false;
bonfireImg.onload  = () => { bonfireImgLoaded = true;  };
bonfireImg.onerror = () => { bonfireImgLoaded = false; };
bonfireImg.src = "assets/bonfire.png";

// ─── Trees sprite-sheet ───────────────────────────────────────
const treesSheet = new Image();
let treesSheetLoaded = false;
treesSheet.onload = () => {
  treesSheetLoaded = true;
  try {
    const shW = treesSheet.naturalWidth, shH = treesSheet.naturalHeight;
    const tW = shW / 4, tH = shH / 2;
    for (let col = 0; col < 4; col++)
      for (let row = 0; row < 2; row++)
        try { getBottomYFromRegion(treesSheet, col*tW, row*tH, tW, tH, _bottomCacheSheet, `${col}_${row}`); } catch (_) {}
  } catch (_) {}
};
treesSheet.onerror = () => { treesSheetLoaded = false; };
treesSheet.src = "assets/trees_sheet.png";

// ─── Per-season tree images ───────────────────────────────────
const treeImgs = {
  spring: { center: new Image(), centerIn: new Image(), small: new Image() },
  summer: { center: new Image(), centerIn: new Image(), small: new Image() },
  autumn: { center: new Image(), centerIn: new Image(), small: new Image() },
  winter: { center: new Image(), centerIn: new Image(), small: new Image() },
};

function loadTreeImages() {
  treeImgs.spring.center.src   = "assets/spring_out.png";
  treeImgs.summer.center.src   = "assets/summer_out.png";
  treeImgs.autumn.center.src   = "assets/autum_out.png";
  treeImgs.winter.center.src   = "assets/winter_out.png";

  treeImgs.spring.centerIn.src = "assets/spring_in.png";
  treeImgs.summer.centerIn.src = "assets/summer_in.png";
  treeImgs.autumn.centerIn.src = "assets/autum_in.png";
  treeImgs.winter.centerIn.src = "assets/winter_in.png";

  treeImgs.spring.small.src = "assets/spring_small.png";
  treeImgs.summer.small.src = "assets/summer_small.png";
  treeImgs.autumn.small.src = "assets/autum_small.png";
  treeImgs.winter.small.src = "assets/winter_small.png";

  Object.entries(treeImgs).forEach(([season, imgs]) => {
    Object.entries(imgs).forEach(([type, img]) => {
      img.onload = () => {
        try {
          if (img.complete && img.naturalWidth)
            getBottomYFromRegion(img, 0, 0, img.naturalWidth, img.naturalHeight, _bottomCacheImg, img.src);
        } catch (_) {}
        const btn = document.getElementById(`${season}-${type}-btn`);
        if (btn) { btn.classList.add("loaded"); btn.innerText = "OK"; }
      };
      img.onerror = () => {
        const btn = document.getElementById(`${season}-${type}-btn`);
        if (btn) { btn.innerText = "—"; btn.style.opacity = "0.5"; }
      };
    });
  });
}

// Hole placement fraction (raccoon hiding inside center tree)
const holeFrac = { x: 0.5, y: 0.76, r: 0.11 };
