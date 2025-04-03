# online_menu.py
import pygame
import math
import time
import threading
import ipaddress
import logging
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GRID_BLUE, 
    MENU_PRINCIPAL, MENU_ONLINE, JEU_ONLINE, PLACEMENT_NAVIRES
)
from ui.ui_elements import Button, TextBox, ProgressBar
from network.client import NetworkClient

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('OnlineMenu')

class OnlineMenu:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        self.title_font = pygame.font.SysFont("Arial", 48, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 28)
        self.small_font = pygame.font.SysFont("Arial", 20)
        
        # Client réseau - IMPORTANT: Créer une nouvelle instance à chaque initialisation
        self.network_client = None
        self._create_new_network_client()
        
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
        self.ip_box = TextBox((SCREEN_WIDTH // 2, 400), (500, 70), 28)
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
    
    def _create_new_network_client(self):
        """Crée une nouvelle instance du client réseau"""
        # D'abord nettoyer l'ancienne instance si elle existe
        if self.network_client:
            try:
                self.network_client.disconnect()
            except Exception as e:
                logger.error(f"Erreur lors de la déconnexion: {e}")
        
        # Créer une nouvelle instance
        self.network_client = NetworkClient()
        logger.info("Nouvelle instance de NetworkClient créée")
    
    def draw(self, screen, background_drawer):
        """Dessine le menu en ligne local"""
        # Fond animé de la mer
        background_drawer()
        
        # Titre avec effet de flottement
        offset_y = 5 * math.sin(time.time() * 2)
        
        if self.state == "main":
            titre = self.title_font.render("JOUER EN RÉSEAU LOCAL", True, WHITE)
            shadow = self.title_font.render("JOUER EN RÉSEAU LOCAL", True, GRID_BLUE)
            
            screen.blit(shadow, (SCREEN_WIDTH // 2 - shadow.get_width() // 2 + 3, 153 + offset_y))
            screen.blit(titre, (SCREEN_WIDTH // 2 - titre.get_width() // 2, 150 + offset_y))
            
            # Informations supplémentaires
            ip_info = self.text_font.render(f"Votre adresse IP: {self.network_client._get_local_ip()}", True, WHITE)
            screen.blit(ip_info, (SCREEN_WIDTH // 2 - ip_info.get_width() // 2, 220))
            
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
            connection_status = "Non connecté"
            if self.network_client:
                connection_status = self.network_client.connection_status
            
            status_text = self.text_font.render(
                f"État: {connection_status}", 
                True, 
                (50, 255, 100) if "Connecté" in connection_status else WHITE
            )
            screen.blit(status_text, (SCREEN_WIDTH // 2 - status_text.get_width() // 2, 460))
            
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
            format_text = self.small_font.render("Format: XX-XX-XX-XX", True, (200, 200, 200))
            screen.blit(format_text, (SCREEN_WIDTH // 2 - 250, 350))
            
            # Champ d'IP (optionnel)
            ip_label = self.text_font.render("IP (optionnel):", True, WHITE)
            screen.blit(ip_label, (SCREEN_WIDTH // 2 - 250, 400))
            
            # Indication que ce champ est actif
            active_indicator = " ▼" if self.active_box == "ip" else ""
            active_text = self.small_font.render(active_indicator, True, (50, 255, 100))
            screen.blit(active_text, (SCREEN_WIDTH // 2 - 250 + ip_label.get_width() + 10, 400))
            
            # Champ d'IP
            self.ip_box.draw(screen, self.server_ip, self.active_box == "ip")
            
            # Message d'aide
            help_text = self.small_font.render("Si vous connaissez l'IP de l'hôte, entrez-la pour une connexion plus rapide", True, WHITE)
            screen.blit(help_text, (SCREEN_WIDTH // 2 - help_text.get_width() // 2, 470))
            
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
                progress_text = self.text_font.render(f"Recherche de l'hôte en cours... {self.scan_progress}%", True, (50, 255, 100))
                screen.blit(progress_text, (SCREEN_WIDTH // 2 - progress_text.get_width() // 2, 680))
    
    def handle_event(self, event):
        """Gère les événements du menu en ligne local"""
        # Vérifier d'abord les événements personnalisés
        if event.type == pygame.USEREVENT:
            if event.dict.get('success'):
                # Connexion réussie
                self.game_manager.network_client = self.network_client
                self.game_manager.start_online_game()
                return PLACEMENT_NAVIRES
            elif 'error' in event.dict:
                # Erreur de connexion
                self.error_message = event.dict['error']
                self.error_time = time.time()
                self.scanning = False
                # Créer une nouvelle instance du client réseau pour éviter des problèmes
                self._create_new_network_client()
                self.state = "main"
                return MENU_ONLINE
        
        # Gérer les clics de souris
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = pygame.mouse.get_pos()
            
            # Menu principal
            if self.state == "main":
                if self.button_create.check_click():
                    # Être sûr d'avoir une nouvelle instance du client
                    self._create_new_network_client()
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
                    # Être sûr d'avoir une nouvelle instance du client
                    self._create_new_network_client()
                    self.state = "join"
                    self.game_code = ""
                    self.server_ip = ""
                    return MENU_ONLINE
                
                if self.button_back.check_click():
                    return MENU_PRINCIPAL
            
            # Écran de création
            elif self.state == "create":
                if self.button_cancel.check_click():
                    logger.info("Annulation de la création de partie")
                    # Fermer proprement le client réseau avant de retourner au menu
                    if self.network_client:
                        self.network_client.disconnect()
                    # Créer une nouvelle instance pour éviter les problèmes après annulation
                    self._create_new_network_client()
                    self.state = "main"
                    return MENU_ONLINE
            
            # Écran de connexion
            elif self.state == "join":
                # Vérifier si le clic est sur les champs de texte
                if self.code_box.rect.collidepoint(mouse_pos):
                    self.active_box = "code"
                elif self.ip_box.rect.collidepoint(mouse_pos):
                    self.active_box = "ip"
                
                # Gestion des clics sur les boutons
                if self.button_connect.check_click():
                    self._try_join_game()
                    return MENU_ONLINE
                
                if self.button_cancel.check_click():
                    logger.info("Annulation de la connexion à une partie")
                    # Fermer proprement le client réseau avant de retourner au menu
                    if self.network_client:
                        self.network_client.disconnect()
                    # Créer une nouvelle instance pour éviter les problèmes après annulation
                    self._create_new_network_client()
                    self.state = "main"
                    return MENU_ONLINE
        
        # Gestion de la saisie de texte
        if event.type == pygame.KEYDOWN:
            if self.state == "join":
                # Changer de champ avec Tab
                if event.key == pygame.K_TAB:
                    self.active_box = "ip" if self.active_box == "code" else "code"
                
                # Tenter de se connecter avec Enter
                elif event.key == pygame.K_RETURN:
                    self._try_join_game()
                    return MENU_ONLINE
                
                # Gestion de la touche Escape pour annuler
                elif event.key == pygame.K_ESCAPE:
                    # Fermer proprement le client réseau avant de retourner au menu
                    if self.network_client:
                        self.network_client.disconnect()
                    # Créer une nouvelle instance pour éviter les problèmes après annulation
                    self._create_new_network_client()
                    self.state = "main"
                    return MENU_ONLINE
                
                # Saisie du code de partie
                elif self.active_box == "code":
                    if event.key == pygame.K_BACKSPACE:
                        # Si on supprime un caractère, supprimer aussi le tiret si nécessaire
                        if len(self.game_code) > 0:
                            if self.game_code[-1] == '-':
                                self.game_code = self.game_code[:-1]
                            self.game_code = self.game_code[:-1]
                    # Saisie du code avec gestion simplifiée - MODIFICATION SPÉCIFIQUE ICI
                    elif event.unicode and event.unicode.isalnum():
                        # Si le code est vide, on ajoute simplement le caractère
                        if not self.game_code:
                            self.game_code = event.unicode.upper()
                        else:
                            # On compte les parties et le nombre de caractères dans la dernière partie
                            parts = self.game_code.split('-')
                            last_part = parts[-1] if parts else ""
                            
                            # Si la dernière partie contient déjà 2 caractères, on ajoute un tiret
                            if len(last_part) == 2 and len(parts) < 4:
                                self.game_code += "-" + event.unicode.upper()
                            # Sinon, on ajoute simplement le caractère
                            else:
                                self.game_code += event.unicode.upper()
                
                # Saisie de l'IP
                elif self.active_box == "ip":
                    if event.key == pygame.K_BACKSPACE:
                        self.server_ip = self.server_ip[:-1]
                    elif event.unicode:
                        if event.unicode.isdigit() or event.unicode == '.':
                            self.server_ip += event.unicode
        
        return MENU_ONLINE
    
    def _wait_for_connection(self):
        """Attend la connexion d'un autre joueur"""
        def wait_thread():
            # Attend la connexion (avec un timeout de 5 minutes)
            try:
                connection_success = self.network_client.wait_for_connection(300)
                
                if connection_success and self.network_client.is_connected():
                    # Lancer la partie
                    pygame.event.post(pygame.event.Event(pygame.USEREVENT, 
                                        {'success': True}))
                else:
                    # Timeout ou erreur
                    error_msg = "Connexion impossible - aucun joueur n'a rejoint la partie"
                    pygame.event.post(pygame.event.Event(pygame.USEREVENT, 
                                        {'error': error_msg}))
            except Exception as e:
                logger.error(f"Erreur dans le thread d'attente: {e}")
                pygame.event.post(pygame.event.Event(pygame.USEREVENT, 
                                  {'error': f"Erreur de connexion: {str(e)}"}))
        
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
        
        # Vérifier et compléter le code si nécessaire
        parts = self.game_code.split('-')
        
        # S'assurer qu'il y a au moins 3 parties avec 2 caractères chacune
        if len(parts) < 3 or any(len(part) < 2 for part in parts[:3]):
            self.error_message = "Format de code invalide. Utilisez le format XX-XX-XX-XX"
            self.error_time = time.time()
            return
        
        # Compléter le code si nécessaire
        completed_code = self.game_code
        if len(parts) == 3:
            # Ajouter la quatrième partie manquante
            completed_code += "-"
        
        # Mettre à jour le code affiché
        self.game_code = completed_code
        
        # Vérifier l'IP si fournie
        server_host = None
        if self.server_ip:
            try:
                ipaddress.ip_address(self.server_ip)  # Valide l'IP
                server_host = self.server_ip
            except ValueError:
                self.error_message = "Adresse IP invalide"
                self.error_time = time.time()
                return
        
        # Indiquer que la recherche est en cours
        self.scanning = True
        
        # Tentative de rejoindre la partie
        def join_thread():
            try:
                # Essayer de rejoindre la partie
                success, error_code = self.network_client.join_game(self.game_code, server_host)
                
                if success:
                    # Posté comme événement personnalisé pour la sécurité du thread
                    pygame.event.post(pygame.event.Event(pygame.USEREVENT, {'success': True}))
                else:
                    # Traduire le code d'erreur
                    error_msg = self.network_client.ERROR_CODES.get(error_code, f"Erreur de connexion: {error_code}")
                    
                    pygame.event.post(pygame.event.Event(pygame.USEREVENT, {'error': error_msg}))
            except Exception as e:
                # Gérer toute autre exception
                logger.error(f"Erreur lors de la tentative de connexion: {e}")
                pygame.event.post(pygame.event.Event(pygame.USEREVENT, {'error': str(e)}))
            finally:
                self.scanning = False
        
        # Lancer la tentative de connexion dans un thread séparé
        connection_thread = threading.Thread(target=join_thread)
        connection_thread.daemon = True
        connection_thread.start()
    
    def reset(self):
        """Réinitialise l'état du menu"""
        self.state = "main"
        self.game_code = ""
        self.server_ip = ""
        self.error_message = ""
        self.error_time = 0
        self.scanning = False
        
        # Déconnecter le client réseau et en créer un nouveau
        self._create_new_network_client()