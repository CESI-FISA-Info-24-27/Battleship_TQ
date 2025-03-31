# src/ui/screens/host_screen.py
import pygame
import os
from ...utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, BLUE, 
    RED, GREEN, DARK_BLUE, LIGHT_BLUE
)
from ..components.button import Button
from ..components.back_button import BackButton
from ..components.panel import Panel

class HostScreen:
    """Écran d'attente pour l'hôte d'une partie"""
    
    def __init__(self, game):
        self.game = game
        
        # Polices
        self.title_font = pygame.font.Font(None, 48)
        self.info_font = pygame.font.Font(None, 24)
        self.ip_font = pygame.font.Font(None, 36)
        
        # Titre
        self.title_text = self.title_font.render("En attente d'un adversaire", True, WHITE)
        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        
        # Panneau principal
        panel_width = 600
        panel_height = 300
        panel_x = (SCREEN_WIDTH - panel_width) // 2
        panel_y = (SCREEN_HEIGHT - panel_height) // 2
        
        self.main_panel = Panel(
            panel_x, panel_y, panel_width, panel_height,
            DARK_BLUE, BLUE, 2, 0.9, 15, True
        )
        
        # Bouton de retour
        self.back_button = BackButton(30, 30, 30, self._back_to_menu)
        
        # Bouton pour copier l'IP
        self.copy_button = Button(
            panel_x + panel_width // 2 - 100,
            panel_y + 300,
            200,
            40,
            "Copier l'adresse IP",
            self._copy_ip_to_clipboard,
            font_size=20,
            border_radius=10,
            bg_color=GREEN
        )
        
        # Messages de statut
        self.status_text = "Initialisation du serveur..."
        self.status_color = WHITE
        self.ip_text = ""
        
        # Animation pour montrer que le serveur est en attente
        self.waiting_dots = 0
        self.waiting_timer = 0
        
        # Image de fond
        self.background = None
        try:
            bg_path = os.path.join("assets", "images", "ocean_bg.jpg")
            if os.path.exists(bg_path):
                bg = pygame.image.load(bg_path)
                self.background = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            print("Impossible de charger l'image de fond")
            
        # Variables
        self.server_started = False
        self.client_connected = False
        
    def handle_event(self, event):
        """Gérer les événements d'entrée"""
        # Gérer les événements du bouton de retour
        self.back_button.handle_event(event)
        
        # Gérer les événements du bouton de copie
        self.copy_button.handle_event(event)
            
    def update(self):
        """Mettre à jour l'état de l'écran"""
        self.back_button.update()
        self.copy_button.update()
        
        # Démarrer le serveur si ce n'est pas déjà fait
        if not self.server_started:
            self._start_server()
            
        # Vérifier si un client s'est connecté
        if self.server_started and self.game.client:
            if hasattr(self.game.client, 'game_state') and self.game.client.game_state:
                if len(self.game.client.game_state.players) >= 2:
                    if self.game.client.game_state.players[1].ready:
                        self.client_connected = True
                        self.status_text = "Joueur connecté! Redirection..."
                        self.status_color = GREEN
                        
                        # Rediriger vers l'écran de placement après un court délai
                        import threading
                        import time
                        
                        def redirect():
                            time.sleep(1)
                            self.game.change_screen("ship_placement")
                            
                        thread = threading.Thread(target=redirect)
                        thread.daemon = True
                        thread.start()
                        
        # Animation des points d'attente
        self.waiting_timer += 1
        if self.waiting_timer >= 30:
            self.waiting_timer = 0
            self.waiting_dots = (self.waiting_dots + 1) % 4
            
            if not self.client_connected:
                self.status_text = "En attente d'un joueur" + "." * self.waiting_dots
            
    def render(self, screen):
        """Rendre l'écran d'attente"""
        # Fond
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill(BLACK)
            
        # Titre
        screen.blit(self.title_text, self.title_rect)
        
        # Panneau principal
        self.main_panel.draw(screen)
        
        # Adresse IP
        if self.ip_text:
            ip_surface = self.ip_font.render(self.ip_text, True, WHITE)
            ip_rect = ip_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(ip_surface, ip_rect)
            
            # Instructions
            instructions = [
                "Partagez cette adresse IP avec votre adversaire",
                "Il devra cliquer sur \"Rejoindre une partie\" et saisir cette adresse"
            ]
            
            for i, text in enumerate(instructions):
                instr_surface = self.info_font.render(text, True, LIGHT_BLUE)
                instr_rect = instr_surface.get_rect(
                    center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40 + i * 30)
                )
                screen.blit(instr_surface, instr_rect)
        
        # Statut
        status_surface = self.info_font.render(self.status_text, True, self.status_color)
        status_rect = status_surface.get_rect(
            center=(SCREEN_WIDTH // 2, self.main_panel.rect.bottom - 50)
        )
        screen.blit(status_surface, status_rect)
        
        # Bouton de retour
        self.back_button.draw(screen)
        
        # Bouton pour copier l'IP
        if self.ip_text:
            self.copy_button.draw(screen)
            
    def _start_server(self):
        """Démarrer le serveur de jeu"""
        from ...network.server import Server
        
        # Démarrer le serveur
        self.game.server = Server()
        if self.game.server.start():
            # Récupérer l'IP locale
            if hasattr(self.game.server, 'local_ip'):
                self.ip_text = f"{self.game.server.local_ip}:{self.game.server.port}"
                self.status_text = "Serveur démarré, en attente d'un joueur..."
                self.status_color = GREEN
                
                # Se connecter aussi en tant que client (joueur 0)
                from ...network.client import Client
                self.game.client = Client()
                if self.game.client.connect():
                    self.game.set_network_mode("host")
                    self.server_started = True
                else:
                    # Échec de la connexion en tant que client
                    self.game.server.stop()
                    self.game.server = None
                    self.status_text = "Erreur: Impossible de se connecter en tant qu'hôte"
                    self.status_color = RED
            else:
                self.status_text = "Erreur: Impossible d'obtenir l'adresse IP locale"
                self.status_color = RED
        else:
            # Échec du démarrage du serveur
            self.game.server = None
            self.status_text = "Erreur: Impossible de démarrer le serveur"
            self.status_color = RED
            
    def _copy_ip_to_clipboard(self):
        """Copier l'adresse IP dans le presse-papiers"""
        if self.ip_text:
            try:
                import pyperclip
                pyperclip.copy(self.ip_text)
                self.status_text = "Adresse IP copiée dans le presse-papiers!"
                self.status_color = GREEN
            except:
                # Fallback si pyperclip n'est pas disponible
                self.status_text = "Impossible de copier (pyperclip non installé)"
                self.status_color = RED
    
    def _back_to_menu(self):
        """Retourner au menu principal"""
        # Arrêter le serveur
        if self.game.server:
            self.game.server.stop()
            self.game.server = None
            
        # Déconnecter le client
        if self.game.client:
            self.game.client.disconnect()
            self.game.client = None
            
        # Retourner au menu principal
        self.game.change_screen("main_screen")