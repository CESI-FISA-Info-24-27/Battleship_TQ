import pygame
from ...utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GRID_SIZE, CELL_SIZE, 
    WHITE, BLACK, BLUE, GREEN, RED, SHIPS
)
from ..components.button import Button
from ..components.grid import Grid
from ...game.ship import Ship
from ...game.player import Player
from ...game.game_state import GameState

class ShipPlacement:
    """Screen for placing ships before the game starts"""
    
    def __init__(self, game):
        self.game = game
        
        # Title
        self.title_font = pygame.font.Font(None, 48)
        self.title_text = self.title_font.render("Placez vos navires", True, WHITE)
        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
        
        # Create grid
        grid_x = (SCREEN_WIDTH - (GRID_SIZE * CELL_SIZE)) // 2 - CELL_SIZE
        grid_y = 100
        self.grid = Grid(grid_x, grid_y, is_player_grid=True)
        
        # Player setup
        if self.game.network_mode == "local":
            # In local mode, we'll use the game_state directly
            self.game_state = GameState()
            self.current_player_index = 0
            self.player = self.game_state.players[self.current_player_index]
        else:
            # In network mode, we create a local player for ship placement
            # The real game state will come from the server later
            self.player = Player(0)
            
        # Selected ship
        self.selected_ship_index = 0
        self.ship_rotation = True  # True for horizontal, False for vertical
        
        # Ship preview
        self.ship_preview = None
        
        # UI elements
        button_width = 150
        button_height = 40
        button_margin = 20
        
        # Rotation button
        self.rotate_button = Button(
            grid_x,
            grid_y + (GRID_SIZE + 1) * CELL_SIZE + button_margin,
            button_width,
            button_height,
            "Tourner (R)",
            self._rotate_ship
        )
        
        # Random placement button
        self.random_button = Button(
            grid_x + button_width + button_margin,
            grid_y + (GRID_SIZE + 1) * CELL_SIZE + button_margin,
            button_width,
            button_height,
            "Aléatoire",
            self._random_placement
        )
        
        # Reset button
        self.reset_button = Button(
            grid_x + 2 * (button_width + button_margin),
            grid_y + (GRID_SIZE + 1) * CELL_SIZE + button_margin,
            button_width,
            button_height,
            "Réinitialiser",
            self._reset_placement
        )
        
        # Ready button
        self.ready_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2,
            grid_y + (GRID_SIZE + 1) * CELL_SIZE + 2 * button_margin + button_height,
            button_width,
            button_height,
            "Prêt",
            self._ready
        )
        
        # Status message
        self.status_font = pygame.font.Font(None, 24)
        self.status_text = "Sélectionnez un navire et placez-le sur la grille"
        self.status_color = WHITE
        
        # Group buttons for easier handling
        self.buttons = [
            self.rotate_button,
            self.random_button,
            self.reset_button,
            self.ready_button
        ]
        
    def handle_event(self, event):
        """Handle input events"""
        # Handle button events
        for button in self.buttons:
            button.handle_event(event)
            
        # Handle grid events
        cell = self.grid.handle_event(event)
        if cell:
            self._place_ship_at_cell(*cell)
            
        # Handle keyboard events
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                # Rotate ship with 'R' key
                self._rotate_ship()
            elif event.key == pygame.K_LEFT or event.key == pygame.K_UP:
                # Previous ship
                self._select_prev_ship()
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_DOWN:
                # Next ship
                self._select_next_ship()
                
        # Update ship preview on mouse movement
        if event.type == pygame.MOUSEMOTION:
            self._update_ship_preview()
            
    def update(self):
        """Update screen state"""
        for button in self.buttons:
            button.update()
            
        # Check if all ships are placed
        all_placed = all(ship.is_placed() for ship in self.player.ships)
        self.ready_button.normal_color = GREEN if all_placed else BLUE
            
    def render(self, screen):
        """Render the ship placement screen"""
        # Background
        screen.fill(BLACK)
        
        # Title
        screen.blit(self.title_text, self.title_rect)
        
        # Draw grid with ships and preview
        self.grid.draw(
            screen, 
            self.player.board, 
            show_ships=True, 
            ship_preview=self.ship_preview
        )
        
        # Draw ships selection
        self._draw_ships_selection(screen)
        
        # Status message
        status_surface = self.status_font.render(self.status_text, True, self.status_color)
        status_rect = status_surface.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50)
        )
        screen.blit(status_surface, status_rect)
        
        # Render buttons
        for button in self.buttons:
            button.draw(screen)
            
    def _draw_ships_selection(self, screen):
        """Draw the ship selection UI"""
        font = pygame.font.Font(None, 24)
        
        # Calculate position
        ships_x = 50
        ships_y = 150
        ship_height = 30
        ship_spacing = 10
        
        for i, ship in enumerate(self.player.ships):
            # Highlight selected ship
            background_color = BLUE if i == self.selected_ship_index else BLACK
            
            # Gray out placed ships
            text_color = GRAY if ship.is_placed() else WHITE
            
            # Ship name and size
            ship_text = f"{ship.name} ({ship.size})"
            text_surface = font.render(ship_text, True, text_color)
            text_rect = text_surface.get_rect(
                topleft=(ships_x, ships_y + i * (ship_height + ship_spacing))
            )
            
            # Background for selected ship
            if i == self.selected_ship_index:
                bg_rect = text_rect.inflate(10, 5)
                pygame.draw.rect(screen, background_color, bg_rect)
                pygame.draw.rect(screen, WHITE, bg_rect, 1)
                
            screen.blit(text_surface, text_rect)
            
    def _select_next_ship(self):
        """Select the next ship in the list"""
        self.selected_ship_index = (self.selected_ship_index + 1) % len(self.player.ships)
        self._update_ship_preview()
        
    def _select_prev_ship(self):
        """Select the previous ship in the list"""
        self.selected_ship_index = (self.selected_ship_index - 1) % len(self.player.ships)
        self._update_ship_preview()
        
    def _rotate_ship(self):
        """Rotate the currently selected ship"""
        self.ship_rotation = not self.ship_rotation
        self._update_ship_preview()
        
    def _update_ship_preview(self):
        """Update the ship preview based on hover position"""
        if self.grid.hover_cell:
            ship = self.player.ships[self.selected_ship_index]
            x, y = self.grid.hover_cell
            self.ship_preview = (ship, x, y, self.ship_rotation)
        else:
            self.ship_preview = None
            
    def _place_ship_at_cell(self, x, y):
        """Attempt to place the selected ship at the given cell"""
        ship_index = self.selected_ship_index
        horizontal = self.ship_rotation
        
        # Try to place the ship
        success = self.player.place_ship(ship_index, x, y, horizontal)
        
        if success:
            # Ship placed successfully
            self.status_text = f"{self.player.ships[ship_index].name} placé avec succès"
            self.status_color = GREEN
            
            # Network mode: send ship placement to server
            if self.game.network_mode in ["host", "client"] and self.game.client:
                self.game.client.place_ship(ship_index, x, y, horizontal)
                
            # Select next unplaced ship
            for i, ship in enumerate(self.player.ships):
                if not ship.is_placed():
                    self.selected_ship_index = i
                    break
        else:
            # Invalid placement
            self.status_text = "Placement invalide!"
            self.status_color = RED
            
    def _random_placement(self):
        """Randomly place all ships"""
        success = self.player.auto_place_ships()
        
        if success:
            self.status_text = "Navires placés aléatoirement"
            self.status_color = GREEN
            
            # Network mode: send each ship placement to server
            if self.game.network_mode in ["host", "client"] and self.game.client:
                for i, ship in enumerate(self.player.ships):
                    self.game.client.place_ship(i, ship.x, ship.y, ship.horizontal)
        else:
            self.status_text = "Échec du placement aléatoire"
            self.status_color = RED
            
    def _reset_placement(self):
        """Reset all ship placements"""
        self.player.reset()
        
        # Reset the ships on the server in network mode
        if self.game.network_mode in ["host", "client"] and self.game.client:
            # No direct reset command, we'll just tell the server we're ready
            # when we place ships again
            pass
            
        self.status_text = "Placement réinitialisé"
        self.status_color = WHITE
        
    def _ready(self):
        """Mark player as ready and proceed to game"""
        # Check if all ships are placed
        all_placed = all(ship.is_placed() for ship in self.player.ships)
        
        if not all_placed:
            self.status_text = "Placez tous vos navires avant de continuer!"
            self.status_color = RED
            return
            
        # Mark player as ready
        self.player.ready = True
        
        # Network mode: send ready signal to server
        if self.game.network_mode in ["host", "client"] and self.game.client:
            self.game.client.player_ready()
            self.status_text = "En attente de l'adversaire..."
            self.status_color = BLUE
        elif self.game.network_mode == "local":
            # In local mode, switch to other player if not ready
            if self.current_player_index == 0 and not self.game_state.players[1].ready:
                self.current_player_index = 1
                self.player = self.game_state.players[self.current_player_index]
                self.title_text = self.title_font.render("Joueur 2 - Placez vos navires", True, WHITE)
                self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
                self.status_text = "Joueur 2, placez vos navires"
                self.status_color = WHITE
            else:
                # Both players ready, start the game
                self.game_state.player_ready(0)
                self.game_state.player_ready(1)
                self.game.change_screen("game")