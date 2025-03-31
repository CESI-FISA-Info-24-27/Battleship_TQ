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
        
        # Créer la fenêtre
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Tenter de charger l'icône si elle existe
        try:
            icon_path = os.path.join("assets", "images", "icon.png")
            if os.path.exists(icon_path):
                icon = pygame.image.load(icon_path)
                pygame.display.set_icon(icon)
        except:
            print("Impossible de charger l'icône")
        
        # Initialiser l'horloge pour limiter les FPS
        self.clock = pygame.time.Clock()
        self.running = True
        self.current_screen = "main_screen"  # Écran de démarrage (modifié de "main_screen" à "main_screen")
        
        # Initialiser les paramètres de réseau
        self.network_mode = None  # "host", "client", or "local"
        self.client = None
        self.server = None
        
        # Initialiser les écrans
        self.screens = {
            "main_screen": MainScreen(self),  # Modifié de "main_screen" à "main_screen"
            "connection": ConnectionScreen(self),
            "ship_placement": ShipPlacement(self),
            "game_screen": GameScreen(self),
            "host_screen": HostScreen(self)  # Nouvel écran d'hôte
        }
        
        # Créer les dossiers d'assets s'ils n'existent pas
        self._ensure_assets_folders()
        
    def change_screen(self, screen_name):
        """
        Changer l'écran actif
        
        Args:
            screen_name: Nom de l'écran à afficher
        """
        if screen_name in self.screens:
            self.current_screen = screen_name
        else:
            print(f"Erreur: écran '{screen_name}' non défini")
        
    def set_network_mode(self, mode):
        """
        Définir le mode réseau du jeu
        
        Args:
            mode: "host", "client", ou "local"
        """
        self.network_mode = mode
        
    def run(self):
        """Boucle principale du jeu"""
        while self.running:
            # Gérer les événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                # Déléguer la gestion de l'événement à l'écran actif
                if self.current_screen in self.screens:
                    self.screens[self.current_screen].handle_event(event)
                
            # Mettre à jour l'écran actif
            if self.current_screen in self.screens:
                self.screens[self.current_screen].update()
            
            # Effacer l'écran
            self.screen.fill(BLACK)
            
            # Afficher l'écran actif
            if self.current_screen in self.screens:
                self.screens[self.current_screen].render(self.screen)
            
            # Mettre à jour l'affichage
            pygame.display.flip()
            self.clock.tick(FPS)
            
        # Nettoyage avant de quitter
        self._cleanup()
        
    def _cleanup(self):
        """Nettoyer les ressources avant de quitter"""
        if self.server:
            self.server.stop()
        if self.client:
            self.client.disconnect()
        pygame.quit()
        sys.exit()

    def _host_game(self):
        """Héberger une partie en réseau"""
        self.game.set_network_mode("host")
        self.game.change_screen("host_screen")  # Aller à l'écran d'attente

    def _play_solo(self):
        """Lancer une partie solo contre l'IA"""
        print("Définition du mode solo")  # Message de débogage
        self.game.set_network_mode("solo")  # S'assurer que c'est bien "solo", et pas "local"
        self.game.change_screen("ship_placement")
            
    def _ensure_assets_folders(self):
        """S'assurer que les dossiers d'assets existent"""
        # Créer les dossiers necessaires s'ils n'existent pas
        asset_folders = ["assets", "assets/images", "assets/sounds", "assets/fonts"]
        for folder in asset_folders:
            if not os.path.exists(folder):
                try:
                    os.makedirs(folder)
                except:
                    print(f"Impossible de créer le dossier: {folder}")

if __name__ == "__main__":
    game = Game()
    game.run()