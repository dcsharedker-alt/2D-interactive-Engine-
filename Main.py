import pygame
import sys
from config import Config

# Updated imports to match your folder structure
from ui.world_selector import WorldSelector
from physics.normal_mode import NormalPhysicsMode

def main():
    pygame.init()
    screen = pygame.display.set_mode((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
    pygame.display.set_caption(Config.TITLE)
    clock = pygame.time.Clock()
    
    # State
    current_state = "MENU" 
    world_selector = WorldSelector(screen, clock)
    physics_mode = None
    
    running = True
    while running:
        dt = clock.tick(Config.FPS) / 1000.0
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if current_state == "MENU":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    current_state = "WORLD_SELECT"
                    
            elif current_state == "WORLD_SELECT":
                if world_selector.handle_event(event):
                    selected_world = world_selector.get_selected_world()
                    if selected_world:
                        physics_mode = NormalPhysicsMode(screen, clock, selected_world)
                        current_state = "SIMULATION"
                        
            elif current_state == "SIMULATION":
                physics_mode.handle_event(event)
                if not physics_mode.running:
                    current_state = "MENU"
                    physics_mode = None

        if current_state == "MENU":
            screen.fill(Config.COLOR_BG)
            font = pygame.font.SysFont("Arial", 40)
            txt = font.render("Click to Start", True, Config.COLOR_TEXT)
            screen.blit(txt, (Config.SCREEN_WIDTH//2 - txt.get_width()//2, Config.SCREEN_HEIGHT//2))
            
        elif current_state == "WORLD_SELECT":
            world_selector.draw()
            
        elif current_state == "SIMULATION":
            physics_mode.update(dt)
            physics_mode.draw()
            
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()