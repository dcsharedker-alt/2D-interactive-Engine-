import pygame
from config import Config
from ui.ui_components import Button

class WorldSelector:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.buttons = []
        self.selected = None
        
        worlds = [
            {"name": "Standard Gravity", "gravity": 9.8},
            {"name": "Low Gravity (Moon)", "gravity": 1.6},
            {"name": "High Gravity (Jupiter)", "gravity": 24.8},
            {"name": "Zero Gravity", "gravity": 0}
        ]
        
        y_start = 150
        for i, world in enumerate(worlds):
            rect = pygame.Rect(Config.SCREEN_WIDTH//2 - 150, y_start + i*60, 300, 50)
            btn = Button(rect, world["name"])
            # Use a default arg to capture current world
            btn.callback = lambda w=world: setattr(self, 'selected', w) # type: ignore
            self.buttons.append(btn)

    def handle_event(self, event):
        for btn in self.buttons:
            if btn.handle_event(event):
                return True
        return False

    def get_selected_world(self):
        return self.selected

    def draw(self):
        self.screen.fill(Config.COLOR_BG)
        font = pygame.font.SysFont("Arial", 30)
        title = font.render("Select a World", True, Config.COLOR_TEXT)
        self.screen.blit(title, (Config.SCREEN_WIDTH//2 - title.get_width()//2, 50))
        for btn in self.buttons:
            btn.draw(self.screen)