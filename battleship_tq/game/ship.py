# ship.py
import pygame
from game.constants import CELL_SIZE, DEEP_BLUE, LIGHT_BLUE, WHITE

class Ship:
    def __init__(self, name, size, color=DEEP_BLUE):
        self.name = name
        self.size = size
        self.row = 0
        self.col = 0
        self.orientation = 'H'  # 'H' pour horizontal, 'V' pour vertical
        self.color = color
        self.placed = False
        self.hits = [False] * size
    
    def is_hit(self, row, col):
        """Vérifie si une position donnée touche ce navire"""
        if self.orientation == 'H':
            if row != self.row:
                return False
            if not (self.col <= col < self.col + self.size):
                return False
            index = col - self.col
            self.hits[index] = True
            return True
        else:  # Vertical
            if col != self.col:
                return False
            if not (self.row <= row < self.row + self.size):
                return False
            index = row - self.row
            self.hits[index] = True
            return True
    
    def is_sunk(self):
        """Vérifie si le navire est coulé (toutes les cases touchées)"""
        return all(self.hits)
    
    def get_positions(self):
        """Renvoie toutes les positions occupées par ce navire"""
        positions = []
        if self.orientation == 'H':
            for i in range(self.size):
                positions.append((self.row, self.col + i))
        else:
            for i in range(self.size):
                positions.append((self.row + i, self.col))
        return positions
    
    def place(self, row, col, orientation):
        """Place le navire à une position donnée"""
        self.row = row
        self.col = col
        self.orientation = orientation
        self.placed = True
    
    def rotate(self):
        """Change l'orientation du navire"""
        self.orientation = 'V' if self.orientation == 'H' else 'H'
    
    def draw(self, screen, x, y, preview=False, valid=True):
        """Dessine le navire à l'écran comme un simple cube blanc"""
        # Déterminer la couleur en fonction du contexte
        if preview:
            # Utiliser des couleurs différentes pour l'aperçu
            color = (50, 255, 100) if valid else (255, 50, 50)  # Vert si valide, rouge sinon
            border_color = color
        else:
            # Couleur normale pour les navires placés (blanc)
            color = WHITE
            border_color = (200, 200, 200)  # Bordure grise claire
        
        # Dessiner chaque segment du navire comme un simple rectangle blanc
        if self.orientation == 'H':
            for i in range(self.size):
                # Créer un rectangle pour chaque cellule du navire
                rect = pygame.Rect(x + i * CELL_SIZE, y, CELL_SIZE, CELL_SIZE)
                
                # Remplir le rectangle
                pygame.draw.rect(screen, color, rect, 0)
                
                # Ajouter une bordure
                pygame.draw.rect(screen, border_color, rect, 1)
                
                # Ajouter une ligne diagonale pour indiquer un coup si la cellule est touchée
                if i < len(self.hits) and self.hits[i] and not preview:
                    pygame.draw.line(screen, (255, 0, 0), 
                                  (x + i * CELL_SIZE + 5, y + 5),
                                  (x + i * CELL_SIZE + CELL_SIZE - 5, y + CELL_SIZE - 5), 2)
                    pygame.draw.line(screen, (255, 0, 0), 
                                  (x + i * CELL_SIZE + CELL_SIZE - 5, y + 5),
                                  (x + i * CELL_SIZE + 5, y + CELL_SIZE - 5), 2)
        else:  # Vertical
            for i in range(self.size):
                # Créer un rectangle pour chaque cellule du navire
                rect = pygame.Rect(x, y + i * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                
                # Remplir le rectangle
                pygame.draw.rect(screen, color, rect, 0)
                
                # Ajouter une bordure
                pygame.draw.rect(screen, border_color, rect, 1)
                
                # Ajouter une ligne diagonale pour indiquer un coup si la cellule est touchée
                if i < len(self.hits) and self.hits[i] and not preview:
                    pygame.draw.line(screen, (255, 0, 0), 
                                  (x + 5, y + i * CELL_SIZE + 5),
                                  (x + CELL_SIZE - 5, y + i * CELL_SIZE + CELL_SIZE - 5), 2)
                    pygame.draw.line(screen, (255, 0, 0), 
                                  (x + CELL_SIZE - 5, y + i * CELL_SIZE + 5),
                                  (x + 5, y + i * CELL_SIZE + CELL_SIZE - 5), 2)