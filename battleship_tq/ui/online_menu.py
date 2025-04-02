# online_menu.py
import pygame
import math
import time
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GRID_BLUE, DARK_BLUE, 
    MENU_PRINCIPAL, MENU_ONLINE, JEU_ONLINE
)
from ui.ui_elements import Button, TextBox

class OnlineMenu:
    def __init__(self):
        self.title_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 24)
        self.small_font = pygame.font.SysFont("Arial", 18)
        
        # Boutons
        self.button_create = Button("Créer une partie", (SCREEN_WIDTH // 2, 300))
        self.button_join = Button("Rejoindre une partie", (SCREEN_WIDTH // 2, 380))
        self.button_ai = Button("Jouer contre l'IA en ligne", (SCREEN_WIDTH // 2, 460))
        self.button_back = Button("Retour", (SCREEN_WIDTH // 2, 540))
        
        # État du menu
        self.state = "main"  # "main", "create", "join"
        self.game_code = ""
        self.error_message = ""
        self.error_time = 0
        
        # Champs de texte
        self.code_box = TextBox((SCREEN_WIDTH // 2, 360), (400, 60))
        
        # Boutons supplémentaires
        self.button_connect = Button("Connecter", (SCREEN_WIDTH // 2, 450), (200, 50))
        self.button_cancel = Button("Annuler", (SCREEN_WIDTH // 2, 520), (200, 50))
    
    def draw(self, screen, background_drawer):
        """Dessine le menu en ligne"""
        # Fond animé de la mer
        background_drawer()
        
        # Titre avec effet de flottement
        offset_y = 5 * math.sin(time.time() * 2)
        
        if self.state == "main":
            titre = self.title_font.render("JOUER EN LIGNE", True, WHITE)
            shadow = self.title_font.render("JOUER EN LIGNE", True, GRID_BLUE)
            
            screen.blit(shadow, (SCREEN_WIDTH // 2 - shadow.get_width() // 2 + 3, 103 + offset_y))
            screen.blit(titre, (SCREEN_WIDTH // 2 - titre.get_width() // 2, 100 + offset_y))
            
            # Information sur le serveur
            info = self.small_font.render("Connexion au serveur de jeu en ligne", True, WHITE)
            screen.blit(info, (SCREEN_WIDTH // 2 - info.get_width() // 2, 190))
            
            # Boutons
            self.button_create.draw(screen, time.time())
            self.button_join.draw(screen, time.time())
            self.button_ai.draw(screen, time.time())
            self.button_back.draw(screen, time.time())
            
        elif self.state == "create":
            titre = self.title_font.render("CRÉER UNE PARTIE", True, WHITE)
            shadow = self.title_font.render("CRÉER UNE PARTIE", True, GRID_BLUE)
            
            screen.blit(shadow, (SCREEN_WIDTH // 2 - shadow.get_width() // 2 + 3, 103 + offset_y))
            screen.blit(titre, (SCREEN_WIDTH // 2 - titre.get_width() // 2, 100 + offset_y))
            
            # Information
            info = self.text_font.render("Création d'une nouvelle partie...", True, WHITE)
            screen.blit(info, (SCREEN_WIDTH // 2 - info.get_width() // 2, 200))
            
            # Code de partie généré
            code_text = self.text_font.render("Votre code de partie:", True, WHITE)
            screen.blit(code_text, (SCREEN_WIDTH // 2 - code_text.get_width() // 2, 260))
            
            code = self.title_font.render(self.game_code or "...", True, GRID_BLUE)
            screen.blit(code, (SCREEN_WIDTH // 2 - code.get_width() // 2, 300))
            
            # Message d'attente
            waiting = self.text_font.render("En attente d'un autre joueur...", True, WHITE)
            screen.blit(waiting, (SCREEN_WIDTH // 2 - waiting.get_width() // 2, 370))
            
            # Bouton annuler
            self.button_cancel.draw(screen, time.time())
            
            # Animation d'attente
            dots = "." * (int(time.time() * 2) % 4)
            waiting_anim = self.text_font.render(dots, True, WHITE)
            screen.blit(waiting_anim, (SCREEN_WIDTH // 2 + waiting.get_width() // 2 + 5, 370))
            
        elif self.state == "join":
            titre = self.title_font.render("REJOINDRE UNE PARTIE", True, WHITE)
            shadow = self.title_font.render("REJOINDRE UNE PARTIE", True, GRID_BLUE)
            
            screen.blit(shadow, (SCREEN_WIDTH // 2 - shadow.get_width() // 2 + 3, 103 + offset_y))
            screen.blit(titre, (SCREEN_WIDTH // 2 - titre.get_width() // 2, 100 + offset_y))
            
            # Information
            info = self.text_font.render("Entrez le code de la partie à rejoindre:", True, WHITE)
            screen.blit(info, (SCREEN_WIDTH // 2 - info.get_width() // 2, 200))
            
            # Champ de code
            self.code_box.draw(screen, self.game_code)
            
            # Message d'erreur éventuel
            if self.error_message and time.time() - self.error_time < 3:
                error = self.text_font.render(self.error_message, True, (255, 100, 100))
                screen.blit(error, (SCREEN_WIDTH // 2 - error.get_width() // 2, 420))
            
            # Boutons
            self.button_connect.draw(screen, time.time())
            self.button_cancel.draw(screen, time.time())
    
    def handle_event(self, event):
        """Gère les événements du menu en ligne"""
        if self.state == "main":
            if self.button_create.check_click():
                self.state = "create"
                self.game_code = self._generate_game_code()
                return ("create_game", self.game_code)
            
            if self.button_join.check_click():
                self.state = "join"
                self.game_code = ""
                return MENU_ONLINE
            
            if self.button_ai.check_click():
                return ("start_online_ai",)
            
            if self.button_back.check_click():
                return MENU_PRINCIPAL
        
        elif self.state == "join":
            if self.button_connect.check_click():
                if len(self.game_code) < 5:
                    self.error_message = "Code de partie invalide"
                    self.error_time = time.time()
                    return MENU_ONLINE
                
                return ("join_game", self.game_code)
            
            if self.button_cancel.check_click():
                self.state = "main"
                return MENU_ONLINE
            
            # Gestion de la saisie du code
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.game_code = self.game_code[:-1]
                elif event.key == pygame.K_RETURN:
                    if len(self.game_code) < 5:
                        self.error_message = "Code de partie invalide"
                        self.error_time = time.time()
                    else:
                        return ("join_game", self.game_code)
                elif event.unicode.isalnum() and len(self.game_code) < 6:
                    self.game_code += event.unicode.upper()
        
        elif self.state == "create":
            if self.button_cancel.check_click():
                self.state = "main"
                return ("cancel_game", self.game_code)
        
        return MENU_ONLINE
    
    def _generate_game_code(self):
        """Génère un code de partie aléatoire"""
        import random
        import string
        
        # Générer un code de 6 caractères (lettres et chiffres)
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(6))
    
    def game_created(self, code):
        """Appelé quand une partie est créée"""
        self.state = "create"
        self.game_code = code
    
    def show_error(self, message):
        """Affiche un message d'erreur"""
        self.error_message = message
        self.error_time = time.time()
    
    def reset(self):
        """Réinitialise l'état du menu"""
        self.state = "main"
        self.game_code = ""
        self.error_message = ""

