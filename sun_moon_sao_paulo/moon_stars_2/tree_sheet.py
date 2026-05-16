import pygame
import os

SHEET_PATH = "sprites/trees.png"
GRID_CONFIG = "sprites/trees.cfg"

SEASONS = ["summer", "autumn", "winter", "spring"]


class TreeSheet:
    def __init__(self):
        self._image = None
        self._vlines = []
        self._hlines = []
        self._loaded = False
        self._load()

    def _load(self):
        if not os.path.exists(SHEET_PATH):
            return
        img = pygame.image.load(SHEET_PATH).convert_alpha()
        iw, ih = img.get_size()

        if os.path.exists(GRID_CONFIG):
            vlines = []
            hlines = []
            with open(GRID_CONFIG) as f:
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
                        vlines[idx] = int(float(v))
                    elif k.startswith("h"):
                        idx = int(k[1:])
                        while len(hlines) <= idx:
                            hlines.append(0)
                        hlines[idx] = int(float(v))
            if len(vlines) >= 2 and len(hlines) >= 2:
                self._vlines = vlines
                self._hlines = hlines
            else:
                self._vlines = [i * (iw // 3) for i in range(4)]
                self._hlines = [i * (ih // 4) for i in range(5)]
        else:
            self._vlines = [i * (iw // 3) for i in range(4)]
            self._hlines = [i * (ih // 4) for i in range(5)]

        self._image = img
        self._loaded = True

    @property
    def available(self):
        return self._loaded

    def get(self, season, variant, size):
        if not self._loaded:
            return None
        try:
            row = SEASONS.index(season)
        except ValueError:
            return None
        cols = len(self._vlines) - 1
        col = max(0, min(cols - 1, variant))
        rows = len(self._hlines) - 1
        if row >= rows:
            return None

        inset = 10
        sx = self._vlines[col] + inset
        sy = self._hlines[row] + inset
        sw = self._vlines[col + 1] - sx - inset
        sh = self._hlines[row + 1] - sy - inset

        if sw <= 0 or sh <= 0:
            return None

        clip = pygame.Surface((sw, sh))
        clip.blit(self._image, (0, 0), (sx, sy, sw, sh))
        clip.set_colorkey((0, 0, 0))
        clip = clip.convert_alpha()
        return pygame.transform.scale(clip, (size, size))

    def reload(self):
        self._image = None
        self._loaded = False
        self._load()
