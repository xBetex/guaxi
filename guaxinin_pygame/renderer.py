"""
Rendering functions for the game environment
"""
import pygame
import math
import random
from constants import *


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
    def draw_gradient_sky(self, theme):
        """Draw gradient sky background"""
        sky1 = theme["sky1"]
        sky2 = theme["sky2"]
        sky3 = theme["sky3"]
        
        gradient_height = int(self.height * 0.8)
        
        for y in range(gradient_height):
            # Three-stage gradient
            if y < gradient_height * 0.4:
                t = y / (gradient_height * 0.4)
                color = self._lerp_color(sky1, sky2, t)
            else:
                t = (y - gradient_height * 0.4) / (gradient_height * 0.6)
                color = self._lerp_color(sky2, sky3, t)
            
            pygame.draw.line(self.screen, color, (0, y), (self.width, y))
        
        # Fill bottom with sky3
        pygame.draw.rect(
            self.screen, sky3,
            (0, gradient_height, self.width, self.height - gradient_height)
        )
    
    def _lerp_color(self, c1, c2, t):
        """Linear interpolation between two colors"""
        return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
    
    def draw_stars(self, stars):
        """Draw twinkling stars"""
        for star in stars:
            star["twinkle"] += star["speed"] * 0.4
            alpha = int(((math.sin(star["twinkle"]) + 1) / 2) * 255)
            
            x = int(star["x"] * self.width)
            y = int(star["y"] * self.height * 0.7)
            
            color = (255, 255, 255)
            surf = pygame.Surface((4, 4))
            surf.set_alpha(alpha)
            surf.fill(color)
            self.screen.blit(surf, (x, y))
    
    def draw_shooting_star(self, ss):
        """Draw a single shooting star"""
        pygame.draw.line(
            self.screen,
            (255, 255, 255),
            (ss["x"], ss["y"]),
            (ss["x"] - ss["len"], ss["y"] - ss["len"]),
            2
        )
    
    def draw_celestial_body(self, cx, cy, radius, is_sun, moon_phase=0):
        """Draw sun or moon"""
        if is_sun:
            self._draw_sun(cx, cy, radius)
        else:
            self._draw_moon(cx, cy, radius, moon_phase)
    
    def _draw_sun(self, cx, cy, radius):
        """Draw the sun with rays"""
        # Draw sun disk
        pygame.draw.circle(self.screen, (255, 202, 40), (int(cx), int(cy)), int(radius))
        
        # Draw rays (simplified, no rotation for performance)
        num_rays = 16
        for i in range(num_rays):
            angle = (i / num_rays) * 2 * math.pi
            is_long = i % 2 == 0
            length = radius * (0.58 if is_long else 0.32)
            width = int(radius * (0.09 if is_long else 0.045))
            
            start_x = cx + math.cos(angle) * radius * 1.2
            start_y = cy + math.sin(angle) * radius * 1.2
            end_x = cx + math.cos(angle) * (radius * 1.2 + length)
            end_y = cy + math.sin(angle) * (radius * 1.2 + length)
            
            color = (255, 235, 110) if is_long else (255, 200, 60)
            pygame.draw.line(
                self.screen, color,
                (int(start_x), int(start_y)),
                (int(end_x), int(end_y)),
                max(1, width)
            )
    
    def _draw_moon(self, cx, cy, radius, phase):
        """Draw moon with correct phase"""
        cx, cy, radius = int(cx), int(cy), int(radius)
        
        # Calculate illumination
        illum = (1 - math.cos(phase * 2 * math.pi)) / 2
        waxing = phase <= 0.5
        
        moon_light = (236, 240, 241)
        moon_shadow = (4, 4, 26)
        
        # Draw dark base
        pygame.draw.circle(self.screen, moon_shadow, (cx, cy), radius)
        
        # New moon - draw subtle rim
        if illum < 0.01:
            pygame.draw.circle(self.screen, (180, 190, 210), (cx, cy), int(radius * 0.88), 2)
            return
        
        # Create moon surface
        moon_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        moon_surf.fill((0, 0, 0, 0))
        
        # Draw lit portion
        term_scale = 1 - 2 * illum
        DEAD_BAND = 0.02
        
        if waxing:
            # Right half lit
            pygame.draw.circle(moon_surf, moon_light, (radius, radius), radius)
            
            if term_scale > DEAD_BAND:
                # Crescent - dark ellipse
                ellipse_rect = pygame.Rect(
                    radius, 0,
                    int(radius * term_scale), radius * 2
                )
                pygame.draw.ellipse(moon_surf, moon_shadow, ellipse_rect)
            elif term_scale < -DEAD_BAND:
                # Gibbous - light ellipse extends left
                ellipse_rect = pygame.Rect(
                    radius - int(radius * abs(term_scale)), 0,
                    int(radius * abs(term_scale)), radius * 2
                )
                pygame.draw.ellipse(moon_surf, moon_light, ellipse_rect)
        else:
            # Left half lit
            pygame.draw.circle(moon_surf, moon_light, (radius, radius), radius)
            pygame.draw.circle(moon_surf, moon_shadow, (radius, radius), radius)
            pygame.draw.rect(moon_surf, moon_light, (0, 0, radius, radius * 2))
            
            wts = -term_scale
            if wts > DEAD_BAND:
                ellipse_rect = pygame.Rect(
                    0, 0,
                    int(radius * wts), radius * 2
                )
                pygame.draw.ellipse(moon_surf, moon_light, ellipse_rect)
            elif wts < -DEAD_BAND:
                ellipse_rect = pygame.Rect(
                    radius - int(radius * abs(wts)), 0,
                    int(radius * abs(wts)), radius * 2
                )
                pygame.draw.ellipse(moon_surf, moon_shadow, ellipse_rect)
        
        # Clip to circle
        mask_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(mask_surf, (255, 255, 255, 255), (radius, radius), radius)
        moon_surf.blit(mask_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        
        self.screen.blit(moon_surf, (cx - radius, cy - radius))
    
    def draw_sprite(self, sprite, x, y, scale, season):
        """Draw a pixel sprite at given position"""
        for row_idx, row in enumerate(sprite):
            for col_idx, char in enumerate(row):
                if char == "T":
                    continue
                
                color = get_color(char, season)
                if color:
                    rect = pygame.Rect(
                        x + col_idx * scale,
                        y + row_idx * scale,
                        scale, scale
                    )
                    pygame.draw.rect(self.screen, color, rect)
    
    def draw_blocky_mountain(self, center_x, ground_y, peak_height, base_width, 
                            color_shadow, color_light, has_snow):
        """Draw a blocky mountain"""
        block_size = 16
        steps = max(1, int(peak_height / block_size))
        step_width = base_width / 2 / steps
        
        for i in range(steps):
            cy = ground_y - i * block_size
            chw = base_width / 2 - i * step_width
            
            # Snow on peaks
            if has_snow and i > steps * 0.65:
                shadow_color = (223, 230, 233)
                light_color = (255, 255, 255)
            else:
                shadow_color = color_shadow
                light_color = color_light
            
            # Left side (shadow)
            pygame.draw.rect(
                self.screen, shadow_color,
                (center_x - chw, cy - block_size, chw, block_size)
            )
            
            # Right side (light)
            pygame.draw.rect(
                self.screen, light_color,
                (center_x, cy - block_size, chw, block_size)
            )
    
    def draw_rain(self, ground_y, intensity):
        """Draw rain effect"""
        drop_count = int(100 + intensity * 200)
        
        for _ in range(drop_count):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            length = random.randint(10, 25)
            
            pygame.draw.line(
                self.screen,
                (255, 255, 255, 30),
                (x, y),
                (x - 4, y + length),
                1
            )
    
    def draw_snow(self, snowflakes):
        """Draw snow particles"""
        for flake in snowflakes:
            pygame.draw.circle(
                self.screen,
                (255, 255, 255),
                (int(flake["x"]), int(flake["y"])),
                int(flake["size"])
            )
