"""
Interactive grid alignment tool for tree sprite sheet.

Click near a grid line to select it, then drag or use arrow keys.
Tab cycles through lines. Saves explicit line positions.

Usage:  python crop_trees.py

Keys:
  Click+drag   — move selected line
  Arrows       — nudge selected line 1px
  Shift+arrows — nudge 10px
  Tab          — cycle selected line
  Wheel        — zoom in/out
  Space+drag   — pan view
  S            — save config
  R            — reset grid
  ESC          — quit
"""

import pygame
import os
import sys

SHEET = "sprites/trees.png"
CONFIG = "sprites/trees.cfg"
COLS, ROWS = 3, 4

pygame.init()
screen = pygame.display.set_mode((1200, 800), pygame.RESIZABLE)
pygame.display.set_caption("Tree Sheet Grid Tool")
font = pygame.font.SysFont("sans", 14)
font_big = pygame.font.SysFont("sans", 18)

if not os.path.exists(SHEET):
    print(f"Create {SHEET} first, then run this tool.")
    sys.exit(1)

img = pygame.image.load(SHEET).convert_alpha()
iw, ih = img.get_size()

vlines = [i * (iw // COLS) for i in range(COLS + 1)]
hlines = [i * (ih // ROWS) for i in range(ROWS + 1)]
selected = 0
mode = "v"
zoom = 1.0
scroll_x, scroll_y = 0, 0
drag_line = -1
drag_off = 0
panning = False
pan_start = (0, 0)
pan_origin = (0, 0)


def save():
    with open(CONFIG, "w") as f:
        f.write("# Tree sprite sheet grid\n")
        for i, x in enumerate(vlines):
            f.write(f"v{i}={int(x)}\n")
        for i, y in enumerate(hlines):
            f.write(f"h{i}={int(y)}\n")
    print(f"Saved {CONFIG}")


def load():
    global vlines, hlines
    if not os.path.exists(CONFIG):
        return
    with open(CONFIG) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            k, _, v = line.partition("=")
            k, v = k.strip(), v.strip()
            if k.startswith("v"):
                idx = int(k[1:])
                while len(vlines) <= idx:
                    vlines.append(0)
                vlines[idx] = int(v)
            elif k.startswith("h"):
                idx = int(k[1:])
                while len(hlines) <= idx:
                    hlines.append(0)
                hlines[idx] = int(v)


def screen_to_img(sx, sy):
    w, h = screen.get_size()
    img_w = iw * zoom
    img_h = ih * zoom
    ox = (w - img_w) // 2 + scroll_x
    oy = 40 + scroll_y
    return (sx - ox) / zoom, (sy - oy) / zoom


load()

running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_s:
                save()
            elif event.key == pygame.K_r:
                vlines[:] = [i * (iw // COLS) for i in range(COLS + 1)]
                hlines[:] = [i * (ih // ROWS) for i in range(ROWS + 1)]
            elif event.key == pygame.K_TAB:
                if mode == "v":
                    selected += 1
                    if selected >= len(vlines):
                        selected = 0
                        mode = "h"
                else:
                    selected += 1
                    if selected >= len(hlines):
                        selected = 0
                        mode = "v"
            elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                step = 10 if pygame.key.get_mods() & pygame.KMOD_SHIFT else 1
                if mode == "v":
                    if event.key == pygame.K_LEFT:
                        vlines[selected] = max(0, vlines[selected] - step)
                    elif event.key == pygame.K_RIGHT:
                        vlines[selected] = min(iw, vlines[selected] + step)
                else:
                    if event.key == pygame.K_UP:
                        hlines[selected] = max(0, hlines[selected] - step)
                    elif event.key == pygame.K_DOWN:
                        hlines[selected] = min(ih, hlines[selected] + step)
            elif event.key == pygame.K_SPACE:
                panning = True
                pan_start = pygame.mouse.get_pos()
                pan_origin = (scroll_x, scroll_y)

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                panning = False

        elif event.type == pygame.MOUSEWHEEL:
            cx, cy = screen.get_size()
            mx, my = pygame.mouse.get_pos()
            img_cx, img_cy = screen_to_img(mx, my)
            old_zoom = zoom
            zoom *= 1.15 if event.y > 0 else (1 / 1.15)
            zoom = max(0.1, min(10, zoom))
            img_w_n = iw * zoom
            img_h_n = ih * zoom
            ox = (cx - img_w_n) // 2
            oy = 40
            scroll_x = int((mx - ox) - img_cx * zoom)
            scroll_y = int((my - oy) - img_cy * zoom)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            space_held = pygame.key.get_pressed()[pygame.K_SPACE]
            if event.button == 1 and space_held:
                panning = True
                pan_start = event.pos
                pan_origin = (scroll_x, scroll_y)
            elif event.button == 1:
                    ix, iy = screen_to_img(*event.pos)
                    best_d = 12 / zoom
                    best = -1
                    best_m = ""
                    for i, x in enumerate(vlines):
                        d = abs(ix - x)
                        if d < best_d:
                            best_d = d
                            best = i
                            best_m = "v"
                    for i, y in enumerate(hlines):
                        d = abs(iy - y)
                        if d < best_d:
                            best_d = d
                            best = i
                            best_m = "h"
                    if best >= 0:
                        selected = best
                        mode = best_m
                        if best_m == "v":
                            drag_line = best
                            drag_off = ix - vlines[best]
                        else:
                            drag_line = best
                            drag_off = iy - hlines[best]
            elif event.button == 2:
                panning = True
                pan_start = event.pos
                pan_origin = (scroll_x, scroll_y)

        elif event.type == pygame.MOUSEMOTION:
            if panning:
                dx = event.pos[0] - pan_start[0]
                dy = event.pos[1] - pan_start[1]
                scroll_x = pan_origin[0] + dx
                scroll_y = pan_origin[1] + dy
            elif drag_line >= 0:
                ix, iy = screen_to_img(*event.pos)
                if mode == "v":
                    vlines[drag_line] = max(0, min(iw, ix - drag_off))
                else:
                    hlines[drag_line] = max(0, min(ih, iy - drag_off))

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button in (1, 2):
                panning = False
                drag_line = -1

        elif event.type == pygame.VIDEORESIZE:
            pass

    w, h = screen.get_size()
    surf = pygame.Surface((w, h))
    surf.fill((20, 22, 30))

    img_w = iw * zoom
    img_h = ih * zoom
    ox = int((w - img_w) // 2 + scroll_x)
    oy = int(40 + scroll_y)

    scaled = pygame.transform.scale(img, (int(img_w), int(img_h)))
    surf.blit(scaled, (ox, oy))

    for i, x in enumerate(vlines):
        gx = int(ox + x * zoom)
        is_sel = (mode == "v" and i == selected)
        color = (255, 80, 80) if is_sel else (255, 200, 80)
        if is_sel:
            pygame.draw.line(surf, (255, 255, 200, 60), (gx, oy - 10), (gx, oy + int(hlines[-1] * zoom) + 10), 3)
        pygame.draw.line(surf, color, (gx, oy), (gx, oy + int(hlines[-1] * zoom)), 2 if is_sel else 1)
        lbl = font.render(str(x), True, color)
        surf.blit(lbl, (gx + 4, oy + int(hlines[-1] * zoom) + 2))

    for i, y in enumerate(hlines):
        gy = int(oy + y * zoom)
        is_sel = (mode == "h" and i == selected)
        color = (80, 200, 255) if is_sel else (255, 200, 80)
        if is_sel:
            pygame.draw.line(surf, (200, 255, 255, 60), (ox - 10, gy), (ox + int(vlines[-1] * zoom) + 10, gy), 3)
        pygame.draw.line(surf, color, (ox, gy), (ox + int(vlines[-1] * zoom), gy), 2 if is_sel else 1)
        lbl = font.render(str(y), True, color)
        surf.blit(lbl, (ox + int(vlines[-1] * zoom) + 4, gy - 8))

    season_names = ["summer", "autumn", "winter", "spring"]
    vnames = ["begin", "mid", "end"]
    for row, name in enumerate(season_names):
        if row < len(hlines) - 1:
            ly = int(oy + (hlines[row] + hlines[row + 1]) // 2 * zoom - 8)
            lbl = font.render(name, True, (160, 200, 255))
            surf.blit(lbl, (ox + int(vlines[-1] * zoom) + 80, ly))
    for col, name in enumerate(vnames):
        if col < len(vlines) - 1:
            lx = int(ox + (vlines[col] + vlines[col + 1]) // 2 * zoom)
            lbl = font.render(name, True, (160, 200, 255))
            surf.blit(lbl, (lx - lbl.get_width() // 2, oy - 22))

    sel_name = f"{mode}{selected}"
    info_y = oy + int(hlines[-1] * zoom) + 40
    info_lines = [
        f"Image: {iw}x{ih}  Zoom: {zoom:.0%}  Selected: {sel_name} ({vlines[selected] if mode=='v' else hlines[selected]})",
        "",
        "Click line → drag    Wheel → zoom    Space+drag → pan    Arrows → nudge",
        "Tab → cycle    S → save    R → reset    ESC → quit",
    ]
    for line in info_lines:
        t = font.render(line, True, (140, 150, 180))
        surf.blit(t, (20, info_y))
        info_y += 18

    preview_x = ox + int(vlines[-1] * zoom) + 200
    preview_y = 40 + scroll_y
    grid_bottom = oy + int(hlines[-1] * zoom)
    if preview_x + 200 < w:
        if preview_y < 30:
            preview_y = 30
        ph = font_big.render("Cells:", True, (160, 200, 255))
        surf.blit(ph, (preview_x, preview_y))
        preview_y += 26
        for row in range(ROWS):
            for col in range(COLS):
                if col >= len(vlines) - 1 or row >= len(hlines) - 1:
                    continue
                sx = vlines[col]
                sy = hlines[row]
                sw = vlines[col + 1] - sx
                sh = hlines[row + 1] - sy
                if sw <= 0 or sh <= 0:
                    continue
                cell = pygame.Surface((sw, sh), pygame.SRCALPHA)
                cell.blit(img, (0, 0), (sx, sy, sw, sh))
                scale = min(42, sw, sh)
                thumb = pygame.transform.scale(cell, (scale, scale))
                tx = preview_x + col * (scale + 4)
                ty = preview_y + row * (scale + 4)
                surf.blit(thumb, (tx, ty))

    screen.blit(surf, (0, 0))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
