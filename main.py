import pygame
import sys
import os
from src.utils.constants import SCREEN_WIDTH, SCREEN_HEIGHT, TITLE, FPS, BLACK, WHITE, GRAY
from src.ui.screens.main_screen import MainScreen
from src.ui.screens.game_screen import GameScreen
from src.ui.screens.ship_placement import ShipPlacement
from src.ui.screens.connection_screen import ConnectionScreen
from src.ui.screens.host_screen import HostScreen
from src.ui.screens.loading_screen import LoadingScreen


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)
        
        # Initialiser le mixer audio pour la musique et les effets sonores
        try:
            pygame.mixer.init()
        except:
            print("Avertissement: Impossible d'initialiser le système audio")
        
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
        
        # Create asset folders if they don't exist
        self._ensure_assets_folders()
        
        # Afficher l'écran de chargement avant d'initialiser le reste
        loading = LoadingScreen(self)
        loading.run()
        
        # Initialiser le reste du jeu après l'écran de chargement
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
        
        # Musique de fond
        self.background_music_playing = False
        self.play_background_music()
        
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
        # Arrêter la musique avant de quitter
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
            
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
    
    def play_background_music(self):
        """Charge et joue la musique de fond en boucle"""
        if not pygame.mixer.get_init():
            return
            
        try:
            # Chemin vers le fichier de musique
            music_path = os.path.join("assets", "sounds", "background_music.mp3")
            
            # Vérifier si le fichier existe
            if os.path.exists(music_path):
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(0.5)  # Volume à 50%
                pygame.mixer.music.play(-1)  # -1 signifie boucle infinie
                self.background_music_playing = True
                print("Musique de fond lancée")
            else:
                print(f"Fichier de musique introuvable: {music_path}")
        except Exception as e:
            print(f"Erreur lors du chargement de la musique: {e}")
    
    def toggle_music(self):
        """Active ou désactive la musique de fond"""
        if not pygame.mixer.get_init():
            return
            
        if self.background_music_playing:
            pygame.mixer.music.pause()
            self.background_music_playing = False
        else:
            pygame.mixer.music.unpause()
            self.background_music_playing = True
    
if __name__ == "__main__":
    game = Game()
    game.run()