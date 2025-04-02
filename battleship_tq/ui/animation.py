# animation.py
import pygame
import math
import time
from game.constants import SCREEN_WIDTH, SCREEN_HEIGHT, DARK_BLUE, LIGHT_BLUE, DEEP_BLUE

class BackgroundAnimation:
    """Classe pour gérer l'animation du fond de la mer"""
    def __init__(self):
        self.wave_time = 0
        self.boats = [
            # [x, y, taille, orientation, vitesse, décalage]
            [0, 550, 3, 'H', 20, 0],
            [SCREEN_WIDTH, 650, 2, 'H', -15, 1],
            [0, 700, 4, 'H', 10, 2]
        ]
    
    def draw(self, screen):
        """Dessine le fond animé de la mer"""
        # Fond noir pour l'océan
        screen.fill((0, 0, 0))
        
        # Ajouter des effets d'ondulation sous-marine (vagues légères)
        for y in range(0, SCREEN_HEIGHT, 20):
            amplitude = 5
            frequence = 0.05
            for x in range(0, SCREEN_WIDTH, 4):
                offset = amplitude * math.sin(frequence * x + time.time())
                pygame.draw.line(screen, DARK_BLUE, (x, y + offset), (x, y + 10 + offset), 2)
        
        # Dessiner quelques bateaux décoratifs qui se déplacent lentement
        self._dessiner_bateaux_decoratifs(screen)
    
    def _dessiner_bateaux_decoratifs(self, screen):
        """Dessine les bateaux décoratifs qui se déplacent sur l'eau"""
        t = time.time()
        
        for boat in self.boats:
            x, y, taille, orientation, vitesse, offset = boat
            
            # Mettre à jour la position x
            x = (vitesse * (t + offset) % (SCREEN_WIDTH + 100)) - 50 if vitesse > 0 else SCREEN_WIDTH - ((abs(vitesse) * (t + offset) % (SCREEN_WIDTH + 100)) - 50)
            
            # Stocker la nouvelle position
            boat[0] = x
            
            # Dessiner le bateau
            self._dessiner_bateau(screen, x, y, taille, orientation, LIGHT_BLUE if offset % 2 == 0 else DEEP_BLUE)
    
    def _dessiner_bateau(self, screen, x, y, taille, orientation, couleur):
        """Dessine un bateau stylisé"""
        cell_size = 40  # Même valeur que dans constants.py
        
        if orientation == 'H':
            width = cell_size * taille
            height = cell_size
            rect = pygame.Rect(x, y, width, height)
            
            # Corps du bateau
            pygame.draw.rect(screen, couleur, rect, 0)
            
            # Pont supérieur
            pont_height = height // 2
            pygame.draw.rect(screen, 
                           (min(255, couleur[0] + 40), min(255, couleur[1] + 40), min(255, couleur[2] + 40)),
                           (x + width//10, y + height//4, width - width//5, pont_height))
            
            # Avant du bateau en forme de flèche
            points = [(x, y), (x, y + height), (x + width//10, y + height//2)]
            pygame.draw.polygon(screen, couleur, points)
            
            # Cabine si le bateau est assez grand
            if taille >= 3:
                pygame.draw.rect(screen, 
                               (min(255, couleur[0] + 30), min(255, couleur[1] + 30), min(255, couleur[2] + 30)),
                               (x + width//3, y + 2, width//3, height//2))
        else:  # Vertical
            width = cell_size
            height = cell_size * taille
            rect = pygame.Rect(x, y, width, height)
            
            # Corps du bateau
            pygame.draw.rect(screen, couleur, rect, 0)
            
            # Pont supérieur
            pygame.draw.rect(screen, 
                           (min(255, couleur[0] + 40), min(255, couleur[1] + 40), min(255, couleur[2] + 40)),
                           (x + width//4, y + height//10, width//2, height - height//5))
            
            # Avant du bateau en forme de flèche
            points = [(x, y), (x + width, y), (x + width//2, y + height//10)]
            pygame.draw.polygon(screen, couleur, points)
            
            # Cabine
            if taille >= 3:
                pygame.draw.rect(screen, 
                               (min(255, couleur[0] + 30), min(255, couleur[1] + 30), min(255, couleur[2] + 30)),
                               (x + 2, y + height//3, width//2, height//3))

