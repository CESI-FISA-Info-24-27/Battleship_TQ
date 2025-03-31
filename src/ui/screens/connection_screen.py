import pygame
import os
import math  # Ajout de l'import de la bibliothèque standard math
from ...utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, BLUE, 
    RED, GREEN, DARK_BLUE, LIGHT_BLUE
)
from ..components.button import Button
from ..components.back_button import BackButton
from ..components.panel import Panel
from ...network.client import Client

class ConnectionScreen:
    """Écran pour entrer l'adresse IP du serveur à rejoindre"""
    
    def __init__(self, game):
        self.game = game
        
        # Polices
        self.title_font = pygame.font.Font(None, 48)
        self.info_font = pygame.font.Font(None, 24)
        self.input_font = pygame.font.Font(None, 32)
        
        # Titre
        self.title_text = self.title_font.render("Rejoindre une partie", True, WHITE)
        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        
        # Panneau principal
        panel_width = 500
        panel_height = 300
        panel_x = (SCREEN_WIDTH - panel_width) // 2
        panel_y = (SCREEN_HEIGHT - panel_height) // 2
        
        self.main_panel = Panel(
            panel_x, panel_y, panel_width, panel_height,
            DARK_BLUE, BLUE, 2, 0.9, 15, True
        )
        
        # Champ de saisie
        input_width = 400
        input_height = 50
        self.input_rect = pygame.Rect(
            panel_x + (panel_width - input_width) // 2,
            panel_y + 120,
            input_width,
            input_height
        )
        self.input_text = "localhost"  # Valeur par défaut
        self.input_active = True
        self.cursor_visible = True
        self.cursor_timer = 0
        
        # Instructions
        self.instructions_text = self.info_font.render(
            "Entrez l'adresse IP du serveur", True, WHITE
        )
        self.instructions_rect = self.instructions_text.get_rect(
            center=(SCREEN_WIDTH // 2, panel_y + 80)
        )
        
        # Bouton de connexion
        button_width = 200
        button_height = 50
        button_margin = 20
        
        self.connect_button = Button(
            panel_x + (panel_width - button_width) // 2,
            panel_y + 200,
            button_width,
            button_height,
            "Se connecter",
            self._connect_to_server,
            font_size=28,
            border_radius=10,
            bg_color=GREEN
        )
        
        # Bouton de retour
        self.back_button = BackButton(30, 30, 30, self._back_to_menu)
        
        # Message d'état (pour les tentatives de connexion)
        self.status_text = ""
        self.status_color = WHITE
        
        # Indicateur de connexion
        self.connecting = False
        self.connection_dots = 0
        self.connection_timer = 0
        
        # Image de fond
        self.background = None
        try:
            bg_path = os.path.join("assets", "images", "ocean_bg.jpg")
            if os.path.exists(bg_path):
                bg = pygame.image.load(bg_path)
                self.background = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            print("Impossible de charger l'image de fond")
        
        # Rassembler les boutons pour faciliter la gestion
        self.buttons = [
            self.connect_button,
            self.back_button
        ]
        
    def handle_event(self, event):
        """Gérer les événements d'entrée"""
        # Gérer les événements des boutons sauf pendant la connexion
        if not self.connecting:
            for button in self.buttons:
                button.handle_event(event)
                
        # Gérer la saisie de texte pour l'adresse du serveur
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Activer/désactiver le champ de saisie lors du clic
            self.input_active = self.input_rect.collidepoint(event.pos)
            
        if event.type == pygame.KEYDOWN and self.input_active and not self.connecting:
            if event.key == pygame.K_RETURN:
                # Se connecter lorsque Entrée est pressée
                self._connect_to_server()
            elif event.key == pygame.K_BACKSPACE:
                # Supprimer le dernier caractère
                self.input_text = self.input_text[:-1]
            else:
                # Ajouter le caractère à la saisie
                if len(self.input_text) < 25:  # Limiter la longueur
                    # Vérifier que le caractère est valide pour une adresse IP
                    valid_chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.-_:"
                    if event.unicode in valid_chars:
                        self.input_text += event.unicode
                    
    def update(self):
        """Mettre à jour l'état de l'écran"""
        # Mettre à jour les boutons
        for button in self.buttons:
            button.update()
            
        # Animation du curseur
        self.cursor_timer += 1
        if self.cursor_timer >= 30:
            self.cursor_timer = 0
            self.cursor_visible = not self.cursor_visible
            
        # Animation de connexion
        if self.connecting:
            self.connection_timer += 1
            if self.connection_timer >= 20:
                self.connection_timer = 0
                self.connection_dots = (self.connection_dots + 1) % 4
                
                # Mettre à jour le texte d'état
                self.status_text = "Tentative de connexion" + "." * self.connection_dots
                
    def render(self, screen):
        """Rendre l'écran de connexion"""
        # Fond
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill(BLACK)
            
            # Dessiner un motif de fond
            self._draw_background_pattern(screen)
        
        # Titre
        screen.blit(self.title_text, self.title_rect)
        
        # Panneau principal
        self.main_panel.draw(screen)
        
        # Instructions
        screen.blit(self.instructions_text, self.instructions_rect)
        
        # Instructions supplémentaires
        instructions_extra = self.info_font.render(
            "Exemple: 192.168.1.10:5555", True, LIGHT_BLUE
        )
        instructions_extra_rect = instructions_extra.get_rect(
            center=(SCREEN_WIDTH // 2, self.instructions_rect.bottom + 20)
        )
        screen.blit(instructions_extra, instructions_extra_rect)
        
        # Champ de saisie
        input_color = LIGHT_BLUE if self.input_active else WHITE
        pygame.draw.rect(screen, BLACK, self.input_rect.inflate(4, 4), border_radius=8)
        pygame.draw.rect(screen, input_color, self.input_rect, 2, border_radius=8)
        
        # Texte de saisie
        text_surface = self.input_font.render(self.input_text, True, WHITE)
        # Assurer que le texte n'est pas trop large pour le champ de saisie
        text_rect = text_surface.get_rect(midleft=(self.input_rect.x + 10, self.input_rect.centery))
        screen.blit(text_surface, text_rect)
        
        # Curseur (si actif)
        if self.input_active and self.cursor_visible and not self.connecting:
            cursor_x = text_rect.right + 2
            if cursor_x < self.input_rect.right - 10:
                pygame.draw.line(
                    screen,
                    WHITE,
                    (cursor_x, self.input_rect.y + 10),
                    (cursor_x, self.input_rect.y + self.input_rect.height - 10),
                    2
                )
        
        # Message d'état (si présent)
        if self.status_text:
            status_surface = self.info_font.render(self.status_text, True, self.status_color)
            status_rect = status_surface.get_rect(center=(SCREEN_WIDTH // 2, self.input_rect.bottom + 50))
            screen.blit(status_surface, status_rect)
        
        # Dessiner les boutons
        if not self.connecting:
            for button in self.buttons:
                button.draw(screen)
                
    def _draw_background_pattern(self, screen):
        """Dessiner un motif de fond"""
        # Dessiner des vagues et des points pour simuler l'eau
        for y in range(0, SCREEN_HEIGHT, 30):
            for x in range(0, SCREEN_WIDTH, 30):
                # Variation de la couleur bleue
                blue_var = (x + y) % 30
                color = (0, 20 + blue_var, 60 + blue_var)
                
                # Dessiner un petit cercle
                pygame.draw.circle(
                    screen, 
                    color, 
                    (x + math.sin(y / 50) * 5, y),  # Utiliser math.sin
                    2
                )
            
    def _connect_to_server(self):
        """Tenter de se connecter au serveur avec l'IP saisie"""
        if self.connecting:
            return
            
        self.connecting = True
        self.status_text = "Tentative de connexion..."
        self.status_color = WHITE
        
        # Créer un nouveau client
        host = self.input_text.strip()
        
        # Séparer l'hôte et le port si spécifiés
        if ":" in host:
            host_parts = host.split(":")
            host_address = host_parts[0]
            try:
                port = int(host_parts[1])
            except ValueError:
                port = 5555  # Port par défaut
            self.game.client = Client(host=host_address, port=port)
        else:
            # Utiliser le port par défaut si non spécifié
            self.game.client = Client(host=host)
        
        # Essayer de se connecter
        def connect_thread():
            """Fonction pour exécuter la connexion dans un thread"""
            import threading
            import time
            
            # Attendre un peu pour montrer l'animation
            time.sleep(1)
            
            success = self.game.client.connect()
            
            if success:
                # Configurer l'écouteur d'état du jeu
                def on_game_state_update(game_state):
                    # Cette fonction sera appelée lorsque le serveur enverra une mise à jour d'état du jeu
                    pass
                    
                self.game.client.set_callback(on_game_state_update)
                
                # Passer à l'écran de placement des navires
                self.status_text = "Connexion réussie!"
                self.status_color = GREEN
                
                # Attendre un court instant pour montrer le message de succès
                time.sleep(0.5)
                
                # Passer à l'écran suivant dans le thread principal
                self.game.set_network_mode("client")
                self.game.change_screen("ship_placement")
                self.connecting = False
            else:
                self.status_text = "Échec de la connexion"
                self.status_color = RED
                self.game.client = None
                self.connecting = False
        
        # Lancer la connexion dans un thread séparé pour ne pas bloquer l'interface
        import threading
        connect_thread = threading.Thread(target=connect_thread)
        connect_thread.daemon = True
        connect_thread.start()
            
    def _back_to_menu(self):
        """Retourner au menu principal"""
        self.game.change_screen("main_screen")
