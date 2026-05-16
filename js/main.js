// ============================================================
// js/main.js — Main game loop and initialization
// ============================================================

function resize() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  raccoonX = canvas.width / 2;
  initGrass();
}

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

  let centerHoleTarget = canvas.width / 2;
  const centerTreeX = canvas.width / 2 - 40;

  // ── Raccoon AI ──
  const isUncomfortable = weather === "rain" || weather === "storm" || weather === "snow";
  if (Date.now() > randomHoleTime + 15000)
    randomHoleTime = Date.now() + Math.random() * 50000 + 20000;
  const isRandomlyHiding = Date.now() > randomHoleTime && Date.now() < randomHoleTime + 15000;
  const shouldHide = isUncomfortable || isRandomlyHiding;

  if (shouldHide) {
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

  // ── 1. SKY ──
  const skyGrad = ctx.createLinearGradient(0, 0, 0, canvas.height * 0.8);
  skyGrad.addColorStop(0, theme.sky1);
  skyGrad.addColorStop(0.4, theme.sky2);
  skyGrad.addColorStop(1, theme.sky3);
  ctx.fillStyle = skyGrad;
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // ── 2. Weather darkness overlay ──
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

  // ── 3. Stars & shooting stars ──
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

  // ── 4. Sun or Moon ──
  const celestialR = Math.min(canvas.width, canvas.height) * 0.15;
  if (!isNight) {
    const tp = (h - 6) / 12;
    const sunCx = canvas.width * 0.1 + canvas.width * 0.8 * tp;
    const sunCy = canvas.height * 0.12 + Math.sin(tp * Math.PI) * -canvas.height * 0.06;
    drawPixelatedCelestial(drawSun, sunCx, sunCy, celestialR);
  } else {
    const nightH = h >= 18 ? h - 18 : h + 6;
    const tp = nightH / 12;
    const moonCx = canvas.width * 0.1 + canvas.width * 0.8 * tp;
    const moonCy = canvas.height * 0.16;
    drawPixelatedCelestial(drawMoonPhase, moonCx, moonCy, celestialR);
  }

  // ── 5. Clouds ──
  const windKmh = typeof weatherInfo.windspeed === "number" ? weatherInfo.windspeed : 8;
  const windFactor = Math.min(2.0, Math.max(0.4, windKmh / 20));
  const cloudList = weather !== "rain" && weather !== "storm" && weather !== "snow"
    ? clouds
    : clouds.concat([
        { x: 35, y: 18, speed: 0.35, scale: 5 },
        { x: 70, y: 22, speed: 0.45, scale: 6 },
      ]);
  cloudList.forEach((c) => {
    c.x += c.speed * 0.2 * windFactor;
    if (c.x > 110) c.x = -20;
    drawSprite(CLOUD, (c.x / 100) * canvas.width, (c.y / 100) * canvas.height, c.scale * 2.4, season);
  });

  // ── 6. Mountains ──
  const mtnSnow = season === "winter" || weather === "snow";
  drawBlockyMountain(canvas.width * 0.25, groundY, canvas.height * 0.45, canvas.width * 0.6, theme.mountain, theme.mountainLight, mtnSnow);
  drawBlockyMountain(canvas.width * 0.75, groundY, canvas.height * 0.35, canvas.width * 0.5, theme.mountain, theme.mountainLight, mtnSnow);
  drawBlockyMountain(canvas.width * 0.5, groundY, canvas.height * 0.25, canvas.width * 0.4, theme.mountain, theme.mountainLight, season === "winter");

  // ── 7. Ground ──
  ctx.fillStyle = SEASON_COLORS[season].grass2;
  ctx.fillRect(0, groundY, canvas.width, canvas.height - groundY);
  ctx.fillStyle = SEASON_COLORS[season].grass1;
  grassBlades.forEach((b) => {
    if (b.x < canvas.width)
      ctx.fillRect(b.x, groundY - b.height, b.width, b.height);
  });
  ctx.fillRect(0, groundY, canvas.width, canvas.height - groundY);

  // ── 8. Rocks, bushes, flowers ──
  drawSprite(ROCK, canvas.width * 0.3, groundY - 15, 4, season);
  drawSprite(ROCK, canvas.width * 0.65, groundY - 10, 3, season);
  drawSprite(BUSH, canvas.width * 0.2, groundY - BUSH.length * 6 + 10, 6, season);
  drawSprite(BUSH, canvas.width * 0.85, groundY - BUSH.length * 5 + 5, 5, season);
  drawSprite(BUSH, canvas.width * 0.1, groundY - BUSH.length * 4 + 15, 4, season);
  if (season === "spring" || season === "summer") {
    grassBlades.forEach((b) => {
      if (b.isFlower && b.x < canvas.width)
        drawSprite(FLOWER, b.x, groundY + b.height * 2, 3, season);
    });
  }

  // ── 9. Side trees ──
  const seasonTrees = treeImgs[season];
  if (seasonTrees && seasonTrees.small.complete && seasonTrees.small.naturalWidth) {
    const si = seasonTrees.small;
    const dsw = Math.min(canvas.width * 0.12, 260);
    const ss = dsw / si.naturalWidth;
    const sW = si.naturalWidth * ss;
    const sH = si.naturalHeight * ss;
    const bot = getBottomYFromRegion(si, 0, 0, si.naturalWidth, si.naturalHeight, _bottomCacheImg, si.src);
    const nudge = sheetBottomNudgeValNum;
    ctx.drawImage(si, (tree1Pct / 100) * canvas.width - sW / 2, groundY - bot * ss + nudge + tree1YOff, sW, sH);
    ctx.drawImage(si, (tree2Pct / 100) * canvas.width - sW / 2, groundY - bot * ss + nudge + tree2YOff, sW, sH);
  } else if (treesSheetLoaded && treesSheet.naturalWidth) {
    const shW = treesSheet.naturalWidth, shH = treesSheet.naturalHeight;
    const tW = shW / 4, tH = shH / 2;
    const col = { winter: 0, spring: 1, summer: 2, autumn: 3 }[season] ?? 1;
    const dsw = Math.min(canvas.width * 0.12, 260);
    const ss = dsw / tW;
    const sW = tW * ss, sH = tH * ss;
    const botS = getBottomYFromRegion(treesSheet, col * tW, tH, tW, tH, _bottomCacheSheet, `${col}_1`);
    ctx.drawImage(treesSheet, col * tW, tH, tW, tH, (tree1Pct / 100) * canvas.width - sW / 2, groundY - botS * ss + sheetBottomNudgeValNum + tree1YOff, sW, sH);
    ctx.drawImage(treesSheet, col * tW, tH, tW, tH, (tree2Pct / 100) * canvas.width - sW / 2, groundY - botS * ss + sheetBottomNudgeValNum + tree2YOff, sW, sH);
  } else {
    drawSprite(TREE, (tree1Pct / 100) * canvas.width, groundY - TREE.length * 8 + 15 + tree1YOff, 8, season);
    drawSprite(TREE, (tree2Pct / 100) * canvas.width, groundY - TREE.length * 8 + 15 + tree2YOff, 8, season);
  }

  // ── 10. Center tree ──
  let centerTreeImgX = centerTreeX;
  let centerTreeImgY = groundY - TREE.length * 8 + 25;
  let centerTreeImgW = 0, centerTreeImgH = 0;
  let centerHoleX = centerTreeX, centerHoleY = groundY, centerHoleR = 40;
  centerTreeUsingSheetTop = false;

  if (seasonTrees) {
    const useIn = raccoonState === "hiding" && seasonTrees.centerIn.complete && seasonTrees.centerIn.naturalWidth;
    const ciBase = seasonTrees.center.complete && seasonTrees.center.naturalWidth ? seasonTrees.center : null;
    const ci = useIn ? seasonTrees.centerIn : ciBase;
    if (ci) {
      const layoutRef = ciBase || ci;
      const dw = Math.min(canvas.width * 0.28, 520);
      const sc = dw / layoutRef.naturalWidth;
      centerTreeImgW = layoutRef.naturalWidth * sc;
      centerTreeImgH = layoutRef.naturalHeight * sc;
      const imgBot = getBottomYFromRegion(layoutRef, 0, 0, layoutRef.naturalWidth, layoutRef.naturalHeight, _bottomCacheImg, layoutRef.src);
      centerTreeImgX = canvas.width / 2 - centerTreeImgW / 2;
      centerTreeImgY = groundY - imgBot * sc + centerTreeYOffset + sheetBottomNudgeValNum;
      ctx.drawImage(ci, centerTreeImgX, centerTreeImgY, centerTreeImgW, centerTreeImgH);
      centerHoleX = centerTreeImgX + centerTreeImgW * holeFrac.x;
      centerHoleY = centerTreeImgY + centerTreeImgH * holeFrac.y;
      centerHoleR = centerTreeImgW * holeFrac.r;
      centerHoleTarget = centerHoleX;
      centerTreeUsingSheetTop = useIn;
    } else if (treesSheetLoaded && treesSheet.naturalWidth) {
      const shW = treesSheet.naturalWidth, shH = treesSheet.naturalHeight;
      const tW = shW / 4, tH = shH / 2;
      const col = { winter: 0, spring: 1, summer: 2, autumn: 3 }[season] ?? 1;
      const row = shouldHide ? 0 : 1;
      const dw = Math.min(canvas.width * 0.28, 520);
      const sc = dw / tW;
      centerTreeImgW = tW * sc;
      centerTreeImgH = tH * sc;
      const sx = col * tW, sy = row * tH;
      const botTile = getBottomYFromRegion(treesSheet, sx, sy, tW, tH, _bottomCacheSheet, `${col}_${row}`);
      centerTreeImgX = canvas.width / 2 - centerTreeImgW / 2;
      centerTreeImgY = groundY - botTile * sc + centerTreeYOffset + sheetBottomNudgeValNum;
      ctx.drawImage(treesSheet, sx, sy, tW, tH, centerTreeImgX, centerTreeImgY, centerTreeImgW, centerTreeImgH);
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
  }

  // ── 11. Hiding badge ──
  if (raccoonState === "hiding" && Math.abs(raccoonX - centerHoleTarget) < 160 && centerTreeImgW > 0) {
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

  // ── 12. Bonfire + fireflies ──
  if (isNight) {
    const bfX = (bonfirePct / 100) * canvas.width;
    if (bonfireImgLoaded && bonfireImg.naturalWidth) {
      const bfSc = 80 / bonfireImg.naturalHeight;
      const bfW = bonfireImg.naturalWidth * bfSc;
      const bfH = bonfireImg.naturalHeight * bfSc;
      ctx.save();
      ctx.globalAlpha = (Math.sin(Date.now() / 420) + 1) / 8 + 0.1;
      ctx.fillStyle = "#e67e22";
      ctx.beginPath();
      ctx.arc(bfX, groundY - 20, 80, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
      ctx.drawImage(bonfireImg, bfX - bfW / 2, groundY - bfH + bonfireYOff, bfW, bfH);
    } else {
      const bfSprite = Math.floor(Date.now() / 320) % 2 === 0 ? BONFIRE_1 : BONFIRE_2;
      drawSprite(bfSprite, bfX, groundY - BONFIRE_1.length * 6 + 15 + bonfireYOff, 6, season);
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

  // ── 13. Raccoon ──
  raccoon.frame++;
  if (raccoonState === "walking") {
    if (raccoon.frame % 30 === 0) raccoon.bounceOffset = raccoon.bounceOffset === 0 ? -25 : 0;
  } else {
    if (raccoon.frame % 90 === 0) {
      if (Math.random() > 0.6) raccoon.flip = !raccoon.flip;
      raccoon.bounceOffset = raccoon.bounceOffset === 0 ? -10 : 0;
    }
  }

  if (raccoonImg.complete && raccoonImg.naturalHeight !== 0 && raccoonScale > 0) {
    const spW = 260, spH = 260;
    const hidingAtCenter = raccoonState === "hiding" && Math.abs(raccoonX - centerHoleTarget) < 160;

    if (raccoonScale > 0.3) {
      ctx.fillStyle = "rgba(0,0,0,0.3)";
      ctx.beginPath();
      ctx.ellipse(
        raccoonX, groundY,
        (raccoon.bounceOffset === 0 ? 60 : 40) * raccoonScale * raccoonSizeMultiplier,
        8 * raccoonScale * raccoonSizeMultiplier,
        0, 0, Math.PI * 2
      );
      ctx.fill();
    }

    if (hidingAtCenter) {
      raccoonX = centerHoleTarget;
      if (!centerTreeUsingSheetTop) {
        const iW = spW * 0.6 * raccoonScale * raccoonSizeMultiplier;
        const iH = spH * 0.6 * raccoonScale * raccoonSizeMultiplier;
        ctx.save();
        ctx.translate(centerHoleX, centerHoleY + iH * 0.08);
        ctx.rotate(-0.08);
        ctx.drawImage(raccoonImg, -iW / 2, -iH / 2, iW, iH);
        ctx.strokeStyle = "rgba(20,20,20,0.95)";
        ctx.lineWidth = Math.max(2, iW * 0.02);
        ctx.lineCap = "round";
        const eyeY = -iH * 0.12, eyeLX = -iW * 0.12, eyeRX = iW * 0.12;
        ctx.beginPath(); ctx.moveTo(eyeLX - iW * 0.04, eyeY); ctx.quadraticCurveTo(eyeLX, eyeY + iH * 0.03, eyeLX + iW * 0.04, eyeY); ctx.stroke();
        ctx.beginPath(); ctx.moveTo(eyeRX - iW * 0.04, eyeY); ctx.quadraticCurveTo(eyeRX, eyeY + iH * 0.03, eyeRX + iW * 0.04, eyeY); ctx.stroke();
        ctx.fillStyle = "rgba(255,255,255,0.9)";
        ctx.font = `${Math.max(12, Math.floor(iW * 0.08))}px "Outfit", sans-serif`;
        ctx.textAlign = "center";
        for (let i = 0; i < 3; i++) {
          ctx.globalAlpha = 1 - i * 0.28;
          ctx.fillText("Z", iW * 0.18 + i * iW * 0.06, -iH * 0.6 - i * iH * 0.12);
        }
        ctx.globalAlpha = 1;
        ctx.restore();
      }
    } else {
      ctx.save();
      ctx.translate(raccoonX, groundY + raccoon.bounceOffset);
      ctx.scale(raccoonScale * raccoonSizeMultiplier, raccoonScale * raccoonSizeMultiplier);
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

  // ── 14. Rain / Snow ──
  if (weather === "rain" || weather === "storm")
    drawRain(groundY, weather === "storm" ? 1 : 0.6);
  else if (weather === "snow") drawSnow();

  // ── 15. Lightning ──
  if (lightningFlash > 0) {
    ctx.fillStyle = `rgba(255,255,255,${lightningFlash / 20})`;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    lightningFlash -= 1;
  }

  // ── 16. Weather bar update ──
  updateTimeDisplay(h);

  requestAnimationFrame(loop);
}

// ─── INIT ──
window.addEventListener("resize", resize);
window.addEventListener("load", () => {
  resize();
  loadAllSettings();
  loadTreeImages();
  loadExternalFromStorage(); // Added this to reload cached API data on startup

  const syncAll = () => {
    fetchWeatherForCity(currentCity).then(() => {
      updateWeatherSyncTime();
      updateWeatherBar();
    });
    fetchMoonPhase();
  };

  syncAll();

  setInterval(syncAll, 15 * 60 * 1000);

  loop();
});
