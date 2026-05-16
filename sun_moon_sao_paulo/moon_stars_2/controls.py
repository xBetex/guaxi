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
    ("Space", "Play / Pause"),
    ("Arrows", "Scroll time"),
    ("+ / -", "Speed"),
    ("W", "Weather debug"),
    ("F2", "Debug overlay"),
    ("F3", "Calendar"),
    ("F5", "Test menu"),
    ("F11", "Fullscreen"),
    ("H", "Help"),
    ("S", "Hide/show controls"),
    ("Now btn", "Jump to current time"),
    ("Mouse drag", "Sliders"),
    ("Scroll", "Days"),
]


def draw_help(screen, font):
    w, h = screen.get_size()
    panel = pygame.Surface((w, h), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 180))
    lines = ["Controls"] + [""] + [f"{k:>12}  {d}" for k, d in HELP_TEXT]
    total_h = len(lines) * 28 + 40
    y = (h - total_h) // 2
    for line in lines:
        if line == "Controls":
            t = font.render(line, True, (200, 210, 255))
        elif line == "":
            y += 14
            continue
        else:
            t = font.render(line, True, (180, 190, 210))
        tw = t.get_width()
        panel.blit(t, ((w - tw) // 2, y))
        y += 28
    screen.blit(panel, (0, 0))


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
