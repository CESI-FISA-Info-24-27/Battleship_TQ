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
        self.game_state = None
        self.game_state_initialized = False
        
    def _init_game_state(self):
        """Initialize game state based on network mode"""
        if not self.game_state_initialized:
            try:
                if self.game.network_mode in ["solo", "local"]:
                    # Toujours récupérer le dernier état de l'écran de placement
                    if hasattr(self.game, 'screens') and "ship_placement" in self.game.screens and hasattr(self.game.screens["ship_placement"], 'game_state'):
                        self.game_state = self.game.screens["ship_placement"].game_state
                        print("État du jeu récupéré de l'écran de placement")
                    else:
                        # Créer un nouveau GameState si nécessaire
                        from ...game.game_state import GameState
                        self.game_state = GameState()
                        print("Nouvel état de jeu créé")
                else:
                    # En mode réseau, l'état du jeu vient du serveur
                    if self.game.client:
                        def on_game_state_update(game_state):
                            self.game_state = game_state
                            
                            # Vérifier les animations de tir si nous avons un last_shot
                            if game_state.last_shot:
                                x, y, hit, _, _ = game_state.last_shot
                                self.animation_coords = (x, y)
                                self.animation_hit = hit
                                self.animation_timer = 30  # frames
                        
                        self.game.client.set_callback(on_game_state_update)
                
                self.game_state_initialized = True
            except Exception as e:
                print(f"Erreur lors de l'initialisation du game state: {e}")
                import traceback
                traceback.print_exc()
                    
    def handle_event(self, event):
        """Handle input events"""
        # Initialize game state if needed
        if not self.game_state_initialized:
            self._init_game_state()
            
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
        # Initialize game state if needed
        if not self.game_state_initialized:
            self._init_game_state()
            
        for button in self.buttons:
            button.update()
            
        # Update status text based on game state
        self._update_status_text()
        
        # Gérer le tour du bot en mode solo
        if (self.game.network_mode == "solo" and self.game_state and 
            self.game_state.state == OPPONENT_TURN and 
            self.animation_timer <= 0):
            
            # Faire jouer le bot
            try:
                bot_result = self.game_state.bot_play()
                
                if bot_result:
                    # Configurer l'animation pour le tir du bot
                    x, y, hit, _, _ = bot_result
                    self.animation_coords = (x, y)
                    self.animation_hit = hit
                    self.animation_timer = 30  # frames
            except Exception as e:
                print(f"Erreur pendant le tour du bot: {e}")
                import traceback
                traceback.print_exc()
                
        # Update animations
        if self.animation_timer > 0:
            self.animation_timer -= 1
            
    def _update_status_text(self):
        """Update the status text based on the current game state"""
        if not hasattr(self, 'game_state') or not self.game_state:
            if self.game.network_mode == "solo":
                self.status_text = "Mode Solo - En attente de l'initialisation..."
                self.status_color = BLUE
            else:
                self.status_text = "En attente de la connexion..."
                self.status_color = BLUE
            return
            
        state = self.game_state.state
        
        if state == PLACING_SHIPS:
            self.status_text = "En attente que les joueurs placent leurs navires..."
            self.status_color = BLUE
        elif state == WAITING_FOR_OPPONENT:
            if self.game.network_mode == "solo":
                self.status_text = "Prêt à jouer - À votre tour"
                self.status_color = GREEN
            else:
                self.status_text = "En attente de l'adversaire..."
                self.status_color = BLUE
        elif state == YOUR_TURN:
            self.status_text = "À votre tour - cliquez sur la grille adverse pour tirer"
            self.status_color = GREEN
        elif state == OPPONENT_TURN:
            if self.game.network_mode == "solo":
                self.status_text = "Tour de l'IA - L'ordinateur réfléchit..."
                self.status_color = RED
            else:
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
        # Initialize game state if needed
        if not self.game_state_initialized:
            self._init_game_state()
            
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
            
        # Local or solo game
        if self.game.network_mode in ["local", "solo"]:
            # Check if the shot is valid
            player_id = self.game_state.current_player_index
            if self.game_state.process_shot(player_id, x, y):
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
            
        if self.game.network_mode in ["local", "solo"]:
            # In local mode, current_player_index indicates whose turn it is
            return self.game_state.current_player_index == 0
        else:
            # In network mode, check if state is YOUR_TURN
            return self.game_state.state == YOUR_TURN
            
    def _get_player_id(self):
        """Get the player ID based on game mode"""
        if self.game.network_mode in ["local", "solo"]:
            # In local mode, we're always player 0
            return 0
        else:
            # In network mode, we have a fixed player ID
            return self.game.client.player_id if self.game.client else 0
            
    def _new_game(self):
        """Start a new game"""
        try:
            if self.game.network_mode in ["local", "solo"]:
                # Marquer que nous devons réinitialiser pour la prochaine fois
                self.game_state_initialized = False
                
                # Informer l'écran de placement qu'il doit aussi se réinitialiser
                if hasattr(self.game, 'screens') and "ship_placement" in self.game.screens:
                    ship_screen = self.game.screens["ship_placement"]
                    
                    # Réinitialiser l'ID statique des navires 
                    from ...game.ship import Ship
                    Ship.next_id = 1
                    
                    # Créer un nouveau GameState
                    from ...game.game_state import GameState
                    new_game_state = GameState()
                    
                    # Mettre à jour l'écran de placement
                    ship_screen.game_state = new_game_state
                    ship_screen.current_player_index = 0
                    ship_screen.player = new_game_state.players[0]
                    ship_screen.selected_ship_index = 0
                    ship_screen.ship_rotation = True
                    ship_screen.ship_preview = None
                    
                    # Effacer les status messages
                    ship_screen.status_text = ""
                
                # Aller à l'écran de placement des navires
                self.game.change_screen("ship_placement")
            else:
                # En mode réseau, nous devons coordonner avec le serveur
                # Pour l'instant, revenir au menu principal
                self._return_to_menu()
        except Exception as e:
            print(f"Erreur lors de la nouvelle partie: {e}")
            import traceback
            traceback.print_exc()
            
    def _return_to_menu(self):
        """Return to the main menu"""
        try:
            # Close connections in network mode
            if self.game.network_mode in ["host", "client"]:
                if self.game.client:
                    self.game.client.disconnect()
                    self.game.client = None
                    
                if self.game.server:
                    self.game.server.stop()
                    self.game.server = None
            
            # Réinitialiser les données d'état du jeu
            self.game_state = None
            self.game_state_initialized = False
                    
            # Go back to main menu
            print("Retour au menu principal")
            self.game.change_screen("main_menu")
        except Exception as e:
            print(f"Erreur lors du retour au menu: {e}")
            import traceback
            traceback.print_exc()
                
        # Go back to main menu
        self.game.change_screen("main_screen")