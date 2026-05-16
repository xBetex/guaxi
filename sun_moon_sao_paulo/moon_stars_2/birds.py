import pygame
import math
import random

BIRD_SHAPE = [" TT ", "T T", " TT "]


class Flock:
    def __init__(self, w, h):
        self.birds = []
        self.active = False
        self._timer = 0

    def update(self, dt, hour, speed, w, h):
        spawn_chance = 0.004 * speed
        if hour < 5 or hour >= 20:
            spawn_chance *= 0.3
        elif 6 <= hour < 17:
            spawn_chance *= 0.6

        if not self.active and random.random() < spawn_chance:
            self.active = True
            side = random.choice([-1, 1])
            start_x = -50 if side == 1 else w + 50
            start_y = random.randint(int(h * 0.08), int(h * 0.30))
            count = random.randint(5, 14)
            self.birds = []
            for i in range(count):
                self.birds.append({
                    "x": start_x + i * random.randint(10, 22) * side,
                    "y": start_y + random.randint(-20, 20),
                    "vx": side * random.uniform(40, 90),
                    "vy": random.uniform(-12, 12),
                    "phase": random.uniform(0, math.pi * 2),
                    "flap": random.uniform(0, math.pi * 2),
                })
            self._timer = 0

        if not self.active:
            return

        self._timer += dt * speed
        for b in self.birds[:]:
            b["phase"] += dt * 8 * speed
            b["flap"] += dt * 12 * speed
            b["x"] += b["vx"] * dt * speed
            b["y"] += math.sin(b["phase"]) * 2 + b["vy"] * dt * speed
            if b["x"] < -100 or b["x"] > w + 100 or b["y"] < -80 or b["y"] > h * 0.5:
                self.birds.remove(b)

        if not self.birds or self._timer > 15:
            self.active = False
            self.birds.clear()

    def draw(self, screen):
        if not self.active:
            return
        for b in self.birds:
            sz = 3
            flap = math.sin(b["flap"])
            s = pygame.Surface((sz * 4, sz * 3), pygame.SRCALPHA)
            if flap > 0:
                shape = ["  T ", " T T", "  T "]
            else:
                shape = [" T T", "  T  ", " T T"]
            for y, row in enumerate(shape):
                for x, ch in enumerate(row):
                    if ch == "T":
                        for dx in range(sz):
                            for dy in range(sz):
                                sx = x * sz + dx
                                sy = y * sz + dy
                                if 0 <= sx < s.get_width() and 0 <= sy < s.get_height():
                                    s.set_at((sx, sy), (15, 18, 28))
            screen.blit(s, (int(b["x"]), int(b["y"])))
