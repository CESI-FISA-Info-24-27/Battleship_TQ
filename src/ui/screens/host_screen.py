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
        self.back_button.handle_event(event)
        if self.ip_text:
            self.copy_button.handle_event(event)
            
    def update(self):
        self.back_button.update()
        self.copy_button.update()
        
        if not self.server_started and not self.connection_problem:
            self._start_server()
            
        if self.server_started and not self.client_connected:
            self.connection_check_timer += 1
            if self.connection_check_timer >= 120:
                self.connection_check_timer = 0
                if self._check_client_connected():
                    self.client_connected = True
                    self.status_text = "Joueur connecté! Redirection..."
                    self.status_color = GREEN
                    self._redirect_to_placement()
                else:
                    current_time = time.time()
                    if current_time - self.server_start_time > 60:  # 60 secondes
                        # Correction : afficher le port correct (65432)
                        self.status_text = "Conseil: Vérifiez que le port 65432 est ouvert"
                        
        self.waiting_timer += 1
        if self.waiting_timer >= 30:
            self.waiting_timer = 0
            self.waiting_dots = (self.waiting_dots + 1) % 4
            if not self.client_connected and not self.connection_problem:
                self.status_text = "En attente d'un joueur" + "." * self.waiting_dots
                
    def render(self, screen):
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill(BLACK)
        screen.blit(self.title_text, self.title_rect)
        self.main_panel.draw(screen)
        if self.ip_text:
            ip_surface = self.ip_font.render(self.ip_text, True, WHITE)
            ip_rect = ip_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
            screen.blit(ip_surface, ip_rect)
            instructions = [
                "Partagez cette adresse IP avec votre adversaire",
                "Il devra cliquer sur \"Rejoindre une partie\" et saisir cette adresse"
            ]
            for i, text in enumerate(instructions):
                instr_surface = self.info_font.render(text, True, LIGHT_BLUE)
                instr_rect = instr_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20 + i * 30))
                screen.blit(instr_surface, instr_rect)
        status_surface = self.info_font.render(self.status_text, True, self.status_color)
        status_rect = status_surface.get_rect(center=(SCREEN_WIDTH // 2, self.main_panel.rect.bottom - 50))
        screen.blit(status_surface, status_rect)
        self.back_button.draw(screen)
        if self.ip_text:
            self.copy_button.draw(screen)
            
    def _get_local_ip(self):
        try:
            temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            temp_socket.connect(("8.8.8.8", 80))
            local_ip = temp_socket.getsockname()[0]
            temp_socket.close()
            return local_ip
        except:
            try:
                return socket.gethostbyname(socket.gethostname())
            except:
                try:
                    hostname = socket.gethostname()
                    for addrinfo in socket.getaddrinfo(hostname, None):
                        if addrinfo[0] == socket.AF_INET:
                            ip = addrinfo[4][0]
                            if not ip.startswith('127.'):
                                return ip
                except:
                    pass
                return "127.0.0.1"
            
    def _start_server(self):
        from src.network.server import Server 
        self.server_start_time = time.time()
        
        def start_server_thread():
            try:
                self.game.server = Server(port=65432)
                
                if hasattr(self.game.server, 'port') and self.game.server.port != 65432:
                    print(f"AVERTISSEMENT: Port serveur incorrect: {self.game.server.port}. Correction à 65432.")
                    self.game.server.port = 65432
                
                if self.game.server.start():
                    if hasattr(self.game.server, 'local_ip'):
                        ip = self.game.server.local_ip
                    else:
                        ip = self._get_local_ip()
                    
                    port = 65432
                    self.ip_text = f"{ip}:{port}"
                    self.status_text = "Serveur démarré, en attente d'un joueur..."
                    self.status_color = GREEN
                    
                    self._connect_as_client(ip, port)
                    self.server_started = True
                else:
                    self.game.server = None
                    self.status_text = "Erreur: Impossible de démarrer le serveur"
                    self.status_color = RED
                    self.connection_problem = True
            except Exception as e:
                self.game.server = None
                self.status_text = f"Erreur serveur: {str(e)}"
                self.status_color = RED
                self.connection_problem = True
                print(f"Erreur lors du démarrage du serveur: {e}")
                import traceback
                traceback.print_exc()
        
        server_thread = threading.Thread(target=start_server_thread)
        server_thread.daemon = True
        server_thread.start()

    def _connect_as_client(self, ip, port):
        from src.network.client import Client 
        def connect_client_thread():
            try:
                port = 65432  # Forcer l'utilisation du port 65432
                self.game.client = Client(username="Hôte", host="localhost", port=port)
                if self.game.client.connect():
                    print("Client (hôte) connecté avec succès")
                else:
                    print("Erreur lors de la connexion du client hôte")
            except Exception as e:
                print(f"Erreur lors de la connexion en tant que client: {e}")
        client_thread = threading.Thread(target=connect_client_thread)
        client_thread.daemon = True
        client_thread.start()

    def _check_client_connected(self):
        # Vérifier si le client a reçu le game_state (signal que la partie a commencé)
        if self.game.client and self.game.client.game_state:
            return True
        return False

    def _redirect_to_placement(self):
        # Rediriger vers l'écran de placement après une courte attente
        time.sleep(2)
        self.game.change_screen("ship_placement")
        
    def _back_to_menu(self):
        # Retourner au menu principal et arrêter le serveur si nécessaire
        if self.game.server:
            self.game.server.stop()
        self.game.change_screen("main_screen")
        
    def _copy_ip_to_clipboard(self):
        try:

            pyperclip.copy(self.ip_text)
            print("Adresse IP copiée dans le presse-papiers.")
        except Exception as e:
            print(f"Erreur lors de la copie de l'adresse IP: {e}")
