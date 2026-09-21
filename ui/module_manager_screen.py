import pygame

def draw_module_manager(screen, font, updater, mouse_pos, mouse_clicked):
    screen.fill((30, 30, 40))
    
    title = font.render("Engine Module Manager (Press ESC to return)", True, (255, 255, 255))
    screen.blit(title, (50, 40))
    
    y_offset = 120
    clicked_module = None

    for module_name, remote_ver in updater.remote_versions.items():
        local_ver = updater.local_versions.get(module_name, "None")
        is_installed = local_ver != "None"
        needs_update = is_installed and local_ver < remote_ver
        
        name_surf = font.render(f"{module_name.upper()} [Local: {local_ver} | Remote: {remote_ver}]", True, (220, 220, 220))
        screen.blit(name_surf, (50, y_offset))
        
        # Disable button logic if something is currently downloading
        button_active = not updater.is_downloading and (not is_installed or needs_update)
        button_rect = pygame.Rect(600, y_offset - 5, 140, 35)
        is_hovering = button_rect.collidepoint(mouse_pos)
        
        if updater.is_downloading and updater.download_target == module_name:
            btn_text = "Downloading..."
            btn_color = (200, 150, 0)
        elif not is_installed:
            btn_text = "Download"
            btn_color = (100, 160, 210) if is_hovering and button_active else (70, 130, 180)
        elif needs_update:
            btn_text = "Update!"
            btn_color = (39, 174, 96) if is_hovering and button_active else (46, 204, 113)
        else:
            btn_text = "Installed"
            btn_color = (100, 100, 100)
            
        pygame.draw.rect(screen, btn_color, button_rect, border_radius=5)
        btn_label = font.render(btn_text, True, (255, 255, 255))
        screen.blit(btn_label, btn_label.get_rect(center=button_rect.center))
        
        if is_hovering and mouse_clicked and button_active:
            clicked_module = module_name
            
        y_offset += 60

    # --- DRAW PROGRESS BAR ---
    if updater.is_downloading:
        bar_width = 800
        bar_height = 30
        x_pos, y_pos = 100, 500
        
        # Background bar
        pygame.draw.rect(screen, (50, 50, 50), (x_pos, y_pos, bar_width, bar_height), border_radius=10)
        
        # Fill bar
        fill_width = int(bar_width * updater.download_progress)
        if fill_width > 0:
            pygame.draw.rect(screen, (46, 204, 113), (x_pos, y_pos, fill_width, bar_height), border_radius=10)
            
        # Progress text
        pct_text = font.render(f"Downloading {updater.download_target}: {int(updater.download_progress * 100)}%", True, (255, 255, 255))
        screen.blit(pct_text, (x_pos, y_pos - 30))

    return clicked_module