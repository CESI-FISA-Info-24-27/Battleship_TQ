import random
from game.constants import FACILE, MOYEN, DIFFICILE, GRID_SIZE
from game.grid import Grid  # ✅ Ajouté

class AIPlayer:
    def __init__(self, difficulty=MOYEN):
        self.difficulty = difficulty
        self.last_hit = None
        self.successful_hits = []
        self.hunt_direction = None
        self.grid = Grid()  # ✅ Corrige le bug

    def place_ships(self, grid, ships):
        """Place aléatoirement les navires sur la grille"""
        for ship in ships:
            placed = False
            while not placed:
                orientation = random.choice(['H', 'V'])
                
                if orientation == 'H':
                    row = random.randint(0, GRID_SIZE - 1)
                    col = random.randint(0, GRID_SIZE - ship.size)
                else:
                    row = random.randint(0, GRID_SIZE - ship.size)
                    col = random.randint(0, GRID_SIZE - 1)
                
                if grid.can_place_ship(ship.size, row, col, orientation):
                    ship.orientation = orientation
                    placed = grid.place_ship(ship, row, col, orientation)

    def make_shot(self, opponent_grid):
        if self.difficulty == FACILE:
            return self._easy_shot(opponent_grid)
        elif self.difficulty == MOYEN:
            return self._medium_shot(opponent_grid)
        else:
            return self._hard_shot(opponent_grid)

    def _easy_shot(self, grid):
        while True:
            row = random.randint(0, GRID_SIZE - 1)
            col = random.randint(0, GRID_SIZE - 1)
            if grid.shots[row][col] == ' ':
                return row, col

    def _medium_shot(self, grid):
        if self.last_hit and grid.shots[self.last_hit[0]][self.last_hit[1]] == 'X':
            row, col = self.last_hit
            directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
            random.shuffle(directions)
            for dr, dc in directions:
                new_row, new_col = row + dr, col + dc
                if (0 <= new_row < GRID_SIZE and 
                    0 <= new_col < GRID_SIZE and 
                    grid.shots[new_row][new_col] == ' '):
                    self.last_hit = (new_row, new_col)
                    return new_row, new_col
        shot = self._easy_shot(grid)
        self.last_hit = shot
        return shot

    def _hard_shot(self, grid):
        if self.successful_hits:
            row, col = self.successful_hits[0]
            if self.hunt_direction:
                dr, dc = self.hunt_direction
                new_row, new_col = row + dr, col + dc
                if (0 <= new_row < GRID_SIZE and 
                    0 <= new_col < GRID_SIZE and 
                    grid.shots[new_row][new_col] == ' '):
                    self.last_hit = (new_row, new_col)
                    return new_row, new_col
                self.hunt_direction = (-dr, -dc)
                new_row, new_col = self.successful_hits[0][0] + self.hunt_direction[0], self.successful_hits[0][1] + self.hunt_direction[1]
                if (0 <= new_row < GRID_SIZE and 
                    0 <= new_col < GRID_SIZE and 
                    grid.shots[new_row][new_col] == ' '):
                    self.last_hit = (new_row, new_col)
                    return new_row, new_col
                self.successful_hits.pop(0)
                self.hunt_direction = None
                return self._hard_shot(grid)
            directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
            random.shuffle(directions)
            for dr, dc in directions:
                new_row, new_col = row + dr, col + dc
                if (0 <= new_row < GRID_SIZE and 
                    0 <= new_col < GRID_SIZE and 
                    grid.shots[new_row][new_col] == ' '):
                    self.last_hit = (new_row, new_col)
                    return new_row, new_col
            self.successful_hits.pop(0)
            return self._hard_shot(grid)
        checkerboard = []
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if (row + col) % 2 == 0 and grid.shots[row][col] == ' ':
                    checkerboard.append((row, col))
        if checkerboard and random.random() < 0.7:
            row, col = random.choice(checkerboard)
            self.last_hit = (row, col)
            return row, col
        shot = self._easy_shot(grid)
        self.last_hit = shot
        return shot

    def process_shot_result(self, result, row, col):
        if self.difficulty == DIFFICILE:
            if result == "hit":
                self.successful_hits.append((row, col))
            elif result == "sunk":
                self.successful_hits = []
                self.hunt_direction = None
            elif result == "hit" and self.last_hit and not self.hunt_direction:
                for prev_hit in self.successful_hits[:-1]:
                    prev_row, prev_col = prev_hit
                    if prev_row == row:
                        self.hunt_direction = (0, 1 if col > prev_col else -1)
                        break
                    elif prev_col == col:
                        self.hunt_direction = (1 if row > prev_row else -1, 0)
                        break
