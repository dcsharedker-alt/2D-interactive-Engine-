import pygame

def draw_settings_screen(screen, font, mouse_pos, mouse_clicked):
    # Dark modern background
    screen.fill((45, 45, 55))
    
    title = font.render("Engine Settings (Press ESC to return)", True, (255, 255, 255))
    screen.blit(title, (50, 40))

    # Mockup of setting options
    settings = [
        {"label": "Master Volume", "val": 0.8},
        {"label": "Music Volume", "val": 0.3},
        {"label": "SFX Volume", "val": 0.6},
        {"label": "Show FPS", "val": 1.0}
    ]
    
    y = 120
    for item in settings:
        # Draw Label
        label = font.render(item["label"], True, (220, 220, 220))
        screen.blit(label, (50, y))
        
        # Draw Background Track
        track_rect = pygame.Rect(300, y + 5, 200, 10)
        pygame.draw.rect(screen, (30, 30, 40), track_rect, border_radius=5)
        
        # Draw Fill and Handle
        fill_width = int(200 * item["val"])
        if fill_width > 0:
            pygame.draw.rect(screen, (70, 130, 180), (300, y + 5, fill_width, 10), border_radius=5)
        pygame.draw.circle(screen, (200, 220, 255), (300 + fill_width, y + 10), 10)
        
        y += 60