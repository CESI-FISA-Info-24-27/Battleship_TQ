import pygame
import sys
import os
from src.utils.constants import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, FPS, BLACK, WHITE
from src.ui.screens.main_screen import MainScreen
from src.ui.screens.game_screen import GameScreen
from src.ui.screens.ship_placement import ShipPlacement
from src.ui.screens.connection_screen import ConnectionScreen
from src.ui.screens.host_screen import HostScreen


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        
        # Create the window
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Try to load the icon if it exists
        try:
            icon_path = os.path.join("assets", "images", "icon.png")
            if os.path.exists(icon_path):
                icon = pygame.image.load(icon_path)
                pygame.display.set_icon(icon)
        except:
            print("Unable to load icon")
        
        # Initialize clock to limit FPS
        self.clock = pygame.time.Clock()
        self.running = True
        self.current_screen = "main_screen"  # Starting screen
        
        # Initialize network settings
        self.network_mode = None  # "host", "client", or "local"
        self.client = None
        self.server = None
        
        # Initialize screens
        self.screens = {
            "main_screen": MainScreen(self),
            "connection": ConnectionScreen(self),
            "ship_placement": ShipPlacement(self),
            "game_screen": GameScreen(self),
            "host_screen": HostScreen(self)  # New host screen
        }
        
        # Create asset folders if they don't exist
        self._ensure_assets_folders()
        
    def change_screen(self, screen_name):
        """
        Change the active screen
        
        Args:
            screen_name: Name of the screen to display
        """
        if screen_name in self.screens:
            self.current_screen = screen_name
        else:
            print(f"Error: screen '{screen_name}' not defined")
        
    def set_network_mode(self, mode):
        """
        Set the game's network mode
        
        Args:
            mode: "host", "client", or "local"
        """
        self.network_mode = mode
        
    def run(self):
        """Main game loop"""
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                # Delegate event handling to the active screen
                if self.current_screen in self.screens:
                    self.screens[self.current_screen].handle_event(event)
                
            # Update the active screen
            if self.current_screen in self.screens:
                self.screens[self.current_screen].update()
            
            # Clear the screen
            self.screen.fill(BLACK)
            
            # Render the active screen
            if self.current_screen in self.screens:
                self.screens[self.current_screen].render(self.screen)
            
            # Update display
            pygame.display.flip()
            self.clock.tick(FPS)
            
        # Cleanup before quitting
        self._cleanup()
        
    def _cleanup(self):
        """Clean up resources before quitting"""
        if self.server:
            self.server.stop()
        if self.client:
            self.client.disconnect()
        pygame.quit()
        sys.exit()

    def _host_game(self):
        """Host a network game"""
        self.set_network_mode("host")
        self.change_screen("host_screen")  # Go to waiting screen

    def _play_solo(self):
        """Start a solo game against AI"""
        print("Setting solo mode")  # Debug message
        self.set_network_mode("solo")  # Ensure it's "solo", not "local"
        self.change_screen("ship_placement")
            
    def _ensure_assets_folders(self):
        """Ensure asset folders exist"""
        # Create necessary folders if they don't exist
        asset_folders = ["assets", "assets/images", "assets/sounds", "assets/fonts"]
        for folder in asset_folders:
            if not os.path.exists(folder):
                try:
                    os.makedirs(folder)
                except:
                    print(f"Unable to create folder: {folder}")
    
if __name__ == "__main__":
    game = Game()
    game.run()