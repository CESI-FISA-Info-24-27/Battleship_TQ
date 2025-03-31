from .board import Board
from .ship import Ship
from ..utils.constants import SHIPS

class Player:
    def __init__(self, id):
        self.id = id
        self.board = Board()
        self.ships = [Ship(ship["name"], ship["size"]) for ship in SHIPS]
        self.ready = False  # Flag to indicate if player has placed all ships
        
    def reset(self):
        """Reset the player for a new game"""
        self.board.reset()
        Ship.reset_ids()
        self.ships = [Ship(ship["name"], ship["size"]) for ship in SHIPS]
        self.ready = False
        
    def place_ship(self, ship_index, x, y, horizontal):
        """
        Place a ship on the player's board
        
        Args:
            ship_index: Index of the ship in the ships list
            x, y: Coordinates for placement
            horizontal: True for horizontal placement, False for vertical
            
        Returns:
            True if placement was successful, False otherwise
        """
        if ship_index < 0 or ship_index >= len(self.ships):
            return False
            
        ship = self.ships[ship_index]
        if ship.is_placed():
            # Remove ship from board if it's already placed
            self._remove_ship_from_board(ship)
            
        result = self.board.place_ship(ship, x, y, horizontal)
        
        # Check if all ships are placed
        self.ready = all(ship.is_placed() for ship in self.ships)
        
        return result
        
    def _remove_ship_from_board(self, ship):
        """
        Remove a ship from the board 
        (useful for repositioning during placement phase)
        """
        if not ship.is_placed():
            return
            
        # Clear the ship from the grid
        for x, y in ship.get_coordinates():
            if 0 <= x < len(self.board.grid[0]) and 0 <= y < len(self.board.grid):
                self.board.grid[y][x] = 0
                
        # Reset ship position
        ship.x = -1
        ship.y = -1
        
        # Remove from ships list if it's there
        if ship in self.board.ships:
            self.board.ships.remove(ship)
            
    def auto_place_ships(self):
        """
        Automatically place all ships on the board randomly
        
        Returns:
            True if all ships were placed successfully, False otherwise
        """
        import random
        
        # First reset the board
        self.board.reset()
        
        # Maximum number of retries for the whole placement
        max_total_attempts = 3
        total_attempts = 0
        
        while total_attempts < max_total_attempts:
            # Reset board for a new attempt
            self.board.reset()
            ships_placed = 0
            
            # Try to place each ship
            for ship in self.ships:
                placed = False
                max_attempts_per_ship = 100
                attempts = 0
                
                while not placed and attempts < max_attempts_per_ship:
                    # Random position
                    x = random.randint(0, len(self.board.grid[0]) - 1)
                    y = random.randint(0, len(self.board.grid) - 1)
                    horizontal = random.choice([True, False])
                    
                    placed = self.board.place_ship(ship, x, y, horizontal)
                    attempts += 1
                    
                if not placed:
                    # If we couldn't place this ship, break the loop and try again
                    break
                else:
                    ships_placed += 1
            
            # If all ships were placed successfully
            if ships_placed == len(self.ships):
                self.ready = True
                return True
                
            total_attempts += 1
            
        # If we couldn't place all ships after max retries
        return False
        
    def receive_shot(self, x, y):
        """Process a shot from the opponent"""
        return self.board.receive_shot(x, y)
        
    def has_lost(self):
        """Check if the player has lost (all ships sunk)"""
        return self.board.all_ships_sunk()