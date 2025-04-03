import pygame
import os
import threading
import time
import math  # Utilisé pour les effets de dessin

from ...utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, BLUE, 
    RED, GREEN, DARK_BLUE, LIGHT_BLUE, YELLOW
)
from ..components.button import Button
from ..components.back_button import BackButton
from ..components.panel import Panel

# Import du client personnalisé directement au niveau du module
# Utilisez l'import qui correspond à votre structure de projet
from src.network.client import Client  # Import absolu (à modifier en fonction de votre structure)

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
        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, 80))
        
        # Panneau principal
        panel_width = 550
        panel_height = 350
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
            panel_y + 190,
            button_width,
            button_height,
            "Se connecter",
            self._connect_to_server,
            font_size=28,
            border_radius=10,
            bg_color=GREEN
        )
        
        # Historique des connexions (ajout d'une nouvelle fonctionnalité)
        self.show_history = False
        self.history_button = Button(
            panel_x + (panel_width - button_width) // 2,
            panel_y + 190 + button_height + button_margin,
            button_width,
            button_height,
            "Historique",
            self._toggle_history,
            font_size=24,
            border_radius=10,
            bg_color=BLUE
        )
        
        # Liste des adresses récentes (simulé pour l'exemple, à remplacer par un stockage persistant)
        self.recent_addresses = []
        self._load_recent_addresses()
        
        # Bouton de retour
        self.back_button = BackButton(30, 30, 30, self._back_to_menu)
        
        # Message d'état (pour les tentatives de connexion)
        self.status_text = ""
        self.status_color = WHITE
        
        # Indicateur de connexion
        self.connecting = False
        self.connection_dots = 0
        self.connection_timer = 0
        
        # Histoire de connexion (liste déroulante)
        history_height = 150
        self.history_list_rect = pygame.Rect(
            panel_x + 50,
            panel_y + 250,
            panel_width - 100,
            history_height
        )
        self.history_scroll = 0
        self.max_visible_history = 5  # Nombre maximum d'éléments visibles à la fois
        
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
            self.history_button,
            self.back_button
        ]
        
    def _load_recent_addresses(self):
        """Charger les adresses récentes depuis un fichier"""
        try:
            # Essayer de charger depuis un fichier
            history_path = os.path.join("assets", "recent_servers.txt")
            if os.path.exists(history_path):
                with open(history_path, "r") as f:
                    self.recent_addresses = [line.strip() for line in f.readlines() if line.strip()]
            
            # Si pas d'historique ou fichier inexistant, ajouter des exemples
            if not self.recent_addresses:
                self.recent_addresses = ["localhost:65432", "127.0.0.1:65432"]
        except Exception as e:
            print(f"Erreur lors du chargement de l'historique: {e}")
            self.recent_addresses = ["localhost:65432", "127.0.0.1:65432"]
            
    def _save_recent_addresses(self):
        """Sauvegarder les adresses récentes dans un fichier"""
        try:
            # Créer le dossier assets s'il n'existe pas
            if not os.path.exists("assets"):
                os.makedirs("assets")
                
            # Sauvegarder dans un fichier
            history_path = os.path.join("assets", "recent_servers.txt")
            with open(history_path, "w") as f:
                for addr in self.recent_addresses:
                    f.write(f"{addr}\n")
        except Exception as e:
            print(f"Erreur lors de la sauvegarde de l'historique: {e}")
            
    def _add_to_history(self, address):
        """Ajouter une adresse à l'historique"""
        # Supprimer l'adresse si elle existe déjà
        if address in self.recent_addresses:
            self.recent_addresses.remove(address)
            
        # Ajouter l'adresse au début de la liste
        self.recent_addresses.insert(0, address)
        
        # Limiter la taille de l'historique
        if len(self.recent_addresses) > 10:
            self.recent_addresses = self.recent_addresses[:10]
            
        # Sauvegarder l'historique
        self._save_recent_addresses()
        
    def _toggle_history(self):
        """Afficher/masquer l'historique des connexions"""
        self.show_history = not self.show_history
        
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
            
            # Gérer les clics sur les éléments de l'historique
            if self.show_history:
                for i, addr in enumerate(self.recent_addresses):
                    if i >= self.max_visible_history:
                        break
                        
                    y_pos = self.history_list_rect.y + i * 30 - self.history_scroll
                    item_rect = pygame.Rect(
                        self.history_list_rect.x,
                        y_pos,
                        self.history_list_rect.width,
                        25
                    )
                    
                    if item_rect.collidepoint(event.pos):
                        self.input_text = addr
                        break
                        
            # Gérer le défilement de l'historique
            if event.button == 4:  # Molette vers le haut
                self.history_scroll = max(0, self.history_scroll - 30)
            elif event.button == 5:  # Molette vers le bas
                max_scroll = max(0, len(self.recent_addresses) * 30 - self.history_list_rect.height)
                self.history_scroll = min(max_scroll, self.history_scroll + 30)
            
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
            "Format: adresse:65432 (exemple: 192.168.1.10:65432)", True, LIGHT_BLUE
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
                
        # Afficher l'historique si demandé
        if self.show_history and not self.connecting:
            self._draw_history(screen)
                
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
                
    def _draw_history(self, screen):
        """Dessiner la liste de l'historique des connexions"""
        # Fond de l'historique
        history_bg = pygame.Rect(
            self.history_list_rect.x - 10,
            self.history_list_rect.y - 10,
            self.history_list_rect.width + 20,
            self.history_list_rect.height + 20
        )
        pygame.draw.rect(screen, (0, 0, 0, 180), history_bg, border_radius=10)
        pygame.draw.rect(screen, LIGHT_BLUE, history_bg, 2, border_radius=10)
        
        # Titre de l'historique
        history_title = self.info_font.render("Connexions récentes", True, LIGHT_BLUE)
        history_title_rect = history_title.get_rect(
            center=(self.history_list_rect.centerx, self.history_list_rect.y - 20)
        )
        screen.blit(history_title, history_title_rect)
        
        # Zone de clip pour limiter l'affichage à la taille de la liste
        original_clip = screen.get_clip()
        screen.set_clip(self.history_list_rect)
        
        # Éléments de l'historique
        for i, addr in enumerate(self.recent_addresses):
            y_pos = self.history_list_rect.y + i * 30 - self.history_scroll
            
            # Ne dessiner que les éléments visibles
            if (y_pos + 25 >= self.history_list_rect.y and 
                y_pos <= self.history_list_rect.y + self.history_list_rect.height):
                
                # Fond de l'élément (alternance de couleurs)
                bg_color = (10, 40, 80) if i % 2 == 0 else (5, 30, 60)
                item_rect = pygame.Rect(
                    self.history_list_rect.x + 5,
                    y_pos,
                    self.history_list_rect.width - 10,
                    25
                )
                pygame.draw.rect(screen, bg_color, item_rect, border_radius=5)
                
                # Texte de l'élément
                addr_text = self.info_font.render(addr, True, WHITE)
                addr_rect = addr_text.get_rect(
                    midleft=(self.history_list_rect.x + 15, y_pos + 12)
                )
                screen.blit(addr_text, addr_rect)
        
        # Restaurer le clip original
        screen.set_clip(original_clip)
        
        # Dessiner des indicateurs de défilement si nécessaire
        max_scroll = max(0, len(self.recent_addresses) * 30 - self.history_list_rect.height)
        if max_scroll > 0:
            # Indicateur vers le haut
            if self.history_scroll > 0:
                pygame.draw.polygon(
                    screen,
                    LIGHT_BLUE,
                    [
                        (self.history_list_rect.right + 20, self.history_list_rect.y + 10),
                        (self.history_list_rect.right + 30, self.history_list_rect.y),
                        (self.history_list_rect.right + 40, self.history_list_rect.y + 10)
                    ]
                )
            
            # Indicateur vers le bas
            if self.history_scroll < max_scroll:
                pygame.draw.polygon(
                    screen,
                    LIGHT_BLUE,
                    [
                        (self.history_list_rect.right + 20, self.history_list_rect.bottom - 10),
                        (self.history_list_rect.right + 30, self.history_list_rect.bottom),
                        (self.history_list_rect.right + 40, self.history_list_rect.bottom - 10)
                    ]
                )
            
    def _connect_to_server(self):
        """Se connecter au serveur"""
        if self.connecting:
            return
            
        self.connecting = True
        self.status_text = "Tentative de connexion..."
        self.status_color = WHITE
        
        # Séparer l'hôte et le port
        host_parts = self.input_text.strip().split(":")
        
        host_address = None
        port = 65432  # Port FIXE à 65432 pour correspondre à l'autre projet
        
        if len(host_parts) == 2:
            host_address = host_parts[0]
            try:
                # On récupère le port mais on force quand même à 65432
                input_port = int(host_parts[1])
                if input_port != 65432:
                    self.status_text = f"Attention: utilisation du port 65432 au lieu de {input_port}"
                    self.status_color = YELLOW
            except ValueError:
                pass
        else:
            host_address = host_parts[0]
        
        # Créer un nouveau client avec l'adresse et le port spécifiés
        def connect_thread():
            time.sleep(1)  # Animation de connexion
            
            # Message de debug
            print(f"Tentative de connexion à {host_address}:{port}")
            
            # Créer le client avec un port explicite
            self.game.client = Client(username="Player", host=host_address, port=port)
            
            # Forcer une nouvelle vérification du port
            if hasattr(self.game.client, 'port') and self.game.client.port != 65432:
                self.game.client.port = 65432
                print(f"Port corrigé à 65432")
            
            success = self.game.client.connect()
            
            if success:
                # Ajouter l'adresse à l'historique des connexions
                self._add_to_history(self.input_text)
                
                # Configuration supplémentaire en cas de connexion réussie
                def on_game_state_update(game_state):
                    print("Game state update received")
                    # Logique de mise à jour si nécessaire
                
                # Enregistrer un callback pour le début de la partie
                self.game.client.register_callback('game_start', 
                    lambda msg: print(f"Partie commencée contre {msg.get('opponent')}"))
                
                # Message et transition
                self.status_text = "Connexion réussie!"
                self.status_color = GREEN
                
                time.sleep(0.5)
                
                # Changer d'écran dans le thread principal
                self.game.set_network_mode("client")
                self.game.change_screen("ship_placement")
                self.connecting = False
            else:
                self.status_text = f"Échec de la connexion à {host_address}:{port}"
                self.status_color = RED
                self.game.client = None
                self.connecting = False
        
        # Lancer la connexion dans un thread séparé
        connect_thread_obj = threading.Thread(target=connect_thread)
        connect_thread_obj.daemon = True
        connect_thread_obj.start()
            
    def _back_to_menu(self):
        """Retourner au menu principal"""
        self.game.change_screen("main_screen")