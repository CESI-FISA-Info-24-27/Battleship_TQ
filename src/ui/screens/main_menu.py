import pygame
from ...utils.constants import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, BLUE, LIGHT_BLUE
from ..components.button import Button

class MainMenu:
    """Main menu screen for the game"""
    
    def __init__(self, game):
        self.game = game
        
        # Title
        self.title_font = pygame.font.Font(None, 64)
        self.title_text = self.title_font.render("Bataille Navale", True, WHITE)
        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        
        # Create buttons
        button_width = 200
        button_height = 50
        button_margin = 20
        
        button_y = 250
        self.host_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2,
            button_y,
            button_width,
            button_height,
            "Héberger une partie",
            self._host_game
        )
        
        button_y += button_height + button_margin
        self.join_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2,
            button_y,
            button_width,
            button_height,
            "Rejoindre une partie",
            self._join_game
        )
        
        button_y += button_height + button_margin
        self.local_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2,
            button_y,
            button_width,
            button_height,
            "Jouer en local",
            self._play_local
        )
        
        button_y += button_height + button_margin
        self.quit_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2,
            button_y,
            button_width,
            button_height,
            "Quitter",
            self._quit_game
        )
        
        # Group buttons for easier handling
        self.buttons = [
            self.host_button,
            self.join_button,
            self.local_button,
            self.quit_button
        ]
        
    def handle_event(self, event):
        """Handle input events"""
        for button in self.buttons:
            button.handle_event(event)
            
    def update(self):
        """Update screen state"""
        for button in self.buttons:
            button.update()
            
    def render(self, screen):
        """Render the menu on the screen"""
        # Background
        screen.fill(BLACK)
        
        # Add a decorative background
        for i in range(10):
            for j in range(10):
                rect = pygame.Rect(
                    50 + i * 70,
                    150 + j * 40,
                    60,
                    30
                )
                if (i + j) % 2 == 0:
                    pygame.draw.rect(screen, BLUE, rect, 1)
                else:
                    pygame.draw.rect(screen, LIGHT_BLUE, rect, 1)
        
        # Title
        screen.blit(self.title_text, self.title_rect)
        
        # Render buttons
        for button in self.buttons:
            button.draw(screen)
            
    def _host_game(self):
        """Start a new game as server"""
        from ...network.server import Server
        
        # Start the server
        self.game.server = Server()
        if self.game.server.start():
            # Also connect as a client (player 0)
            from ...network.client import Client
            self.game.client = Client()
            if self.game.client.connect():
                self.game.set_network_mode("host")
                self.game.change_screen("ship_placement")
            else:
                # Failed to connect as client
                self.game.server.stop()
                self.game.server = None
        else:
            # Failed to start server
            self.game.server = None
            
    def _join_game(self):
        """Join an existing game"""
        self.game.set_network_mode("client")
        self.game.change_screen("connection")
        
    def _play_local(self):
        """Start a local game (no networking)"""
        self.game.set_network_mode("local")
        self.game.change_screen("ship_placement")
        
    def _quit_game(self):
        """Exit the game"""
        self.game.running = False