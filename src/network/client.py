import socket
import threading
import json
import time
import logging

# Configuration client - PORT FIXÉ À 65432
DEFAULT_HOST = 'localhost'
DEFAULT_PORT = 65432  # Port explicitement défini à 65432
TIMEOUT = 30  # Timeout en secondes
PING_INTERVAL = 15  # Intervalle en secondes entre les pings

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
        self.ping_thread = None
        self.ping_enabled = False
        self.last_pong_time = 0
        self.connection_lost_retries = 0
        self.max_retries = 3
        
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
            'connection_lost': [],
            'error': []
        }
        
        # État du jeu
        self.opponent_username = ""
        self.my_grid = None
        self.opponent_grid = None
        self.my_turn = False
        
        # Ajout de l'attribut game_state pour stocker l'état de la partie en mode réseau
        self.game_state = None
        
        # Verrou pour les opérations d'envoi/réception
        self.socket_lock = threading.Lock()
    
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
            
            # Démarrer le thread de ping si activé
            self._start_ping_thread()
            
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
    
    def _start_ping_thread(self):
        """Démarrer le thread de ping pour maintenir la connexion"""
        if not self.ping_thread:
            self.ping_enabled = True
            self.ping_thread = threading.Thread(target=self._ping_server)
            self.ping_thread.daemon = True
            self.ping_thread.start()
            self.logger.info("Thread de ping démarré")
    
    def _ping_server(self):
        """Envoyer des pings périodiques au serveur pour vérifier la connexion"""
        while self.connected and self.ping_enabled:
            try:
                # Attendre l'intervalle de ping
                time.sleep(PING_INTERVAL)
                
                if not self.connected:
                    break
                
                # Calculer le temps depuis le dernier pong
                time_since_last_pong = time.time() - self.last_pong_time
                
                # Si nous n'avons pas reçu de pong depuis trop longtemps
                if self.last_pong_time > 0 and time_since_last_pong > TIMEOUT:
                    self.logger.warning(f"Pas de réponse du serveur depuis {time_since_last_pong:.1f} secondes")
                    self.connection_lost_retries += 1
                    
                    if self.connection_lost_retries >= self.max_retries:
                        self.logger.error("Connexion au serveur perdue")
                        self._trigger_connection_lost()
                        break
                
                # Envoyer un ping
                ping_message = {
                    'type': 'ping',
                    'timestamp': time.time()
                }
                
                self._send_message(ping_message)
                
            except Exception as e:
                self.logger.error(f"Erreur dans le thread de ping: {e}")
                if self.connected:
                    time.sleep(1)
    
    def _trigger_connection_lost(self):
        """Déclencher les callbacks de perte de connexion"""
        if self.connected:
            self.connected = False
            
            # Exécuter les callbacks de perte de connexion
            for callback in self.callbacks['connection_lost']:
                try:
                    callback()
                except Exception as e:
                    self.logger.error(f"Erreur dans un callback de perte de connexion: {e}")
    
    def disconnect(self):
        """
        Se déconnecter du serveur
        """
        self.connected = False
        self.ping_enabled = False
        
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
            # Acquérir le verrou pour éviter les problèmes d'accès concurrent
            with self.socket_lock:
                # Sérialiser le message en JSON
                message_json = json.dumps(message)
                message_bytes = message_json.encode('utf-8')
                
                # Envoyer d'abord la taille du message (4 octets)
                size_bytes = len(message_bytes).to_bytes(4, byteorder='big')
                self.socket.sendall(size_bytes + message_bytes)
                
                return True
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi du message : {e}")
            self._trigger_connection_lost()
            return False
    
    def _receive_message(self):
        """
        Recevoir un message du serveur au format JSON
        """
        if not self.connected or not self.socket:
            return None
        
        try:
            # Acquérir le verrou pour éviter les problèmes d'accès concurrent
            with self.socket_lock:
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
            self._trigger_connection_lost()
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
                    self._trigger_connection_lost()
                    break
                
                # Extraire le type de message
                message_type = message.get('type')
                
                # Gérer les pongs pour la vérification de la connexion
                if message_type == 'pong':
                    self.last_pong_time = time.time()
                    self.connection_lost_retries = 0
                    continue
                
                if message_type == 'login_success':
                    self.client_id = message.get('id')
                    self.logger.info(f"Connecté avec succès. ID: {self.client_id}")
                    # Initialiser le temps du dernier pong
                    self.last_pong_time = time.time()
                
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
                
                elif message_type == 'opponent_disconnected':
                    self.logger.info("L'adversaire s'est déconnecté")
                    # Réinitialiser l'état de la partie
                    self.opponent_username = ""
                    self.game_state = None
                
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
                    
    def reconnect(self):
        """
        Tenter de se reconnecter au serveur après une perte de connexion
        
        Returns:
            True si la reconnexion est réussie, False sinon
        """
        self.logger.info(f"Tentative de reconnexion à {self.host}:{self.port}")
        
        # S'assurer que l'ancienne connexion est fermée
        self.disconnect()
        
        # Réinitialiser les attributs de connexion
        self.connected = False
        self.socket = None
        self.listener_thread = None
        self.ping_thread = None
        self.connection_lost_retries = 0
        
        # Tenter de se reconnecter
        return self.connect()