# ship.py
import pygame
from game.constants import CELL_SIZE, DEEP_BLUE, LIGHT_BLUE

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
        """Dessine le navire à l'écran"""
        color = self.color
        if preview:
            color = (50, 255, 100) if valid else (255, 50, 50)
        
        if self.orientation == 'H':
            width = CELL_SIZE * self.size
            height = CELL_SIZE
            
            # Corps du bateau
            rect = pygame.Rect(x, y, width, height)
            pygame.draw.rect(screen, color, rect, 0 if not preview else 2)
            
            # Pont supérieur
            pont_height = height // 2
            pygame.draw.rect(screen, 
                           (min(255, color[0] + 40), min(255, color[1] + 40), min(255, color[2] + 40)),
                           (x + width//10, y + height//4, width - width//5, pont_height), 
                           0 if not preview else 1)
            
            # Avant du bateau en forme de flèche
            points = [(x, y), (x, y + height), (x + width//10, y + height//2)]
            pygame.draw.polygon(screen, color, points)
            
            # Cabine
            if self.size >= 3:
                pygame.draw.rect(screen, 
                               (min(255, color[0] + 30), min(255, color[1] + 30), min(255, color[2] + 30)),
                               (x + width//3, y + 2, width//3, height//2), 
                               0 if not preview else 1)
        else:  # Vertical
            width = CELL_SIZE
            height = CELL_SIZE * self.size
            
            # Corps du bateau
            rect = pygame.Rect(x, y, width, height)
            pygame.draw.rect(screen, color, rect, 0 if not preview else 2)
            
            # Pont supérieur
            pygame.draw.rect(screen, 
                           (min(255, color[0] + 40), min(255, color[1] + 40), min(255, color[2] + 40)),
                           (x + width//4, y + height//10, width//2, height - height//5), 
                           0 if not preview else 1)
            
            # Avant du bateau en forme de flèche
            points = [(x, y), (x + width, y), (x + width//2, y + height//10)]
            pygame.draw.polygon(screen, color, points)
            
            # Cabine
            if self.size >= 3:
                pygame.draw.rect(screen, 
                               (min(255, color[0] + 30), min(255, color[1] + 30), min(255, color[2] + 30)),
                               (x + 2, y + height//3, width//2, height//3), 
                               0 if not preview else 1)

