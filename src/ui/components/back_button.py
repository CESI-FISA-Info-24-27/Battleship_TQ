import pygame
from ...utils.constants import WHITE, BLACK, GRAY, DARK_BLUE, LIGHT_BLUE

class BackButton:
    """
    Bouton de retour pour naviguer vers l'écran précédent
    """
    
    def __init__(self, x, y, size=30, action=None):
        self.x = x
        self.y = y
        self.size = size
        self.action = action
        
        # Créer un rectangle pour la zone cliquable
        self.rect = pygame.Rect(x - size//2, y - size//2, size, size)
        
        # Couleurs
        self.normal_color = DARK_BLUE
        self.hover_color = LIGHT_BLUE
        self.border_color = BLACK
        
        # État
        self.hovered = False
        self.clicked = False
        
    def handle_event(self, event):
        """
        Gérer les événements pour le bouton de retour
        
        Args:
            event: Objet d'événement Pygame
        """
        if event.type == pygame.MOUSEMOTION:
            # Survol de la souris
            self.hovered = self.rect.collidepoint(event.pos)
            
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # Clic de la souris
            if event.button == 1 and self.rect.collidepoint(event.pos):
                self.clicked = True
                
        elif event.type == pygame.MOUSEBUTTONUP:
            # Relâchement de la souris
            was_clicked = self.clicked
            self.clicked = False
            
            if event.button == 1 and self.rect.collidepoint(event.pos) and was_clicked:
                if self.action:
                    self.action()
                    
    def update(self):
        """Mettre à jour l'état du bouton"""
        # Rien à faire pour le moment
        pass
        
    def draw(self, surface):
        """
        Dessiner le bouton sur la surface donnée
        
        Args:
            surface: Surface Pygame sur laquelle dessiner
        """
        # Déterminer la couleur en fonction de l'état
        color = self.hover_color if self.hovered else self.normal_color
        if self.clicked:
            # Assombrir légèrement la couleur lorsque cliqué
            color = tuple(max(0, c - 30) for c in color)
            
        # Dessiner le cercle de fond
        pygame.draw.circle(surface, color, (self.x, self.y), self.size // 2)
        
        # Dessiner la bordure
        pygame.draw.circle(surface, self.border_color, (self.x, self.y), self.size // 2, 2)
        
        # Dessiner la flèche (triangle)
        arrow_size = self.size // 3
        
        # Points du triangle (flèche vers la gauche)
        points = [
            (self.x + arrow_size//2, self.y - arrow_size//2),  # Haut
            (self.x - arrow_size//2, self.y),                  # Pointe 
            (self.x + arrow_size//2, self.y + arrow_size//2)   # Bas
        ]
        
        pygame.draw.polygon(surface, WHITE, points)
        
        # Texte "Retour" à côté du bouton
        if self.hovered:
            font = pygame.font.Font(None, 20)
            text = font.render("Retour", True, WHITE)
            text_rect = text.get_rect(midleft=(self.x + self.size//2 + 5, self.y))
            surface.blit(text, text_rect)