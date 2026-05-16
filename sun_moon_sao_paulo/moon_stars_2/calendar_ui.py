import pygame
from datetime import datetime, timedelta
from celestial import compute_moon_phase

MONTHS = ["January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December"]
DAYS_IN_MONTH = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
WEEKDAYS = ["S", "M", "T", "W", "T", "F", "S"]


class Calendar:
    def __init__(self, font, font_small):
        self.visible = False
        self.view_month = 1
        self.view_year = 2026
        self.font = font
        self.font_small = font_small
        self.cell = 48
        self.gap = 3
        self._icons = {}
        self._cached_month = -1
        self._arrow_left = pygame.Rect(0, 0, 30, 30)
        self._arrow_right = pygame.Rect(0, 0, 30, 30)

    def toggle(self):
        self.visible = not self.visible

    def go_to_day(self, day_of_year):
        dt = datetime(2026, 1, 1) + timedelta(days=int(day_of_year))
        self.view_month = dt.month

    def _doy(self, month, day):
        return (datetime(2026, month, day) - datetime(2026, 1, 1)).days

    def _first_weekday(self, month):
        return (datetime(2026, month, 1).weekday() + 1) % 7

    def _days_in(self, month):
        return DAYS_IN_MONTH[month - 1]

    def _ensure_icons(self):
        if self._cached_month == self.view_month:
            return
        self._cached_month = self.view_month
        self._icons.clear()
        nd = self._days_in(self.view_month)
        for d in range(1, nd + 1):
            dt = datetime(2026, self.view_month, d)
            phase = compute_moon_phase(dt)
            sz = 18
            icon = pygame.Surface((sz, sz), pygame.SRCALPHA)
            c = sz // 2
            r = sz // 2 - 1
            pygame.draw.circle(icon, (230, 225, 215), (c, c), r)
            if phase <= 0.5:
                soff = -int(4 * r * phase)
            else:
                soff = int(4 * r * (1 - phase))
            shadow = pygame.Surface((sz, sz), pygame.SRCALPHA)
            pygame.draw.circle(shadow, (30, 30, 45), (c + soff, c), r)
            mask = pygame.Surface((sz, sz), pygame.SRCALPHA)
            pygame.draw.circle(mask, (255, 255, 255, 255), (c, c), r)
            shadow.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            icon.blit(shadow, (0, 0))
            pygame.draw.circle(icon, (180, 175, 165), (c, c), r, width=1)
            self._icons[d] = icon

    def handle_event(self, event, slider):
        if not self.visible:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            pw = self._panel_w()
            ph = self._panel_h()
            px = self._panel_x()
            py = self._panel_y()
            if not (px <= mx <= px + pw and py <= my <= py + ph):
                self.visible = False
                return True
            if self._arrow_left.collidepoint(mx, my):
                self.view_month -= 1
                if self.view_month < 1:
                    self.view_month = 12
                self._cached_month = -1
                return True
            if self._arrow_right.collidepoint(mx, my):
                self.view_month += 1
                if self.view_month > 12:
                    self.view_month = 1
                self._cached_month = -1
                return True
            grid_x = px + 20
            grid_y = py + 60
            col = (mx - grid_x) // (self.cell + self.gap)
            row = (my - grid_y) // (self.cell + self.gap)
            if 0 <= col < 7 and 0 <= row < 6:
                cell_idx = row * 7 + col
                first_wd = self._first_weekday(self.view_month)
                day_num = cell_idx - first_wd + 1
                if 1 <= day_num <= self._days_in(self.view_month):
                    doy = self._doy(self.view_month, day_num)
                    slider.value = doy + 0.0
                    self.visible = False
                    return "date_selected"
        return False

    def _panel_x(self):
        return 20

    def _panel_y(self):
        return 60

    def _panel_w(self):
        return 7 * (self.cell + self.gap) + 40

    def _panel_h(self):
        return 6 * (self.cell + self.gap) + 80

    def draw(self, screen):
        if not self.visible:
            return
        px = self._panel_x()
        py = self._panel_y()
        pw = self._panel_w()
        ph = self._panel_h()
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((14, 18, 30, 230))
        for i in range(0, pw, 2):
            pygame.draw.rect(panel, (22, 28, 44, 40), (i, 0, 1, ph))
        pygame.draw.rect(panel, (40, 48, 70), panel.get_rect(), width=2, border_radius=8)

        header = f"{MONTHS[self.view_month - 1]} {self.view_year}"
        ht = self.font.render(header, True, (200, 210, 230))
        panel.blit(ht, (20, 14))

        self._arrow_left = pygame.Rect(px + pw - 70, py + 12, 26, 26)
        self._arrow_right = pygame.Rect(px + pw - 36, py + 12, 26, 26)
        al = self._arrow_left.copy()
        al.x -= px
        al.y -= py
        ar = self._arrow_right.copy()
        ar.x -= px
        ar.y -= py
        pygame.draw.circle(panel, (50, 58, 80), al.center, 13)
        pygame.draw.circle(panel, (50, 58, 80), ar.center, 13)
        pts_l = [(al.centerx - 5, al.centery), (al.centerx + 3, al.centery - 5), (al.centerx + 3, al.centery + 5)]
        pts_r = [(ar.centerx + 5, ar.centery), (ar.centerx - 3, ar.centery - 5), (ar.centerx - 3, ar.centery + 5)]
        pygame.draw.polygon(panel, (160, 175, 210), pts_l)
        pygame.draw.polygon(panel, (160, 175, 210), pts_r)

        self._ensure_icons()
        grid_x = 20
        grid_y = 55
        for i, wd in enumerate(WEEKDAYS):
            wt = self.font_small.render(wd, True, (100, 110, 140))
            wx = grid_x + i * (self.cell + self.gap) + (self.cell - wt.get_width()) // 2
            panel.blit(wt, (wx, grid_y - 16))

        first_wd = self._first_weekday(self.view_month)
        nd = self._days_in(self.view_month)
        current_doy = (datetime.now() - datetime(2026, 1, 1)).days if self.view_year == 2026 else 0

        cell_w = self.cell
        cell_h = self.cell
        for d in range(1, nd + 1):
            idx = first_wd + d - 1
            row = idx // 7
            col = idx % 7
            cx = grid_x + col * (cell_w + self.gap)
            cy = grid_y + row * (cell_h + self.gap)

            doy = self._doy(self.view_month, d)
            is_today = (doy == current_doy)

            cell_bg = (28, 34, 52) if not is_today else (45, 55, 90)
            pygame.draw.rect(panel, cell_bg, (cx, cy, cell_w, cell_h), border_radius=4)
            if is_today:
                pygame.draw.rect(panel, (80, 95, 150), (cx, cy, cell_w, cell_h), width=1, border_radius=4)

            icon = self._icons.get(d)
            if icon:
                ix = cx + (cell_w - icon.get_width()) // 2
                iy = cy + 4
                panel.blit(icon, (ix, iy))

            dn = self.font_small.render(str(d), True, (180, 190, 210))
            dx = cx + (cell_w - dn.get_width()) // 2
            dy = cy + cell_h - dn.get_height() - 3
            panel.blit(dn, (dx, dy))

        screen.blit(panel, (px, py))
