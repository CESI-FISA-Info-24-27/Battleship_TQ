import socket
import threading
import json
import time
import logging

# Configuration client - PORT FIXÉ À 65432
DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 65432  # Port explicitement défini à 65432
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
        self.port = port  # Ce port devrait être 65432 par défaut
        
        # Vérification explicite du port
        if self.port != 65432:
            self.logger.warning(f"Port incorrect détecté: {self.port}, utilisation du port 65432 à la place")
            self.port = 65432
        
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
        
        # Ajout de l'attribut game_state pour stocker l'état de la partie en mode réseau
        self.game_state = None
    
    def connect(self):
        """
        Se connecter au serveur
        
        Returns:
            True si la connexion est réussie, False sinon
        """
        try:
            # Vérification explicite du port
            if self.port != 65432:
                self.logger.warning(f"Correction du port: {self.port} -> 65432")
                self.port = 65432
                
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
        """
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
    
    def place_ships(self, grid):
        """
        Envoyer le placement des bateaux au serveur
        """
        message = {
            'type': 'place_ships',
            'grid': grid
        }
        
        return self._send_message(message)
    
    def fire_shot(self, row, column):
        """
        Envoyer un tir au serveur
        """
        message = {
            'type': 'fire_shot',
            'position': [row, column]
        }
        
        return self._send_message(message)
    
    def ready_for_new_game(self):
        """
        Signaler au serveur qu'on est prêt pour une nouvelle partie
        """
        message = {
            'type': 'ready_for_new_game'
        }
        
        return self._send_message(message)
    
    def _send_message(self, message):
        """
        Envoyer un message au serveur au format JSON
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
        except socket.timeout:
            # En cas de timeout, ne pas considérer cela comme une perte de connexion
            return "timeout"
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
                if message == "timeout":
                    # Attendre un court instant pour éviter une boucle trop rapide
                    time.sleep(0.1)
                    continue
                if not message:
                    self.logger.warning("Connexion perdue avec le serveur")
                    self.connected = False
                    break
                
                # Extraire le type de message
                message_type = message.get('type')
                
                if message_type == 'login_success':
                    self.client_id = message.get('id')
                    self.logger.info(f"Connecté avec succès. ID: {self.client_id}")
                
                elif message_type == 'game_start':
                    self.opponent_username = message.get('opponent', "Adversaire")
                    self.my_grid = message.get('my_grid')
                    self.opponent_grid = message.get('opponent_grid')
                    self.my_turn = message.get('first_player', False)
                    self.logger.info(f"Partie commencée contre {self.opponent_username}")
                    # Stocker le game_state reçu du serveur
                    self.game_state = message
                
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
                
                # Exécuter les callbacks associés
                if message_type in self.callbacks:
                    for callback in self.callbacks[message_type]:
                        try:
                            callback(message)
                        except Exception as e:
                            self.logger.error(f"Erreur dans un callback : {e}")
            
            except Exception as e:
                self.logger.error(f"Erreur dans la boucle d'écoute : {e}")
                if self.connected:
                    time.sleep(0.1)
