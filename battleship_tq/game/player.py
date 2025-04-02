# player.py
import random
from game.grid import Grid
from game.ship import Ship
from game.constants import NAVIRES

class Player:
    def __init__(self, name="Joueur"):
        self.name = name
        self.grid = Grid(owner="player")
        self.ships_to_place = []
        self.current_ship_index = 0
        self.ready = False
        self._initialize_ships()
    
    def _initialize_ships(self):
        """Initialise les navires à placer"""
        self.ships_to_place = []
        for name, size in NAVIRES.items():
            self.ships_to_place.append(Ship(name, size))
        random.shuffle(self.ships_to_place)  # Les navires peuvent être placés dans n'importe quel ordre
    
    def get_current_ship(self):
        """Retourne le navire actuellement en cours de placement"""
        if self.current_ship_index < len(self.ships_to_place):
            return self.ships_to_place[self.current_ship_index]
        return None
    
    def place_current_ship(self, row, col, orientation):
        """Place le navire actuel sur la grille"""
        if self.current_ship_index >= len(self.ships_to_place):
            return False
        
        ship = self.ships_to_place[self.current_ship_index]
        ship.orientation = orientation
        
        if self.grid.place_ship(ship, row, col, orientation):
            self.current_ship_index += 1
            
            # Vérifier si tous les navires sont placés
            if self.current_ship_index >= len(self.ships_to_place):
                self.ready = True
            
            return True
        
        return False
    
    def next_ship(self):
        """Passe au navire suivant"""
        if self.current_ship_index < len(self.ships_to_place) - 1:
            self.current_ship_index += 1
            return True
        return False
    
    def previous_ship(self):
        """Revient au navire précédent"""
        if self.current_ship_index > 0:
            self.current_ship_index -= 1
            return True
        return False
    
    def rotate_current_ship(self):
        """Change l'orientation du navire actuel"""
        ship = self.get_current_ship()
        if ship:
            ship.rotate()
            return True
        return False
    
    def make_shot(self, opponent_grid, row, col):
        """Effectue un tir sur la grille de l'adversaire"""
        return opponent_grid.receive_shot(row, col)
    
    def get_ships_left(self):
        """Retourne le nombre de navires qui ne sont pas coulés"""
        return len(self.grid.ships) - self.grid.get_sunk_ships_count()
    
    def reset(self):
        """Réinitialise le joueur pour une nouvelle partie"""
        self.grid = Grid(owner="player")
        self.ships_to_place = []
        self.current_ship_index = 0
        self.ready = False
        self._initialize_ships()

