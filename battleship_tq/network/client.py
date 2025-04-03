# client.py
import socket
import threading
import json
import random
import string
import logging

class NetworkClient:
    """Client réseau pour le jeu de bataille navale"""
    
    ERROR_CODES = {
        'NOT_FOUND': "Code de partie invalide",
        'FULL': "La partie est déjà complète",
        'IN_PROGRESS': "La partie est déjà en cours",
        'NETWORK_ERROR': "Erreur de connexion réseau"
    }
    
    def __init__(self, port=5555):
        self.host = self._get_local_ip()
        self.port = port
        self.socket = None
        self.server_socket = None
        self.connected = False
        self.game_code = None
        self.is_host = False
        self.connection_status = "Non connecté"
        self.connection_event = threading.Event()
        self.message_callback = None
    
    def _get_local_ip(self):
        """Obtient l'adresse IP locale"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return 'localhost'
    
    def generate_game_code(self, length=6):
        """Génère un code de partie unique"""
        characters = string.ascii_uppercase + string.digits
        return ''.join(random.choice(characters) for _ in range(length))
    
    def create_game(self):
        """Crée une partie en attente"""
        try:
            # Générer un code de partie unique
            self.game_code = self.generate_game_code()
            
            # Créer un socket serveur
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            
            self.is_host = True
            self.connection_status = "En attente de connexion"
            
            # Thread pour attendre la connexion du client
            def wait_for_connection():
                try:
                    client_socket, client_address = self.server_socket.accept()
                    
                    # Vérifier la connexion
                    self.socket = client_socket
                    self.connected = True
                    self.connection_status = "Connecté"
                    
                    # Signaler la connexion réussie
                    self.connection_event.set()
                except Exception as e:
                    self.connection_status = f"Erreur de connexion : {e}"
                    self.connection_event.set()
            
            # Démarrer le thread d'attente
            connection_thread = threading.Thread(target=wait_for_connection)
            connection_thread.daemon = True
            connection_thread.start()
            
            return self.game_code
        except Exception as e:
            self.connection_status = f"Erreur de création : {e}"
            return None
    
    def join_game(self, game_code, server_host='localhost'):
        """Rejoint une partie via son code"""
        try:
            # Validation du code
            if not game_code or len(game_code) != 6:
                return False, 'NOT_FOUND'
            
            # Créer une connexion
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((server_host, self.port))
            
            # Envoyer le code de partie au serveur
            join_message = {
                'type': 'join_game',
                'game_code': game_code
            }
            self.send_message(join_message)
            
            # Attendre la réponse du serveur
            response = self.receive_message()
            
            if response and response.get('status') == 'success':
                self.game_code = game_code
                self.is_host = False
                self.connected = True
                self.connection_status = "Connecté"
                return True, None
            elif response and response.get('error'):
                return False, response['error']
            
            return False, 'NETWORK_ERROR'
        except Exception as e:
            self.connection_status = f"Erreur de connexion : {e}"
            return False, 'NETWORK_ERROR'
    
    def wait_for_connection(self, timeout=None):
        """Attend la connexion avec un timeout optionnel"""
        return self.connection_event.wait(timeout)
    
    def send_message(self, message):
        """Envoie un message au serveur"""
        if not self.connected:
            return False
        
        try:
            encoded_message = json.dumps(message).encode('utf-8')
            self.socket.sendall(encoded_message + b'\n')
            return True
        except Exception:
            self.disconnect()
            return False
    
    def receive_message(self):
        """Reçoit un message du serveur"""
        if not self.connected:
            return None
        
        try:
            data = self.socket.recv(1024).decode('utf-8')
            return json.loads(data) if data else None
        except Exception:
            self.disconnect()
            return None
    
    def disconnect(self):
        """Ferme la connexion"""
        self.connected = False
        self.connection_status = "Déconnecté"
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
        
        self.game_code = None
        self.is_host = False
        self.connection_event.clear()