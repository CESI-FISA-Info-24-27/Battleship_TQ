import pygame
import sys
from src.utils.constants import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, FPS, BLACK, WHITE
from src.ui.screens.main_menu import MainMenu
from src.ui.screens.game_screen import GameScreen
from src.ui.screens.ship_placement import ShipPlacement
from src.ui.screens.connection_screen import ConnectionScreen

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.current_screen = "main_menu"
        self.screens = {
            "main_menu": MainMenu(self),
            "connection": ConnectionScreen(self),
            "ship_placement": ShipPlacement(self),
            "game": GameScreen(self)
        }
        self.network_mode = None  # "host", "client", or "local"
        self.client = None
        self.server = None
        
    def change_screen(self, screen_name):
        self.current_screen = screen_name
        
    def set_network_mode(self, mode):
        self.network_mode = mode
        
    def run(self):
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.screens[self.current_screen].handle_event(event)
                
            # Update current screen
            self.screens[self.current_screen].update()
            
            # Clear screen
            self.screen.fill(BLACK)
            
            # Render current screen
            self.screens[self.current_screen].render(self.screen)
            
            # Flip display
            pygame.display.flip()
            self.clock.tick(FPS)
            
        # Clean up
        if self.server:
            self.server.stop()
        if self.client:
            self.client.disconnect()
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()