import pygame
from ...utils.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, GRID_SIZE, CELL_SIZE, 
    WHITE, BLACK, BLUE, RED, GREEN, GRAY,
    PLACING_SHIPS, WAITING_FOR_OPPONENT, YOUR_TURN, OPPONENT_TURN, GAME_OVER
)
from ..components.button import Button
from ..components.grid import Grid

class GameScreen:
    """Main game screen where the actual gameplay happens"""
    
    def __init__(self, game):
        self.game = game
        
        # Fonts
        self.title_font = pygame.font.Font(None, 36)
        self.info_font = pygame.font.Font(None, 24)
        
        # Title
        self.title_text = self.title_font.render("Bataille Navale", True, WHITE)
        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, 30))
        
        # Status message
        self.status_text = ""
        self.status_color = WHITE
        
        # Calculate grid positions
        grid_width = (GRID_SIZE + 1) * CELL_SIZE
        grid_height = (GRID_SIZE + 1) * CELL_SIZE
        margin = 50
        
        # Create player grid (left)
        player_grid_x = margin
        player_grid_y = 70
        self.player_grid = Grid(player_grid_x, player_grid_y, is_player_grid=True)
        
        # Create opponent grid (right)
        opponent_grid_x = SCREEN_WIDTH - margin - grid_width
        opponent_grid_y = 70
        self.opponent_grid = Grid(opponent_grid_x, opponent_grid_y, is_player_grid=False)
        
        # Grid labels
        self.player_label = self.title_font.render("Votre grille", True, WHITE)
        self.player_label_rect = self.player_label.get_rect(
            center=(player_grid_x + grid_width // 2, player_grid_y - 20)
        )
        
        self.opponent_label = self.title_font.render("Grille adversaire", True, WHITE)
        self.opponent_label_rect = self.opponent_label.get_rect(
            center=(opponent_grid_x + grid_width // 2, opponent_grid_y - 20)
        )
        
        # Buttons
        button_width = 150
        button_height = 40
        button_y = player_grid_y + grid_height + 20
        
        self.new_game_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2,
            button_y,
            button_width,
            button_height,
            "Nouvelle partie",
            self._new_game
        )
        
        self.main_menu_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2,
            button_y + button_height + 10,
            button_width,
            button_height,
            "Menu principal",
            self._return_to_menu
        )
        
        # Group buttons for easier handling
        self.buttons = [
            self.new_game_button,
            self.main_menu_button
        ]
        
        # Animation for shots
        self.animation_timer = 0
        self.animation_coords = None
        self.animation_hit = False
        
        # Game state reference
        if self.game.network_mode == "local":
            # Use the game state created in the ship placement screen
            self.game_state = self.game.screens["ship_placement"].game_state
        else:
            # In network mode, the game state comes from the server
            # We'll set the callback to update our state
            if self.game.client:
                def on_game_state_update(game_state):
                    self.game_state = game_state
                    
                self.game.client.set_callback(on_game_state_update)
                
    def handle_event(self, event):
        """Handle input events"""
        # Handle button events
        for button in self.buttons:
            button.handle_event(event)
            
        # In player's turn, handle clicks on opponent grid
        if self._is_player_turn():
            # Only allow clicks on opponent grid
            cell = self.opponent_grid.handle_event(event)
            if cell:
                self._fire_shot(*cell)
                
    def update(self):
        """Update screen state"""
        for button in self.buttons:
            button.update()
            
        # Update status text based on game state
        self._update_status_text()
        
        # Update animations
        if self.animation_timer > 0:
            self.animation_timer -= 1
            
    def _update_status_text(self):
        """Update the status text based on the current game state"""
        if not hasattr(self, 'game_state') or not self.game_state:
            self.status_text = "En attente de la connexion..."
            self.status_color = BLUE
            return
            
        state = self.game_state.state
        
        if state == PLACING_SHIPS:
            self.status_text = "En attente que les joueurs placent leurs navires..."
            self.status_color = BLUE
        elif state == WAITING_FOR_OPPONENT:
            self.status_text = "En attente de l'adversaire..."
            self.status_color = BLUE
        elif state == YOUR_TURN:
            self.status_text = "À votre tour - cliquez sur la grille adverse pour tirer"
            self.status_color = GREEN
        elif state == OPPONENT_TURN:
            self.status_text = "Tour de l'adversaire - attendez votre tour"
            self.status_color = RED
        elif state == GAME_OVER:
            if self.game_state.winner == self._get_player_id():
                self.status_text = "Victoire! Tous les navires adverses ont été coulés!"
                self.status_color = GREEN
            else:
                self.status_text = "Défaite! Tous vos navires ont été coulés!"
                self.status_color = RED
                
    def render(self, screen):
        """Render the game screen"""
        # Background
        screen.fill(BLACK)
        
        # Title
        screen.blit(self.title_text, self.title_rect)
        
        # Grid labels
        screen.blit(self.player_label, self.player_label_rect)
        screen.blit(self.opponent_label, self.opponent_label_rect)
        
        # Only render if we have a game state
        if hasattr(self, 'game_state') and self.game_state:
            # Get player ID and boards
            player_id = self._get_player_id()
            player_board = self.game_state.players[player_id].board
            opponent_board = self.game_state.players[1 - player_id].board
            
            # Draw player grid (show ships)
            self.player_grid.draw(screen, player_board, show_ships=True)
            
            # Draw opponent grid (hide ships)
            self.opponent_grid.draw(screen, opponent_board, show_ships=False)
            
            # Draw shot animations
            if self.animation_timer > 0 and self.animation_coords:
                self._draw_shot_animation(screen)
                
        # Status message
        status_surface = self.info_font.render(self.status_text, True, self.status_color)
        status_rect = status_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 70))
        screen.blit(status_surface, status_rect)
        
        # Render buttons
        for button in self.buttons:
            button.draw(screen)
            
    def _draw_shot_animation(self, screen):
        """Draw animation for a shot"""
        grid_x, grid_y = self.animation_coords
        
        # Determine which grid to draw on
        if self._is_player_turn():
            # Player's shot on opponent grid
            x = self.opponent_grid.x + CELL_SIZE * (grid_x + 1) + CELL_SIZE // 2
            y = self.opponent_grid.y + CELL_SIZE * (grid_y + 1) + CELL_SIZE // 2
        else:
            # Opponent's shot on player grid
            x = self.player_grid.x + CELL_SIZE * (grid_x + 1) + CELL_SIZE // 2
            y = self.player_grid.y + CELL_SIZE * (grid_y + 1) + CELL_SIZE // 2
            
        # Animation size depends on timer
        max_size = CELL_SIZE * 0.8
        size = max_size * (1 - self.animation_timer / 30)
        
        # Draw circle for the shot
        color = RED if self.animation_hit else BLUE
        pygame.draw.circle(screen, color, (x, y), size)
        
    def _fire_shot(self, x, y):
        """Fire a shot at the given coordinates on the opponent's grid"""
        if not self._is_player_turn():
            return
            
        # Local game
        if self.game.network_mode == "local":
            # Check if the shot is valid
            player_id = self.game_state.current_player_index
            self.game_state.process_shot(player_id, x, y)
            
            # Set animation
            self.animation_coords = (x, y)
            self.animation_hit = self.game_state.last_shot[2]  # hit status
            self.animation_timer = 30  # frames
        
        # Network game
        elif self.game.client:
            self.game.client.fire_shot(x, y)
            
            # Animation will be triggered when we get the game state update
            
    def _is_player_turn(self):
        """Check if it's the player's turn"""
        if not hasattr(self, 'game_state') or not self.game_state:
            return False
            
        if self.game.network_mode == "local":
            # In local mode, current_player_index indicates whose turn it is
            return True
        else:
            # In network mode, check if state is YOUR_TURN
            return self.game_state.state == YOUR_TURN
            
    def _get_player_id(self):
        """Get the player ID based on game mode"""
        if self.game.network_mode == "local":
            # In local mode, we're always the current player
            return self.game_state.current_player_index
        else:
            # In network mode, we have a fixed player ID
            return self.game.client.player_id if self.game.client else 0
            
    def _new_game(self):
        """Start a new game"""
        if self.game.network_mode == "local":
            # Reset the game state
            self.game_state.reset()
            
            # Go back to ship placement
            self.game.change_screen("ship_placement")
        else:
            # In network mode, we need to coordinate with the server
            # For now, just go back to main menu
            self._return_to_menu()
            
    def _return_to_menu(self):
        """Return to the main menu"""
        # Close connections in network mode
        if self.game.network_mode in ["host", "client"]:
            if self.game.client:
                self.game.client.disconnect()
                self.game.client = None
                
            if self.game.server:
                self.game.server.stop()
                self.game.server = None
                
        # Go back to main menu
        self.game.change_screen("main_menu")