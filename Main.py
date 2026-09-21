import pygame
import sys
import os

# Add current directory to path to ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from ui.world_selector import WorldSelector
from physics.normal_mode import NormalPhysicsMode

def main():
    pygame.init()
    # Try to init mixer, but don't crash if it fails
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    except:
        pass
        
    screen = pygame.display.set_mode((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
    pygame.display.set_caption(Config.TITLE)
    clock = pygame.time.Clock()
    
    # State
    current_state = "MENU" 
    world_selector = None
    physics_mode = None
    
    running = True
    while running:
        dt = clock.tick(Config.FPS) / 1000.0
        
        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if current_state == "MENU":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    world_selector = WorldSelector(screen, clock)
                    current_state = "WORLD_SELECT"
                    
            elif current_state == "WORLD_SELECT":
                if world_selector:
                    result = world_selector.handle_event(event)
                    if result:
                        selected_world = result
                        physics_mode = NormalPhysicsMode(screen, clock, selected_world)
                        current_state = "SIMULATION"
                        
            elif current_state == "SIMULATION":
                if physics_mode:
                    physics_mode.handle_event(event)
                    if not physics_mode.running:
                        current_state = "MENU"
                        physics_mode = None
                        world_selector = None

        # Drawing & Updates
        if current_state == "MENU":
            screen.fill(Config.COLOR_BG)
            font = pygame.font.SysFont("Arial", 40, bold=True)
            txt = font.render("Click to Start", True, Config.COLOR_TEXT)
            rect = txt.get_rect(center=(Config.SCREEN_WIDTH//2, Config.SCREEN_HEIGHT//2))
            screen.blit(txt, rect)
            
        elif current_state == "WORLD_SELECT":
            if world_selector:
                world_selector.draw()
                
        elif current_state == "SIMULATION":
            if physics_mode:
                physics_mode.update(dt)
                physics_mode.draw()
            
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()