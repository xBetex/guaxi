# Sun & Moon Sky Simulator — Pygame Port Specification

## Overview
A full-screen window showing a landscape with a sky that transitions through day/night. A single slider controls day-of-year (0–364.99) where integer = day, fractional = time-of-day. Sun and moon arc across the full sky width, never appearing simultaneously.

---

## Window & Setup
- **Resolution**: 1280×720 default, resizable
- **Fullscreen**: toggle with F11
- **Font**: loaded TTF with fallback (Outfit or similar sans-serif)
- **FPS**: capped at 60, delta-time for play advancement

---

## Celestial Bodies

### Size
Both sun and moon have radius `r = 0.13 × min(window_width, window_height)` (gigantic).

### Shared Arc Formula
```
progress = clamp((hour − 6) / 12, 0, 1)     # 0 = rise, 1 = set, for both day and moon-hour
angle = progress × π
center_x = window_width × (0.02 + 0.96 × progress)
center_y = window_height × base_frac − sin(angle) × window_height × amplitude
```

| Body | base_frac | amplitude | Hour source |
|------|-----------|-----------|-------------|
| Sun  | 0.40      | 0.22      | Scene hour `h` |
| Moon | 0.38      | 0.16      | Moon-hour `mh = (h + fraction × 12) % 24` |

### Visibility & Fade
- **Sun visible**: scene hour 6–18 only.  
  Fade-in α = `h − 6` during 6→7.  
  Fade-out α = `18 − h` during 17→18.  
  α clamped [0, 1].

- **Moon visible**: scene hour 18–6 only.  
  Fade-in α = `h − 18` during 18→19.  
  Fade-out α = `6 − h` during 5→6.  
  α clamped [0, 1].

Never both visible (scene hour gating ensures mutual exclusion).

### Sun Rendering (12 corona rays + glow + gradient core)
1. **Save** context, set `global_alpha = vis`.
2. **Corona rays** (12 rays): translate to center. For each ray `i`:
   - angle = `(i/12) × 2π + progress × 0.3`
   - length = `r × (1.2 + sin(angle×3 + hour) × 0.3)`
   - Draw a filled circle at `(cos(angle)×length×0.5, sin(angle)×length×0.5)` with radius `length×0.5`
   - Color: warm yellow with alpha pulsing via `sin`
3. **Multi-layer glow** (4 layers): For `i = 0..3`:
   - Radius = `r × (1 + i × 0.5)`
   - Radial gradient from center (alpha `0.08/(i+1)`, color `rgb(255,230,180)`) to transparent
4. **Core**: radial gradient `rgb(255,248,236)` → `rgb(255,228,130)` → `rgb(255,179,71)` → `rgb(232,131,26)`
5. **Bright spot**: white circle at offset `(−r×0.15, −r×0.15)` radius `r×0.4`, alpha 0.6
6. **Restore** context.

### Moon Rendering (crater texture + phase + glow)
1. **Save** context, set `global_alpha = vis`.
2. **Halo** (3 layers): For `i = 0..2`:
   - Radius = `r × (1.5 + i × 0.8)`
   - Radial gradient from center (alpha `fraction×0.04/(i+1)`, color `rgb(180,165,140)`) to transparent
3. **Dark base**: radial gradient `rgb(46,46,72)` → `rgb(28,28,48)` → `rgb(14,14,24)`
4. **Lit portion**: clip to circle, draw overlapping circle shifted by `r × (1 − 2 × fraction)`, fill with warm gradient `rgb(245,238,219)` → `rgb(227,216,190)` → `rgb(205,191,162)`
5. **Surface texture** (precomputed 96×96 array, applied every 3rd pixel): skip if outside circle or on dark side. Draw 5×5 dark squares with alpha based on texture value.
6. **Rim stroke**: 1px `rgba(255,255,255,0.03)`
7. **Restore** context.

### Texture Precomputation (run once)
- 96×96 grid, each cell value 0–255.
- For each pixel `(px, py)` normalized to `−1..1`:
  - Start brightness `b = 0.88`
  - For each of 12 craters `(cx, cy, cr)`:
    - distance `d = hypot(dx−cx, dy−cy)`, `t = d / cr`
    - if `t < 1`: `b −= (1−t²) × 0.12`
    - if `t < 1.4`: `b += exp(−(t−0.85)² / 0.02) × 0.05`
  - Add procedural noise: `sin(dx×5.5 + dy×4.0) × 0.01 + cos(dx×2.5 − dy×3.5) × 0.007`
  - Clamp `b` to `[0.48, 0.97]`, store `b × 255` as Uint8.

### Crater positions (12)
```
x: 0.10, y: -0.20, r: 0.30
x: -0.26, y: 0.14, r: 0.24
x: 0.38, y: -0.08, r: 0.18
x: 0.20, y: -0.32, r: 0.15
x: -0.37, y: 0.26, r: 0.11
x: 0.52, y: 0.34, r: 0.10
x: -0.16, y: -0.54, r: 0.08
x: 0.20, y: 0.57, r: 0.07
x: -0.52, y: -0.12, r: 0.09
x: 0.42, y: -0.42, r: 0.07
x: -0.42, y: 0.44, r: 0.06
x: 0.08, y: 0.12, r: 0.16
```

---

## Sky

### 4-stop gradient (top to bottom)
Time-of-day determines the four color stops.

**Night** (h < 5 or h ≥ 19):  
`(2,5,12)` → `(4,10,22)` → `(8,18,36)` → `(1,3,8)`

**Dawn** (h 5→7): lerp from night to day values with `f = (h−5)/2`.

**Day** (h 7→17): used directly from season table (see below).  
Each layer has a darker "backup" version (×0.6, ×0.4, ×0.7 of sky colors).

**Dusk** (h 17→19): lerp from day to night with `f = (h−17)/2`.

### Season Color Tables
| Season   | sky1            | sky2            | sky3            |
|----------|-----------------|-----------------|-----------------|
| summer   | rgb(25,70,170)  | rgb(100,185,230)| rgb(180,220,240)|
| autumn   | rgb(20,55,140)  | rgb(120,150,170)| rgb(190,185,175)|
| winter   | rgb(15,40,110)  | rgb(90,130,165) | rgb(170,185,190)|
| spring   | rgb(30,75,165)  | rgb(120,190,220)| rgb(195,220,230)|

### Season from day-of-year (Southern Hemisphere)
```
doy 0–79:     summer
doy 80–171:   autumn
doy 172–263:  winter
doy 264–354:  spring
doy 355–364:  summer
```

### Stars (night only, 6pm–6am)
- 200 stars, random positions in top 72% of window
- 8% are "big" (radius 2), rest are 1×1 pixels
- Each star has phase `p`, speed `sp`, brightness `b`
- Twinkle: `alpha = visibility × b × (0.5 + 0.5 × sin(p))`
- visibility fades during 18→20 (1→0) and 5→6 (0→1)

### Shooting Stars
- 0.4% chance per frame of a new shooting star
- Starts at random top position, travels diagonally down-left
- Length 20–70px, speed 4–9
- Removed when below 70% of window height

---

## Landscape

### Mountains (4 layers)
- Ground Y = `window_height × 0.78`
- Each layer drawn as a filled polygon with sine-wave peaks
- Layer heights: 22%, 17%, 13%, 9% of window height
- Peak counts: 9, 7, 6, 5
- Layer colors: progressive lighter shades of mountain color from season table
- Night version: fixed darker colors (`#0a1525`, `#152238`, `#1e3050`, `#2a3f60`)
- Winter extra: semi-transparent white snow cap layer on top

### Ground
- Rect from ground Y to bottom
- Gradient: `grass` → `grass2` from season table

### Trees (3 trees)
- Ground Y = `window_height × 0.78`
- Scale = `min(w, h) / 800`
- Positions: 15%, 50%, 82% of width (center tree 1.4× larger)
- **Shadow**: dark ellipse at base
- **Trunk**: brown rect, width 8×scale, height 50×scale
- **Winter**: 4 branches drawn as lines (no foliage)
- **Other seasons**: foliage circle at top + small highlight arc

---

## Controls

### Slider
- Range: 0 to 364.99, step 0.01
- Draw as a horizontal track with thumb, styled accent color `#a29bfe`
- Label shows: day number, month name (Jan–Dez), and HH:MM time

### Play/Pause Button
- Toggles automatic time advancement
- Rate: `+0.005` per tick, normalized to 200ms base interval (i.e., 0.025 days/second of real time)
- Uses delta-time so it's framerate-independent

### Keyboard
- `←/↑`: subtract 0.05 from days (≈1.2h)
- `→/↓`: add 0.05 to days
- `Space`: toggle play/pause

### Debug Panel (toggle with "dbg" button)
- Shows on a semi-transparent overlay in top-left
- Fields: day, time, season, sun/moon visibility + position + radius, moon hour, phase fraction, window size

---

## Implementation Notes for Pygame
- Use `pygame.RESIZABLE` flag
- For smooth rendering, use `pygame.transform.smoothscale` or blit to a surface and scale
- `math.hypot` for distance calculations
- Precompute moon texture as a 96×96 `pygame.Surface` or numpy array at init
- Cache radial gradients (or re-create each frame — in CPython this is fast enough at 60fps for 1280×720)
- For the multi-layer glow, draw circles with increasing radius and decreasing alpha (pre-multiplied alpha or `BLEND_ALPHA_SDL2`)
- The `outfit` font can be downloaded from Google Fonts or use a built-in sans-serif as fallback
- Use `pygame.font.Font` for the date/time label, rendered once per frame (cheap)
- Sun/Moon alpha: use `Surface.set_alpha()` before blitting, or pass alpha as draw argument
- The crater texture overlay is the heaviest part: 32×33 iterations × 2 (step 3 on 96) = ~1050 pixel checks per frame — negligible

---

## File Structure
```
sky_sim/
├── main.py          # Pygame init, loop, events
├── celestial.py     # Sun, Moon drawing functions + texture building
├── landscape.py     # Sky, mountains, ground, trees
├── controls.py      # Slider, button, keyboard handling
├── data.py          # Color tables, season function, crater positions
└── README.md
```
