import pygame
import os
import math  # Utilisation de math.sin pour les motifs
from ...utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GRID_SIZE, CELL_SIZE, 
    WHITE, BLACK, BLUE, GREEN, RED, GRAY, DARK_BLUE, LIGHT_BLUE, YELLOW,
    SHIPS
)
from ...game.game_state import GameState, YOUR_TURN  # Import de YOUR_TURN pour éviter une erreur
from ..components.button import Button
from ..components.back_button import BackButton
from ..components.panel import Panel
from ..components.grid import Grid
from ...game.ship import Ship
from ...game.player import Player

class ShipPlacement:
    """Écran de placement des navires avec design amélioré"""
    
    def __init__(self, game):
        self.game = game
        
        # Polices
        self.title_font = pygame.font.Font(None, 48)
        self.subtitle_font = pygame.font.Font(None, 32)
        self.info_font = pygame.font.Font(None, 24)
        self.ship_font = pygame.font.Font(None, 22)
        
        # Titre
        self.title_text = self.title_font.render("Placez vos navires", True, WHITE)
        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        
        # Grille
        grid_x = (SCREEN_WIDTH - (GRID_SIZE * CELL_SIZE)) // 2 - CELL_SIZE
        grid_y = 120
        self.grid = Grid(grid_x, grid_y, is_player_grid=True)
        
        # Configuration du joueur et game_state selon le mode
        self.current_player_index = 0
        if self.game.network_mode in ["solo", "local"]:
            self.game_state = GameState()
            self.player = self.game_state.players[self.current_player_index]
        else:
            # Mode réseau : l'état réel viendra du serveur ultérieurement
            self.player = Player(0)
        
        # Navire sélectionné et son orientation
        self.selected_ship_index = 0
        self.ship_rotation = True  # True = horizontal, False = vertical
        self.ship_preview = None
        
        # Panneau pour la sélection des navires
        ships_panel_width = 300
        ships_panel_height = 280
        ships_panel_x = 20
        ships_panel_y = 150
        self.ships_panel = Panel(
            ships_panel_x, ships_panel_y, ships_panel_width, ships_panel_height,
            DARK_BLUE, BLUE, 2, 0.8, 10, True
        )
        
        # Création des boutons
        button_width = 180
        button_height = 45
        button_margin = 15
        grid_bottom = grid_y + (GRID_SIZE * CELL_SIZE)
        total_buttons_width = 2 * button_width + button_margin
        buttons_start_x = (SCREEN_WIDTH - total_buttons_width) // 2

        self.rotate_button = Button(
            buttons_start_x,
            grid_bottom + 50,  # Position ajustée
            button_width,
            button_height,
            "Tourner (R)",
            self._rotate_ship,
            font_size=24,
            border_radius=10,
            bg_color=BLUE
        )

        # Bouton de difficulté 
        self.difficulty_button = Button(
            buttons_start_x,
            grid_bottom + 50 + button_height + button_margin,
            button_width * 2 + button_margin,
            button_height,
            "Difficulté: Moyenne",
            self._cycle_difficulty,
            font_size=24,
            border_radius=10,
            bg_color=BLUE
        )

        self.random_button = Button(
            buttons_start_x + button_width + button_margin,
            grid_bottom + 50,
            button_width,
            button_height,
            "Aléatoire",
            self._random_placement,
            font_size=24,
            border_radius=10,
            bg_color=BLUE
        )

        self.reset_button = Button(
            buttons_start_x,
            grid_bottom + 50 + 2 * (button_height + button_margin),
            button_width,
            button_height,
            "Réinitialiser",
            self._reset_placement,
            font_size=24,
            border_radius=10,
            bg_color=RED
        )

        self.ready_button = Button(
            buttons_start_x + button_width + button_margin,
            grid_bottom + 50 + 2 * (button_height + button_margin),
            button_width,
            button_height,
            "Prêt !",
            self._ready,
            font_size=24,
            border_radius=10,
            bg_color=GREEN
        )
                        
        self.back_button = BackButton(30, 30, 30, self._return_to_menu)
        
        # Message de statut pour l'utilisateur
        self.status_text = ""
        self.status_color = WHITE

        # Gestion des difficultés
        self.difficulties = ['Facile', 'Moyenne', 'Difficile', 'Expert']
        self.current_difficulty_index = 1  # Moyenne par défaut
        
        # Rassembler les boutons pour faciliter leur gestion
        self.buttons = [
            self.rotate_button,
            self.random_button,
            self.difficulty_button,
            self.reset_button,
            self.ready_button
        ]
        
        # Chargement de l'image de fond
        self.background = self._load_background()
        
    def _cycle_difficulty(self):
        """
        Faire défiler les niveaux de difficulté
        """
        self.current_difficulty_index = (self.current_difficulty_index + 1) % len(self.difficulties)
        difficulty = self.difficulties[self.current_difficulty_index].lower()
        
        # Mettre à jour le texte du bouton
        self.difficulty_button.text = f"Difficulté: {self.difficulties[self.current_difficulty_index]}"
        
        # En mode solo, définir la difficulté pour le GameState
        if self.game.network_mode == "solo":
            if not hasattr(self, 'game_state'):
                # Créer un game_state s'il n'existe pas encore
                from ...game.game_state import GameState
                self.game_state = GameState()
                self.game_state.is_solo_mode = True
                print("Nouveau game_state créé pour stocker la difficulté")
                
            # Maintenant on peut définir la difficulté
            self.game_state.difficulty = difficulty
            print(f"Difficulté mise à jour dans game_state: {difficulty}")
        
        # Stocker également la difficulté dans une variable de classe pour s'assurer qu'elle est conservée
        self.__class__.last_selected_difficulty = difficulty
        
        self.status_text = f"Difficulté réglée sur {self.difficulties[self.current_difficulty_index]}"
        self.status_color = WHITE
            
    def _load_background(self):
        """Charger et redimensionner l'image de fond si disponible"""
        try:
            bg_path = os.path.join("assets", "images", "ocean_bg.jpg")
            if os.path.exists(bg_path):
                bg = pygame.image.load(bg_path)
                return pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except Exception as e:
            print("Impossible de charger l'image de fond:", e)
        return None
        
    def handle_event(self, event):
        """Gérer les événements d'entrée"""
        for button in self.buttons:
            button.handle_event(event)
        self.back_button.handle_event(event)
            
        cell = self.grid.handle_event(event)
        if cell:
            self._place_ship_at_cell(*cell)
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self._rotate_ship()
            elif event.key in (pygame.K_LEFT, pygame.K_UP):
                self._select_prev_ship()
            elif event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                self._select_next_ship()
                
        if event.type == pygame.MOUSEMOTION:
            self._update_ship_preview()
            
    def update(self):
        """Mettre à jour l'état de l'écran"""
        for button in self.buttons:
            button.update()
        self.back_button.update()
            
        # Activer le bouton "Prêt" uniquement si tous les navires sont placés
        all_placed = all(ship.is_placed() for ship in self.player.ships)
        self.ready_button.normal_color = GREEN if all_placed else (100, 100, 100)
        self.ready_button.hover_color = (100, 220, 100) if all_placed else (120, 120, 120)
        self.ready_button.disabled = not all_placed
            
    def render(self, screen):
        """Rendre l'écran de placement des navires"""
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill(BLACK)
            self._draw_background_pattern(screen)
        
        screen.blit(self.title_text, self.title_rect)
        self.back_button.draw(screen)
        self.grid.draw(
            screen, 
            self.player.board, 
            show_ships=True, 
            ship_preview=self.ship_preview
        )
        self.ships_panel.draw(screen)
        
        # Sous-titre du panneau
        ships_title = self.info_font.render("Flotte disponible", True, WHITE)
        ships_title_rect = ships_title.get_rect(
            center=(self.ships_panel.rect.centerx, self.ships_panel.rect.y + 25)
        )
        screen.blit(ships_title, ships_title_rect)
        
        self._draw_ships_selection(screen)
        
            # Assurez-vous d'initialiser la police en haut de votre code
        self.info_font = pygame.font.Font(None, 18)  # Police par défaut, taille 18

        instructions = [
            "1. Cliquez sur la grille pour placer le navire sélectionné",
            "2. Utilisez R ou le bouton Tourner pour changer l'orientation",
            "3. Utilisez les flèches < > pour changer de navire"
        ]
        x_position = SCREEN_WIDTH * 0.85
        y_base = SCREEN_HEIGHT * 0.5

        # Trouver la largeur maximale pour aligner correctement
        max_width = 0
        temp_surfaces = []
        for text in instructions:
            instr_surface = self.info_font.render(text, True, LIGHT_BLUE)
            temp_surfaces.append(instr_surface)
            max_width = max(max_width, instr_surface.get_width())

        for i, instr_surface in enumerate(temp_surfaces):
            # On calcule la position x pour que le bloc reste centré à x_position
            left_x = x_position - (max_width / 2)
            instr_rect = instr_surface.get_rect(
                topleft=(left_x, y_base - 25 + i * 25 - instr_surface.get_height()/2)
            )
            screen.blit(instr_surface, instr_rect)
        
        if self.status_text:
            status_surface = self.info_font.render(self.status_text, True, self.status_color)
            status_rect = status_surface.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30)
            )
            screen.blit(status_surface, status_rect)
        
        for button in self.buttons:
            button.draw(screen)
            
    def _draw_background_pattern(self, screen):
        """Dessiner un motif de fond simulant l'eau"""
        for y in range(0, SCREEN_HEIGHT, 30):
            for x in range(0, SCREEN_WIDTH, 30):
                blue_var = (x + y) % 30
                color = (0, 20 + blue_var, 60 + blue_var)
                pygame.draw.circle(
                    screen, 
                    color, 
                    (x + math.sin(y / 50) * 5, y),
                    2
                )
            
    def _draw_ships_selection(self, screen):
        """Dessiner l'interface de sélection des navires"""
        panel_rect = self.ships_panel.rect
        ships_x = panel_rect.x + 20
        ships_y = panel_rect.y + 50
        ship_height = 38
        ship_spacing = 5
        
        for i, ship in enumerate(self.player.ships):
            if i == self.selected_ship_index:
                bg_rect = pygame.Rect(
                    panel_rect.x + 10, 
                    ships_y + i * (ship_height + ship_spacing) - 5,
                    panel_rect.width - 20,
                    ship_height + 10
                )
                for j in range(5):
                    color = (30 + j*5, 100 + j*5, 200 + j*5) if not ship.is_placed() else (80, 80, 80)
                    pygame.draw.rect(
                        screen,
                        color,
                        pygame.Rect(bg_rect.x, bg_rect.y + j*2, bg_rect.width, bg_rect.height - j*4),
                        border_radius=5
                    )
                pygame.draw.rect(
                    screen,
                    WHITE,
                    bg_rect,
                    2,
                    border_radius=5
                )
                
            text_color = GRAY if ship.is_placed() else WHITE
            ship_text = f"{ship.name} ({ship.size} cases)"
            text_surface = self.ship_font.render(ship_text, True, text_color)
            text_rect = text_surface.get_rect(
                midleft=(ships_x, ships_y + i * (ship_height + ship_spacing) + ship_height // 2)
            )
            screen.blit(text_surface, text_rect)
            
            cell_size = 8
            ship_viz_x = panel_rect.right - 20 - ship.size * cell_size
            ship_viz_y = ships_y + i * (ship_height + ship_spacing) + ship_height // 2 - cell_size // 2
            
            for j in range(ship.size):
                cell_rect = pygame.Rect(
                    ship_viz_x + j * cell_size,
                    ship_viz_y,
                    cell_size,
                    cell_size
                )
                pygame.draw.rect(screen, text_color, cell_rect)
                pygame.draw.rect(screen, BLACK, cell_rect, 1)
            
    def _select_next_ship(self):
        """Sélectionner le navire suivant dans la liste"""
        self.selected_ship_index = (self.selected_ship_index + 1) % len(self.player.ships)
        self._update_ship_preview()
        
    def _select_prev_ship(self):
        """Sélectionner le navire précédent dans la liste"""
        self.selected_ship_index = (self.selected_ship_index - 1) % len(self.player.ships)
        self._update_ship_preview()
        
    def _rotate_ship(self):
        """Tourner le navire actuellement sélectionné"""
        self.ship_rotation = not self.ship_rotation
        self._update_ship_preview()
        
    def _update_ship_preview(self):
        """Mettre à jour l'aperçu du navire en fonction du survol de la souris"""
        if self.grid.hover_cell:
            ship = self.player.ships[self.selected_ship_index]
            x, y = self.grid.hover_cell
            self.ship_preview = (ship, x, y, self.ship_rotation)
        else:
            self.ship_preview = None
            
    def _place_ship_at_cell(self, x, y):
        """Tenter de placer le navire sélectionné à la cellule donnée"""
        ship_index = self.selected_ship_index
        horizontal = self.ship_rotation
        success = self.player.place_ship(ship_index, x, y, horizontal)
        
        if success:
            self.status_text = f"{self.player.ships[ship_index].name} placé avec succès"
            self.status_color = GREEN
            if self.game.network_mode in ["host", "client"] and self.game.client:
                self.game.client.place_ship(ship_index, x, y, horizontal)
            for i, ship in enumerate(self.player.ships):
                if not ship.is_placed():
                    self.selected_ship_index = i
                    break
        else:
            self.status_text = "Placement invalide !"
            self.status_color = RED
            
    def _random_placement(self):
        """Placer aléatoirement tous les navires"""
        success = self.player.auto_place_ships()
        
        if success:
            self.status_text = "Navires placés aléatoirement"
            self.status_color = GREEN
            if self.game.network_mode in ["host", "client"] and self.game.client:
                for i, ship in enumerate(self.player.ships):
                    self.game.client.place_ship(i, ship.x, ship.y, ship.horizontal)
        else:
            self.status_text = "Échec du placement aléatoire"
            self.status_color = RED
            
    def _reset_placement(self):
        """Réinitialiser tous les placements de navires"""
        self.player.reset()
        if self.game.network_mode in ["host", "client"] and self.game.client:
            pass
        self.status_text = "Placement réinitialisé"
        self.status_color = WHITE
        
    def _ready(self):
        """Marquer le joueur comme prêt et passer au jeu"""
        # Vérifier que tous les navires sont placés
        if not all(ship.is_placed() for ship in self.player.ships):
            self.status_text = "Placez tous vos navires avant de continuer !"
            self.status_color = RED
            return
        
        # Marquer le joueur comme prêt
        self.player.ready = True
        
        # Mode réseau : envoyer le signal prêt au serveur
        if self.game.network_mode in ["host", "client"] and self.game.client:
            self.game.client.player_ready()
            self.status_text = "En attente de l'adversaire..."
            self.status_color = BLUE
        elif self.game.network_mode == "solo":
            try:
                if hasattr(self, 'game_state'):
                    # S'assurer que le mode solo est activé
                    self.game_state.is_solo_mode = True
                    
                    # Enregistrer le placement des navires du joueur
                    for i, ship in enumerate(self.player.ships):
                        if ship.is_placed():
                            self.game_state.players[0].place_ship(i, ship.x, ship.y, ship.horizontal)
                            
                    self.game_state.player_ready(0)
                    print("Placement des navires de l'IA...")
                    if self.game_state.players[1].auto_place_ships():
                        print("Navires de l'IA placés avec succès")
                        self.game_state.player_ready(1)
                        
                        # Définir que c'est le tour du joueur humain
                        self.game_state.current_player_index = 0
                        self.game_state.state = YOUR_TURN
                        
                        # Passer à l'écran de jeu
                        self.game.change_screen("game_screen")
                    else:
                        print("Erreur: impossible de placer les navires de l'IA")
                else:
                    print("Initialisation de game_state en mode solo")
                    self.game_state = GameState()
                    self.game_state.is_solo_mode = True
                    self.current_player_index = 0
                    for i, ship in enumerate(self.player.ships):
                        if ship.is_placed():
                            self.game_state.players[0].place_ship(i, ship.x, ship.y, ship.horizontal)
                    self.game_state.player_ready(0)
                    if self.game_state.players[1].auto_place_ships():
                        self.game_state.player_ready(1)
                        self.game.change_screen("game_screen")
                    else:
                        print("Échec du placement des navires du bot")
            except Exception as e:
                print(f"Erreur en mode solo: {e}")
                import traceback
                traceback.print_exc()
                self.status_text = "Erreur lors du lancement du jeu"
                self.status_color = RED
            
    def _return_to_menu(self):
        """Retourner au menu principal"""
        if any(ship.is_placed() for ship in self.player.ships):
            pass
        if self.game.network_mode in ["host", "client"] and self.game.client:
            self.game.client.disconnect()
            self.game.client = None
        if self.game.server:
            self.game.server.stop()
            self.game.server = None
        self.game.change_screen("main_screen")
