import socket
import threading
import json
import time
import logging

# Configuration client
DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 65432  # Port utilisé par l'autre projet
TIMEOUT = 30  # Timeout en secondes

# Constantes pour la grille
WATER = '~'
SHIP = 'B'
MISSED_SHOT = 'X'
HIT_SHOT = 'O'
GRID_SIZE = 10
SHIP_SIZES = [5, 4, 3, 3, 2]

class Client:
    """
    Client pour se connecter au serveur de bataille navale
    """
    
    def __init__(self, username="Player", host=DEFAULT_HOST, port=DEFAULT_PORT):
        # Configuration du logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger("BattleshipClient")
        
        # Informations de connexion
        self.username = username
        self.host = host
        self.port = port
        self.client_id = None
        
        # État de la connexion
        self.socket = None
        self.connected = False
        self.listener_thread = None
        
        # Callbacks pour les événements
        self.callbacks = {
            'login_success': [],
            'ships_placed': [],
            'waiting_opponent': [],
            'game_start': [],
            'your_turn': [],
            'shot_result': [],
            'opponent_shot': [],
            'game_over': [],
            'opponent_disconnected': [],
            'error': []
        }
        
        # État du jeu
        self.opponent_username = ""
        self.my_grid = None
        self.opponent_grid = None
        self.my_turn = False
    
    def connect(self):
        """
        Se connecter au serveur
        
        Returns:
            True si la connexion est réussie, False sinon
        """
        try:
            print(f"Tentative de connexion TCP à {self.host}:{self.port}")
            self.logger.info(f"Tentative de connexion à {self.host}:{self.port}")
            
            # Créer le socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(TIMEOUT)
            
            # Se connecter au serveur
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            # Envoyer les informations de login
            login_message = {
                'type': 'login',
                'username': self.username
            }
            
            if not self._send_message(login_message):
                self.logger.error("Erreur lors de l'envoi du message de login")
                self.disconnect()
                return False
            
            # Démarrer le thread d'écoute
            self.listener_thread = threading.Thread(target=self._listen_for_messages)
            self.listener_thread.daemon = True
            self.listener_thread.start()
            
            return True
            
        except socket.timeout:
            self.logger.error(f"Délai de connexion dépassé pour {self.host}:{self.port}")
            return False
        except ConnectionRefusedError:
            self.logger.error(f"Connexion refusée par {self.host}:{self.port}")
            return False
        except Exception as e:
            self.logger.error(f"Erreur de connexion : {e}")
            return False
    
    def disconnect(self):
        """
        Se déconnecter du serveur
        """
        self.connected = False
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        self.logger.info("Déconnecté du serveur")
    
    def register_callback(self, event_type, callback):
        """
        Enregistrer une fonction de callback pour un type d'événement
        
        Args:
            event_type: Type d'événement ('login_success', 'game_start', etc.)
            callback: Fonction à appeler quand l'événement se produit
        """
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
    
    def place_ships(self, grid):
        """
        Envoyer le placement des bateaux au serveur
        
        Args:
            grid: Grille avec les bateaux placés
            
        Returns:
            True si l'envoi est réussi, False sinon
        """
        message = {
            'type': 'place_ships',
            'grid': grid
        }
        
        return self._send_message(message)
    
    def fire_shot(self, row, column):
        """
        Envoyer un tir au serveur
        
        Args:
            row, column: Coordonnées du tir
            
        Returns:
            True si l'envoi est réussi, False sinon
        """
        message = {
            'type': 'fire_shot',
            'position': [row, column]
        }
        
        return self._send_message(message)
    
    def ready_for_new_game(self):
        """
        Signaler au serveur qu'on est prêt pour une nouvelle partie
        
        Returns:
            True si l'envoi est réussi, False sinon
        """
        message = {
            'type': 'ready_for_new_game'
        }
        
        return self._send_message(message)
    
    def _send_message(self, message):
        """
        Envoyer un message au serveur au format JSON
        
        Args:
            message: Message à envoyer (dictionnaire)
            
        Returns:
            True si l'envoi est réussi, False sinon
        """
        if not self.connected or not self.socket:
            self.logger.warning("Tentative d'envoi de message sans connexion")
            return False
        
        try:
            # Sérialiser le message en JSON
            message_json = json.dumps(message)
            message_bytes = message_json.encode('utf-8')
            
            # Envoyer d'abord la taille du message (4 octets)
            size_bytes = len(message_bytes).to_bytes(4, byteorder='big')
            self.socket.sendall(size_bytes + message_bytes)
            
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi du message : {e}")
            self.connected = False
            return False
    
    def _receive_message(self):
        """
        Recevoir un message du serveur au format JSON
        
        Returns:
            Message reçu (dictionnaire) ou None en cas d'erreur
        """
        if not self.connected or not self.socket:
            return None
        
        try:
            # Recevoir d'abord la taille du message
            size_bytes = self.socket.recv(4)
            if not size_bytes:
                return None
            
            message_size = int.from_bytes(size_bytes, byteorder='big')
            
            # Recevoir le message complet
            message_bytes = b''
            remaining = message_size
            
            while remaining > 0:
                chunk = self.socket.recv(min(remaining, 4096))
                if not chunk:
                    return None
                message_bytes += chunk
                remaining -= len(chunk)
            
            # Désérialiser le message JSON
            message_json = message_bytes.decode('utf-8')
            return json.loads(message_json)
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la réception du message : {e}")
            self.connected = False
            return None
    
    def _listen_for_messages(self):
        """
        Écouter et traiter les messages du serveur en continu
        """
        while self.connected:
            try:
                message = self._receive_message()
                
                if not message:
                    self.logger.warning("Connexion perdue avec le serveur")
                    self.connected = False
                    break
                
                # Extraire le type de message
                message_type = message.get('type')
                
                # Mettre à jour l'état du client selon le type de message
                if message_type == 'login_success':
                    self.client_id = message.get('id')
                    self.logger.info(f"Connecté avec succès. ID: {self.client_id}")
                
                elif message_type == 'game_start':
                    self.opponent_username = message.get('opponent', "Adversaire")
                    self.my_grid = message.get('my_grid')
                    self.opponent_grid = message.get('opponent_grid')
                    self.my_turn = message.get('first_player', False)
                    self.logger.info(f"Partie commencée contre {self.opponent_username}")
                
                elif message_type == 'your_turn':
                    self.my_turn = True
                    self.logger.info("C'est votre tour")
                
                elif message_type == 'shot_result':
                    self.opponent_grid = message.get('opponent_grid', self.opponent_grid)
                    self.my_turn = False
                    self.logger.info(f"Résultat du tir: {message.get('result')}")
                
                elif message_type == 'opponent_shot':
                    self.my_grid = message.get('my_grid', self.my_grid)
                    self.my_turn = True
                    self.logger.info(f"L'adversaire a tiré en {message.get('position')}")
                
                # Exécuter les callbacks associés au type de message
                if message_type in self.callbacks:
                    for callback in self.callbacks[message_type]:
                        try:
                            callback(message)
                        except Exception as e:
                            self.logger.error(f"Erreur dans un callback : {e}")
            
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle d'écoute : {e}")
                if self.connected:
                    time.sleep(0.1)  # Éviter une utilisation excessive du CPU
    
    def create_empty_grid(self):
        """
        Créer une grille vide
        
        Returns:
            Grille vide au format attendu par le serveur
        """
        return {
            'matrix': [[WATER for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)],
            'ships': []
        }
    
    def place_ship_on_grid(self, grid, row, col, size, horizontal):
        """
        Placer un bateau sur une grille
        
        Args:
            grid: Grille sur laquelle placer le bateau
            row, col: Position de départ du bateau
            size: Taille du bateau
            horizontal: True si horizontal, False si vertical
            
        Returns:
            True si le placement est réussi, False sinon
        """
        # Vérifier si le placement est valide
        if not self._is_valid_placement(grid, row, col, size, horizontal):
            return False
        
        # Placer le bateau sur la grille
        positions = []
        if horizontal:
            for i in range(size):
                grid['matrix'][row][col + i] = SHIP
                positions.append([row, col + i])
        else:
            for i in range(size):
                grid['matrix'][row + i][col] = SHIP
                positions.append([row + i, col])
        
        # Ajouter le bateau à la liste des bateaux
        grid['ships'].append({
            'size': size,
            'positions': positions,
            'hits': []
        })
        
        return True
    
    def _is_valid_placement(self, grid, row, col, size, horizontal):
        """
        Vérifier si un placement de bateau est valide
        
        Args:
            grid: Grille à vérifier
            row, col: Position de départ du bateau
            size: Taille du bateau
            horizontal: True si horizontal, False si vertical
            
        Returns:
            True si le placement est valide, False sinon
        """
        # Vérifier si le bateau sort de la grille
        if horizontal:
            if col + size > GRID_SIZE:
                return False
        else:
            if row + size > GRID_SIZE:
                return False
        
        # Vérifier si le bateau chevauche un autre bateau
        if horizontal:
            for i in range(size):
                if grid['matrix'][row][col + i] != WATER:
                    return False
        else:
            for i in range(size):
                if grid['matrix'][row + i][col] != WATER:
                    return False
        
        return True
    
    def place_ships_randomly(self, grid=None):
        """
        Placer aléatoirement tous les bateaux
        
        Args:
            grid: Grille à utiliser (en crée une nouvelle si None)
            
        Returns:
            Grille avec les bateaux placés aléatoirement
        """
        import random
        
        if grid is None:
            grid = self.create_empty_grid()
        
        # Essayer plusieurs fois pour chaque bateau
        for size in SHIP_SIZES:
            placed = False
            attempts = 0
            
            while not placed and attempts < 100:
                # Position aléatoire
                row = random.randint(0, GRID_SIZE - 1)
                col = random.randint(0, GRID_SIZE - 1)
                horizontal = random.choice([True, False])
                
                # Tenter de placer le bateau
                placed = self.place_ship_on_grid(grid, row, col, size, horizontal)
                attempts += 1
        
        return grid

# Exemple d'utilisation
if __name__ == "__main__":
    # Initialiser le client
    client = Client(username="TestPlayer")
    
    # Se connecter au serveur
    if client.connect():
        print("Connecté au serveur!")
        
        # Placer les bateaux aléatoirement
        grid = client.place_ships_randomly()
        
        # Envoyer les bateaux au serveur
        if client.place_ships(grid):
            print("Bateaux placés avec succès!")
        
        # Garder le thread principal en vie
        try:
            while client.connected:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nDéconnexion...")
        finally:
            client.disconnect()
    else:
        print("Impossible de se connecter au serveur.")