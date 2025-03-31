import pygame
from ...utils.constants import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, BLUE, RED, GREEN
from ..components.button import Button
from ...network.client import Client

class ConnectionScreen:
    """Screen for entering server IP to connect to"""
    
    def __init__(self, game):
        self.game = game
        
        # Title
        self.title_font = pygame.font.Font(None, 48)
        self.title_text = self.title_font.render("Rejoindre une partie", True, WHITE)
        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, 100))
        
        # Input field
        self.input_rect = pygame.Rect(SCREEN_WIDTH // 2 - 150, 200, 300, 40)
        self.input_text = "localhost"  # Default value
        self.input_active = True
        self.input_font = pygame.font.Font(None, 32)
        
        # Instructions
        self.instructions_font = pygame.font.Font(None, 24)
        self.instructions_text = self.instructions_font.render(
            "Entrez l'adresse IP du serveur", True, WHITE
        )
        self.instructions_rect = self.instructions_text.get_rect(
            center=(SCREEN_WIDTH // 2, 170)
        )
        
        # Connect button
        button_width = 150
        button_height = 40
        self.connect_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2,
            270,
            button_width,
            button_height,
            "Connecter",
            self._connect_to_server
        )
        
        # Back button
        self.back_button = Button(
            SCREEN_WIDTH // 2 - button_width // 2,
            330,
            button_width,
            button_height,
            "Retour",
            self._back_to_menu
        )
        
        # Status message (for connection attempts)
        self.status_font = pygame.font.Font(None, 24)
        self.status_text = ""
        self.status_color = WHITE
        
        # Group buttons for easier handling
        self.buttons = [
            self.connect_button,
            self.back_button
        ]
        
    def handle_event(self, event):
        """Handle input events"""
        # Handle button events
        for button in self.buttons:
            button.handle_event(event)
            
        # Handle text input for the server address
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Toggle input field active state when clicked
            self.input_active = self.input_rect.collidepoint(event.pos)
            
        if event.type == pygame.KEYDOWN and self.input_active:
            if event.key == pygame.K_RETURN:
                # Connect when Enter is pressed
                self._connect_to_server()
            elif event.key == pygame.K_BACKSPACE:
                # Remove last character
                self.input_text = self.input_text[:-1]
            else:
                # Add character to input text
                if len(self.input_text) < 30:  # Limit length
                    self.input_text += event.unicode
                    
    def update(self):
        """Update screen state"""
        for button in self.buttons:
            button.update()
            
    def render(self, screen):
        """Render the connection screen"""
        # Background
        screen.fill(BLACK)
        
        # Title
        screen.blit(self.title_text, self.title_rect)
        
        # Instructions
        screen.blit(self.instructions_text, self.instructions_rect)
        
        # Input field
        input_color = BLUE if self.input_active else WHITE
        pygame.draw.rect(screen, input_color, self.input_rect, 2)
        
        # Input text
        text_surface = self.input_font.render(self.input_text, True, WHITE)
        # Ensure text is not too wide for the input box
        text_rect = text_surface.get_rect(midleft=(self.input_rect.x + 10, self.input_rect.centery))
        screen.blit(text_surface, text_rect)
        
        # Status message (if any)
        if self.status_text:
            status_surface = self.status_font.render(self.status_text, True, self.status_color)
            status_rect = status_surface.get_rect(center=(SCREEN_WIDTH // 2, 380))
            screen.blit(status_surface, status_rect)
        
        # Render buttons
        for button in self.buttons:
            button.draw(screen)
            
    def _connect_to_server(self):
        """Attempt to connect to the server with the entered IP"""
        self.status_text = "Tentative de connexion..."
        self.status_color = WHITE
        
        # Create a new client
        host = self.input_text.strip()
        self.game.client = Client(host=host)
        
        # Try to connect
        if self.game.client.connect():
            self.status_text = "Connexion réussie!"
            self.status_color = GREEN
            
            # Set up game state listener
            def on_game_state_update(game_state):
                # This will be called when the server sends a game state update
                pass
                
            self.game.client.set_callback(on_game_state_update)
            
            # Move to ship placement screen
            self.game.change_screen("ship_placement")
        else:
            self.status_text = "Échec de la connexion"
            self.status_color = RED
            self.game.client = None
            
    def _back_to_menu(self):
        """Return to the main menu"""
        self.game.change_screen("main_menu")