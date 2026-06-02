import pygame
import os

SHEET_PATH = "sprites/low_poly_seasons_trees.png"
GRID_CONFIG = "sprites/trees.cfg"

# User explicitly said: spring summer fall and winter from top to bottom
SEASONS = ["spring", "summer", "autumn", "winter"]

class TreeSheet:
    def __init__(self):
        self._image = None
        self._individual_trees = {}
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
                self._vlines = [int(i * iw / 4) for i in range(5)]
                self._hlines = [int(i * ih / 4) for i in range(5)]
        else:
            self._vlines = [int(i * iw / 4) for i in range(5)]
            self._hlines = [int(i * ih / 4) for i in range(5)]

        self._image = img
        self._loaded = True

    @property
    def available(self):
        return self._loaded

    def get_variant_count(self, season):
        if not os.path.exists(f"sprites/trees/{season}"):
            return 0
        count = 0
        while os.path.exists(f"sprites/trees/{season}/tree_{count}.png"):
            count += 1
        return count

    def get(self, season, variant, size):
        if not self._loaded:
            return None
        try:
            row = SEASONS.index(season)
        except ValueError:
            return None
        # 1. Try to load individually cropped tree if it exists
        indiv_key = (season, variant)
        if indiv_key not in self._individual_trees:
            path = f"sprites/trees/{season}/tree_{variant}.png"
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                self._individual_trees[indiv_key] = img
            else:
                self._individual_trees[indiv_key] = None
                
        indiv_img = self._individual_trees[indiv_key]
        if indiv_img is not None:
            iw, ih = indiv_img.get_size()
            new_w = int(size * (iw / ih))
            return pygame.transform.smoothscale(indiv_img, (new_w, size))
            
        # If the user has extracted ANY trees for this season, but this specific variant 
        # doesn't exist, we wrap around instead of falling back to grid!
        count = self.get_variant_count(season)
        if count > 0:
            return self.get(season, variant % count, size)

        # 2. Fallback to grid slicing
        cols = len(self._vlines) - 1
        col = max(0, min(cols - 1, variant))
        rows = len(self._hlines) - 1
        if row >= rows:
            return None

        inset = 5
        sx = self._vlines[col] + inset
        sy = self._hlines[row] + inset
        sw = self._vlines[col + 1] - sx - inset
        sh = self._hlines[row + 1] - sy - inset

        if sw <= 0 or sh <= 0:
            return None

        clip = pygame.Surface((sw, sh), pygame.SRCALPHA)
        clip.blit(self._image, (0, 0), (sx, sy, sw, sh))
        new_w = int(size * (sw / sh))
        return pygame.transform.smoothscale(clip, (new_w, size))

    def reload(self):
        self._image = None
        self._loaded = False
        self._load()
