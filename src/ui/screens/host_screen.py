import pygame
import os
import threading
import time
import socket
from ...utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, BLUE, 
    RED, GREEN, DARK_BLUE, LIGHT_BLUE, DEFAULT_PORT
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
            panel_y + 200,
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
        self.connection_problem = False
        
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
        self.connection_check_timer = 0
        self.max_connection_attempts = 3
        self.connection_attempts = 0
        self.server_start_time = 0
        
    def handle_event(self, event):
        """Gérer les événements d'entrée"""
        # Gérer les événements du bouton de retour
        self.back_button.handle_event(event)
        
        # Gérer les événements du bouton de copie
        if self.ip_text:
            self.copy_button.handle_event(event)
            
    def update(self):
        """Mettre à jour l'état de l'écran"""
        self.back_button.update()
        self.copy_button.update()
        
        # Démarrer le serveur si ce n'est pas déjà fait
        if not self.server_started and not self.connection_problem:
            self._start_server()
            
        # Vérifier la connexion du client
        if self.server_started and not self.client_connected:
            self.connection_check_timer += 1
            
            # Vérifier toutes les 2 secondes (120 frames à 60 FPS)
            if self.connection_check_timer >= 120:
                self.connection_check_timer = 0
                if self._check_client_connected():
                    self.client_connected = True
                    self.status_text = "Joueur connecté! Redirection..."
                    self.status_color = GREEN
                    
                    # Rediriger vers l'écran de placement après un court délai
                    self._redirect_to_placement()
                else:
                    # Après un certain temps sans connexion, afficher un message d'info
                    current_time = time.time()
                    if current_time - self.server_start_time > 60:  # 60 secondes
                        self.status_text = "Conseil: Vérifiez que le port 5555 est ouvert"
                                    
        # Animation des points d'attente
        self.waiting_timer += 1
        if self.waiting_timer >= 30:
            self.waiting_timer = 0
            self.waiting_dots = (self.waiting_dots + 1) % 4
            
            if not self.client_connected and not self.connection_problem:
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
            ip_rect = ip_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
            screen.blit(ip_surface, ip_rect)
            
            # Instructions
            instructions = [
                "Partagez cette adresse IP avec votre adversaire",
                "Il devra cliquer sur \"Rejoindre une partie\" et saisir cette adresse"
            ]
            
            for i, text in enumerate(instructions):
                instr_surface = self.info_font.render(text, True, LIGHT_BLUE)
                instr_rect = instr_surface.get_rect(
                    center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20 + i * 30)
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
            
    def _get_local_ip(self):
        """Obtenir l'adresse IP locale avec des méthodes de secours"""
        try:
            # Méthode 1 : utiliser une connexion externe pour déterminer l'interface
            temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            temp_socket.connect(("8.8.8.8", 80))
            local_ip = temp_socket.getsockname()[0]
            temp_socket.close()
            return local_ip
        except:
            try:
                # Méthode 2 : utiliser gethostbyname
                return socket.gethostbyname(socket.gethostname())
            except:
                try:
                    # Méthode 3 : utiliser gethostname et getaddrinfo
                    hostname = socket.gethostname()
                    for addrinfo in socket.getaddrinfo(hostname, None):
                        if addrinfo[0] == socket.AF_INET:  # IPv4 uniquement
                            ip = addrinfo[4][0]
                            if not ip.startswith('127.'):
                                return ip
                except:
                    pass
                
                # Si toutes les méthodes échouent, utiliser l'adresse loopback
                return "127.0.0.1"
            
    def _start_server(self):
        """Démarrer le serveur de jeu"""
        from ...network.server import Server
        
        # Définir le minuteur de démarrage
        self.server_start_time = time.time()
        
        # Démarrer le serveur dans un thread pour éviter de bloquer l'interface
        def start_server_thread():
            try:
                # Créer le serveur
                self.game.server = Server()
                
                # Tenter de démarrer le serveur
                if self.game.server.start():
                    # Récupérer l'IP locale
                    if hasattr(self.game.server, 'local_ip'):
                        ip = self.game.server.local_ip
                    else:
                        ip = self._get_local_ip()
                        
                    port = self.game.server.port
                    self.ip_text = f"{ip}:{port}"
                    self.status_text = "Serveur démarré, en attente d'un joueur..."
                    self.status_color = GREEN
                    
                    # Se connecter aussi en tant que client (joueur 0)
                    self._connect_as_client(ip, port)
                else:
                    # Échec du démarrage du serveur
                    self.game.server = None
                    self.status_text = "Erreur: Impossible de démarrer le serveur"
                    self.status_color = RED
                    self.connection_problem = True
            except Exception as e:
                # Capture de toute exception imprévue
                self.game.server = None
                self.status_text = f"Erreur serveur: {str(e)}"
                self.status_color = RED
                self.connection_problem = True
                print(f"Erreur lors du démarrage du serveur: {e}")
                import traceback
                traceback.print_exc()
        
        # Lancer le thread
        server_thread = threading.Thread(target=start_server_thread)
        server_thread.daemon = True
        server_thread.start()
    
    def _connect_as_client(self, ip, port):
        """Se connecter en tant que client au serveur local"""
        from ...network.client import Client
        
        def connect_client_thread():
            try:
                # Créer le client - utiliser localhost au lieu de l'IP externe pour se connecter localement
                self.game.client = Client(host="localhost", port=port)
                
                # Tenter de se connecter
                if self.game.client.connect():
                    self.game.set_network_mode("host")
                    self.server_started = True
                    self.connection_attempts = 0
                else:
                    # Échec de la connexion
                    self._handle_connection_failure()
            except Exception as e:
                # Capture de toute exception imprévue
                self._handle_connection_failure(str(e))
        
        # Lancer le thread
        client_thread = threading.Thread(target=connect_client_thread)
        client_thread.daemon = True
        client_thread.start()
    
    def _handle_connection_failure(self, error_msg=None):
        """Gérer l'échec de connexion"""
        self.connection_attempts += 1
        
        if self.connection_attempts < self.max_connection_attempts:
            # Réessayer
            self.status_text = f"Tentative de connexion {self.connection_attempts + 1}/{self.max_connection_attempts}..."
            self.status_color = YELLOW
            
            # Attendre un peu avant de réessayer
            time.sleep(1)
            self._connect_as_client("localhost", DEFAULT_PORT)
        else:
            # Abandonner après plusieurs tentatives
            if error_msg:
                self.status_text = f"Erreur client: {error_msg}"
            else:
                self.status_text = "Impossible de se connecter au serveur"
            self.status_color = RED
            self.connection_problem = True
            
            # Arrêter le serveur si nécessaire
            if self.game.server:
                self.game.server.stop()
                self.game.server = None
    
    def _check_client_connected(self):
        """Vérifier si un client s'est connecté au serveur"""
        if not self.game.client or not hasattr(self.game.client, 'game_state'):
            return False
            
        if self.game.client.game_state is None:
            return False
            
        # Vérifier s'il y a deux joueurs et si le second joueur est prêt
        if (len(self.game.client.game_state.players) >= 2 and 
            hasattr(self.game.client.game_state.players[1], 'ready') and 
            self.game.client.game_state.players[1].ready):
            return True
            
        return False
    
    def _redirect_to_placement(self):
        """Rediriger vers l'écran de placement après un court délai"""
        def redirect():
            time.sleep(1)
            self.game.change_screen("ship_placement")
            
        thread = threading.Thread(target=redirect)
        thread.daemon = True
        thread.start()
            
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