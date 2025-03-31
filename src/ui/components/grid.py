import pygame
from ...utils.constants import (
    GRID_SIZE, CELL_SIZE, WHITE, BLACK, BLUE, LIGHT_BLUE, 
    RED, GREEN, GRAY
)

class Grid:
    """
    A grid component for rendering the game board
    """
    
    def __init__(self, x, y, is_player_grid=True):
        self.x = x
        self.y = y
        self.is_player_grid = is_player_grid
        self.width = GRID_SIZE * CELL_SIZE
        self.height = GRID_SIZE * CELL_SIZE
        
        # Labels for rows and columns
        self.font = pygame.font.Font(None, 24)
        
        # Selection
        self.selected_cell = None
        self.hover_cell = None
        
    def handle_event(self, event):
        """
        Handle mouse events on the grid
        
        Args:
            event: Pygame event
            
        Returns:
            (x, y): Cell coordinates if a cell was clicked, None otherwise
        """
        if event.type == pygame.MOUSEMOTION:
            mouse_x, mouse_y = event.pos
            cell_x, cell_y = self._get_cell_at_pos(mouse_x, mouse_y)
            
            if 0 <= cell_x < GRID_SIZE and 0 <= cell_y < GRID_SIZE:
                self.hover_cell = (cell_x, cell_y)
            else:
                self.hover_cell = None
                
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = event.pos
            cell_x, cell_y = self._get_cell_at_pos(mouse_x, mouse_y)
            
            if 0 <= cell_x < GRID_SIZE and 0 <= cell_y < GRID_SIZE:
                self.selected_cell = (cell_x, cell_y)
                return (cell_x, cell_y)
                
        return None
        
    def _get_cell_at_pos(self, mouse_x, mouse_y):
        """
        Get the cell coordinates at the given mouse position
        
        Args:
            mouse_x, mouse_y: Mouse coordinates
            
        Returns:
            (cell_x, cell_y): Cell coordinates (may be out of bounds)
        """
        # Adjust for row/column labels
        grid_x = mouse_x - (self.x + CELL_SIZE)
        grid_y = mouse_y - (self.y + CELL_SIZE)
        
        cell_x = grid_x // CELL_SIZE
        cell_y = grid_y // CELL_SIZE
        
        return (cell_x, cell_y)
        
    def draw(self, surface, board=None, show_ships=True, ship_preview=None):
        """
        Draw the grid on the given surface
        
        Args:
            surface: Pygame surface to draw on
            board: Board object to visualize (optional)
            show_ships: Whether to show ships on the board
            ship_preview: (ship, x, y, horizontal) for ship placement preview
        """
        # Draw labels
        # Column labels (A-J)
        for i in range(GRID_SIZE):
            label = self.font.render(chr(65 + i), True, WHITE)
            label_rect = label.get_rect(
                center=(self.x + CELL_SIZE * (i + 1) + CELL_SIZE // 2, self.y + CELL_SIZE // 2)
            )
            surface.blit(label, label_rect)
            
        # Row labels (1-10)
        for i in range(GRID_SIZE):
            label = self.font.render(str(i + 1), True, WHITE)
            label_rect = label.get_rect(
                center=(self.x + CELL_SIZE // 2, self.y + CELL_SIZE * (i + 1) + CELL_SIZE // 2)
            )
            surface.blit(label, label_rect)
            
        # Draw grid cells
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                rect = pygame.Rect(
                    self.x + CELL_SIZE * (x + 1),
                    self.y + CELL_SIZE * (y + 1),
                    CELL_SIZE,
                    CELL_SIZE
                )
                
                # Default cell color
                cell_color = LIGHT_BLUE
                
                # Draw cell based on board state
                if board:
                    # Ship cell
                    if board.grid[y][x] != 0 and show_ships:
                        cell_color = GRAY
                        
                    # Shot cell
                    for shot_x, shot_y, hit in board.shots:
                        if shot_x == x and shot_y == y:
                            cell_color = RED if hit else BLUE
                            break
                
                # Draw the cell
                pygame.draw.rect(surface, cell_color, rect)
                pygame.draw.rect(surface, BLACK, rect, 1)
                
                # Highlight selected cell
                if self.selected_cell == (x, y):
                    pygame.draw.rect(surface, WHITE, rect, 3)
                    
                # Highlight hovered cell
                elif self.hover_cell == (x, y):
                    pygame.draw.rect(surface, WHITE, rect, 2)
                    
        # Draw ship placement preview
        if ship_preview:
            ship, ship_x, ship_y, horizontal = ship_preview
            
            # Draw preview cells
            for i in range(ship.size):
                if horizontal:
                    x, y = ship_x + i, ship_y
                else:
                    x, y = ship_x, ship_y + i
                    
                if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                    rect = pygame.Rect(
                        self.x + CELL_SIZE * (x + 1),
                        self.y + CELL_SIZE * (y + 1),
                        CELL_SIZE,
                        CELL_SIZE
                    )
                    
                    # Use green for valid placement, red for invalid
                    if board and board.is_valid_placement(ship, ship_x, ship_y, horizontal):
                        pygame.draw.rect(surface, GREEN, rect)
                    else:
                        pygame.draw.rect(surface, RED, rect)
                        
                    pygame.draw.rect(surface, BLACK, rect, 1)