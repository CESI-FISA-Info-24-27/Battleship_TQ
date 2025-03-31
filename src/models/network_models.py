class Action:
    """
    Class representing an action sent over the network
    """
    
    # Action types
    PLACE_SHIP = "place_ship"
    PLAYER_READY = "player_ready"
    FIRE_SHOT = "fire_shot"
    CHAT_MESSAGE = "chat_message"
    
    def __init__(self, type, player_id, data=None):
        self.type = type
        self.player_id = player_id
        self.data = data or {}
        
    @staticmethod
    def create_place_ship(player_id, ship_index, x, y, horizontal):
        """
        Create a PLACE_SHIP action
        
        Args:
            player_id: ID of the player placing the ship
            ship_index: Index of the ship in the player's ships list
            x, y: Coordinates for placement
            horizontal: True for horizontal placement, False for vertical
        """
        return Action(
            Action.PLACE_SHIP,
            player_id,
            {
                "ship_index": ship_index,
                "x": x,
                "y": y,
                "horizontal": horizontal
            }
        )
        
    @staticmethod
    def create_player_ready(player_id):
        """
        Create a PLAYER_READY action
        
        Args:
            player_id: ID of the player who is ready
        """
        return Action(Action.PLAYER_READY, player_id)
        
    @staticmethod
    def create_fire_shot(player_id, x, y):
        """
        Create a FIRE_SHOT action
        
        Args:
            player_id: ID of the player firing the shot
            x, y: Coordinates of the shot
        """
        return Action(
            Action.FIRE_SHOT,
            player_id,
            {
                "x": x,
                "y": y
            }
        )
        
    @staticmethod
    def create_chat_message(player_id, message):
        """
        Create a CHAT_MESSAGE action
        
        Args:
            player_id: ID of the player sending the message
            message: Text of the chat message
        """
        return Action(
            Action.CHAT_MESSAGE,
            player_id,
            {
                "message": message
            }
        )


class GameStateUpdate:
    """
    Class representing a game state update sent over the network
    """
    
    def __init__(self, game_state):
        self.game_state = game_state