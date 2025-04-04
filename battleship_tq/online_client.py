import pygame
import sys
import os
import json
import time
import threading

# === Vérifier le système et les imports ===
print("Démarrage du client Bataille Navale...")
print("Python version:", sys.version)

# === VÉRIFICATION DU FICHIER DE CONFIG ===
if not os.path.exists("config.json"):
    print("⚠️ Le fichier config.json n'existe pas. Création d'un fichier par défaut...")
    with open("config.json", "w") as f:
        json.dump({
            "username": "JoueurBattleship",
            "port": 5555,
            "matchmaking_url": "https://rfosse.pythonanywhere.com"
        }, f, indent=2)
    print("✅ Fichier config.json créé. Veuillez le modifier avec vos informations.")

# === CHARGEMENT DE LA CONFIGURATION ===
with open("config.json") as f:
    config = json.load(f)

USERNAME = config.get("username", "JoueurBattleship")
PORT = config.get("port", 5555)
SERVER_URL = config.get("matchmaking_url", "https://rfosse.pythonanywhere.com")

if USERNAME == "JoueurBattleship":
    USERNAME = input("👤 Entrez votre nom d'utilisateur: ").strip()
    if USERNAME:
        config["username"] = USERNAME
        with open("config.json", "w") as f:
            json.dump(config, f, indent=2)
        print(f"✅ Nom d'utilisateur '{USERNAME}' enregistré dans config.json")

# === Import de la classe de connexion ===
try:
    from network.battleship_connection import BattleshipConnection
    print("✅ Modules réseau importés avec succès")
except ImportError as e:
    print(f"❌ Erreur d'import du module réseau: {e}")
    print("Vérifiez que le fichier network/battleship_connection.py existe.")
    sys.exit(1)

# === INITIALISATION PYGAME ===
print("Initialisation de Pygame...")
try:
    pygame.init()
    print("✅ Pygame initialisé avec succès:", pygame.get_init())
except Exception as e:
    print(f"❌ Erreur d'initialisation Pygame: {e}")
    sys.exit(1)

# === PARAMÈTRES DU JEU ===
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 5
CELL_SIZE = 60
MARGIN = 40
GRID_WIDTH = GRID_SIZE * CELL_SIZE
GRID_HEIGHT = GRID_SIZE * CELL_SIZE

# === COULEURS ===
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_BLUE = (0, 30, 60)
GRID_BLUE = (0, 120, 215)
LIGHT_BLUE = (135, 206, 250)
RED = (220, 20, 60)
GREEN = (34, 139, 34)
YELLOW = (255, 255, 0)
GRAY = (200, 200, 200)
WATER_BLUE = (10, 75, 120)

# === Création de la fenêtre ===
print(f"Création de la fenêtre {SCREEN_WIDTH}x{SCREEN_HEIGHT}...")
try:
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(f"🌊 Bataille Navale Online - {USERNAME}")
    print("✅ Fenêtre créée avec succès")
except Exception as e:
    print(f"❌ Erreur lors de la création de la fenêtre: {e}")
    sys.exit(1)

# === Chargement des polices ===
try:
    print("Chargement des polices...")
    font_title = pygame.font.SysFont("Arial", 28, bold=True)
    font_normal = pygame.font.SysFont("Arial", 20)
    font_small = pygame.font.SysFont("Arial", 16)
    print("✅ Polices chargées avec succès")
except Exception as e:
    print(f"❌ Erreur lors du chargement des polices: {e}")
    sys.exit(1)

# === CALCUL DES POSITIONS DES GRILLES ===
player_grid_pos = (MARGIN, 150)
opponent_grid_pos = (SCREEN_WIDTH - GRID_WIDTH - MARGIN, 150)
grid_width = GRID_SIZE * CELL_SIZE

# === CLASSE DE GESTION DU JEU ===
class OnlineGame:
    def __init__(self, username, port, server_url):
        self.connection = BattleshipConnection(username, port, server_url)
        self.opponent_board = {}  # Pour suivre les coups sur la grille adverse
        self.placing_ships = True
        self.ships_placed = 0
        self.ship_limit = 3  # Nombre de navires à placer
        self.status_message = f"🌊 Bataille Navale Online - {username}"
        self.status_color = WHITE
        self.preview_ship_pos = None
        self.message_timeout = 0
        
    def draw_board(self, board, pos, title, show_ships=True):
        x, y = pos
        
        # Titre de la grille
        title_text = font_normal.render(title, True, WHITE)
        screen.blit(title_text, (x + GRID_WIDTH // 2 - title_text.get_width() // 2, y - 30))
        
        # Grille
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                rect = pygame.Rect(x + col * CELL_SIZE, y + row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                
                # Fond de la cellule
                pygame.draw.rect(screen, DARK_BLUE, rect)
                
                # Contenu
                cell_pos = (col, row)
                cell_value = board.get(cell_pos)
                
                if cell_value == "SHIP" and show_ships:
                    pygame.draw.rect(screen, LIGHT_BLUE, rect.inflate(-4, -4))
                elif cell_value == "HIT":
                    pygame.draw.rect(screen, RED, rect.inflate(-4, -4))
                    # Dessiner un X
                    pygame.draw.line(screen, WHITE, 
                                  (rect.left + 10, rect.top + 10), 
                                  (rect.right - 10, rect.bottom - 10), 3)
                    pygame.draw.line(screen, WHITE, 
                                  (rect.left + 10, rect.bottom - 10), 
                                  (rect.right - 10, rect.top + 10), 3)
                elif cell_value == "MISS":
                    pygame.draw.circle(screen, WATER_BLUE, rect.center, CELL_SIZE // 4)
                elif cell_value == "PENDING":
                    # Tir en attente de réponse
                    pygame.draw.circle(screen, YELLOW, rect.center, CELL_SIZE // 4, 2)
                
                # Bordure de la cellule
                pygame.draw.rect(screen, GRID_BLUE, rect, 1)
                
        # Afficher les coordonnées
        for i in range(GRID_SIZE):
            # Lettres (A-E)
            letter = chr(65 + i)
            letter_text = font_small.render(letter, True, WHITE)
            screen.blit(letter_text, (x + i * CELL_SIZE + CELL_SIZE // 2 - letter_text.get_width() // 2, y - 20))
            
            # Chiffres (0-4)
            number_text = font_small.render(str(i), True, WHITE)
            screen.blit(number_text, (x - 20, y + i * CELL_SIZE + CELL_SIZE // 2 - number_text.get_height() // 2))
    
    def draw_status(self):
        """Affiche une barre de statut en bas de l'écran"""
        status_rect = pygame.Rect(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40)
        pygame.draw.rect(screen, BLACK, status_rect)
        
        if time.time() < self.message_timeout:
            text = font_normal.render(self.status_message, True, self.status_color)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT - 30))
    
    def show_message(self, message, color=WHITE, duration=3.0):
        """Affiche un message temporaire dans la barre de statut"""
        self.status_message = message
        self.status_color = color
        self.message_timeout = time.time() + duration
        print(message)  # Aussi afficher dans la console
    
    def get_cell_at_position(self, mouse_pos, grid_pos):
        """Convertit une position de souris en coordonnées de grille"""
        x, y = mouse_pos
        grid_x, grid_y = grid_pos
        
        if (grid_x <= x < grid_x + GRID_WIDTH and 
            grid_y <= y < grid_y + GRID_HEIGHT):
            col = (x - grid_x) // CELL_SIZE
            row = (y - grid_y) // CELL_SIZE
            return (col, row)
        
        return None
    
    def matchmaking(self):
        """Gère la phase de matchmaking"""
        match_code = input("🎮 Entrez le code de match (laissez vide pour en créer un nouveau): ").strip()
        
        if match_code:
            # Rejoindre un match existant
            if self.connection.join_match(match_code):
                self.show_message(f"✅ Match rejoint! Adversaire: {self.connection.opponent}", GREEN)
                return True
            else:
                print("❌ Impossible de rejoindre le match.")
                return False
        else:
            # Générer un code de match automatiquement
            match_code = f"{USERNAME}_{int(time.time())}"
            print(f"Code de match généré: {match_code}")
            
            # Créer un match et attendre un adversaire
            if self.connection.create_match(match_code):
                self.show_message(f"✅ Match créé et rejoint!", GREEN)
                return True
            else:
                opponent_name = input("👥 Nom de l'adversaire à inviter: ").strip()
                if opponent_name:
                    # Proposer directement un match à cet adversaire
                    if self.connection.propose_match(opponent_name, match_code):
                        self.show_message(f"✅ Match créé avec {opponent_name}!", GREEN)
                        return True
                
                print("❌ Impossible de créer ou proposer le match.")
                return False
    
    def run(self):
        """Exécute la boucle principale du jeu"""
        print("Initialisation du matchmaking...")
        if not self.matchmaking():
            print("❌ Échec du matchmaking. Fin du programme.")
            return
        
        print("✅ Matchmaking réussi, démarrage du jeu...")
        self.show_message(f"📝 Placez vos {self.ship_limit} navires", LIGHT_BLUE)
        
        clock = pygame.time.Clock()
        running = True
        
        # Boucle principale
        while running:
            # Gérer les événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Gestion des clics
                    mouse_pos = pygame.mouse.get_pos()
                    
                    if self.placing_ships:
                        # Phase de placement des navires
                        cell = self.get_cell_at_position(mouse_pos, player_grid_pos)
                        if cell and cell not in self.connection.game_board:
                            self.connection.update_game_board(cell, opponent=False)
                            self.ships_placed += 1
                            self.show_message(f"🚢 Navire {self.ships_placed}/{self.ship_limit} placé", LIGHT_BLUE)
                            
                            if self.ships_placed >= self.ship_limit:
                                self.placing_ships = False
                                self.connection.start_game()
                                self.show_message("🎮 Partie démarrée! " + 
                                              ("C'est votre tour!" if self.connection.my_turn else "Au tour de l'adversaire!"), 
                                              GREEN)
                    
                    elif self.connection.is_match_active and self.connection.my_turn and not self.connection.winner:
                        # Phase de jeu - tir sur la grille adverse
                        cell = self.get_cell_at_position(mouse_pos, opponent_grid_pos)
                        if cell and cell not in self.opponent_board:
                            # Afficher le coup comme en attente
                            self.opponent_board[cell] = "PENDING"
                            
                            # Envoyer le coup
                            if self.connection.send_move(cell):
                                self.connection.my_turn = False
                                self.show_message(f"🎯 Tir en {cell}, au tour de l'adversaire", LIGHT_BLUE)
                            else:
                                # Si échec de l'envoi, annuler le marquage
                                del self.opponent_board[cell]
                                self.show_message("❌ Échec de l'envoi du coup", RED)
            
            # Affichage
            screen.fill(DARK_BLUE)  # Fond
            
            # Titre
            title = font_title.render("BATAILLE NAVALE ONLINE", True, WHITE)
            screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 30))
            
            # Sous-titre: statut de la partie
            if self.connection.winner:
                subtitle = f"🏆 {self.connection.winner} a gagné la partie!"
                color = GREEN if self.connection.winner == USERNAME else RED
            elif self.placing_ships:
                subtitle = f"📝 Placez vos navires ({self.ships_placed}/{self.ship_limit})"
                color = LIGHT_BLUE
            elif self.connection.is_match_active:
                subtitle = "🎮 C'est votre tour!" if self.connection.my_turn else "⏳ Tour de l'adversaire..."
                color = GREEN if self.connection.my_turn else LIGHT_BLUE
            else:
                subtitle = "En attente..."
                color = WHITE
                
            subtitle_text = font_normal.render(subtitle, True, color)
            screen.blit(subtitle_text, (SCREEN_WIDTH // 2 - subtitle_text.get_width() // 2, 70))
            
            # Grilles
            self.draw_board(self.connection.game_board, player_grid_pos, f"🛡️ Votre flotte ({USERNAME})", True)
            self.draw_board(self.opponent_board, opponent_grid_pos, f"🎯 Tirs sur {self.connection.opponent or 'adversaire'}", False)
            
            # Barre d'information des joueurs
            info_text = font_small.render(f"Vous: {USERNAME} vs {self.connection.opponent or 'En attente...'}", True, WHITE)
            screen.blit(info_text, (10, 10))
            
            server_text = font_small.render(f"Serveur: {SERVER_URL}", True, GRAY)
            screen.blit(server_text, (SCREEN_WIDTH - server_text.get_width() - 10, 10))
            
            # Message de statut
            self.draw_status()
            
            # Rafraîchissement de l'écran
            pygame.display.flip()
            clock.tick(30)
        
        pygame.quit()
        print("Fin du programme.")

# === POINT D'ENTRÉE ===
if __name__ == "__main__":
    print(f"🌊 Bataille Navale Online - v1.0")
    print(f"👤 Joueur: {USERNAME}")
    print(f"🌐 Serveur: {SERVER_URL}")
    
    game = OnlineGame(USERNAME, PORT, SERVER_URL)
    game.run()