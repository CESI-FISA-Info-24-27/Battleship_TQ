# grid.py
import pygame
import math
import time
from game.constants import GRID_SIZE, CELL_SIZE, DARK_BLUE, GRID_BLUE, WHITE, RED, YELLOW, WATER_BLUE, LIGHT_BLUE, BLACK

class Grid:
    def __init__(self, owner="player"):
        self.size = GRID_SIZE
        self.cells = [[' ' for _ in range(self.size)] for _ in range(self.size)]
        self.shots = [[' ' for _ in range(self.size)] for _ in range(self.size)]
        self.owner = owner
        self.ships = []
    
    def place_ship(self, ship, row, col, orientation):
        """Place un navire sur la grille"""
        if not self.can_place_ship(ship.size, row, col, orientation):
            return False
        
        ship.place(row, col, orientation)
        
        # Marquer les cellules occupées
        positions = ship.get_positions()
        for r, c in positions:
            self.cells[r][c] = 'N'
        
        self.ships.append(ship)
        return True
    
    def can_place_ship(self, size, row, col, orientation):
        """Vérifie si un navire peut être placé sur la grille"""
        if orientation == 'H':
            if col + size > self.size:
                return False
            
            # Vérifier si les cellules sont libres
            for i in range(size):
                if self.cells[row][col + i] != ' ':
                    return False
            
            return True
        else:  # Vertical
            if row + size > self.size:
                return False
            
            # Vérifier si les cellules sont libres
            for i in range(size):
                if self.cells[row + i][col] != ' ':
                    return False
            
            return True
    
    def receive_shot(self, row, col):
        """Traite un tir sur cette grille et retourne le résultat"""
        if not (0 <= row < self.size and 0 <= col < self.size):
            return "invalid"
        
        if self.shots[row][col] != ' ':
            return "already_shot"
        
        if self.cells[row][col] == 'N':
            self.shots[row][col] = 'X'
            self.cells[row][col] = 'X'
            
            # Vérifier si un navire est coulé
            for ship in self.ships:
                if ship.is_hit(row, col) and ship.is_sunk():
                    return "sunk"
            
            return "hit"
        else:
            self.shots[row][col] = 'O'
            return "miss"
    
    def are_all_ships_sunk(self):
        """Vérifie si tous les navires sont coulés"""
        return all(ship.is_sunk() for ship in self.ships)
    
    def get_sunk_ships_count(self):
        """Retourne le nombre de navires coulés"""
        return sum(1 for ship in self.ships if ship.is_sunk())
    
    def draw(self, screen, position, show_ships=True, preview_ship=None, preview_pos=None, preview_valid=True):
        """Dessine la grille à l'écran"""
        x_start, y_start = position
        
        # Dessiner le fond de la grille
        grid_rect = pygame.Rect(x_start, y_start, CELL_SIZE * self.size, CELL_SIZE * self.size)
        pygame.draw.rect(screen, DARK_BLUE, grid_rect)
        pygame.draw.rect(screen, GRID_BLUE, grid_rect, 3)
        
        # Dessiner les lignes de la grille
        for i in range(1, self.size):
            # Lignes horizontales
            pygame.draw.line(screen, GRID_BLUE, 
                          (x_start, y_start + i * CELL_SIZE),
                          (x_start + CELL_SIZE * self.size, y_start + i * CELL_SIZE), 1)
            
            # Lignes verticales
            pygame.draw.line(screen, GRID_BLUE, 
                          (x_start + i * CELL_SIZE, y_start),
                          (x_start + i * CELL_SIZE, y_start + CELL_SIZE * self.size), 1)
        
        # Dessiner d'abord les navires (pour qu'ils soient en dessous des indicateurs de tir)
        if show_ships:
            for ship in self.ships:
                if ship.orientation == 'H':
                    ship.draw(screen, x_start + ship.col * CELL_SIZE, y_start + ship.row * CELL_SIZE)
                else:
                    ship.draw(screen, x_start + ship.col * CELL_SIZE, y_start + ship.row * CELL_SIZE)
        
        # Dessiner les tirs
        for row in range(self.size):
            for col in range(self.size):
                cell_x = x_start + col * CELL_SIZE
                cell_y = y_start + row * CELL_SIZE
                cell_rect = pygame.Rect(cell_x, cell_y, CELL_SIZE, CELL_SIZE)
                
                # Dessiner les tirs - Style simplifié
                if self.shots[row][col] == 'X':
                    # Case touchée - X rouge
                    pygame.draw.line(screen, RED, 
                                  (cell_x + 5, cell_y + 5), 
                                  (cell_x + CELL_SIZE - 5, cell_y + CELL_SIZE - 5), 2)
                    pygame.draw.line(screen, RED, 
                                  (cell_x + CELL_SIZE - 5, cell_y + 5), 
                                  (cell_x + 5, cell_y + CELL_SIZE - 5), 2)
                
                elif self.shots[row][col] == 'O':
                    # Case manquée - Cercle bleu
                    center_x, center_y = cell_x + CELL_SIZE // 2, cell_y + CELL_SIZE // 2
                    pygame.draw.circle(screen, WATER_BLUE, (center_x, center_y), CELL_SIZE // 3, 2)
                
                # Marquage pour les tirs en attente (mode réseau)
                elif self.shots[row][col] == '?':
                    # Afficher un point d'interrogation en attente de réponse
                    center_x, center_y = cell_x + CELL_SIZE // 2, cell_y + CELL_SIZE // 2
                    question_font = pygame.font.SysFont("Arial", CELL_SIZE // 2)
                    question_text = question_font.render("?", True, YELLOW)
                    screen.blit(question_text, 
                              (center_x - question_text.get_width() // 2, 
                               center_y - question_text.get_height() // 2))
        
        # Afficher les lettres (A-J) pour les colonnes
        for col in range(self.size):
            lettre = chr(65 + col)
            font = pygame.font.SysFont("Arial", int(CELL_SIZE * 0.4))  # Taille proportionnelle à la cellule
            texte = font.render(lettre, True, WHITE)
            screen.blit(texte, (x_start + col * CELL_SIZE + CELL_SIZE // 2 - texte.get_width() // 2, 
                             y_start - 30))
        
        # Afficher les chiffres (0-9) pour les lignes
        for row in range(self.size):
            font = pygame.font.SysFont("Arial", int(CELL_SIZE * 0.4))
            texte = font.render(str(row), True, WHITE)
            screen.blit(texte, 
                      (x_start - 30 + (30 - texte.get_width()) // 2, 
                       y_start + row * CELL_SIZE + CELL_SIZE // 2 - texte.get_height() // 2))
        
        # Afficher l'aperçu du navire en cours de placement
        if preview_ship and preview_pos:
            preview_row, preview_col = preview_pos
            if 0 <= preview_row < self.size and 0 <= preview_col < self.size:
                x_preview = x_start + preview_col * CELL_SIZE
                y_preview = y_start + preview_row * CELL_SIZE
                preview_ship.draw(screen, x_preview, y_preview, True, preview_valid)