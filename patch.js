// --- State & UI Logic ---
let currentCity = 'São Paulo';
let isAutoTime = true;
let manualTimeVal = 12; 

let isAutoSeason = true;
let manualSeasonVal = 'summer';

let isAutoWeather = true;
let manualWeatherVal = 'clear';

let tree1Pct = 15;
let tree2Pct = 80;
let bonfirePct = 65;
let centerTreeYOffset = parseInt(localStorage.getItem('centerTreeYOffset')) || 160;
let sheetBottomNudgeValue = parseInt(localStorage.getItem('sheetBottomNudge')) || 0;

const uiToggle = document.getElementById('ui-toggle');
const uiPanel = document.getElementById('ui-panel');
const cityInput = document.getElementById('city-input');

const overrideTime = document.getElementById('override-time');
const timeSlider = document.getElementById('time-slider');
const timeDisplay = document.getElementById('time-display');

const overrideSeason = document.getElementById('override-season');
const seasonSelect = document.getElementById('season-select');

const overrideWeather = document.getElementById('override-weather');
const weatherSelect = document.getElementById('weather-select');

const tree1Slider = document.getElementById('tree1-x');
const tree2Slider = document.getElementById('tree2-x');
const bonfireSlider = document.getElementById('bonfire-x');
const centerTreeYSlider = document.getElementById('center-tree-y');
const centerTreeYVal = document.getElementById('center-tree-y-val');
const saveCenterTreeBtn = document.getElementById('save-center-tree');
const sheetBottomNudge = document.getElementById('sheet-bottom-nudge');
const sheetBottomNudgeVal = document.getElementById('sheet-bottom-nudge-val');
const saveSheetBottomBtn = document.getElementById('save-sheet-bottom');

const raccoonImageInput = document.getElementById('raccoon-image-input');
const treeInputs = document.querySelectorAll('.tree-input');

// Helper function to get bottom pixel Y from image region
function getBottomYFromRegion(img, x, y, w, h, imgId) {
    // Simulate bottom detection - actual implementation would analyze pixel data
    // For now, return a reasonable default
    return h;
}

// UI Toggle
if (uiToggle) {
    uiToggle.addEventListener('click', () => {
        uiPanel.classList.toggle('open');
    });
}

// Sliders display
if (centerTreeYSlider) {
    centerTreeYSlider.value = centerTreeYOffset;
    centerTreeYVal.innerText = centerTreeYOffset + 'px';
    centerTreeYSlider.addEventListener('input', (e) => {
        centerTreeYVal.innerText = e.target.value + 'px';
    });
}

if (sheetBottomNudge) {
    sheetBottomNudge.value = sheetBottomNudgeValue;
    sheetBottomNudgeVal.innerText = sheetBottomNudgeValue + 'px';
    sheetBottomNudge.addEventListener('input', (e) => {
        sheetBottomNudgeVal.innerText = e.target.value + 'px';
    });
}

if (saveCenterTreeBtn) {
    saveCenterTreeBtn.addEventListener('click', () => {
        centerTreeYOffset = parseInt(centerTreeYSlider.value);
        localStorage.setItem('centerTreeYOffset', centerTreeYOffset);
        console.log('Center tree Y offset saved:', centerTreeYOffset);
    });
}

if (saveSheetBottomBtn) {
    saveSheetBottomBtn.addEventListener('click', () => {
        sheetBottomNudgeValue = parseInt(sheetBottomNudge.value);
        localStorage.setItem('sheetBottomNudge', sheetBottomNudgeValue);
        console.log('Sheet bottom nudge saved:', sheetBottomNudgeValue);
    });
}

// File input handlers
if (raccoonImageInput) {
    raccoonImageInput.addEventListener('change', async (e) => {
        if (e.target.files[0]) {
            const reader = new FileReader();
            reader.onload = (evt) => {
                raccoonImg.src = evt.target.result;
                console.log('Raccoon image loaded from file');
            };
            reader.readAsDataURL(e.target.files[0]);
        }
    });
}

// Tree image handlers
treeInputs.forEach(input => {
    input.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        const season = input.dataset.season;
        const type = input.dataset.type;
        const btn = document.getElementById(`${season}-${type}-btn`);
        
        const reader = new FileReader();
        reader.onload = (evt) => {
            const img = new Image();
            img.onload = () => {
                if (!treeImgs[season]) treeImgs[season] = {};
                treeImgs[season][type] = img;
                
                if (btn) {
                    btn.classList.add('loaded');
                    btn.innerText = '✓';
                }
                console.log(`Loaded ${season} ${type} tree image`);
            };
            img.src = evt.target.result;
        };
        reader.readAsDataURL(file);
    });
});

// --- Time & Season Logic ---
overrideTime.addEventListener('change', (e) => {
    isAutoTime = !e.target.checked;
    if (isAutoTime) {
        timeSlider.classList.add('hidden');
        updateTimeFromLocation();
    } else {
        timeSlider.classList.remove('hidden');
        manualTimeVal = parseFloat(timeSlider.value);
        updateTimeDisplay(manualTimeVal);
    }
});

timeSlider.addEventListener('input', (e) => {
    if (!isAutoTime) {
        manualTimeVal = parseFloat(e.target.value);
        updateTimeDisplay(manualTimeVal);
    }
});

overrideSeason.addEventListener('change', (e) => {
    isAutoSeason = !e.target.checked;
    if (isAutoSeason) {
        seasonSelect.classList.add('hidden');
        updateSeasonFromLocation();
    } else {
        seasonSelect.classList.remove('hidden');
        manualSeasonVal = seasonSelect.value;
    }
});

seasonSelect.addEventListener('change', (e) => {
    if (!isAutoSeason) {
        manualSeasonVal = e.target.value;
    }
});

overrideWeather.addEventListener('change', (e) => {
    isAutoWeather = !e.target.checked;
    if (isAutoWeather) {
        weatherSelect.classList.add('hidden');
        updateWeatherFromAPI();
    } else {
        weatherSelect.classList.remove('hidden');
        manualWeatherVal = weatherSelect.value;
    }
});

weatherSelect.addEventListener('change', (e) => {
    if (!isAutoWeather) {
        manualWeatherVal = e.target.value;
    }
});

// Position sliders
if (tree1Slider) {
    tree1Slider.value = tree1Pct;
    tree1Slider.addEventListener('input', (e) => { tree1Pct = parseFloat(e.target.value); });
}

if (tree2Slider) {
    tree2Slider.value = tree2Pct;
    tree2Slider.addEventListener('input', (e) => { tree2Pct = parseFloat(e.target.value); });
}

if (bonfireSlider) {
    bonfireSlider.value = bonfirePct;
    bonfireSlider.addEventListener('input', (e) => { bonfirePct = parseFloat(e.target.value); });
}

function updateTimeDisplay(time24) {
    const hours = Math.floor(time24);
    const minutes = Math.floor((time24 % 1) * 60);
    timeDisplay.innerText = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
}

function updateTimeFromLocation() {
    const now = new Date();
    const hours = now.getHours();
    const minutes = now.getMinutes();
    manualTimeVal = hours + minutes / 60;
    updateTimeDisplay(manualTimeVal);
    timeSlider.value = manualTimeVal;
}

function updateSeasonFromLocation() {
    const month = new Date().getMonth();
    if (month >= 8 && month <= 10) manualSeasonVal = 'spring';
    else if (month >= 11 || month <= 1) manualSeasonVal = 'summer';
    else if (month >= 2 && month <= 4) manualSeasonVal = 'autumn';
    else manualSeasonVal = 'winter';
    seasonSelect.value = manualSeasonVal;
}

async function updateWeatherFromAPI() {
    try {
        const response = await fetch(`https://wttr.in/${currentCity}?format=%C`);
        const weatherText = await response.text();
        const weatherLower = weatherText.toLowerCase();
        if (weatherLower.includes('rain') || weatherLower.includes('drizzle')) manualWeatherVal = 'rain';
        else if (weatherLower.includes('storm') || weatherLower.includes('thunder')) manualWeatherVal = 'storm';
        else if (weatherLower.includes('snow')) manualWeatherVal = 'snow';
        else if (weatherLower.includes('cloud')) manualWeatherVal = 'cloudy';
        else manualWeatherVal = 'clear';
        weatherSelect.value = manualWeatherVal;
    } catch (error) {
        console.log('Weather API error:', error);
        manualWeatherVal = 'clear';
        weatherSelect.value = 'clear';
    }
}

cityInput.addEventListener('change', (e) => {
    currentCity = e.target.value;
    if (isAutoTime) updateTimeFromLocation();
    if (isAutoSeason) updateSeasonFromLocation();
    if (isAutoWeather) updateWeatherFromAPI();
});

// --- Game Images ---
const raccoonImg = new Image();
// Use a default raccoon image or create a fallback
raccoonImg.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"%3E%3Ccircle cx="50" cy="50" r="45" fill="%23666"/%3E%3Ccircle cx="35" cy="40" r="8" fill="%23333"/%3E%3Ccircle cx="65" cy="40" r="8" fill="%23333"/%3E%3Ccircle cx="35" cy="40" r="3" fill="white"/%3E%3Ccircle cx="65" cy="40" r="3" fill="white"/%3E%3Cellipse cx="50" cy="65" rx="12" ry="8" fill="%23333"/%3E%3C/svg%3E';

// Tree images with fallbacks
const treeImgs = {
    spring: { center: new Image(), small: new Image() },
    summer: { center: new Image(), small: new Image() },
    autumn: { center: new Image(), small: new Image() },
    winter: { center: new Image(), small: new Image() }
};

function createFallbackImage(color, size) {
    const canvas = document.createElement('canvas');
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = color;
    ctx.fillRect(0, 0, size, size);
    ctx.fillStyle = '#000';
    ctx.font = `${size/3}px Arial`;
    ctx.fillText('🌲', size/4, size/2);
    const img = new Image();
    img.src = canvas.toDataURL();
    return img;
}

function loadTreeImages() {
    const seasons = ['spring', 'summer', 'autumn', 'winter'];
    const types = ['center', 'small'];
    const colors = {
        spring: '#55efc4',
        summer: '#78e08f',
        autumn: '#e58e26',
        winter: '#dfe6e9'
    };
    
    seasons.forEach(season => {
        types.forEach(type => {
            const img = treeImgs[season][type];
            img.onerror = () => {
                console.log(`Could not load ${season} ${type} tree, using fallback`);
                const fallback = createFallbackImage(colors[season], type === 'center' ? 100 : 60);
                treeImgs[season][type] = fallback;
                const btn = document.getElementById(`${season}-${type}-btn`);
                if (btn) btn.classList.add('loaded');
            };
            img.src = `${season}_${type}.png`;
        });
    });
}

loadTreeImages();

// --- Canvas & Animation ---
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

let animationId = null;

function resizeCanvas() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
}

window.addEventListener('resize', resizeCanvas);
resizeCanvas();

const THEMES = {
    manha: { sky1: '#74b9ff', sky2: '#81ecec', sky3: '#ffeaa7', mountain: '#827397', mountainLight: '#a29bfe' },
    dia:   { sky1: '#0984e3', sky2: '#74b9ff', sky3: '#81ecec', mountain: '#4a5b63', mountainLight: '#636e72' },
    tarde: { sky1: '#6c5ce7', sky2: '#e84393', sky3: '#fdcb6e', mountain: '#1b1b2f', mountainLight: '#2d3436' },
    noite: { sky1: '#000000', sky2: '#1e272e', sky3: '#0f1423', mountain: '#0a0a0f', mountainLight: '#1e272e' }
};

const SEASON_COLORS = {
    spring: { grass1: '#55efc4', grass2: '#00b894', leafM: '#fd79a8', leafN: '#e84393', leafE: '#d63031' },
    summer: { grass1: '#78e08f', grass2: '#38ada9', leafM: '#2ecc71', leafN: '#27ae60', leafE: '#1e8449' },
    autumn: { grass1: '#e58e26', grass2: '#b71540', leafM: '#f39c12', leafN: '#d35400', leafE: '#e67e22' },
    winter: { grass1: '#dfe6e9', grass2: '#b2bec3', leafM: '#ecf0f1', leafN: '#bdc3c7', leafE: '#95a5a6' }
};

function getCurrentTime() {
    if (!isAutoTime && overrideTime.checked) {
        return manualTimeVal;
    }
    const now = new Date();
    return now.getHours() + now.getMinutes() / 60;
}

function getCurrentSeason() {
    if (!isAutoSeason && overrideSeason.checked) {
        return manualSeasonVal;
    }
    const month = new Date().getMonth();
    if (month >= 8 && month <= 10) return 'spring';
    if (month >= 11 || month <= 1) return 'summer';
    if (month >= 2 && month <= 4) return 'autumn';
    return 'winter';
}

function getCurrentWeather() {
    if (!isAutoWeather && overrideWeather.checked) {
        return manualWeatherVal;
    }
    return 'clear';
}

function getThemeFromTime(hour) {
    if (hour >= 5 && hour < 11) return THEMES.manha;
    if (hour >= 11 && hour < 17) return THEMES.dia;
    if (hour >= 17 && hour < 20) return THEMES.tarde;
    return THEMES.noite;
}

function drawSkyGradient(theme, hour) {
    const grad = ctx.createLinearGradient(0, 0, 0, canvas.height);
    grad.addColorStop(0, theme.sky1);
    grad.addColorStop(0.6, theme.sky2);
    grad.addColorStop(1, theme.sky3);
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
}

function drawSunAndMoon(hour, weather) {
    if (weather === 'storm') return;
    
    const isDay = hour >= 6 && hour < 18;
    if (weather === 'cloudy') {
        ctx.fillStyle = 'rgba(255, 255, 255, 0.2)';
        ctx.beginPath();
        ctx.arc(canvas.width - 80, 80, 40, 0, Math.PI * 2);
        ctx.fill();
        return;
    }
    
    if (isDay) {
        ctx.fillStyle = '#fdcb6e';
        ctx.shadowBlur = 30;
        ctx.shadowColor = '#ff9f43';
        ctx.beginPath();
        ctx.arc(80, 80, 45, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
    } else {
        ctx.fillStyle = '#f5f6fa';
        ctx.shadowBlur = 20;
        ctx.shadowColor = '#dcdde1';
        ctx.beginPath();
        ctx.arc(canvas.width - 80, 80, 35, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = '#2f3640';
        ctx.beginPath();
        ctx.arc(canvas.width - 80, 80, 30, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
    }
}

function drawMountains(theme) {
    ctx.fillStyle = theme.mountain;
    ctx.beginPath();
    ctx.moveTo(0, canvas.height * 0.5);
    ctx.lineTo(canvas.width * 0.2, canvas.height * 0.35);
    ctx.lineTo(canvas.width * 0.4, canvas.height * 0.45);
    ctx.lineTo(canvas.width * 0.6, canvas.height * 0.3);
    ctx.lineTo(canvas.width * 0.8, canvas.height * 0.4);
    ctx.lineTo(canvas.width, canvas.height * 0.32);
    ctx.lineTo(canvas.width, canvas.height);
    ctx.lineTo(0, canvas.height);
    ctx.fill();
}

function drawGround(season) {
    const colors = SEASON_COLORS[season];
    const grad = ctx.createLinearGradient(0, canvas.height * 0.5, 0, canvas.height);
    grad.addColorStop(0, colors.grass2);
    grad.addColorStop(1, colors.grass1);
    ctx.fillStyle = grad;
    ctx.fillRect(0, canvas.height * 0.5, canvas.width, canvas.height * 0.5);
}

function drawTree(x, y, width, height, image) {
    if (image && image.complete && image.naturalWidth > 0) {
        ctx.drawImage(image, x, y, width, height);
    } else {
        ctx.fillStyle = '#8B4513';
        ctx.fillRect(x + width/2 - 5, y + height/2, 10, height/2);
        ctx.fillStyle = '#2ecc71';
        ctx.beginPath();
        ctx.arc(x + width/2, y + height/2 - 20, width/2, 0, Math.PI * 2);
        ctx.fill();
    }
}

function drawRaccoon() {
    const raccoonX = canvas.width / 2 - 40;
    const raccoonY = canvas.height * 0.7 - 40 + sheetBottomNudgeValue;
    
    if (raccoonImg && raccoonImg.complete && raccoonImg.naturalWidth > 0) {
        ctx.drawImage(raccoonImg, raccoonX, raccoonY, 80, 80);
    } else {
        ctx.fillStyle = '#8B7355';
        ctx.fillRect(raccoonX, raccoonY, 80, 80);
        ctx.fillStyle = '#2c3e50';
        ctx.fillRect(raccoonX + 20, raccoonY + 20, 10, 10);
        ctx.fillRect(raccoonX + 50, raccoonY + 20, 10, 10);
        ctx.fillStyle = '#000';
        ctx.fillRect(raccoonX + 35, raccoonY + 50, 10, 15);
    }
}

function drawBonfire(x, y) {
    ctx.fillStyle = '#d35400';
    ctx.fillRect(x - 15, y - 20, 30, 40);
    ctx.fillStyle = '#e67e22';
    ctx.beginPath();
    ctx.moveTo(x, y - 40);
    ctx.lineTo(x - 10, y - 20);
    ctx.lineTo(x + 10, y - 20);
    ctx.fill();
    
    if (Math.random() > 0.95) {
        ctx.fillStyle = '#f39c12';
        ctx.beginPath();
        ctx.moveTo(x, y - 50);
        ctx.lineTo(x - 5, y - 35);
        ctx.lineTo(x + 5, y - 35);
        ctx.fill();
    }
}

function drawWeather(weather, hour) {
    if (weather === 'rain') {
        for (let i = 0; i < 100; i++) {
            ctx.fillStyle = 'rgba(173, 216, 230, 0.3)';
            ctx.fillRect(Math.random() * canvas.width, Math.random() * canvas.height, 2, 10);
        }
    } else if (weather === 'storm') {
        for (let i = 0; i < 200; i++) {
            ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
            ctx.fillRect(Math.random() * canvas.width, Math.random() * canvas.height, 3, 15);
        }
        if (Math.random() > 0.98) {
            ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
            ctx.fillRect(Math.random() * canvas.width, 0, 5, canvas.height);
        }
    } else if (weather === 'snow') {
        for (let i = 0; i < 150; i++) {
            ctx.fillStyle = 'white';
            ctx.beginPath();
            ctx.arc(Math.random() * canvas.width, Math.random() * canvas.height, 3, 0, Math.PI * 2);
            ctx.fill();
        }
    }
}

function animate() {
    const hour = getCurrentTime();
    const season = getCurrentSeason();
    const weather = getCurrentWeather();
    
    const theme = getThemeFromTime(hour);
    
    drawSkyGradient(theme, hour);
    drawSunAndMoon(hour, weather);
    drawMountains(theme);
    drawGround(season);
    
    const tree1X = (tree1Pct / 100) * canvas.width;
    const tree2X = (tree2Pct / 100) * canvas.width;
    const bonfireX = (bonfirePct / 100) * canvas.width;
    const groundY = canvas.height * 0.5;
    
    drawTree(tree1X - 30, groundY - 80 + sheetBottomNudgeValue, 60, 80, treeImgs[season].small);
    drawTree(tree2X - 40, groundY - 100 + centerTreeYOffset + sheetBottomNudgeValue, 80, 100, treeImgs[season].center);
    drawBonfire(bonfireX, groundY + 20);
    drawRaccoon();
    drawWeather(weather, hour);
    
    animationId = requestAnimationFrame(animate);
}

// Start animation when images are ready
function startAnimation() {
    if (animationId) cancelAnimationFrame(animationId);
    animate();
}

// Initialize
resizeCanvas();
startAnimation();
updateTimeFromLocation();
updateSeasonFromLocation();
if (isAutoWeather) updateWeatherFromAPI();

// Refresh time periodically
setInterval(() => {
    if (isAutoTime) {
        updateTimeFromLocation();
    }
}, 1000);

// Refresh weather periodically
setInterval(() => {
    if (isAutoWeather) {
        updateWeatherFromAPI();
    }
}, 600000); // Every 10 minutes