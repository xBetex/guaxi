import pygame

BG_DARK = (12, 14, 22)
BG_PANEL = (18, 22, 34)
BORDER = (32, 38, 55)
ACCENT = (140, 155, 255)
ACCENT_HOVER = (160, 175, 255)
TEXT = (210, 215, 225)
TEXT_DIM = (130, 140, 160)
TRACK = (30, 36, 52)
THUMB = (120, 140, 250)


def draw_panel(screen, rect, title=None, font=None):
    pygame.draw.rect(screen, BG_PANEL, rect, border_radius=10)
    pygame.draw.rect(screen, BORDER, rect, width=1, border_radius=10)
    if title and font:
        t = font.render(title, True, TEXT_DIM)
        screen.blit(t, (rect.x + 12, rect.y + 8))


class Slider:
    def __init__(self, x, y, width, height, minv, maxv, value):
        self.rect = pygame.Rect(x, y, width, height)
        self.width = width
        self.min = minv
        self.max = maxv
        self.value = value
        self.dragging = False
        self.hover = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self._set_from_pos(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
            if self.dragging:
                self._set_from_pos(event.pos[0])

    def _set_from_pos(self, mx):
        rel = (mx - self.rect.x) / self.rect.w
        rel = max(0, min(1, rel))
        self.value = self.min + rel * (self.max - self.min)

    def draw(self, screen):
        pygame.draw.rect(screen, TRACK, self.rect, border_radius=self.rect.h // 2)
        rel = (self.value - self.min) / (self.max - self.min)
        fill_w = int(rel * self.rect.w)
        if fill_w > 2:
            fill = pygame.Rect(self.rect.x, self.rect.y, fill_w, self.rect.h)
            pygame.draw.rect(screen, ACCENT, fill, border_radius=self.rect.h // 2)

        thumb_x = self.rect.x + rel * self.rect.w
        thumb_r = self.rect.h + 4
        color = ACCENT_HOVER if self.hover else THUMB
        pygame.draw.circle(screen, color, (int(thumb_x), self.rect.centery), thumb_r)
        pygame.draw.circle(screen, (255, 255, 255, 40), (int(thumb_x), self.rect.centery), thumb_r - 3)


class Button:
    def __init__(self, x, y, w, h, text):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = pygame.font.SysFont("sans", 18)
        self.hover = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            return self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        return False

    def draw(self, screen):
        color = ACCENT if self.hover else BG_PANEL
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        if not self.hover:
            pygame.draw.rect(screen, BORDER, self.rect, width=1, border_radius=8)
        txt = self.font.render(self.text, True, TEXT)
        screen.blit(txt, txt.get_rect(center=self.rect.center))


HELP_TEXT = [
    ("Space",            "Play / Pause"),
    ("Left / Right",     "Scroll time"),
    ("+ / -",            "Speed up / down"),
    ("T",                "Toggle live time mode"),
    ("G",                "Jump +6 hours"),
    ("", ""),
    ("\u2605 Fun keys \u2605", ""),
    ("R",                "Toggle rain"),
    ("N",                "Trigger meteor shower"),
    ("A",                "Toggle aurora borealis"),
    ("B",                "Lightning bolt"),
    ("V",                "Toggle skycam PIP"),
    ("Click night sky",  "Launch shooting star"),
    ("", ""),
    ("F2",               "Debug overlay"),
    ("F3",               "Calendar"),
    ("F5",               "Test menu"),
    ("F11",              "Fullscreen"),
    ("H",                "Toggle this help"),
    ("S",                "Show / hide controls"),
]


def draw_help(screen, font):
    """Draw a centred help overlay with a proper two-column key / action layout."""
    w, h = screen.get_size()

    # Dim the background
    overlay = pygame.Surface((w, h), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 175))
    screen.blit(overlay, (0, 0))

    COL_GAP   = 24   # gap between key column and action column
    ROW_H     = 26
    TITLE_H   = 38
    PAD_X     = 32
    PAD_Y     = 22
    KEY_COL_W = 160  # fixed width reserved for the key label

    # Measure panel size
    row_count = sum(1 for k, _ in HELP_TEXT if k != "") + sum(1 for k, _ in HELP_TEXT if k == "") + 1  # +1 title
    panel_w = KEY_COL_W + COL_GAP + 260 + PAD_X * 2
    panel_h = TITLE_H + len(HELP_TEXT) * ROW_H + PAD_Y * 2 + 10

    px = (w - panel_w) // 2
    py = (h - panel_h) // 2

    # Panel background
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill((16, 18, 28, 240))
    pygame.draw.rect(panel, (60, 70, 100, 200), panel.get_rect(), width=1, border_radius=10)
    # Accent bar at top
    pygame.draw.rect(panel, (88, 101, 242), pygame.Rect(0, 0, panel_w, 3), border_radius=2)
    screen.blit(panel, (px, py))

    # Title
    title_surf = font.render("Keyboard Controls", True, (200, 210, 255))
    screen.blit(title_surf, (px + PAD_X, py + PAD_Y))

    # Separator
    sep_y = py + PAD_Y + TITLE_H - 6
    pygame.draw.line(screen, (50, 60, 90), (px + PAD_X, sep_y), (px + panel_w - PAD_X, sep_y))

    y = sep_y + 10
    for key, action in HELP_TEXT:
        if key == "" and action == "":
            y += ROW_H // 2
            continue
        if action == "":  # Section header (e.g. "★ Fun keys ★")
            lbl = font.render(key, True, (140, 155, 255))
            screen.blit(lbl, (px + PAD_X, y))
        else:
            key_surf   = font.render(key, True, (255, 230, 130))
            act_surf   = font.render(action, True, (185, 200, 225))
            # Right-align the key inside the key column
            kx = px + PAD_X + KEY_COL_W - key_surf.get_width()
            screen.blit(key_surf, (kx, y))
            # Divider dot
            dot_x = px + PAD_X + KEY_COL_W + COL_GAP // 2 - 2
            pygame.draw.circle(screen, (80, 95, 130), (dot_x, y + ROW_H // 2 - 2), 2)
            screen.blit(act_surf, (px + PAD_X + KEY_COL_W + COL_GAP, y))
        y += ROW_H

    # Dismiss hint at bottom
    hint = font.render("Press  H  to close", True, (90, 105, 140))
    screen.blit(hint, (px + (panel_w - hint.get_width()) // 2, py + panel_h - PAD_Y - hint.get_height()))


def draw_test_menu(screen, font, weather, moon_phase, phase_name):
    w, h = screen.get_size()
    hs = "SNOW" if getattr(weather, '_is_winter', False) and weather.rain_intensity > 0.01 else "no"
    lf = "FLASH!" if getattr(weather, '_flash', 0) > 0.1 else "idle"
    rb = f"active ({getattr(weather, '_rainbow', 0):.2f})" if getattr(weather, '_rainbow', 0) > 0.1 else "inactive"
    lines = [
        "=== WEATHER TEST ===",
        "Rain  Fog   Hum    hotkeys:",
        "  ↓     ↓     ↓    1-6 below",
        f"Snow: {hs}          4 lightning",
        f"Lightning: {lf}     5 rainbow",
        f"Rainbow: {rb}       6 reset",
        f"Clouds: {len(weather.clouds)}",
        f"Moon: {moon_phase:.4f} ({phase_name})",
        "",
        "F2 debug | F3 cal | F5 close | H help",
    ]
    panel = pygame.Surface((200, len(lines) * 20 + 20), pygame.SRCALPHA)
    panel.fill((6, 8, 16, 220))
    pygame.draw.rect(panel, (40, 48, 70), panel.get_rect(), width=1, border_radius=4)
    for i, line in enumerate(lines):
        c = (200, 210, 230) if not line.startswith("==") else (140, 155, 255)
        t = font.render(line, True, c)
        panel.blit(t, (10, 10 + i * 20))
    screen.blit(panel, (10, 60))


def draw_debug_overlay(screen, font, fps, elements):
    panel = pygame.Surface((screen.get_width(), screen.get_height()), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 0))
    for name, rect in elements:
        pygame.draw.rect(panel, (255, 50, 50, 80), rect, width=2)
        lbl = font.render(name, True, (255, 100, 100))
        panel.blit(lbl, (rect.x, rect.y - 18))

    info = [
        f"FPS: {fps:.0f}",
        f"Window: {screen.get_width()}x{screen.get_height()}",
    ]
    y = 10
    for line in info:
        t = font.render(line, True, (255, 200, 100))
        panel.blit(t, (10, y))
        y += 24

    screen.blit(panel, (0, 0))
