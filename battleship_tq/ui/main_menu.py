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
        self.title_font = pygame.font.SysFont("Arial", 72, bold=True)  # Agrandi
        self.text_font = pygame.font.SysFont("Arial", 28)  # Agrandi
        
        # Boutons
        button_y_start = 350  # Position verticale du premier bouton
        button_spacing = 100  # Espacement entre les boutons
        
        self.button_solo = Button("Jouer en Solo", (SCREEN_WIDTH // 2, button_y_start), (500, 80), 32)
        self.button_online = Button("Jouer en Réseau Local", (SCREEN_WIDTH // 2, button_y_start + button_spacing), (500, 80), 32)
        self.button_quit = Button("Quitter", (SCREEN_WIDTH // 2, button_y_start + 2 * button_spacing), (500, 80), 32)
    
    def draw(self, screen, background_drawer):
        """Dessine le menu principal"""
        # Fond animé de la mer
        background_drawer()
        
        # Panneau semi-transparent pour le titre
        title_panel = pygame.Surface((800, 150), pygame.SRCALPHA)
        title_panel.fill((0, 30, 60, 180))
        pygame.draw.rect(title_panel, GRID_BLUE, (0, 0, 800, 150), 3, 15)
        screen.blit(title_panel, (SCREEN_WIDTH // 2 - 400, 100))
        
        # Titre avec effet de flottement
        offset_y = 5 * math.sin(time.time() * 2)
        
        titre = self.title_font.render("BATTLESHIP TQ", True, WHITE)
        shadow = self.title_font.render("BATTLESHIP TQ", True, GRID_BLUE)
        
        shadow_width = int(titre.get_width() * 1.05)
        shadow_height = int(titre.get_height() * 1.05)
        shadow_scaled = pygame.transform.scale(shadow, (shadow_width, shadow_height))
        
        screen.blit(shadow_scaled, (SCREEN_WIDTH // 2 - shadow_width // 2 + 3, 153 + offset_y))
        screen.blit(titre, (SCREEN_WIDTH // 2 - titre.get_width() // 2, 150 + offset_y))
        
        # Sous-titre
        subtitle = self.text_font.render("Bataille navale tactique", True, WHITE)
        screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 220))
        
        # Panneau semi-transparent pour les boutons
        button_panel = pygame.Surface((600, 350), pygame.SRCALPHA)
        button_panel.fill((0, 30, 60, 180))
        pygame.draw.rect(button_panel, GRID_BLUE, (0, 0, 600, 350), 3, 15)
        screen.blit(button_panel, (SCREEN_WIDTH // 2 - 300, 300))
        
        # Boutons du menu
        self.button_solo.draw(screen, time.time())
        self.button_online.draw(screen, time.time())
        self.button_quit.draw(screen, time.time())
        
        # Version
        version_text = self.text_font.render("v2.0", True, WHITE)
        screen.blit(version_text, (SCREEN_WIDTH - version_text.get_width() - 20, SCREEN_HEIGHT - version_text.get_height() - 20))
    
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
        self.title_font = pygame.font.SysFont("Arial", 48, bold=True)  # Agrandi
        self.text_font = pygame.font.SysFont("Arial", 28)  # Agrandi
        self.small_font = pygame.font.SysFont("Arial", 22)  # Agrandi
        
        # Boutons
        button_y_start = 380  # Position verticale du premier bouton
        button_spacing = 100  # Espacement entre les boutons
        
        self.button_easy = Button("Facile", (SCREEN_WIDTH // 2, button_y_start), (400, 80), 32)
        self.button_medium = Button("Moyen", (SCREEN_WIDTH // 2, button_y_start + button_spacing), (400, 80), 32)
        self.button_hard = Button("Difficile", (SCREEN_WIDTH // 2, button_y_start + 2 * button_spacing), (400, 80), 32)
        self.button_back = Button("Retour", (SCREEN_WIDTH // 2, button_y_start + 3 * button_spacing), (400, 80), 32)
    
    def draw(self, screen, background_drawer):
        """Dessine le menu de difficulté"""
        # Fond animé de la mer
        background_drawer()
        
        # Panneau du titre
        title_panel = pygame.Surface((800, 100), pygame.SRCALPHA)
        title_panel.fill((0, 30, 60, 180))
        pygame.draw.rect(title_panel, GRID_BLUE, (0, 0, 800, 100), 3, 15)
        screen.blit(title_panel, (SCREEN_WIDTH // 2 - 400, 100))
        
        # Titre
        offset_y = 5 * math.sin(time.time() * 2)
        
        titre = self.title_font.render("CHOIX DE LA DIFFICULTÉ", True, WHITE)
        shadow = self.title_font.render("CHOIX DE LA DIFFICULTÉ", True, GRID_BLUE)
        
        screen.blit(shadow, (SCREEN_WIDTH // 2 - shadow.get_width() // 2 + 3, 133 + offset_y))
        screen.blit(titre, (SCREEN_WIDTH // 2 - titre.get_width() // 2, 130 + offset_y))
        
        # Panneau descriptif
        desc_panel = pygame.Surface((800, 180), pygame.SRCALPHA)
        desc_panel.fill((0, 30, 60, 180))
        pygame.draw.rect(desc_panel, GRID_BLUE, (0, 0, 800, 180), 3, 15)
        screen.blit(desc_panel, (SCREEN_WIDTH // 2 - 400, 220))
        
        # Description des difficultés
        descriptions = [
            ("Facile:", "L'adversaire tire au hasard sur votre grille.", (255, 200, 100)),
            ("Moyen:", "L'adversaire cherche à cibler vos navires une fois touchés.", (100, 200, 255)),
            ("Difficile:", "L'adversaire utilise une stratégie avancée pour vous couler.", (255, 100, 100))
        ]
        
        for i, (title, text, color) in enumerate(descriptions):
            title_surf = self.text_font.render(title, True, color)
            desc_surf = self.small_font.render(text, True, WHITE)
            
            screen.blit(title_surf, (SCREEN_WIDTH // 2 - 350, 240 + i * 50))
            screen.blit(desc_surf, (SCREEN_WIDTH // 2 - 200, 240 + i * 50))
        
        # Panneau des boutons
        button_panel = pygame.Surface((600, 450), pygame.SRCALPHA)
        button_panel.fill((0, 30, 60, 180))
        pygame.draw.rect(button_panel, GRID_BLUE, (0, 0, 600, 450), 3, 15)
        screen.blit(button_panel, (SCREEN_WIDTH // 2 - 300, 330))
        
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