from .player import Player
from ..utils.constants import PLACING_SHIPS, WAITING_FOR_OPPONENT, YOUR_TURN, OPPONENT_TURN, GAME_OVER, GRID_SIZE

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
        self.is_solo_mode = False  # Flag pour indiquer le mode solo
        
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
            OU (x, y, hit, ship_id, sunk) en mode solo
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
        
        # En mode solo, retourner le tuple complet pour faciliter l'animation
        if self.is_solo_mode and player_id == 1:  # Si c'est le bot qui tire en mode solo
            return self.last_shot
                
        return True
    
    def bot_play(self):
        """
        Faire jouer le bot (en mode solo)
        
        Returns:
            (x, y, hit, ship_id, sunk): Résultat du tir du bot
        """
        import random
        
        # Vérifier si c'est le tour du bot (joueur 1)
        if self.current_player_index != 1:
            return None
            
        player = self.get_opponent_player()  # Joueur humain
        
        # Stratégie simple pour l'IA:
        # 1. Si un navire a été touché mais pas coulé, tirer autour
        # 2. Sinon, tirer aléatoirement dans une case non explorée
        
        # Obtenir les tirs précédents
        shots = player.board.shots
        
        # Lister les cases où un tir a touché mais pas coulé
        hits = []
        for x, y, hit in shots:
            if hit:
                ship_id = player.board.grid[y][x]
                ship = next((s for s in player.board.ships if s.id == ship_id), None)
                if ship and ship.hits < ship.size:  # Vérifie si le navire n'est pas coulé
                    hits.append((x, y))
        
        # Liste des directions possibles pour explorer autour d'un hit
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        
        # Si nous avons des hits non coulés, tirer autour
        for hit_x, hit_y in hits:
            for dx, dy in directions:
                x, y = hit_x + dx, hit_y + dy
                if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                    # Vérifier si la case a déjà été touchée
                    if not any(shot_x == x and shot_y == y for shot_x, shot_y, _ in shots):
                        # Tirer dans cette case
                        shot_result = self.process_shot(1, x, y)
                        
                        # Si le résultat est un booléen (True), utilisez last_shot 
                        if isinstance(shot_result, bool):
                            if shot_result and self.last_shot:
                                return self.last_shot
                        else:
                            # Si c'est déjà un tuple, retournez-le directement
                            return shot_result
        
        # Si pas de stratégie spécifique, tirer aléatoirement
        untargeted = []
        for x in range(GRID_SIZE):
            for y in range(GRID_SIZE):
                if not any(shot_x == x and shot_y == y for shot_x, shot_y, _ in shots):
                    untargeted.append((x, y))
        
        # S'il reste des cases non ciblées, en choisir une aléatoirement
        if untargeted:
            x, y = random.choice(untargeted)
            shot_result = self.process_shot(1, x, y)
            
            # Même logique pour gérer le résultat
            if isinstance(shot_result, bool):
                if shot_result and self.last_shot:
                    return self.last_shot
            else:
                return shot_result
                
        # Si toutes les cases ont été ciblées, la partie devrait être terminée
        return None
        
    def reset(self):
        """Reset the game state for a new game"""
        for player in self.players:
            player.reset()
            
        self.current_player_index = 0
        self.state = PLACING_SHIPS
        self.winner = None
        self.last_shot = None