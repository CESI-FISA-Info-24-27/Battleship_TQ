from .player import Player
from ..utils.constants import PLACING_SHIPS, WAITING_FOR_OPPONENT, YOUR_TURN, OPPONENT_TURN, GAME_OVER

class GameState:
    """
    Class to track the overall state of the game,
    especially for network synchronization
    """
    
    def __init__(self):
        self.players = [Player(0), Player(1)]
        self.current_player_index = 0  # Index of the player whose turn it is
        self.state = PLACING_SHIPS
        self.winner = None
        self.last_shot = None  # (x, y, hit, ship_id, sunk)
        
    def get_current_player(self):
        """Get the player whose turn it is"""
        return self.players[self.current_player_index]
        
    def get_opponent_player(self):
        """Get the opponent player"""
        return self.players[1 - self.current_player_index]
        
    def switch_turn(self):
        """Switch to the other player's turn"""
        self.current_player_index = 1 - self.current_player_index
        
    def player_ready(self, player_id):
        """Mark a player as ready (all ships placed)"""
        self.players[player_id].ready = True
        
        # If both players are ready, start the game
        if all(player.ready for player in self.players):
            self.state = YOUR_TURN if self.current_player_index == 0 else OPPONENT_TURN
            
    def process_shot(self, player_id, x, y):
        """
        Process a shot from a player
        
        Args:
            player_id: ID of the player making the shot
            x, y: Coordinates of the shot
            
        Returns:
            True if the shot was valid, False otherwise
        """
        # Ensure it's the player's turn
        if self.current_player_index != player_id or self.state not in [YOUR_TURN, OPPONENT_TURN]:
            return False
            
        # Process the shot on the opponent's board
        opponent = self.get_opponent_player()
        hit, ship_id, sunk = opponent.receive_shot(x, y)
        
        # Record the last shot for UI updates
        self.last_shot = (x, y, hit, ship_id, sunk)
        
        # Check if the game is over
        if opponent.has_lost():
            self.state = GAME_OVER
            self.winner = player_id
        else:
            # Switch turns
            self.switch_turn()
            if self.current_player_index == 0:
                self.state = YOUR_TURN
            else:
                self.state = OPPONENT_TURN
                
        return True
        
    def reset(self):
        """Reset the game state for a new game"""
        for player in self.players:
            player.reset()
            
        self.current_player_index = 0
        self.state = PLACING_SHIPS
        self.winner = None
        self.last_shot = None