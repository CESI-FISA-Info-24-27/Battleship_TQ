class Ship:
    """Class representing a ship in the game"""
    
    next_id = 1  # Class variable to ensure unique IDs
    
    def __init__(self, name, size):
        self.id = Ship.next_id
        Ship.next_id += 1
        
        self.name = name
        self.size = size
        self.x = -1  # Initial position (not placed)
        self.y = -1
        self.horizontal = True  # True for horizontal, False for vertical
        self.hits = 0  # Number of times this ship has been hit
        
    def is_placed(self):
        """Check if the ship has been placed on the board"""
        return self.x >= 0 and self.y >= 0
        
    def is_sunk(self):
        """Check if the ship has been sunk"""
        return self.hits >= self.size
        
    def get_coordinates(self):
        """Get the coordinates of all cells occupied by the ship"""
        if not self.is_placed():
            return []
            
        coords = []
        for i in range(self.size):
            if self.horizontal:
                coords.append((self.x + i, self.y))
            else:
                coords.append((self.x, self.y + i))
                
        return coords
        
    def contains_point(self, x, y):
        """Check if the ship contains the given point"""
        if not self.is_placed():
            return False
            
        if self.horizontal:
            return self.y == y and self.x <= x < self.x + self.size
        else:
            return self.x == x and self.y <= y < self.y + self.size
            
    def rotate(self):
        """Rotate the ship"""
        self.horizontal = not self.horizontal
        
    @classmethod
    def reset_ids(cls):
        """Reset the ship ID counter (useful for starting a new game)"""
        cls.next_id = 1