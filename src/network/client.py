import socket
import threading
import pickle
import time
import logging
from ..utils.constants import DEFAULT_HOST, DEFAULT_PORT
from ..models.network_models import Action

class Client:
    """
    Client class for handling network connections to the game server
    """
    
    def __init__(self, host=DEFAULT_HOST, port=DEFAULT_PORT):
        # Configuration du logging
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Paramètres de connexion
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.player_id = None
        self.game_state = None
        
        # Synchronisation et gestion des threads
        self.lock = threading.Lock()
        self.callback = None
        self.network_timeout = 15  # Augmentation du timeout
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 3
        
    def connect(self):
        """
        Tenter de se connecter au serveur avec des mécanismes de gestion d'erreurs améliorés
        
        Returns:
            True si la connexion est réussie, False sinon
        """
        try:
            # Créer un nouveau socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(self.network_timeout)
            
            self.logger.info(f"Tentative de connexion à {self.host}:{self.port}")
            
            # Connexion au serveur
            self.socket.connect((self.host, self.port))
            
            # Recevoir l'ID du joueur
            data = self.socket.recv(4096)
            if not data:
                self.logger.warning("Aucune donnée reçue du serveur")
                self.socket.close()
                return False
            
            player_id = pickle.loads(data)
            
            if player_id == "SERVER_FULL":
                self.logger.warning("Le serveur est complet")
                self.socket.close()
                return False
            
            # Connexion réussie
            self.player_id = player_id
            self.connected = True
            self.reconnect_attempts = 0
            
            # Démarrer un thread pour recevoir les mises à jour
            receive_thread = threading.Thread(target=self._receive_updates)
            receive_thread.daemon = True
            receive_thread.start()
            
            self.logger.info(f"Connecté avec succès en tant que joueur {self.player_id}")
            return True
        
        except socket.timeout:
            self.logger.error(f"Délai de connexion dépassé pour {self.host}:{self.port}")
            self._close_socket()
            return False
        
        except ConnectionRefusedError:
            self.logger.error(f"Connexion refusée par {self.host}:{self.port}")
            self._close_socket()
            return False
        
        except Exception as e:
            self.logger.error(f"Erreur de connexion : {e}")
            self._close_socket()
            return False
    
    def _close_socket(self):
        """Fermer proprement le socket"""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
    
    def disconnect(self):
        """Déconnecter proprement le client"""
        self.logger.info("Déconnexion du serveur")
        self.connected = False
        self._close_socket()
    
    def set_callback(self, callback):
        """
        Définir une fonction de callback pour les mises à jour d'état de jeu
        
        Args:
            callback: Fonction prenant game_state comme paramètre
        """
        self.callback = callback
    
    def _receive_updates(self):
        """
        Recevoir et traiter les mises à jour d'état de jeu du serveur
        """
        while self.connected:
            try:
                # Recevoir les données
                data = self.socket.recv(4096)
                
                if not data:
                    self.logger.warning("Aucune donnée reçue du serveur")
                    break
                
                # Désérialiser la mise à jour
                update = pickle.loads(data)
                
                # Mettre à jour l'état du jeu de manière thread-safe
                with self.lock:
                    self.game_state = update.game_state
                
                # Appeler le callback si défini
                if self.callback:
                    self.callback(self.game_state)
                
                # Réinitialiser les tentatives de reconnexion
                self.reconnect_attempts = 0
            
            except (ConnectionResetError, ConnectionAbortedError):
                self.logger.warning("Connexion réinitialisée par le serveur")
                break
            
            except socket.timeout:
                self.logger.info("Délai de socket dépassé")
                continue
            
            except Exception as e:
                self.logger.error(f"Erreur lors de la réception des mises à jour : {e}")
                time.sleep(0.1)  # Éviter une utilisation CPU excessive
        
        # Gérer la déconnexion
        self.logger.info("Déconnecté du serveur")
        self.connected = False
        self._close_socket()
    
    def send_action(self, action):
        """
        Envoyer une action au serveur
        
        Args:
            action: Objet Action à envoyer
            
        Returns:
            True si envoyé avec succès, False sinon
        """
        if not self.connected:
            self.logger.warning("Tentative d'envoi d'action sans connexion")
            return False
        
        try:
            self.socket.send(pickle.dumps(action))
            return True
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi de l'action : {e}")
            self.connected = False
            return False
    
    def place_ship(self, ship_index, x, y, horizontal):
        """
        Envoyer une action de placement de navire au serveur
        
        Args:
            ship_index: Index du navire dans la liste des navires du joueur
            x, y: Coordonnées de placement
            horizontal: True pour placement horizontal, False pour vertical
        """
        action = Action.create_place_ship(
            self.player_id, ship_index, x, y, horizontal
        )
        return self.send_action(action)
    
    def player_ready(self):
        """
        Signaler que le joueur est prêt
        """
        action = Action.create_player_ready(self.player_id)
        return self.send_action(action)
    
    def fire_shot(self, x, y):
        """
        Envoyer une action de tir au serveur
        
        Args:
            x, y: Coordonnées du tir
        """
        action = Action.create_fire_shot(self.player_id, x, y)
        return self.send_action(action)
    
    def send_chat_message(self, message):
        """
        Envoyer un message de chat au serveur
        
        Args:
            message: Texte du message de chat
        """
        action = Action.create_chat_message(self.player_id, message)
        return self.send_action(action)