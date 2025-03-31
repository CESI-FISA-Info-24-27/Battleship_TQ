import socket
import threading
import pickle
import time
from ..game.game_state import GameState
from ..models.network_models import Action, GameStateUpdate
from ..utils.constants import DEFAULT_PORT

class Server:
    """
    Server class for handling network connections in the game
    """
    
    def __init__(self, host='0.0.0.0', port=DEFAULT_PORT):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.game_state = GameState()
        self.clients = []  # List of (connection, player_id) tuples
        self.lock = threading.Lock()  # Thread lock for modifying game state
        
    def start(self):
        """Start the server and listen for connections"""
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(2)  # Max 2 players
            self.running = True
            
            print(f"Server started on {self.host}:{self.port}")
            
            # Accept connections in a separate thread
            accept_thread = threading.Thread(target=self._accept_connections)
            accept_thread.daemon = True
            accept_thread.start()
            
            return True
        except Exception as e:
            print(f"Error starting server: {e}")
            return False
            
    def stop(self):
        """Stop the server"""
        self.running = False
        
        # Close all client connections
        for conn, _ in self.clients:
            try:
                conn.close()
            except:
                pass
                
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
                
    def _accept_connections(self):
        """Accept connections from clients"""
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                print(f"New connection from {addr}")
                
                # Assign player ID (0 for first player, 1 for second)
                with self.lock:
                    player_id = len(self.clients)
                    if player_id < 2:  # Only accept 2 players
                        self.clients.append((conn, player_id))
                        
                        # Send player ID to the client
                        conn.send(pickle.dumps(player_id))
                        
                        # Start client handler thread
                        handler_thread = threading.Thread(
                            target=self._handle_client,
                            args=(conn, player_id)
                        )
                        handler_thread.daemon = True
                        handler_thread.start()
                    else:
                        # Server full, reject connection
                        conn.send(pickle.dumps("SERVER_FULL"))
                        conn.close()
            except Exception as e:
                if self.running:
                    print(f"Error accepting connection: {e}")
                    time.sleep(1)  # Avoid CPU spike if errors occur repeatedly
                    
    def _handle_client(self, conn, player_id):
        """
        Handle communication with a client
        
        Args:
            conn: Socket connection
            player_id: ID of the player (0 or 1)
        """
        try:
            # Send initial game state
            self._send_game_state(conn)
            
            # Main communication loop
            while self.running:
                # Receive action from client
                try:
                    data = conn.recv(4096)
                    if not data:
                        break
                        
                    action = pickle.loads(data)
                    self._process_action(action)
                    
                    # Send updated game state to all clients
                    self._broadcast_game_state()
                except (ConnectionResetError, ConnectionAbortedError):
                    break
        except Exception as e:
            print(f"Error handling client {player_id}: {e}")
        finally:
            # Clean up connection
            with self.lock:
                self.clients = [(c, pid) for c, pid in self.clients if c != conn]
                
            try:
                conn.close()
            except:
                pass
                
            print(f"Client {player_id} disconnected")
            
    def _process_action(self, action):
        """
        Process an action received from a client
        
        Args:
            action: Action object
        """
        with self.lock:
            if action.type == Action.PLACE_SHIP:
                data = action.data
                player = self.game_state.players[action.player_id]
                player.place_ship(
                    data["ship_index"], 
                    data["x"], 
                    data["y"], 
                    data["horizontal"]
                )
            elif action.type == Action.PLAYER_READY:
                self.game_state.player_ready(action.player_id)
            elif action.type == Action.FIRE_SHOT:
                data = action.data
                self.game_state.process_shot(action.player_id, data["x"], data["y"])
            # Chat messages don't modify game state, just broadcast them
                
    def _send_game_state(self, conn):
        """
        Send current game state to a client
        
        Args:
            conn: Socket connection
        """
        try:
            with self.lock:
                update = GameStateUpdate(self.game_state)
            conn.send(pickle.dumps(update))
        except Exception as e:
            print(f"Error sending game state: {e}")
            
    def _broadcast_game_state(self):
        """Send current game state to all connected clients"""
        with self.lock:
            update = GameStateUpdate(self.game_state)
            data = pickle.dumps(update)
            
            for conn, _ in self.clients:
                try:
                    conn.send(data)
                except:
                    pass  # Connection will be cleaned up in handle_client