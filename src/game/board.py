from ..utils.constants import GRID_SIZE

class Board:
    def __init__(self):
        # Create empty grid - 0 represents water/empty cell
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.ships = []
        self.shots = []  # List of shots (hit or miss) as (x, y, hit)
        
    def place_ship(self, ship, x, y, horizontal):
        """
        Place a ship on the board
        
        Args:
            ship: Ship object to place
            x, y: Coordinates of the ship's start
            horizontal: True if ship is placed horizontally, False for vertical
            
        Returns:
            True if ship was placed successfully, False otherwise
        """
        # Check if placement is valid
        if not self.is_valid_placement(ship, x, y, horizontal):
            return False
            
        # Place the ship on the grid
        ship.x = x
        ship.y = y
        ship.horizontal = horizontal
        
        # Update the grid with the ship ID
        for i in range(ship.size):
            if horizontal:
                self.grid[y][x + i] = ship.id
            else:
                self.grid[y + i][x] = ship.id
                
        self.ships.append(ship)
        return True
        
    def is_valid_placement(self, ship, x, y, horizontal):
        """
        Check if a ship can be placed at the given position
        
        Args:
            ship: Ship object to place
            x, y: Coordinates of the ship's start
            horizontal: True for horizontal placement, False for vertical
            
        Returns:
            True if placement is valid, False otherwise
        """
        # Check if the ship is inside the grid
        if horizontal:
            if x < 0 or x + ship.size > GRID_SIZE or y < 0 or y >= GRID_SIZE:
                return False
        else:
            if x < 0 or x >= GRID_SIZE or y < 0 or y + ship.size > GRID_SIZE:
                return False
                
        # Check if the ship overlaps with any other ship
        for i in range(ship.size):
            if horizontal:
                if self.grid[y][x + i] != 0:
                    return False
            else:
                if self.grid[y + i][x] != 0:
                    return False
        
        # Check if the ship is adjacent to any other ship (optional rule)
        # We'll check a 1-cell border around the ship
        for i in range(ship.size):
            if horizontal:
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        # Skip checking the ship cells themselves
                        if dy == 0 and 0 <= dx < ship.size:
                            continue
                            
                        nx, ny = x + dx, y + dy
                        if (0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and 
                            self.grid[ny][nx] != 0):
                            return False
            else:
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        # Skip checking the ship cells themselves
                        if dx == 0 and 0 <= dy < ship.size:
                            continue
                            
                        nx, ny = x + dx, y + dy
                        if (0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE and 
                            self.grid[ny][nx] != 0):
                            return False
                            
        return True
        
    def receive_shot(self, x, y):
        """
        Process a shot at the given coordinates
        
        Args:
            x, y: Coordinates of the shot
            
        Returns:
            (hit, ship_id, sunk): Tuple indicating if shot hit a ship, 
                                  which ship was hit (if any), 
                                  and if the ship was sunk
        """
        # Check if coordinates are valid
        if not (0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE):
            return False, None, False
            
        # Check if the cell has already been shot
        for shot_x, shot_y, _ in self.shots:
            if shot_x == x and shot_y == y:
                return False, None, False
                
        ship_id = self.grid[y][x]
        hit = ship_id != 0
        
        # Record the shot
        self.shots.append((x, y, hit))
        
        # If a ship was hit, check if it was sunk
        sunk = False
        if hit:
            # Find the ship that was hit
            ship = next((s for s in self.ships if s.id == ship_id), None)
            if ship:
                ship.hits += 1
                sunk = ship.hits >= ship.size
                
        return hit, ship_id, sunk
        
    def all_ships_sunk(self):
        """Check if all ships on the board have been sunk"""
        return all(ship.hits >= ship.size for ship in self.ships)
        
    def reset(self):
        """Reset the board for a new game"""
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.ships = []
        self.shots = []