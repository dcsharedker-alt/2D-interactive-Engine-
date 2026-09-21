import pygame
import os
import json
import glob

class WorldSelector:
    def __init__(self):
        # Fonts initialized securely
        self.font = pygame.font.SysFont("Consolas", 14)
        self.title_font = pygame.font.SysFont("Arial", 24, bold=True)
        self.header_font = pygame.font.SysFont("Arial", 18, bold=True)
        
        self.state = "MAP_SELECT" # "MAP_SELECT" or "WORLD_EDIT"
        self.category = "Official" # "Official" or "Saved"
        
        self.official_maps = [
            {"name": "Standard Earth", "gravity": 0.35, "restitution": 0.85, "desc": "Standard gravity and bounce. Good for testing.", "balls": []},
            {"name": "Moon Base", "gravity": 0.05, "restitution": 0.60, "desc": "Low gravity environment. Objects float longer.", "balls": []},
            {"name": "Bouncy Castle", "gravity": 0.40, "restitution": 1.0, "desc": "Perfect bounce physics. Energy is never lost.", "balls": []}
        ]
        self.saved_maps = []
        self.load_saved_maps()
        
        self.selected_map_data = None
        
        # UI Rects - Map Select
        self.cat_official_rect = pygame.Rect(20, 100, 160, 40)
        self.cat_saved_rect = pygame.Rect(20, 150, 160, 40)
        self.btn_main_menu = pygame.Rect(20, 520, 160, 40) 
        
        # UI Rects - World Edit
        self.btn_play = pygame.Rect(750, 500, 200, 60)
        self.btn_back = pygame.Rect(20, 20, 100, 40)
        
        # Communication triggers for main.py
        self.launch_game = False
        self.exit_to_menu = False
        self.world_config = None

    def load_saved_maps(self):
        self.saved_maps = []
        os.makedirs("saves", exist_ok=True)
        for filepath in glob.glob("saves/*.json"):
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                    data["filepath"] = filepath 
                    self.saved_maps.append(data)
            except Exception as e:
                print(f"Failed to load map save {filepath}: {e}")

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            
            if self.state == "MAP_SELECT":
                if self.btn_main_menu.collidepoint(mx, my):
                    self.exit_to_menu = True
                    return

                # Category Clicks
                if self.cat_official_rect.collidepoint(mx, my):
                    self.category = "Official"
                elif self.cat_saved_rect.collidepoint(mx, my):
                    self.category = "Saved"
                    self.load_saved_maps()
                
                # Map Grid Clicks
                map_list = self.official_maps if self.category == "Official" else self.saved_maps
                start_x, start_y = 220, 100
                spacing_x, spacing_y = 240, 220
                
                for i, map_data in enumerate(map_list):
                    col = i % 3
                    row = i // 3
                    rect = pygame.Rect(start_x + (col * spacing_x), start_y + (row * spacing_y), 200, 180)
                    if rect.collidepoint(mx, my):
                        self.selected_map_data = map_data.copy()
                        # Ensure baseline config values exist
                        if "gravity" not in self.selected_map_data: self.selected_map_data["gravity"] = 0.35
                        if "restitution" not in self.selected_map_data: self.selected_map_data["restitution"] = 0.85
                        self.state = "WORLD_EDIT"
                        return

            elif self.state == "WORLD_EDIT":
                if self.btn_back.collidepoint(mx, my):
                    self.state = "MAP_SELECT"
                    return
                
                if self.btn_play.collidepoint(mx, my):
                    self.world_config = self.selected_map_data
                    self.launch_game = True
                    return

                # Slider interactions
                if pygame.Rect(250, 150, 30, 30).collidepoint(mx, my): 
                    self.selected_map_data["gravity"] = max(0.0, round(self.selected_map_data["gravity"] - 0.05, 2))
                elif pygame.Rect(390, 150, 30, 30).collidepoint(mx, my): 
                    self.selected_map_data["gravity"] = min(2.0, round(self.selected_map_data["gravity"] + 0.05, 2))

                if pygame.Rect(250, 220, 30, 30).collidepoint(mx, my): 
                    self.selected_map_data["restitution"] = max(0.0, round(self.selected_map_data["restitution"] - 0.05, 2))
                elif pygame.Rect(390, 220, 30, 30).collidepoint(mx, my): 
                    self.selected_map_data["restitution"] = min(1.2, round(self.selected_map_data["restitution"] + 0.05, 2))

    def run_frame(self, screen):
        screen.fill((20, 25, 35))
        mouse_pos = pygame.mouse.get_pos()
        
        if self.state == "MAP_SELECT":
            # Sidebar Setup
            pygame.draw.rect(screen, (30, 35, 45), (0, 0, 200, 800))
            screen.blit(self.title_font.render("Worlds", True, (255, 255, 255)), (20, 30))
            
            # Categories
            for cat, rect in [("Official", self.cat_official_rect), ("Saved", self.cat_saved_rect)]:
                color = (100, 150, 200) if self.category == cat else (50, 60, 70)
                if rect.collidepoint(mouse_pos) and self.category != cat: color = (70, 80, 95)
                pygame.draw.rect(screen, color, rect, border_radius=8)
                txt = self.header_font.render(cat, True, (255, 255, 255))
                screen.blit(txt, (rect.x + 20, rect.centery - txt.get_height()//2))

            # Main Menu Return Button
            btn_color = (200, 80, 80) if self.btn_main_menu.collidepoint(mouse_pos) else (150, 60, 60)
            pygame.draw.rect(screen, btn_color, self.btn_main_menu, border_radius=8)
            mm_txt = self.header_font.render("< Main Menu", True, (255, 255, 255))
            screen.blit(mm_txt, (self.btn_main_menu.x + 20, self.btn_main_menu.centery - mm_txt.get_height()//2))

            # Render Map Grid
            map_list = self.official_maps if self.category == "Official" else self.saved_maps
            start_x, start_y = 220, 100
            spacing_x, spacing_y = 240, 220
            
            if not map_list:
                screen.blit(self.header_font.render("No worlds found in this category.", True, (150, 150, 150)), (250, 120))
            
            for i, map_data in enumerate(map_list):
                col = i % 3
                row = i // 3
                card_rect = pygame.Rect(start_x + (col * spacing_x), start_y + (row * spacing_y), 200, 180)
                
                hover = card_rect.collidepoint(mouse_pos)
                pygame.draw.rect(screen, (50, 60, 70) if hover else (40, 45, 55), card_rect, border_radius=10)
                pygame.draw.rect(screen, (100, 150, 200) if hover else (70, 80, 95), card_rect, 2, border_radius=10)
                
                # Map Image Placeholder
                thumb_rect = pygame.Rect(card_rect.x + 10, card_rect.y + 10, 180, 100)
                pygame.draw.rect(screen, (25, 30, 40), thumb_rect, border_radius=6)
                screen.blit(self.font.render("MAP PREVIEW", True, (100, 110, 120)), (thumb_rect.centerx - 40, thumb_rect.centery - 8))
                
                name_txt = self.font.render(map_data.get("name", "Unknown"), True, (255, 255, 255))
                screen.blit(name_txt, (card_rect.x + 10, card_rect.y + 120))
                
                play_txt = self.font.render("Click to Edit & Play", True, (100, 200, 150))
                screen.blit(play_txt, (card_rect.x + 10, card_rect.y + 150))

        elif self.state == "WORLD_EDIT":
            # Back Button
            pygame.draw.rect(screen, (70, 80, 95), self.btn_back, border_radius=5)
            screen.blit(self.font.render("< BACK", True, (255, 255, 255)), (self.btn_back.x + 25, self.btn_back.y + 12))

            # Left Panel (Settings)
            pygame.draw.rect(screen, (35, 40, 50), (20, 80, 480, 500), border_radius=10)
            screen.blit(self.header_font.render("World Settings", True, (255, 255, 255)), (40, 100))
            
            settings = [
                ("World Gravity:", str(self.selected_map_data.get("gravity", 0.35)), 150),
                ("Bounce (Restitution):", str(self.selected_map_data.get("restitution", 0.85)), 220)
            ]
            
            for label, val, y_pos in settings:
                screen.blit(self.font.render(label, True, (200, 200, 200)), (40, y_pos + 5))
                pygame.draw.rect(screen, (70, 80, 95), (250, y_pos, 30, 30), border_radius=4)
                pygame.draw.rect(screen, (70, 80, 95), (390, y_pos, 30, 30), border_radius=4)
                screen.blit(self.font.render("-", True, (255, 255, 255)), (260, y_pos + 6))
                screen.blit(self.font.render("+", True, (255, 255, 255)), (400, y_pos + 6))
                val_surf = self.header_font.render(val, True, (100, 200, 255))
                screen.blit(val_surf, (335 - val_surf.get_width()//2, y_pos + 4))

            # Right Panel (Preview & Launch)
            pygame.draw.rect(screen, (35, 40, 50), (520, 80, 450, 500), border_radius=10)
            
            thumb_box = pygame.Rect(540, 100, 410, 200)
            pygame.draw.rect(screen, (20, 25, 35), thumb_box, border_radius=8)
            screen.blit(self.header_font.render("WORLD PREVIEW", True, (100, 110, 120)), (thumb_box.centerx - 65, thumb_box.centery - 10))
            
            screen.blit(self.title_font.render(self.selected_map_data.get("name", "Unknown"), True, (255, 255, 255)), (540, 320))
            
            # Safe Description Wrapping
            desc = str(self.selected_map_data.get("desc", "No description available."))
            words = desc.split(' ')
            line = ""
            y_offset = 360
            for word in words:
                if self.font.size(line + word)[0] > 400:
                    screen.blit(self.font.render(line, True, (180, 180, 180)), (540, y_offset))
                    line = word + " "
                    y_offset += 20
                else:
                    line += word + " "
            if line:
                screen.blit(self.font.render(line, True, (180, 180, 180)), (540, y_offset))
            
            # Play Button
            play_hover = self.btn_play.collidepoint(mouse_pos)
            pygame.draw.rect(screen, (46, 204, 113) if not play_hover else (60, 220, 130), self.btn_play, border_radius=8)
            p_txt = self.title_font.render("PLAY", True, (255, 255, 255))
            screen.blit(p_txt, (self.btn_play.centerx - p_txt.get_width()//2, self.btn_play.centery - p_txt.get_height()//2))