# main_menu.py
import pygame
import math
import time
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GRID_BLUE, DARK_BLUE, 
    MENU_PRINCIPAL, MENU_DIFFICULTE, JEU_SOLO, MENU_ONLINE
)
from ui.ui_elements import Button

class MainMenu:
    def __init__(self):
        self.title_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 24)
        
        # Boutons
        self.button_solo = Button("Jouer en Solo", (SCREEN_WIDTH // 2, 300))
        self.button_online = Button("Jouer en Ligne", (SCREEN_WIDTH // 2, 380))
        self.button_quit = Button("Quitter", (SCREEN_WIDTH // 2, 460))
    
    def draw(self, screen, background_drawer):
        """Dessine le menu principal"""
        # Fond animé de la mer
        background_drawer()
        
        # Titre avec effet de flottement
        offset_y = 5 * math.sin(time.time() * 2)
        
        titre = self.title_font.render("BATTLESHIP TQ", True, WHITE)
        shadow = self.title_font.render("BATTLESHIP TQ", True, GRID_BLUE)
        
        shadow_width = int(titre.get_width() * 1.05)
        shadow_height = int(titre.get_height() * 1.05)
        shadow_scaled = pygame.transform.scale(shadow, (shadow_width, shadow_height))
        
        screen.blit(shadow_scaled, (SCREEN_WIDTH // 2 - shadow_width // 2 + 3, 103 + offset_y))
        screen.blit(titre, (SCREEN_WIDTH // 2 - titre.get_width() // 2, 100 + offset_y))
        
        # Boutons du menu
        self.button_solo.draw(screen, time.time())
        self.button_online.draw(screen, time.time())
        self.button_quit.draw(screen, time.time())
    
    def handle_event(self, event):
        """Gère les événements du menu principal"""
        if self.button_solo.check_click():
            return MENU_DIFFICULTE
        
        if self.button_online.check_click():
            return MENU_ONLINE
        
        if self.button_quit.check_click():
            return "quit"
        
        return MENU_PRINCIPAL

class DifficultyMenu:
    def __init__(self):
        self.title_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 24)
        
        # Boutons
        self.button_easy = Button("Facile", (SCREEN_WIDTH // 2, 300))
        self.button_medium = Button("Moyen", (SCREEN_WIDTH // 2, 380))
        self.button_hard = Button("Difficile", (SCREEN_WIDTH // 2, 460))
        self.button_back = Button("Retour", (SCREEN_WIDTH // 2, 540))
    
    def draw(self, screen, background_drawer):
        """Dessine le menu de difficulté"""
        # Fond animé de la mer
        background_drawer()
        
        # Titre
        offset_y = 5 * math.sin(time.time() * 2)
        
        titre = self.title_font.render("CHOISISSEZ LA DIFFICULTÉ", True, WHITE)
        shadow = self.title_font.render("CHOISISSEZ LA DIFFICULTÉ", True, GRID_BLUE)
        
        screen.blit(shadow, (SCREEN_WIDTH // 2 - shadow.get_width() // 2 + 3, 103 + offset_y))
        screen.blit(titre, (SCREEN_WIDTH // 2 - titre.get_width() // 2, 100 + offset_y))
        
        # Description des difficultés
        descriptions = [
            ("Facile: L'adversaire tire au hasard", 200),
            ("Moyen: L'adversaire cible les navires touchés", 220),
            ("Difficile: L'adversaire utilise une stratégie avancée", 240)
        ]
        
        for text, y in descriptions:
            desc = self.text_font.render(text, True, WHITE)
            screen.blit(desc, (SCREEN_WIDTH // 2 - desc.get_width() // 2, y))
        
        # Boutons
        self.button_easy.draw(screen, time.time())
        self.button_medium.draw(screen, time.time())
        self.button_hard.draw(screen, time.time())
        self.button_back.draw(screen, time.time())
    
    def handle_event(self, event):
        """Gère les événements du menu de difficulté"""
        if self.button_easy.check_click():
            return ("start_solo", 1)  # FACILE
        
        if self.button_medium.check_click():
            return ("start_solo", 2)  # MOYEN
        
        if self.button_hard.check_click():
            return ("start_solo", 3)  # DIFFICILE
        
        if self.button_back.check_click():
            return MENU_PRINCIPAL
        
        return MENU_DIFFICULTE

