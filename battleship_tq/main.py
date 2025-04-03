# -*- coding: utf-8 -*-
# main.py
import pygame
import sys
import logging
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, MENU_PRINCIPAL, MENU_DIFFICULTE, 
    PLACEMENT_NAVIRES, JEU_SOLO, JEU_ONLINE, MENU_ONLINE, FIN_PARTIE
)
from game.game_manager import GameManager
from ui.main_menu import MainMenu, DifficultyMenu
from ui.ship_placement import ShipPlacementScreen
from ui.game_screen import GameScreen
from ui.online_menu import OnlineMenu
from ui.game_over_screen import GameOverScreen
from ui.animation import BackgroundAnimation

# Configuration des logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('BattleshipTQ')

class BattleshipTQ:
    """Classe principale du jeu de bataille navale"""
    
    def __init__(self):
        # Initialisation de Pygame
        pygame.init()
        pygame.font.init()
        
        # Création de la fenêtre
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("BATTLESHIP TQ")
        self.clock = pygame.time.get_ticks()
        
        # Gestionnaire de jeu
        self.game_manager = GameManager()
        
        # États et écrans
        self.current_state = MENU_PRINCIPAL
        self.previous_state = None
        self.main_menu = MainMenu()
        self.difficulty_menu = DifficultyMenu()
        self.ship_placement = ShipPlacementScreen(self.game_manager)
        self.game_screen = GameScreen(self.game_manager)
        self.online_menu = OnlineMenu(self.game_manager)
        self.game_over_screen = GameOverScreen(self.game_manager)
        
        # Animation de fond
        self.background = BackgroundAnimation()
        
        logger.info("Jeu initialisé")
    
    def run(self):
        """Boucle principale du jeu"""
        running = True
        clock = pygame.time.Clock()
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                new_state = self.handle_event(event)
                
                if new_state == "quit":
                    running = False
                elif new_state != self.current_state:
                    self._handle_state_transition(new_state)
            
            self.update()
            self.draw()
            clock.tick(60)
        
        # Nettoyage avant de quitter
        self.game_manager.cleanup_network()
        pygame.quit()
        sys.exit()
    
    def handle_event(self, event):
        """Gère les événements selon l'état actuel"""
        if self.current_state == MENU_PRINCIPAL:
            return self.main_menu.handle_event(event)
        
        elif self.current_state == MENU_DIFFICULTE:
            result = self.difficulty_menu.handle_event(event)
            if isinstance(result, tuple) and result[0] == "start_solo":
                self.game_manager.start_solo_game(result[1])
                return PLACEMENT_NAVIRES
            return result
        
        elif self.current_state == PLACEMENT_NAVIRES:
            return self.ship_placement.handle_event(event)
        
        elif self.current_state == JEU_SOLO or self.current_state == JEU_ONLINE:
            return self.game_screen.handle_event(event)
        
        elif self.current_state == MENU_ONLINE:
            result = self.online_menu.handle_event(event)
            return result
        
        elif self.current_state == FIN_PARTIE:
            return self.game_over_screen.handle_event(event)
        
        return self.current_state
    
    def update(self):
        """Met à jour l'état actuel"""
        if self.current_state == PLACEMENT_NAVIRES:
            self.ship_placement.update()
        
        elif self.current_state == JEU_SOLO or self.current_state == JEU_ONLINE:
            self.game_screen.update()
    
    def draw(self):
        """Dessine l'écran selon l'état actuel"""
        if self.current_state == MENU_PRINCIPAL:
            self.main_menu.draw(self.screen, lambda: self.background.draw(self.screen))
        
        elif self.current_state == MENU_DIFFICULTE:
            self.difficulty_menu.draw(self.screen, lambda: self.background.draw(self.screen))
        
        elif self.current_state == PLACEMENT_NAVIRES:
            self.ship_placement.draw(self.screen, lambda: self.background.draw(self.screen))
        
        elif self.current_state == JEU_SOLO or self.current_state == JEU_ONLINE:
            self.game_screen.draw(self.screen, lambda: self.background.draw(self.screen))
        
        elif self.current_state == MENU_ONLINE:
            self.online_menu.draw(self.screen, lambda: self.background.draw(self.screen))
        
        elif self.current_state == FIN_PARTIE:
            self.game_over_screen.draw(self.screen, lambda: self.background.draw(self.screen))
        
        pygame.display.flip()
    
    def _handle_state_transition(self, new_state):
        """Gère les transitions entre les états"""
        logger.info(f"Transition d'état: {self.current_state} -> {new_state}")
        
        # Actions spécifiques lors de transitions particulières
        if new_state == MENU_PRINCIPAL and (self.current_state == MENU_ONLINE or self.current_state == FIN_PARTIE):
            # Nettoyage des ressources réseau quand on revient au menu principal
            logger.info("Nettoyage des ressources réseau lors du retour au menu principal")
            self.game_manager.cleanup_network()
            
            # Réinitialiser le menu online
            self.online_menu = OnlineMenu(self.game_manager)
        
        # Si on entre dans le menu online depuis le menu principal
        if new_state == MENU_ONLINE and self.current_state == MENU_PRINCIPAL:
            # S'assurer que le menu online est réinitialisé
            self.online_menu = OnlineMenu(self.game_manager)
        
        # Stocker l'état précédent
        self.previous_state = self.current_state
        self.current_state = new_state

# Point d'entrée du programme
if __name__ == "__main__":
    game = BattleshipTQ()
    game.run()