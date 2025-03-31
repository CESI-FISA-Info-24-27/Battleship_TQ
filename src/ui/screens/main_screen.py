import pygame
import os
import math  # Ajout de l'import math pour la fonction sin()
from ...utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, BLUE, 
    LIGHT_BLUE, DARK_BLUE, GRAY, TITLE, BUTTON_HOVER_COLOR
)
from ..components.button import Button
from ..components.panel import Panel

class MainScreen:
    """
    Écran d'accueil principal avec design moderne
    """
    
    def __init__(self, game):
        self.game = game
        
        # Charger les polices
        self.title_font = pygame.font.Font(None, 72)
        self.subtitle_font = pygame.font.Font(None, 32)
        
        # Titre
        self.title_text = self.title_font.render(TITLE, True, WHITE)
        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))
        
        # Sous-titre
        self.subtitle_text = self.subtitle_font.render("Stratégie navale", True, LIGHT_BLUE)
        self.subtitle_rect = self.subtitle_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4 + 50))
        
        # Créer un panneau pour les boutons
        panel_width = 300
        panel_height = 350
        panel_x = (SCREEN_WIDTH - panel_width) // 2
        panel_y = SCREEN_HEIGHT // 2 - 50
        
        self.button_panel = Panel(
            panel_x, panel_y, panel_width, panel_height,
            DARK_BLUE, BLUE, 5, 0.8
        )
        
        # Créer les boutons
        button_width = 250
        button_height = 50
        button_margin = 20
        button_x = panel_x + (panel_width - button_width) // 2
        
        button_y = panel_y + 40
        self.solo_button = Button(
            button_x, button_y, button_width, button_height,
            "Mode Solo (vs IA)", self._play_solo,
            font_size=28, border_radius=10,
            bg_color=BLUE, hover_color=BUTTON_HOVER_COLOR
        )
        
        button_y += button_height + button_margin
        self.host_button = Button(
            button_x, button_y, button_width, button_height,
            "Héberger une partie", self._host_game,
            font_size=28, border_radius=10,
            bg_color=BLUE, hover_color=BUTTON_HOVER_COLOR
        )
        
        button_y += button_height + button_margin
        self.join_button = Button(
            button_x, button_y, button_width, button_height,
            "Rejoindre une partie", self._join_game,
            font_size=28, border_radius=10,
            bg_color=BLUE, hover_color=BUTTON_HOVER_COLOR
        )
        
        button_y += button_height + button_margin
        self.quit_button = Button(
            button_x, button_y, button_width, button_height,
            "Quitter", self._quit_game,
            font_size=28, border_radius=10,
            bg_color=BLUE, hover_color=BUTTON_HOVER_COLOR
        )
        
        # Rassembler les boutons pour faciliter la gestion
        self.buttons = [
            self.solo_button,
            self.host_button,
            self.join_button,
            self.quit_button
        ]
        
        # Animation d'onde
        self.wave_offset = 0
        self.wave_speed = 0.5
        
        # Tentative de chargement de l'image de fond
        self.background = None
        try:
            bg_path = os.path.join("assets", "images", "ocean_bg.jpg")
            if os.path.exists(bg_path):
                bg = pygame.image.load(bg_path)
                self.background = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            print("Impossible de charger l'image de fond, utilisation du fond par défaut")
        
        # Version
        self.version_text = pygame.font.Font(None, 20).render("v1.0.0", True, GRAY)
        self.version_rect = self.version_text.get_rect(bottomright=(SCREEN_WIDTH - 10, SCREEN_HEIGHT - 10))
        
    def handle_event(self, event):
        """Gérer les événements d'entrée"""
        for button in self.buttons:
            button.handle_event(event)
            
    def update(self):
        """Mettre à jour l'état de l'écran"""
        # Mettre à jour les boutons
        for button in self.buttons:
            button.update()
            
        # Animation de l'onde
        self.wave_offset = (self.wave_offset + self.wave_speed) % (SCREEN_WIDTH * 2)
            
    def render(self, screen):
        """Rendre l'écran de menu sur la surface donnée"""
        # Fond
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill(BLACK)
            
            # Dessiner des ondes comme fond alternatif
            self._draw_waves(screen)
        
        # Titre et sous-titre
        screen.blit(self.title_text, self.title_rect)
        screen.blit(self.subtitle_text, self.subtitle_rect)
        
        # Panneau de boutons
        self.button_panel.draw(screen)
        
        # Dessiner les boutons
        for button in self.buttons:
            button.draw(screen)
            
        # Version
        screen.blit(self.version_text, self.version_rect)
            
    def _draw_waves(self, screen):
        """Dessiner un effet d'ondes pour le fond"""
        for y in range(0, SCREEN_HEIGHT, 40):
            pygame.draw.lines(
                screen, 
                DARK_BLUE, 
                False,
                [(x, y + 10 * math.sin((x + self.wave_offset) / 50)) 
                 for x in range(0, SCREEN_WIDTH, 10)]
            )
        
    def _play_solo(self):
        """Lancer une partie solo contre l'IA"""
        self.game.set_network_mode("solo")  # Mode solo contre l'IA
        self.game.change_screen("ship_placement")
        
    def _host_game(self):
        """Héberger une partie en réseau"""
        from ...network.server import Server
        
        # Démarrer le serveur
        self.game.server = Server()
        if self.game.server.start():
            # Se connecter aussi en tant que client (joueur 0)
            from ...network.client import Client
            self.game.client = Client()
            if self.game.client.connect():
                self.game.set_network_mode("host")
                self.game.change_screen("ship_placement")
            else:
                # Échec de la connexion en tant que client
                self.game.server.stop()
                self.game.server = None
        else:
            # Échec du démarrage du serveur
            self.game.server = None
            
    def _join_game(self):
        """Rejoindre une partie existante"""
        self.game.set_network_mode("client")
        self.game.change_screen("connection")
        
    def _quit_game(self):
        """Quitter le jeu"""
        self.game.running = False