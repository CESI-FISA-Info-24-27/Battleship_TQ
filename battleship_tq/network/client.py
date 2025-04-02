# client.py
import socket
import pickle
import threading
import json
from game.constants import DEFAULT_PORT

class NetworkClient:
    """Client réseau pour le jeu de bataille navale en ligne"""
    
    def __init__(self, host="localhost", port=DEFAULT_PORT):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False
        self.game_id = None
        self.player_id = None
        self.message_callback = None
        self.connection_callback = None
        self.disconnection_callback = None
        self.receive_thread = None
    
    def connect(self, callback=None):
        """
        Établit une connexion avec le serveur.
        
        Args:
            callback: Fonction appelée après la tentative de connexion
        
        Returns:
            bool: True si la connexion réussit, False sinon
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            # Démarrer le thread de réception
            self.receive_thread = threading.Thread(target=self._receive_messages)
            self.receive_thread.daemon = True
            self.receive_thread.start()
            
            if callback:
                callback(True)
            
            if self.connection_callback:
                self.connection_callback()
            
            return True
        
        except Exception as e:
            print(f"Erreur de connexion: {e}")
            self.connected = False
            
            if callback:
                callback(False, str(e))
            
            return False
    
    def disconnect(self):
        """Ferme la connexion avec le serveur"""
        if self.connected:
            try:
                # Envoyer un message de déconnexion propre
                self.send_message({"type": "disconnect"})
                self.socket.close()
            except Exception as e:
                print(f"Erreur lors de la déconnexion: {e}")
            
            self.connected = False
            self.game_id = None
            self.player_id = None
            
            if self.disconnection_callback:
                self.disconnection_callback()
    
    def create_game(self, callback=None):
        """
        Demande la création d'une nouvelle partie au serveur
        
        Args:
            callback: Fonction appelée quand le serveur répond
        """
        self.send_message({"type": "create_game"}, callback)
    
    def join_game(self, game_id, callback=None):
        """
        Rejoint une partie existante
        
        Args:
            game_id: Identifiant de la partie à rejoindre
            callback: Fonction appelée quand le serveur répond
        """
        self.send_message({"type": "join_game", "game_id": game_id}, callback)
    
    def play_online_ai(self, callback=None):
        """
        Demande une partie contre l'IA en ligne
        
        Args:
            callback: Fonction appelée quand le serveur répond
        """
        self.send_message({"type": "play_ai"}, callback)
    
    def send_shot(self, row, col, callback=None):
        """
        Envoie un tir au serveur
        
        Args:
            row: Ligne ciblée
            col: Colonne ciblée
            callback: Fonction appelée quand le serveur répond
        """
        self.send_message({
            "type": "shot",
            "game_id": self.game_id,
            "player_id": self.player_id,
            "row": row,
            "col": col
        }, callback)
    
    def send_ship_positions(self, ships, callback=None):
        """
        Envoie les positions des navires au serveur
        
        Args:
            ships: Liste des objets navires avec leurs positions
            callback: Fonction appelée quand le serveur répond
        """
        # Convertir les objets navires en dictionnaires
        ships_data = []
        for ship in ships:
            ships_data.append({
                "name": ship.name,
                "size": ship.size,
                "row": ship.row,
                "col": ship.col,
                "orientation": ship.orientation
            })
        
        self.send_message({
            "type": "ship_positions",
            "game_id": self.game_id,
            "player_id": self.player_id,
            "ships": ships_data
        }, callback)
    
    def send_message(self, message, callback=None):
        """
        Envoie un message au serveur
        
        Args:
            message: Dictionnaire contenant les données à envoyer
            callback: Fonction appelée quand le serveur répond
        """
        if not self.connected:
            if callback:
                callback(False, "Non connecté au serveur")
            return
        
        try:
            # Convertir le message en JSON puis en bytes
            data = json.dumps(message).encode('utf-8')
            # Envoyer la taille du message d'abord (4 octets)
            message_size = len(data).to_bytes(4, byteorder='big')
            self.socket.sendall(message_size + data)
            
            if callback:
                # La réponse sera traitée par le thread de réception
                # et le callback sera appelé à ce moment-là
                pass
        
        except Exception as e:
            print(f"Erreur d'envoi: {e}")
            if callback:
                callback(False, str(e))
            
            # Fermer la connexion si une erreur se produit
            self.disconnect()
    
    def _receive_messages(self):
        """Thread qui reçoit les messages du serveur"""
        try:
            while self.connected:
                # Recevoir d'abord la taille du message
                size_data = self._recvall(4)
                if not size_data:
                    break
                
                message_size = int.from_bytes(size_data, byteorder='big')
                
                # Recevoir le message complet
                message_data = self._recvall(message_size)
                if not message_data:
                    break
                
                # Décoder et traiter le message
                try:
                    message = json.loads(message_data.decode('utf-8'))
                    self._process_message(message)
                except Exception as e:
                    print(f"Erreur de traitement du message: {e}")
        
        except Exception as e:
            print(f"Erreur de réception: {e}")
        
        finally:
            # Déconnexion
            if self.connected:
                self.disconnect()
    
    def _recvall(self, n):
        """
        Reçoit exactement n octets du serveur
        
        Args:
            n: Nombre d'octets à recevoir
            
        Returns:
            bytes: Les données reçues ou None si la connexion est fermée
        """
        data = bytearray()
        while len(data) < n:
            packet = self.socket.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data
    
    def _process_message(self, message):
        """
        Traite un message reçu du serveur
        
        Args:
            message: Le message décodé
        """
        if "type" not in message:
            print("Message reçu sans type")
            return
        
        message_type = message["type"]
        
        if message_type == "game_created":
            self.game_id = message.get("game_id")
            self.player_id = message.get("player_id")
        
        elif message_type == "game_joined":
            self.game_id = message.get("game_id")
            self.player_id = message.get("player_id")
        
        elif message_type == "disconnect":
            self.disconnect()
        
        # Appeler le callback général pour tous les messages
        if self.message_callback:
            self.message_callback(message)
    
    def set_message_callback(self, callback):
        """
        Définit la fonction appelée quand un message est reçu
        
        Args:
            callback: Fonction à appeler avec le message reçu
        """
        self.message_callback = callback
    
    def set_connection_callback(self, callback):
        """
        Définit la fonction appelée quand la connexion est établie
        
        Args:
            callback: Fonction à appeler
        """
        self.connection_callback = callback
    
    def set_disconnection_callback(self, callback):
        """
        Définit la fonction appelée quand la connexion est fermée
        
        Args:
            callback: Fonction à appeler
        """
        self.disconnection_callback = callback

