from importlib import import_module
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
        
        # Récupérer la difficulté depuis ShipPlacement si disponible
        if hasattr(import_module('src.ui.screens.ship_placement').ShipPlacement, 'last_selected_difficulty'):
            self.difficulty = import_module('src.ui.screens.ship_placement').ShipPlacement.last_selected_difficulty
        else:
            self.difficulty = 'moyenne'  # Valeur par défaut
        
        print(f"GameState initialisé avec difficulté: {self.difficulty}")
        
        # Instance d'IA pour le mode solo
        self.ai = None
        
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
            OR (x, y, hit, ship_id, sunk) en mode solo
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
        
        # Si mode solo et bot qui tire, retourner le tuple complet
        if self.is_solo_mode and player_id == 1:
            # Mettre à jour l'état des navires coulés pour l'IA
            sunk_ships = []
            if self.ai and sunk:
                # Chercher tous les navires coulés
                for ship in opponent.board.ships:
                    if ship.is_sunk():
                        sunk_ships.append(ship.size)
                self.ai.update_ship_status(sunk_ships)
            
            return self.last_shot
                
        return True
    
    
    def bot_play(self):
        """
        Faire jouer le bot (en mode solo)
        
        Returns:
            (x, y, hit, ship_id, sunk): Résultat du tir du bot
        """
        # Vérifier si c'est le tour du bot (joueur 1)
        if self.current_player_index != 1:
            return None
            
        player = self.get_opponent_player()  # Joueur humain
        
        # Initialiser l'IA si ce n'est pas déjà fait
        if not self.ai:
            try:
                from src.game.BattleshipAI import BattleshipAI
                print(f"Initialisation de l'IA avec difficulté: {self.difficulty}")
                self.ai = BattleshipAI(self.difficulty)
            except Exception as e:
                print(f"Erreur lors de l'initialisation de l'IA: {e}")
                # Fallback à la difficulté moyenne en cas d'erreur
                from src.game.BattleshipAI import BattleshipAI
                self.ai = BattleshipAI('moyenne')
        
        # Choisir une cible en fonction de la difficulté
        x, y = self.ai.choose_target(player.board)
        
        if x is None or y is None:
            return None
        
        # Tirer sur la cible
        shot_result = self.process_shot(1, x, y)
        
        # Retourner le résultat
        return shot_result
        
    def reset(self):
        """Reset the game state for a new game"""
        for player in self.players:
            player.reset()
            
        self.current_player_index = 0
        self.state = PLACING_SHIPS
        self.winner = None
        self.last_shot = None
        
        # Réinitialiser l'IA
        if self.ai:
            self.ai.reset()