import pygame
from ...utils.constants import WHITE, BLACK, BLUE, LIGHT_BLUE, BUTTON_HOVER_COLOR

class Button:
    """
    Classe de bouton améliorée avec design moderne
    """
    
    def __init__(self, x, y, width, height, text, action=None, 
                font_size=24, border_radius=5, bg_color=None, 
                hover_color=None, text_color=None, shadow=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.font = pygame.font.Font(None, font_size)
        self.border_radius = border_radius
        self.shadow = shadow
        
        # Couleurs du bouton
        self.normal_color = bg_color if bg_color is not None else BLUE
        self.hover_color = hover_color if hover_color is not None else BUTTON_HOVER_COLOR
        self.text_color = text_color if text_color is not None else WHITE
        
        # État actuel
        self.hovered = False
        self.clicked = False
        self.disabled = False
        
        # Animation
        self.scale = 1.0
        self.target_scale = 1.0
        self.scale_speed = 0.1
        
    def handle_event(self, event):
        """
        Gérer les événements d'entrée pour le bouton
        
        Args:
            event: Objet d'événement Pygame
        """
        if self.disabled:
            return
            
        if event.type == pygame.MOUSEMOTION:
            # Survol de la souris
            self.hovered = self.rect.collidepoint(event.pos)
            self.target_scale = 1.05 if self.hovered else 1.0
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Clic de la souris
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.clicked = True
                self.target_scale = 0.95
                
        elif event.type == pygame.MOUSEBUTTONUP:
            # Relâchement de la souris
            was_clicked = self.clicked
            self.clicked = False
            
            if event.button == 1 and self.rect.collidepoint(event.pos) and was_clicked:
                if self.action:
                    self.action()
            
            self.target_scale = 1.05 if self.hovered else 1.0
            
    def update(self):
        """Mettre à jour l'état du bouton"""
        # Animation d'échelle fluide
        if abs(self.scale - self.target_scale) > 0.01:
            self.scale += (self.target_scale - self.scale) * self.scale_speed
        else:
            self.scale = self.target_scale
        
    def draw(self, surface):
        """
        Dessiner le bouton sur la surface donnée
        
        Args:
            surface: Surface Pygame sur laquelle dessiner
        """
        # Calculer les dimensions mises à l'échelle
        scaled_width = int(self.rect.width * self.scale)
        scaled_height = int(self.rect.height * self.scale)
        
        # Centrer le bouton mis à l'échelle
        x = self.rect.centerx - scaled_width // 2
        y = self.rect.centery - scaled_height // 2
        
        scaled_rect = pygame.Rect(x, y, scaled_width, scaled_height)
        
        # Dessiner l'ombre si activée
        if self.shadow and not self.clicked:
            shadow_rect = scaled_rect.copy()
            shadow_rect.move_ip(2, 2)
            pygame.draw.rect(
                surface, 
                (0, 0, 0, 128), 
                shadow_rect, 
                border_radius=self.border_radius
            )
        
        # Couleur du bouton en fonction de l'état
        if self.disabled:
            color = (100, 100, 100)  # Gris pour désactivé
        elif self.clicked:
            # Assombrir légèrement la couleur lorsque cliqué
            color = tuple(max(0, c - 30) for c in self.normal_color)
        elif self.hovered:
            color = self.hover_color
        else:
            color = self.normal_color
            
        # Fond du bouton
        pygame.draw.rect(
            surface, 
            color, 
            scaled_rect, 
            border_radius=self.border_radius
        )
        
        # Contour du bouton
        pygame.draw.rect(
            surface, 
            BLACK, 
            scaled_rect, 
            2, 
            border_radius=self.border_radius
        )
        
        # Texte du bouton
        text_surface = self.font.render(self.text, True, self.text_color)
        text_rect = text_surface.get_rect(center=scaled_rect.center)
        
        # Décalage du texte lorsque cliqué
        if self.clicked:
            text_rect.move_ip(1, 1)
            
        surface.blit(text_surface, text_rect)
        
    def set_disabled(self, disabled):
        """
        Activer ou désactiver le bouton
        
        Args:
            disabled: True pour désactiver, False pour activer
        """
        self.disabled = disabled
        if disabled:
            self.hovered = False
            self.clicked = False