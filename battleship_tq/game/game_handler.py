import socket
import threading
import json
import time
from BattleshipConnection import BattleshipConnection

class GameHandler:
    """
    Gestionnaire pour le jeu de Bataille Navale
    Cette classe s'occupe de la gestion des coups reçus/envoyés pendant une partie
    """
    
    def __init__(self, connection):
        """
        Initialise un gestionnaire de jeu
        
        Args:
            connection (BattleshipConnection): La connexion au serveur de matchmaking
        """
        self.connection = connection
        self.listener_thread = None
        self.opponent_board = {}  # Pour stocker les coups sur la grille adverse
        
    def start_game_listener(self):
        """Démarre le thread d'écoute des coups adverses"""
        if self.listener_thread and self.listener_thread.is_alive():
            return
            
        self.listener_thread = threading.Thread(target=self._socket_listener_thread, daemon=True)
        self.listener_thread.start()
        
    def _socket_listener_thread(self):
        """Thread d'écoute des coups adverses"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind(("0.0.0.0", self.connection.port))
            server_socket.listen(1)
            server_socket.settimeout(1.0)  # Timeout court pour vérifier régulièrement l'état du match
            
            print(f"🔍 Écoute sur le port {self.connection.port} pour les coups adverses...")
            
            while self.connection.is_match_active and not self.connection.winner:
                try:
                    client_socket, client_address = server_socket.accept()
                    data = client_socket.recv(1024).decode()
                    client_socket.close()
                    
                    if data:
                        self._handle_move_received(data)
                except socket.timeout:
                    continue  # Continuer la boucle en cas de timeout
                except Exception as e:
                    print(f"⚠️ Erreur de réception: {e}")
        except Exception as e:
            print(f"❌ Erreur d'initialisation du socket: {e}")
        finally:
            server_socket.close()
            print("🔒 Socket d'écoute fermé.")
    
    def _handle_move_received(self, data):
        """
        Gère un coup reçu de l'adversaire
        
        Args:
            data (str): Les données JSON du coup reçu
        """
        try:
            move_data = json.loads(data)
            move = tuple(move_data["move"])
            print(f"📥 Coup reçu en {move}")
            
            # Mettre à jour le plateau de jeu
            result = self._process_move(move)
            
            # Indiquer que c'est notre tour
            self.connection.my_turn = True
            
            # Envoyer une réponse à l'adversaire si nécessaire
            # self._send_move_result(move, result)
            
        except Exception as e:
            print(f"❌ Erreur de traitement du coup: {e}")
    
    def _process_move(self, move):
        """
        Traite un coup reçu sur notre grille
        
        Args:
            move (tuple): Les coordonnées (x, y) du coup
            
        Returns:
            str: Le résultat ("HIT", "MISS" ou "SUNK")
        """
        # Vérifier si le coup touche un navire
        if self.connection.game_board.get(move) == "SHIP":
            self.connection.game_board[move] = "HIT"
            print(f"💥 TOUCHÉ en {move}!")
            result = "HIT"
        else:
            self.connection.game_board[move] = "MISS"
            print(f"💦 MANQUÉ en {move}")
            result = "MISS"
        
        # Ajouter le coup à la liste des coups reçus
        self.connection.moves.append(move)
        
        # Vérifier si le jeu est terminé
        self.connection.check_victory()
        
        return result
    
    def send_move(self, move):
        """
        Envoie un coup à l'adversaire
        
        Args:
            move (tuple): Les coordonnées (x, y) du coup
            
        Returns:
            bool: True si le coup a été envoyé avec succès, False sinon
        """
        if not self.connection.opponent:
            print("⚠️ Aucun adversaire connu.")
            return False
            
        try:
            # Récupérer la liste des joueurs
            r = requests.get(f"{self.connection.matchmaking_url}/players")
            if r.status_code != 200:
                print("❌ Impossible de récupérer la liste des joueurs.")
                return False
                
            players = r.json()
            target = next((p for p in players if p["username"] == self.connection.opponent), None)
            
            if not target:
                print(f"❌ Adversaire '{self.connection.opponent}' introuvable.")
                return False
                
            # Envoyer le coup via socket
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5.0)
            client_socket.connect((target["ip"], int(target["port"])))
            client_socket.send(json.dumps({"move": list(move)}).encode())
            client_socket.close()
            
            # Marquer ce coup dans notre grille adverse
            self.opponent_board[move] = "PENDING"
            
            print(f"🎯 Coup envoyé en {move}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur d'envoi du coup: {e}")
            return False
            
    def place_ships(self, positions):
        """
        Place les navires sur la grille
        
        Args:
            positions (list): Liste des coordonnées (x, y) des navires
            
        Returns:
            bool: True si tous les navires ont été placés avec succès
        """
        if not positions:
            return False
            
        for pos in positions:
            self.connection.update_game_board(pos, opponent=False)
            
        print(f"🚢 {len(positions)} navires placés sur la grille.")
        return True