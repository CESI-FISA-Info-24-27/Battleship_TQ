import socket
import threading
import pickle
import time
from ..utils.constants import DEFAULT_HOST, DEFAULT_PORT
from ..models.network_models import Action

class Client:
    """
    Client class for handling network connections to the game server
    """
    
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.player_id = None
        self.game_state = None
        self.lock = threading.Lock()  # Thread lock for modifying game state
        self.callback = None  # Callback function for game state updates
        self.network_timeout = 10  # Timeout en secondes
        
    def connect(self):
        """
        Connect to the game server
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.network_timeout)  # Set timeout
            self.socket.connect((self.host, self.port))
            
            # Receive player ID
            data = self.socket.recv(4096)
            if not data:
                print("No data received from server")
                self.socket.close()
                return False
                
            player_id = pickle.loads(data)
            
            if player_id == "SERVER_FULL":
                print("Server is full")
                self.socket.close()
                return False
                
            self.player_id = player_id
            self.connected = True
            
            # Start listening for updates in a separate thread
            receive_thread = threading.Thread(target=self._receive_updates)
            receive_thread.daemon = True
            receive_thread.start()
            
            return True
        except socket.timeout:
            print(f"Connection timeout to {self.host}:{self.port}")
            if self.socket:
                self.socket.close()
            return False
        except ConnectionRefusedError:
            print(f"Connection refused by {self.host}:{self.port}")
            if self.socket:
                self.socket.close()
            return False
        except Exception as e:
            print(f"Error connecting to server: {e}")
            if self.socket:
                self.socket.close()
            return False
            
    def disconnect(self):
        """Disconnect from the server"""
        self.connected = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
                
    def set_callback(self, callback):
        """
        Set the callback function for game state updates
        
        Args:
            callback: Function taking game_state as parameter
        """
        self.callback = callback
        
    def _receive_updates(self):
        """Receive and process game state updates from the server"""
        reconnect_attempts = 0
        max_reconnect_attempts = 3
        
        while self.connected:
            try:
                data = self.socket.recv(4096)
                if not data:
                    reconnect_attempts += 1
                    if reconnect_attempts > max_reconnect_attempts:
                        print("Connection lost: No data from server")
                        break
                        
                    print(f"No data received, retry {reconnect_attempts}/{max_reconnect_attempts}")
                    time.sleep(1)
                    continue
                    
                reconnect_attempts = 0  # Reset counter on successful receive
                    
                update = pickle.loads(data)
                
                with self.lock:
                    self.game_state = update.game_state
                    
                # Call the callback with the updated game state
                if self.callback:
                    self.callback(self.game_state)
            except (ConnectionResetError, ConnectionAbortedError):
                print("Connection reset by server")
                break
            except socket.timeout:
                print("Socket timeout, retrying...")
                reconnect_attempts += 1
                if reconnect_attempts > max_reconnect_attempts:
                    print("Connection lost: Too many timeouts")
                    break
                continue
            except Exception as e:
                print(f"Error receiving updates: {e}")
                time.sleep(0.1)  # Éviter une utilisation CPU élevée en cas d'erreurs répétées
                
        self.connected = False
        print("Disconnected from server")
        
    def send_action(self, action):
        """
        Send an action to the server
        
        Args:
            action: Action object to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.connected:
            return False
            
        try:
            self.socket.send(pickle.dumps(action))
            return True
        except Exception as e:
            print(f"Error sending action: {e}")
            self.connected = False
            return False
            
    def place_ship(self, ship_index, x, y, horizontal):
        """
        Send a place ship action to the server
        
        Args:
            ship_index: Index of the ship in the player's ships list
            x, y: Coordinates for placement
            horizontal: True for horizontal placement, False for vertical
        """
        action = Action.create_place_ship(
            self.player_id, ship_index, x, y, horizontal
        )
        return self.send_action(action)
        
    def player_ready(self):
        """Send a player ready action to the server"""
        action = Action.create_player_ready(self.player_id)
        return self.send_action(action)
        
    def fire_shot(self, x, y):
        """
        Send a fire shot action to the server
        
        Args:
            x, y: Coordinates to fire at
        """
        action = Action.create_fire_shot(self.player_id, x, y)
        return self.send_action(action)
        
    def send_chat_message(self, message):
        """
        Send a chat message to the server
        
        Args:
            message: Text of the chat message
        """
        action = Action.create_chat_message(self.player_id, message)
        return self.send_action(action)