import pygame
from ...utils.constants import WHITE, GRAY, LIGHT_GRAY, BLACK

class Button:
    """
    A button class for handling UI interactions
    """
    
    def __init__(self, x, y, width, height, text, action=None, font_size=24):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.font = pygame.font.Font(None, font_size)
        
        # Button states
        self.normal_color = GRAY
        self.hover_color = LIGHT_GRAY
        self.text_color = BLACK
        
        # Current state
        self.hovered = False
        self.clicked = False
        
    def handle_event(self, event):
        """
        Handle input events for the button
        
        Args:
            event: Pygame event object
        """
        if event.type == pygame.MOUSEMOTION:
            # Mouse hover
            self.hovered = self.rect.collidepoint(event.pos)
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Mouse click
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.clicked = True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            # Mouse release
            if event.button == 1 and self.rect.collidepoint(event.pos) and self.clicked:
                if self.action:
                    self.action()
            self.clicked = False
            
    def update(self):
        """Update button state"""
        # Nothing to do here for now
        pass
        
    def draw(self, surface):
        """
        Draw the button on the given surface
        
        Args:
            surface: Pygame surface to draw on
        """
        # Button background
        color = self.hover_color if self.hovered else self.normal_color
        if self.clicked:
            # Slightly darken when clicked
            color = tuple(max(0, c - 30) for c in color)
            
        pygame.draw.rect(surface, color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 2)  # Border
        
        # Button text
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)