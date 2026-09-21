import pygame

def draw_home_screen(screen, font, mouse_pos, mouse_clicked):
    screen.fill((20, 20, 20))
    
    title = font.render("HDPS ENGINE - Press 'M' for Modules", True, (255, 255, 255))
    screen.blit(title, (50, 50))
    
    clicked_action = None
    
    # Normal Mode Button
    btn_normal = pygame.Rect(50, 150, 200, 50)
    pygame.draw.rect(screen, (70, 130, 180), btn_normal)
    screen.blit(font.render("Run Normal Mode", True, (255,255,255)), (65, 165))
    
    # HDPS 3D Button
    btn_hdps = pygame.Rect(50, 220, 200, 50)
    pygame.draw.rect(screen, (200, 80, 80), btn_hdps)
    screen.blit(font.render("Run HDPS 3D", True, (255,255,255)), (80, 235))
    
    if mouse_clicked:
        if btn_normal.collidepoint(mouse_pos):
            clicked_action = "NORMAL"
        elif btn_hdps.collidepoint(mouse_pos):
            clicked_action = "HDPS_3D"
            
    return clicked_action