import pygame

class Panel:
    """
    Composant pour créer des panneaux d'interface utilisateur avec un style moderne
    """
    
    def __init__(self, x, y, width, height, bg_color, border_color=None, 
                border_width=0, alpha=1.0, border_radius=10, shadow=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.bg_color = bg_color
        self.border_color = border_color
        self.border_width = border_width
        self.alpha = alpha
        self.border_radius = border_radius
        self.shadow = shadow
        
        # Créer des surfaces pour l'alpha
        self._create_surfaces()
        
    def _create_surfaces(self):
        """Créer les surfaces pour le rendu avec transparence"""
        self.surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        
        # Surface pour l'ombre si activée
        if self.shadow:
            self.shadow_surface = pygame.Surface((self.rect.width + 8, self.rect.height + 8), pygame.SRCALPHA)
        
    def draw(self, screen):
        """
        Dessiner le panneau sur l'écran
        
        Args:
            screen: Surface Pygame sur laquelle dessiner
        """
        # Effacer les surfaces
        self.surface.fill((0, 0, 0, 0))
        if self.shadow:
            self.shadow_surface.fill((0, 0, 0, 0))
            
        # Dessiner l'ombre
        if self.shadow:
            shadow_color = (0, 0, 0, 100)  # Couleur noire semi-transparente
            pygame.draw.rect(
                self.shadow_surface,
                shadow_color,
                pygame.Rect(4, 4, self.rect.width, self.rect.height),
                border_radius=self.border_radius
            )
            shadow_rect = self.shadow_surface.get_rect(topleft=(self.rect.x - 4, self.rect.y - 4))
            screen.blit(self.shadow_surface, shadow_rect)
            
        # Dessiner le fond avec transparence
        bg_color_with_alpha = (*self.bg_color[:3], int(255 * self.alpha))
        pygame.draw.rect(
            self.surface,
            bg_color_with_alpha,
            pygame.Rect(0, 0, self.rect.width, self.rect.height),
            border_radius=self.border_radius
        )
        
        # Dessiner la bordure si nécessaire
        if self.border_color and self.border_width > 0:
            pygame.draw.rect(
                self.surface,
                self.border_color,
                pygame.Rect(0, 0, self.rect.width, self.rect.height),
                self.border_width,
                border_radius=self.border_radius
            )
            
        # Dessiner la surface sur l'écran
        screen.blit(self.surface, self.rect)
        
    def update_position(self, x, y):
        """
        Mettre à jour la position du panneau
        
        Args:
            x: Nouvelle position x
            y: Nouvelle position y
        """
        self.rect.x = x
        self.rect.y = y
        
    def contains_point(self, point):
        """
        Vérifier si un point est à l'intérieur du panneau
        
        Args:
            point: Tuple (x, y) à vérifier
            
        Returns:
            True si le point est à l'intérieur du panneau, False sinon
        """
        return self.rect.collidepoint(point)