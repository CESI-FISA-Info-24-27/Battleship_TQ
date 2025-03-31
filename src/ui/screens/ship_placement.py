import pygame
import os
import math  # Ajout de l'import math pour la fonction sin()
from ...utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GRID_SIZE, CELL_SIZE, 
    WHITE, BLACK, BLUE, GREEN, RED, GRAY, DARK_BLUE, LIGHT_BLUE, YELLOW,
    SHIPS
)
from ..components.button import Button
from ..components.back_button import BackButton
from ..components.panel import Panel
from ..components.grid import Grid
from ...game.ship import Ship
from ...game.player import Player
from ...game.game_state import GameState

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
        
        # Configuration du joueur
        if self.game.network_mode == "local":
            # En mode local, utiliser directement le game_state
            self.game_state = GameState()
            self.current_player_index = 0
            self.player = self.game_state.players[self.current_player_index]
        else:
            # En mode réseau, créer un joueur local pour le placement des navires
            # L'état réel du jeu viendra du serveur plus tard
            self.player = Player(0)
            
        # Navire sélectionné
        self.selected_ship_index = 0
        self.ship_rotation = True  # True pour horizontal, False pour vertical
        
        # Aperçu du navire
        self.ship_preview = None
        
        # Panneau pour la sélection des navires
        ships_panel_width = 220
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
        
        # Positions des boutons
        grid_bottom = grid_y + (GRID_SIZE + 1) * CELL_SIZE + 20
        buttons_centerx = grid_x + (GRID_SIZE + 1) * CELL_SIZE // 2
        
        # Bouton de rotation
        self.rotate_button = Button(
            buttons_centerx - button_width - button_margin,
            grid_bottom,
            button_width,
            button_height,
            "Tourner (R)",
            self._rotate_ship,
            font_size=24,
            border_radius=10,
            bg_color=BLUE
        )
        
        # Bouton de placement aléatoire
        self.random_button = Button(
            buttons_centerx + button_margin,
            grid_bottom,
            button_width,
            button_height,
            "Aléatoire",
            self._random_placement,
            font_size=24,
            border_radius=10,
            bg_color=BLUE
        )
        
        # Bouton de réinitialisation
        self.reset_button = Button(
            buttons_centerx - button_width - button_margin,
            grid_bottom + button_height + button_margin,
            button_width,
            button_height,
            "Réinitialiser",
            self._reset_placement,
            font_size=24,
            border_radius=10,
            bg_color=RED
        )
        
        # Bouton prêt
        self.ready_button = Button(
            buttons_centerx + button_margin,
            grid_bottom + button_height + button_margin,
            button_width,
            button_height,
            "Prêt !",
            self._ready,
            font_size=24,
            border_radius=10,
            bg_color=GREEN
        )
        
        # Bouton de retour
        self.back_button = BackButton(30, 30, 30, self._return_to_menu)
        
        # Message d'état
        self.status_text = "Sélectionnez un navire et placez-le sur la grille"
        self.status_color = WHITE
        
        # Rassembler les boutons pour faciliter la gestion
        self.buttons = [
            self.rotate_button,
            self.random_button,
            self.reset_button,
            self.ready_button
        ]
        
        # Image de fond
        self.background = None
        try:
            bg_path = os.path.join("assets", "images", "ocean_bg.jpg")
            if os.path.exists(bg_path):
                bg = pygame.image.load(bg_path)
                self.background = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            print("Impossible de charger l'image de fond")
        
    def handle_event(self, event):
        """Gérer les événements d'entrée"""
        # Gérer les événements des boutons
        for button in self.buttons:
            button.handle_event(event)
            
        # Gérer le bouton de retour
        self.back_button.handle_event(event)
            
        # Gérer les événements de la grille
        cell = self.grid.handle_event(event)
        if cell:
            self._place_ship_at_cell(*cell)
            
        # Gérer les événements du clavier
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                # Tourner le navire avec la touche 'R'
                self._rotate_ship()
            elif event.key == pygame.K_LEFT or event.key == pygame.K_UP:
                # Navire précédent
                self._select_prev_ship()
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_DOWN:
                # Navire suivant
                self._select_next_ship()
                
        # Mettre à jour l'aperçu du navire lors des mouvements de la souris
        if event.type == pygame.MOUSEMOTION:
            self._update_ship_preview()
            
    def update(self):
        """Mettre à jour l'état de l'écran"""
        for button in self.buttons:
            button.update()
            
        # Mettre à jour le bouton de retour
        self.back_button.update()
            
        # Vérifier si tous les navires sont placés
        all_placed = all(ship.is_placed() for ship in self.player.ships)
        
        # Mettre en évidence le bouton prêt si tous les navires sont placés
        self.ready_button.normal_color = GREEN if all_placed else (100, 100, 100)
        self.ready_button.hover_color = (100, 220, 100) if all_placed else (120, 120, 120)
        self.ready_button.disabled = not all_placed
            
    def render(self, screen):
        """Rendre l'écran de placement des navires"""
        # Fond
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill(BLACK)
            
            # Dessiner un motif de fond alternatif
            self._draw_background_pattern(screen)
        
        # Titre
        screen.blit(self.title_text, self.title_rect)
        
        # Bouton de retour
        self.back_button.draw(screen)
        
        # Dessiner la grille avec les navires et l'aperçu
        self.grid.draw(
            screen, 
            self.player.board, 
            show_ships=True, 
            ship_preview=self.ship_preview
        )
        
        # Panneau de sélection des navires
        self.ships_panel.draw(screen)
        
        # Sous-titre du panneau
        ships_title = self.info_font.render("Flotte disponible", True, WHITE)
        ships_title_rect = ships_title.get_rect(
            center=(self.ships_panel.rect.centerx, self.ships_panel.rect.y + 25)
        )
        screen.blit(ships_title, ships_title_rect)
        
        # Dessiner la sélection des navires
        self._draw_ships_selection(screen)
        
        # Instructions
        instructions = [
            "Cliquez sur la grille pour placer le navire sélectionné",
            "Utilisez R ou le bouton Tourner pour changer l'orientation",
            "Utilisez les flèches ← → pour changer de navire"
        ]
        
        for i, text in enumerate(instructions):
            instr_surface = self.info_font.render(text, True, LIGHT_BLUE)
            instr_rect = instr_surface.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80 + i * 25)
            )
            screen.blit(instr_surface, instr_rect)
        
        # Message d'état
        status_surface = self.info_font.render(self.status_text, True, self.status_color)
        status_rect = status_surface.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 120)
        )
        screen.blit(status_surface, status_rect)
        
        # Dessiner les boutons
        for button in self.buttons:
            button.draw(screen)
            
    def _draw_background_pattern(self, screen):
        """Dessiner un motif de fond pour l'écran"""
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
                    (x + math.sin(y / 50) * 5, y),  # Utilisation de math.sin au lieu de pygame.math.sin
                    2
                )
            
    def _draw_ships_selection(self, screen):
        """Dessiner l'interface de sélection des navires"""
        panel_rect = self.ships_panel.rect
        
        # Position initiale dans le panneau
        ships_x = panel_rect.x + 20
        ships_y = panel_rect.y + 50
        ship_height = 38
        ship_spacing = 5
        
        for i, ship in enumerate(self.player.ships):
            # Zone de fond pour le navire sélectionné
            if i == self.selected_ship_index:
                bg_rect = pygame.Rect(
                    panel_rect.x + 10, 
                    ships_y + i * (ship_height + ship_spacing) - 5,
                    panel_rect.width - 20,
                    ship_height + 10
                )
                
                # Fond de sélection avec dégradé
                for j in range(5):
                    color = (30 + j*5, 100 + j*5, 200 + j*5) if not ship.is_placed() else (80, 80, 80)
                    pygame.draw.rect(
                        screen,
                        color,
                        pygame.Rect(bg_rect.x, bg_rect.y + j*2, bg_rect.width, bg_rect.height - j*4),
                        border_radius=5
                    )
                
                # Bordure
                pygame.draw.rect(
                    screen,
                    WHITE,
                    bg_rect,
                    2,
                    border_radius=5
                )
                
            # Griser les navires déjà placés
            text_color = GRAY if ship.is_placed() else WHITE
            
            # Nom et taille du navire
            ship_text = f"{ship.name} ({ship.size} cases)"
            text_surface = self.ship_font.render(ship_text, True, text_color)
            text_rect = text_surface.get_rect(
                midleft=(ships_x, ships_y + i * (ship_height + ship_spacing) + ship_height // 2)
            )
            
            screen.blit(text_surface, text_rect)
            
            # Dessiner une représentation visuelle du navire
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
        """Mettre à jour l'aperçu du navire en fonction de la position du survol"""
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
        
        # Essayer de placer le navire
        success = self.player.place_ship(ship_index, x, y, horizontal)
        
        if success:
            # Navire placé avec succès
            self.status_text = f"{self.player.ships[ship_index].name} placé avec succès"
            self.status_color = GREEN
            
            # Mode réseau : envoyer le placement du navire au serveur
            if self.game.network_mode in ["host", "client"] and self.game.client:
                self.game.client.place_ship(ship_index, x, y, horizontal)
                
            # Sélectionner le prochain navire non placé
            for i, ship in enumerate(self.player.ships):
                if not ship.is_placed():
                    self.selected_ship_index = i
                    break
        else:
            # Placement invalide
            self.status_text = "Placement invalide !"
            self.status_color = RED
            
    def _random_placement(self):
        """Placer aléatoirement tous les navires"""
        success = self.player.auto_place_ships()
        
        if success:
            self.status_text = "Navires placés aléatoirement"
            self.status_color = GREEN
            
            # Mode réseau : envoyer chaque placement de navire au serveur
            if self.game.network_mode in ["host", "client"] and self.game.client:
                for i, ship in enumerate(self.player.ships):
                    self.game.client.place_ship(i, ship.x, ship.y, ship.horizontal)
        else:
            self.status_text = "Échec du placement aléatoire"
            self.status_color = RED
            
    def _reset_placement(self):
        """Réinitialiser tous les placements de navires"""
        self.player.reset()
        
        # Réinitialiser les navires sur le serveur en mode réseau
        if self.game.network_mode in ["host", "client"] and self.game.client:
            # Pas de commande de réinitialisation directe, on dira au serveur que nous sommes prêts
            # quand nous placerons à nouveau les navires
            pass
            
        self.status_text = "Placement réinitialisé"
        self.status_color = WHITE
        
    def _ready(self):
        """Marquer le joueur comme prêt et passer au jeu"""
        # Vérifier si tous les navires sont placés
        all_placed = all(ship.is_placed() for ship in self.player.ships)
        
        if not all_placed:
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
        elif self.game.network_mode == "local":
            # En mode local, passer à l'autre joueur s'il n'est pas prêt
            if self.current_player_index == 0 and not self.game_state.players[1].ready:
                self.current_player_index = 1
                self.player = self.game_state.players[self.current_player_index]
                self.title_text = self.title_font.render("Joueur 2 - Placez vos navires", True, WHITE)
                self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
                self.status_text = "Joueur 2, placez vos navires"
                self.status_color = WHITE
                
                # Réinitialiser la sélection de navire
                self.selected_ship_index = 0
                self.ship_rotation = True
                self.ship_preview = None
            else:
                # Les deux joueurs sont prêts, démarrer la partie
                self.game_state.player_ready(0)
                self.game_state.player_ready(1)
                self.game.change_screen("game_screen")
    
    def _return_to_menu(self):
        """Retourner au menu principal"""
        # Demander confirmation si des navires ont été placés
        if any(ship.is_placed() for ship in self.player.ships):
            # Dans une version complète, nous pourrions ajouter une boîte de dialogue de confirmation ici
            pass
            
        # En mode réseau, déconnecter du serveur
        if self.game.network_mode in ["host", "client"] and self.game.client:
            self.game.client.disconnect()
            self.game.client = None
            
        if self.game.server:
            self.game.server.stop()
            self.game.server = None
            
        # Retourner au menu principal
        self.game.change_screen("main_screen")