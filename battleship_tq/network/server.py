# server.py - Version simplifiée pour réseau local
import socket
import threading
import json
import random
import string

class LocalGameServer:
    """Serveur simplifié pour jeux en réseau local"""
    
    def __init__(self, port=5555):
        self.host = self._get_local_ip()
        self.port = port
        self.socket = None
        self.running = False
        self.connected_clients = {}
    
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
    
    def start(self):
        """Démarre le serveur de jeu local"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(2)  # Limiter à 2 joueurs max
            
            self.running = True
            print(f"Serveur local démarré sur {self.host}:{self.port}")
            
            # Thread principal d'acceptation des connexions
            def accept_connections():
                while self.running:
                    try:
                        client_socket, client_address = self.socket.accept()
                        
                        # Limiter à 2 clients
                        if len(self.connected_clients) >= 2:
                            client_socket.close()
                            continue
                        
                        # Ajouter le client
                        client_id = self.generate_game_code()
                        self.connected_clients[client_id] = {
                            'socket': client_socket,
                            'address': client_address
                        }
                        
                        # Lancer un thread de gestion du client
                        client_thread = threading.Thread(
                            target=self._handle_client, 
                            args=(client_id,)
                        )
                        client_thread.daemon = True
                        client_thread.start()
                    
                    except Exception as e:
                        print(f"Erreur d'acceptation de connexion : {e}")
                        break
            
            # Démarrer le thread d'acceptation
            connection_thread = threading.Thread(target=accept_connections)
            connection_thread.daemon = True
            connection_thread.start()
            
            return True
        except Exception as e:
            print(f"Erreur de démarrage du serveur : {e}")
            return False
    
    def _handle_client(self, client_id):
        """Gère la communication avec un client"""
        client = self.connected_clients[client_id]
        socket = client['socket']
        
        try:
            # Envoyer un message de confirmation de connexion
            self._broadcast_client_list()
            
            # Recevoir les messages
            buffer = ""
            while True:
                data = socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                buffer += data
                
                # Traiter chaque message
                while '\n' in buffer:
                    message_str, buffer = buffer.split('\n', 1)
                    try:
                        message = json.loads(message_str)
                        # Transmettre le message à tous les autres clients
                        self._broadcast_message(message, sender_id=client_id)
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            print(f"Erreur avec le client {client_id}: {e}")
        finally:
            # Nettoyer la connexion
            socket.close()
            del self.connected_clients[client_id]
            self._broadcast_client_list()
    
    def _broadcast_message(self, message, sender_id=None):
        """Diffuse un message à tous les clients sauf l'expéditeur"""
        for client_id, client in list(self.connected_clients.items()):
            if client_id != sender_id:
                try:
                    encoded_message = json.dumps(message).encode('utf-8')
                    client['socket'].sendall(encoded_message + b'\n')
                except Exception as e:
                    print(f"Erreur d'envoi à {client_id}: {e}")
    
    def _broadcast_client_list(self):
        """Envoie la liste des clients connectés"""
        clients_info = [
            {'id': client_id, 'address': str(client['address'][0])} 
            for client_id, client in self.connected_clients.items()
        ]
        
        for client in self.connected_clients.values():
            try:
                message = {
                    'type': 'client_list',
                    'clients': clients_info
                }
                encoded_message = json.dumps(message).encode('utf-8')
                client['socket'].sendall(encoded_message + b'\n')
            except Exception as e:
                print(f"Erreur d'envoi de la liste des clients : {e}")
    
    def stop(self):
        """Arrête le serveur"""
        self.running = False
        
        # Fermer tous les sockets clients
        for client in list(self.connected_clients.values()):
            try:
                client['socket'].close()
            except Exception:
                pass
        
        # Fermer le socket du serveur
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
        
        print("Serveur arrêté")

def start_server(port=5555):
    """Fonction utilitaire pour démarrer le serveur"""
    server = LocalGameServer(port)
    return server.start()

if __name__ == "__main__":
    start_server()