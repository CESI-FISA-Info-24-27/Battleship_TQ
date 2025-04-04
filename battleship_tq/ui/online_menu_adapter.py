import pygame
import math
import time
import json
import threading
import os
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GRID_BLUE, 
    MENU_PRINCIPAL, MENU_ONLINE, JEU_ONLINE, PLACEMENT_NAVIRES
)
from ui.ui_elements import Button, TextBox, ProgressBar
from network.battleship_connection import BattleshipConnection

class OnlineMenuAdapter:
    """
    Adaptateur pour l'intégration du serveur externe dans le menu en ligne
    Cette classe fait le lien entre l'interface utilisateur existante et la nouvelle connexion
    """
    
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.title_font = pygame.font.SysFont("Arial", 48, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 28)
        self.small_font = pygame.font.SysFont("Arial", 20)
        
        # Chargement de la configuration
        self.load_config()
        
        # Connexion au serveur externe
        self.connection = None
        
        # Boutons
        self.button_create = Button("Créer une partie", (SCREEN_WIDTH // 2, 300), (400, 70), 28)
        self.button_join = Button("Rejoindre une partie", (SCREEN_WIDTH // 2, 400), (400, 70), 28)
        self.button_back = Button("Retour", (SCREEN_WIDTH // 2, 500), (400, 70), 28)
        
        # État du menu
        self.state = "main"
        self.game_code = ""
        self.server_ip = ""
        self.error_message = ""
        self.error_time = 0
        
        # Champs de texte
        self.code_box = TextBox((SCREEN_WIDTH // 2, 300), (500, 70), 28)
        self.active_box = "code"
        
        # Boutons supplémentaires
        self.button_connect = Button("Rejoindre", (SCREEN_WIDTH // 2, 530), (300, 60), 28)
        self.button_cancel = Button("Annuler", (SCREEN_WIDTH // 2, 620), (300, 60), 28)
        
        # Barre de progression pour l'attente
        self.wait_progress = ProgressBar((SCREEN_WIDTH // 2, 400), (500, 30), 100)
        self.wait_counter = 0
        self.scanning = False
        self.scan_progress = 0
        
        # Gestion de la connexion
        self.waiting_connection = False
        self.connection_thread = None
    
    def load_config(self):
        """Charge la configuration depuis config.json"""
        if not os.path.exists("config.json"):
            # Créer un fichier de configuration par défaut
            with open("config.json", "w") as f:
                json.dump({
                    "username": "JoueurBattleship",
                    "port": 5555,
                    "matchmaking_url": "https://rfosse.pythonanywhere.com"
                }, f, indent=2)
        
        # Charger la configuration
        with open("config.json", "r") as f:
            self.config = json.load(f)
            
        self.username = self.config.get("username", "JoueurBattleship")
        self.port = self.config.get("port", 5555)
        self.server_url = self.config.get("matchmaking_url", "https://rfosse.pythonanywhere.com")
    
    def initialize_connection(self):
        """Initialise la connexion au serveur externe"""
        if not self.connection:
            self.connection = BattleshipConnection(self.username, self.port, self.server_url)
            return self.connection is not None
        return True
    
    def draw(self, screen, background_drawer):
        """Dessine le menu en ligne adapté au serveur externe"""
        # Fond animé de la mer
        background_drawer()
        
        # Titre avec effet de flottement
        offset_y = 5 * math.sin(time.time() * 2)
        
        if self.state == "main":
            titre = self.title_font.render("JOUER EN LIGNE", True, WHITE)
            shadow = self.title_font.render("JOUER EN LIGNE", True, GRID_BLUE)
            
            screen.blit(shadow, (SCREEN_WIDTH // 2 - shadow.get_width() // 2 + 3, 153 + offset_y))
            screen.blit(titre, (SCREEN_WIDTH // 2 - titre.get_width() // 2, 150 + offset_y))
            
            # Informations supplémentaires
            server_info = self.text_font.render(f"Serveur: {self.server_url}", True, WHITE)
            screen.blit(server_info, (SCREEN_WIDTH // 2 - server_info.get_width() // 2, 220))
            
            # Boutons
            self.button_create.draw(screen, time.time())
            self.button_join.draw(screen, time.time())
            self.button_back.draw(screen, time.time())
            
            # Afficher l'erreur si présente
            if self.error_message and time.time() - self.error_time < 5:
                error_panel = pygame.Surface((800, 40), pygame.SRCALPHA)
                error_panel.fill((255, 0, 0, 100))
                screen.blit(error_panel, (SCREEN_WIDTH // 2 - 400, 550))
                
                error = self.text_font.render(self.error_message, True, (255, 255, 255))
                screen.blit(error, (SCREEN_WIDTH // 2 - error.get_width() // 2, 555))
        
        elif self.state == "create":
            titre = self.title_font.render("CRÉER UNE PARTIE", True, WHITE)
            shadow = self.title_font.render("CRÉER UNE PARTIE", True, GRID_BLUE)
            
            screen.blit(shadow, (SCREEN_WIDTH // 2 - shadow.get_width() // 2 + 3, 153 + offset_y))
            screen.blit(titre, (SCREEN_WIDTH // 2 - titre.get_width() // 2, 150 + offset_y))
            
            # Code de la partie
            info_text = self.text_font.render("Code de la partie:", True, WHITE)
            screen.blit(info_text, (SCREEN_WIDTH // 2 - info_text.get_width() // 2, 250))
            
            # Panneau pour afficher le code
            code_panel = pygame.Surface((500, 80), pygame.SRCALPHA)
            code_panel.fill((0, 30, 60, 200))
            pygame.draw.rect(code_panel, GRID_BLUE, (0, 0, 500, 80), 3, 15)
            screen.blit(code_panel, (SCREEN_WIDTH // 2 - 250, 300))
            
            code_text = self.title_font.render(self.game_code, True, (50, 255, 100))
            screen.blit(code_text, (SCREEN_WIDTH // 2 - code_text.get_width() // 2, 320))
            
            # Instructions
            tip_text = self.small_font.render("Partagez ce code avec votre adversaire pour qu'il puisse rejoindre la partie", True, WHITE)
            screen.blit(tip_text, (SCREEN_WIDTH // 2 - tip_text.get_width() // 2, 410))
            
            # Statut de connexion
            status_text = "Non connecté"
            if self.connection:
                status_text = f"En attente d'un adversaire..."
            status_color = (255, 255, 255)
            if "attente" in status_text:
                status_color = (255, 255, 0)
            
            status_render = self.text_font.render(f"État: {status_text}", True, status_color)
            screen.blit(status_render, (SCREEN_WIDTH // 2 - status_render.get_width() // 2, 460))
            
            # Animation d'attente
            self.wait_counter = (self.wait_counter + 1) % 100
            self.wait_progress.update(self.wait_counter)
            self.wait_progress.draw(screen, True)
            
            # Bouton Annuler
            self.button_cancel.draw(screen, time.time())
        
        elif self.state == "join":
            titre = self.title_font.render("REJOINDRE UNE PARTIE", True, WHITE)
            shadow = self.title_font.render("REJOINDRE UNE PARTIE", True, GRID_BLUE)
            
            screen.blit(shadow, (SCREEN_WIDTH // 2 - shadow.get_width() // 2 + 3, 153 + offset_y))
            screen.blit(titre, (SCREEN_WIDTH // 2 - titre.get_width() // 2, 150 + offset_y))
            
            # Instructions
            instructions = self.text_font.render("Entrez le code de la partie:", True, WHITE)
            screen.blit(instructions, (SCREEN_WIDTH // 2 - instructions.get_width() // 2, 250))
            
            # Dessiner le champ de code avec un effet de focus
            code_label = self.text_font.render("Code:", True, WHITE)
            screen.blit(code_label, (SCREEN_WIDTH // 2 - 250, 300))
            
            # Indication que ce champ est actif
            active_indicator = " ▼" if self.active_box == "code" else ""
            active_text = self.small_font.render(active_indicator, True, (50, 255, 100))
            screen.blit(active_text, (SCREEN_WIDTH // 2 - 250 + code_label.get_width() + 10, 300))
            
            # Champ de code
            self.code_box.draw(screen, self.game_code, self.active_box == "code")
            
            # Format du code
            format_text = self.small_font.render("Format: XX-XX-XX-XX ou tout autre code fourni", True, (200, 200, 200))
            screen.blit(format_text, (SCREEN_WIDTH // 2 - 250, 350))
            
            # Message d'erreur
            if self.error_message and time.time() - self.error_time < 5:
                error_panel = pygame.Surface((800, 40), pygame.SRCALPHA)
                error_panel.fill((255, 0, 0, 100))
                screen.blit(error_panel, (SCREEN_WIDTH // 2 - 400, 500))
                
                error = self.text_font.render(self.error_message, True, (255, 255, 255))
                screen.blit(error, (SCREEN_WIDTH // 2 - error.get_width() // 2, 505))
            
            # Boutons
            self.button_connect.draw(screen, time.time())
            self.button_cancel.draw(screen, time.time())
            
            # Animation de recherche
            if self.scanning:
                self.scan_progress = (self.scan_progress + 1) % 100
                progress_text = self.text_font.render(f"Recherche de la partie en cours... {self.scan_progress}%", True, (50, 255, 100))
                screen.blit(progress_text, (SCREEN_WIDTH // 2 - progress_text.get_width() // 2, 600))
    
    def handle_event(self, event):
        """Gère les événements du menu en ligne adapté"""
        # Gérer les clics de souris
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.state == "main":
                if self.button_create.check_click():
                    if self.initialize_connection():
                        # Générer un code de partie
                        self.game_code = f"{self.username}_{int(time.time())}"
                        self.state = "create"
                        self._wait_for_opponent()
                    return MENU_ONLINE
                
                if self.button_join.check_click():
                    if self.initialize_connection():
                        self.state = "join"
                        self.game_code = ""
                    return MENU_ONLINE
                
                if self.button_back.check_click():
                    return MENU_PRINCIPAL
            
            elif self.state == "create":
                if self.button_cancel.check_click():
                    # Annuler la création de partie
                    self.state = "main"
                    self.game_code = ""
                    self.waiting_connection = False
                    return MENU_ONLINE
            
            elif self.state == "join":
                # Vérifier si le clic est sur les champs de texte
                if self.code_box.rect.collidepoint(pygame.mouse.get_pos()):
                    self.active_box = "code"
                
                # Gestion des clics sur les boutons
                if self.button_connect.check_click():
                    if self.connection.join_match(self.game_code):
                        # Mise à jour du game_manager
                        self.game_manager.network_client = self.connection
                        self.game_manager.opponent = self.connection.opponent
                        self.game_manager.is_match_active = True
                        self.game_manager.start_online_game(self.connection.opponent)
                        return PLACEMENT_NAVIRES
                    else:
                        self.error_message = "Impossible de rejoindre cette partie"
                        self.error_time = time.time()
                    return MENU_ONLINE
                
                if self.button_cancel.check_click():
                    self.state = "main"
                    self.game_code = ""
                    return MENU_ONLINE
        
        # Gestion de la saisie de texte
        if event.type == pygame.KEYDOWN and self.state == "join":
            # Changer de champ avec Tab
            if event.key == pygame.K_TAB:
                self.active_box = "ip" if self.active_box == "code" else "code"
            
            # Tenter de se connecter avec Enter
            elif event.key == pygame.K_RETURN:
                if self.connection.join_match(self.game_code):
                    # Mise à jour du game_manager
                    self.game_manager.network_client = self.connection
                    self.game_manager.opponent = self.connection.opponent
                    self.game_manager.is_match_active = True
                    self.game_manager.start_online_game(self.connection.opponent)
                    return PLACEMENT_NAVIRES
                else:
                    self.error_message = "Impossible de rejoindre cette partie"
                    self.error_time = time.time()
                return MENU_ONLINE
            
            # Gestion de la touche Escape pour annuler
            elif event.key == pygame.K_ESCAPE:
                self.state = "main"
                self.game_code = ""
                return MENU_ONLINE
            
            # Saisie du code de partie
            elif self.active_box == "code":
                if event.key == pygame.K_BACKSPACE:
                    self.game_code = self.game_code[:-1]
                elif event.unicode.isalnum() or event.unicode == '-' or event.unicode == '_':
                    self.game_code += event.unicode
        
        # Vérifier si une connexion est établie depuis le mode création
        if self.state == "create" and self.connection and self.connection.is_match_active:
            # Mise à jour du game_manager
            self.game_manager.network_client = self.connection
            self.game_manager.opponent = self.connection.opponent
            self.game_manager.is_match_active = True
            self.game_manager.start_online_game(self.connection.opponent)
            return PLACEMENT_NAVIRES
            
        return MENU_ONLINE
    
    def _wait_for_opponent(self):
        """Attend qu'un adversaire rejoigne la partie"""
        # Générer un code et créer un match
        if not self.connection:
            return
            
        def wait_thread():
            try:
                # Créer une partie avec le code généré
                success = self.connection.create_match(self.game_code)
                if not success:
                    self.error_message = "Impossible de créer la partie"
                    self.error_time = time.time()
                    self.state = "main"
                    return
                    
                # Attendre l'adversaire
                for _ in range(60):  # 60 secondes maximum
                    time.sleep(1)
                    if self.connection.is_match_active:
                        # L'adversaire a rejoint, on peut commencer
                        break
                        
                if not self.connection.is_match_active:
                    # Timeout
                    self.error_message = "Aucun adversaire n'a rejoint la partie"
                    self.error_time = time.time()
                    self.state = "main"
            except Exception as e:
                self.error_message = f"Erreur: {str(e)}"
                self.error_time = time.time()
                self.state = "main"
                
        # Lancer le thread d'attente
        self.waiting_connection = True
        threading.Thread(target=wait_thread, daemon=True).start()