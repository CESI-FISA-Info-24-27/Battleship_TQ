# online_menu.py
import pygame
import math
import time
import threading
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GRID_BLUE, 
    MENU_PRINCIPAL, MENU_ONLINE, JEU_ONLINE, PLACEMENT_NAVIRES
)
from ui.ui_elements import Button, TextBox
from network.client import NetworkClient

class OnlineMenu:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.title_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 24)
        self.small_font = pygame.font.SysFont("Arial", 18)
        
        # Client réseau
        self.network_client = NetworkClient()
        
        # Boutons
        self.button_create = Button("Créer une partie", (SCREEN_WIDTH // 2, 300))
        self.button_join = Button("Rejoindre une partie", (SCREEN_WIDTH // 2, 380))
        self.button_back = Button("Retour", (SCREEN_WIDTH // 2, 460))
        
        # État du menu
        self.state = "main"
        self.game_code = ""
        self.error_message = ""
        self.error_time = 0
        
        # Champs de texte
        self.code_box = TextBox((SCREEN_WIDTH // 2, 360), (400, 60))
        
        # Boutons supplémentaires
        self.button_connect = Button("Rejoindre", (SCREEN_WIDTH // 2, 530), (200, 50))
        self.button_cancel = Button("Annuler", (SCREEN_WIDTH // 2, 600), (200, 50))
        
        # Gestion de la connexion
        self.waiting_connection = False
        self.connection_thread = None
    
    def draw(self, screen, background_drawer):
        """Dessine le menu en ligne local"""
        # Fond animé de la mer
        background_drawer()
        
        # Titre avec effet de flottement
        offset_y = 5 * math.sin(time.time() * 2)
        
        if self.state == "main":
            titre = self.title_font.render("JOUER EN LOCAL", True, WHITE)
            shadow = self.title_font.render("JOUER EN LOCAL", True, GRID_BLUE)
            
            screen.blit(shadow, (SCREEN_WIDTH // 2 - shadow.get_width() // 2 + 3, 103 + offset_y))
            screen.blit(titre, (SCREEN_WIDTH // 2 - titre.get_width() // 2, 100 + offset_y))
            
            # Boutons
            self.button_create.draw(screen, time.time())
            self.button_join.draw(screen, time.time())
            self.button_back.draw(screen, time.time())
        
        elif self.state == "create":
            titre = self.title_font.render("CRÉER UNE PARTIE", True, WHITE)
            shadow = self.title_font.render("CRÉER UNE PARTIE", True, GRID_BLUE)
            
            screen.blit(shadow, (SCREEN_WIDTH // 2 - shadow.get_width() // 2 + 3, 103 + offset_y))
            screen.blit(titre, (SCREEN_WIDTH // 2 - titre.get_width() // 2, 100 + offset_y))
            
            # Code de la partie
            info_text = self.text_font.render("Code de la partie :", True, WHITE)
            screen.blit(info_text, (SCREEN_WIDTH // 2 - 200, 300))
            
            code_text = self.title_font.render(self.game_code, True, (50, 255, 100))
            screen.blit(code_text, (SCREEN_WIDTH // 2 - code_text.get_width() // 2, 350))
            
            # Statut de connexion
            status_text = self.text_font.render(
                "En attente d'un joueur...", 
                True, 
                WHITE
            )
            screen.blit(status_text, (SCREEN_WIDTH // 2 - status_text.get_width() // 2, 450))
            
            # Bouton Annuler
            self.button_cancel.draw(screen, time.time())
        
        elif self.state == "join":
            titre = self.title_font.render("REJOINDRE UNE PARTIE", True, WHITE)
            shadow = self.title_font.render("REJOINDRE UNE PARTIE", True, GRID_BLUE)
            
            screen.blit(shadow, (SCREEN_WIDTH // 2 - shadow.get_width() // 2 + 3, 103 + offset_y))
            screen.blit(titre, (SCREEN_WIDTH // 2 - titre.get_width() // 2, 100 + offset_y))
            
            # Champ Code de partie
            code_label = self.text_font.render("Code de la partie :", True, WHITE)
            screen.blit(code_label, (SCREEN_WIDTH // 2 - 250, 350))
            
            # Champ de texte
            self.code_box.draw(screen, self.game_code)
            
            # Message d'erreur
            if self.error_message and time.time() - self.error_time < 3:
                error = self.text_font.render(self.error_message, True, (255, 100, 100))
                screen.blit(error, (SCREEN_WIDTH // 2 - error.get_width() // 2, 520))
            
            # Boutons
            self.button_connect.draw(screen, time.time())
            self.button_cancel.draw(screen, time.time())
    
    def handle_event(self, event):
        """Gère les événements du menu en ligne local"""
        # Vérifier d'abord les événements personnalisés
        if event.type == pygame.USEREVENT:
            if 'game_code' in event.dict:
                # Connexion réussie pour l'hôte
                self.game_manager.network_client = self.network_client
                self.game_manager.start_online_game()
                return PLACEMENT_NAVIRES
            elif 'error' in event.dict:
                # Erreur de connexion
                self.error_message = event.dict['error']
                self.error_time = time.time()
                self.state = "main"
                return MENU_ONLINE
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Gestion des clics de souris
            if self.state == "main":
                if self.button_create.check_click():
                    # Créer une partie
                    game_code = self.network_client.create_game()
                    if game_code:
                        self.game_code = game_code
                        self.state = "create"
                        self._wait_for_connection()
                    else:
                        self.error_message = "Impossible de créer la partie"
                        self.error_time = time.time()
                    return MENU_ONLINE
                
                if self.button_join.check_click():
                    self.state = "join"
                    self.game_code = ""
                    return MENU_ONLINE
                
                if self.button_back.check_click():
                    return MENU_PRINCIPAL
            
            elif self.state == "create":
                if self.button_cancel.check_click():
                    self.network_client.disconnect()
                    self.state = "main"
                    return MENU_ONLINE
            
            elif self.state == "join":
                # Gestion des clics dans l'état de connexion
                if self.button_connect.check_click():
                    self._try_join_game()
                    return MENU_ONLINE
                
                if self.button_cancel.check_click():
                    self.state = "main"
                    return MENU_ONLINE
        
        # Gestion de la saisie de texte
        if event.type == pygame.KEYDOWN:
            if self.state == "join":
                # Saisie du code de partie
                if event.key == pygame.K_BACKSPACE:
                    if len(self.game_code) > 0:
                        self.game_code = self.game_code[:-1]
                elif event.unicode and len(self.game_code) < 6:
                    if event.unicode.isalnum():
                        self.game_code += event.unicode.upper()
        
        return MENU_ONLINE
    
    def _wait_for_connection(self):
        """Attend la connexion d'un autre joueur"""
        def wait_thread():
            # Attend la connexion (avec un timeout de 5 minutes)
            connection_success = self.network_client.wait_for_connection(300)
            
            if connection_success:
                # Lancer la partie
                pygame.event.post(pygame.event.Event(pygame.USEREVENT, 
                                    {'game_code': self.game_code}))
            else:
                # Timeout ou erreur
                pygame.event.post(pygame.event.Event(pygame.USEREVENT, 
                                    {'error': 'Connexion impossible'}))
        
        # Lancer le thread de connexion
        self.connection_thread = threading.Thread(target=wait_thread)
        self.connection_thread.daemon = True
        self.connection_thread.start()
    
    def _try_join_game(self):
        """Tente de rejoindre une partie"""
        # Vérifier que le code est saisi
        if not self.game_code:
            self.error_message = "Veuillez entrer un code de partie"
            self.error_time = time.time()
            return
        
        # Vérifier la longueur du code
        if len(self.game_code) != 6:
            self.error_message = "Le code doit être de 6 caractères"
            self.error_time = time.time()
            return
        
        # Tentative de rejoindre la partie
        def join_thread():
            try:
                # Essayer de rejoindre la partie
                success, error_code = self.network_client.join_game(self.game_code)
                
                if success:
                    # Posté comme événement personnalisé pour la sécurité du thread
                    pygame.event.post(pygame.event.Event(pygame.USEREVENT, 
                                      {'game_code': self.game_code}))
                else:
                    # Traduire le code d'erreur
                    error_messages = {
                        'NOT_FOUND': "Code de partie invalide",
                        'FULL': "La partie est déjà complète",
                        'IN_PROGRESS': "La partie est déjà en cours",
                        'NETWORK_ERROR': "Erreur de connexion réseau"
                    }
                    error_msg = error_messages.get(error_code, "Erreur de connexion")
                    
                    pygame.event.post(pygame.event.Event(pygame.USEREVENT, 
                                      {'error': error_msg}))
            except Exception as e:
                # Gérer toute autre exception
                pygame.event.post(pygame.event.Event(pygame.USEREVENT, 
                                  {'error': str(e)}))
        
        # Lancer la tentative de connexion dans un thread séparé
        connection_thread = threading.Thread(target=join_thread)
        connection_thread.daemon = True
        connection_thread.start()
    
    def reset(self):
        """Réinitialise l'état du menu"""
        self.state = "main"
        self.game_code = ""
        self.error_message = ""
        self.error_time = 0
        
        # Déconnecter le client réseau
        if self.network_client:
            self.network_client.disconnect()