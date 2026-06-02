import pygame
import os
import sys

def main():
    pygame.init()
    SCREEN_W, SCREEN_H = 1200, 900
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
    pygame.display.set_caption("Tree Extractor - Draw box, press 1=Spring, 2=Summer, 3=Autumn, 4=Winter")

    IMG_PATH = "sprites/low_poly_seasons_trees.png"
    if not os.path.exists(IMG_PATH):
        print(f"Cannot find {IMG_PATH}")
        sys.exit()

    img = pygame.image.load(IMG_PATH).convert_alpha()
    iw, ih = img.get_size()

    # Create directories
    os.makedirs("sprites/trees", exist_ok=True)
    seasons = ["spring", "summer", "autumn", "winter"]
    for s in seasons:
        os.makedirs(os.path.join("sprites/trees", s), exist_ok=True)

    counters = {s: len([f for f in os.listdir(f"sprites/trees/{s}") if f.endswith('.png')]) for s in seasons}

    font = pygame.font.SysFont("sans", 20)

    drawing = False
    start_pos = (0, 0)
    current_rect = None
    saved_rects = []

    running = True
    while running:
        # Scale to fit window
        SCREEN_W, SCREEN_H = screen.get_size()
        scale = min((SCREEN_W - 40) / iw, (SCREEN_H - 120) / ih)
        disp_w, disp_h = int(iw * scale), int(ih * scale)
        
        # Don't scale up past original size
        if scale > 1.0:
            scale = 1.0
            disp_w, disp_h = iw, ih

        scaled_img = pygame.transform.smoothscale(img, (disp_w, disp_h))
        ox = (SCREEN_W - disp_w) // 2
        oy = 80

        screen.fill((30, 34, 42))
        
        # Help text
        instructions = [
            "1. Click and drag to draw a box around a tree.",
            "2. Press 1, 2, 3, or 4 to save it to a season (1=Spring, 2=Summer, 3=Autumn, 4=Winter).",
            "3. The tree is instantly saved as a separate PNG file. Close this when you're done!"
        ]
        for i, text in enumerate(instructions):
            lbl = font.render(text, True, (200, 210, 220))
            screen.blit(lbl, (20, 10 + i * 22))

        screen.blit(scaled_img, (ox, oy))
        
        for r, s in saved_rects:
            # We scale the saved rects to current window size
            scaled_r = pygame.Rect(ox + r.x * scale, oy + r.y * scale, r.w * scale, r.h * scale)
            pygame.draw.rect(screen, (50, 255, 100), scaled_r, 2)
            lbl = font.render(s, True, (50, 255, 100))
            screen.blit(lbl, (scaled_r.x, scaled_r.y - 24))
            
        if current_rect:
            pygame.draw.rect(screen, (100, 200, 255), current_rect, 2)
            
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    drawing = True
                    start_pos = event.pos
                    current_rect = pygame.Rect(start_pos[0], start_pos[1], 0, 0)
                    
            elif event.type == pygame.MOUSEMOTION:
                if drawing:
                    current_rect = pygame.Rect(
                        min(start_pos[0], event.pos[0]),
                        min(start_pos[1], event.pos[1]),
                        abs(event.pos[0] - start_pos[0]),
                        abs(event.pos[1] - start_pos[1])
                    )
                    
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    drawing = False
                    if current_rect and current_rect.width < 10:
                        current_rect = None
                        
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif current_rect and not drawing:
                    season = None
                    if event.key == pygame.K_1: season = "spring"
                    elif event.key == pygame.K_2: season = "summer"
                    elif event.key == pygame.K_3: season = "autumn"
                    elif event.key == pygame.K_4: season = "winter"
                    
                    if season:
                        # Map screen rect back to original image
                        rx = (current_rect.x - ox) / scale
                        ry = (current_rect.y - oy) / scale
                        rw = current_rect.width / scale
                        rh = current_rect.height / scale
                        
                        rx = max(0, min(iw, rx))
                        ry = max(0, min(ih, ry))
                        rw = max(1, min(iw - rx, rw))
                        rh = max(1, min(ih - ry, rh))
                        
                        # Crop and save
                        crop = pygame.Surface((int(rw), int(rh)), pygame.SRCALPHA)
                        crop.blit(img, (0, 0), (int(rx), int(ry), int(rw), int(rh)))
                        
                        idx = counters[season]
                        path = f"sprites/trees/{season}/tree_{idx}.png"
                        pygame.image.save(crop, path)
                        print(f"Saved {path}")
                        counters[season] += 1
                        
                        # Store normalized rect
                        norm_rect = pygame.Rect(rx, ry, rw, rh)
                        saved_rects.append((norm_rect, season))
                        current_rect = None

    pygame.quit()

if __name__ == "__main__":
    main()
