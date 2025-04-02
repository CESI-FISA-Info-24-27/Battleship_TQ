import socket
import threading
import json
import time
import logging
import random

# Configuration du serveur
HOST = '0.0.0.0'  # Accepte les connexions de toutes les interfaces
PORT = 65432  # Port utilisé par l'autre projet

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("BattleshipServer")

# Verrou pour la synchronisation des threads
lock = threading.Lock()

# État global du jeu
clients = {}  # Dictionnaire avec socket comme clé et les infos du client comme valeur
id_counter = 0  # Compteur pour attribuer des IDs uniques aux clients

# Constantes pour la grille
WATER = '~'
SHIP = 'B'
MISSED_SHOT = 'X'
HIT_SHOT = 'O'
GRID_SIZE = 10
SHIP_SIZES = [5, 4, 3, 3, 2]

class Server:
    """
    Serveur pour gérer les connexions réseau du jeu de bataille navale
    """
    
    def __init__(self, host=HOST, port=PORT):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        self.local_ip = None
    
    def start(self):
        """
        Démarrer le serveur et écouter les connexions
        
        Returns:
            True si le démarrage est réussi, False sinon
        """
        global clients, id_counter
        
        try:
            # Réinitialiser l'état global
            with lock:
                clients = {}
                id_counter = 0
            
            # Créer le socket serveur
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            # Lier le socket à l'hôte et au port
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)  # Accepter jusqu'à 5 connexions en attente
            self.running = True
            
            # Obtenir l'adresse IP locale
            try:
                temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                temp_socket.connect(("8.8.8.8", 80))
                self.local_ip = temp_socket.getsockname()[0]
                temp_socket.close()
            except:
                self.local_ip = socket.gethostbyname(socket.gethostname())
            
            logger.info(f"Serveur démarré sur {self.host}:{self.port}")
            logger.info(f"Adresse IP locale : {self.local_ip}:{self.port}")
            
            # Démarrer un thread pour accepter les connexions
            accept_thread = threading.Thread(target=self._accept_connections)
            accept_thread.daemon = True
            accept_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur de démarrage du serveur : {e}")
            if self.server_socket:
                self.server_socket.close()
            return False
    
    def stop(self):
        """
        Arrêter le serveur et fermer toutes les connexions
        """
        logger.info("Arrêt du serveur")
        self.running = False
        
        # Fermer toutes les connexions clients
        with lock:
            for client_socket in list(clients.keys()):
                try:
                    client_socket.close()
                except:
                    pass
            
            clients.clear()
        
        # Fermer le socket serveur
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        logger.info("Serveur arrêté")
    
    def _accept_connections(self):
        """
        Accepter les connexions des clients
        """
        self.server_socket.settimeout(1.0)
        
        while self.running:
            try:
                # Accepter une nouvelle connexion
                client_socket, addr = self.server_socket.accept()
                logger.info(f"Nouvelle connexion de {addr}")
                
                # Démarrer un thread pour gérer ce client
                client_thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, addr)
                )
                client_thread.daemon = True
                client_thread.start()
                
            except socket.timeout:
                # Timeout normal, continuer la boucle
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"Erreur lors de l'acceptation des connexions : {e}")
                    time.sleep(1)
    
    def _handle_client(self, client_socket, addr):
        """
        Gérer la communication avec un client
        
        Args:
            client_socket: Socket du client
            addr: Adresse du client
        """
        global id_counter
        
        try:
            # Attendre le message de login
            message = self._receive_message(client_socket)
            if not message or message.get('type') != 'login':
                logger.warning(f"Premier message invalide de {addr}")
                client_socket.close()
                return
            
            username = message.get('username', f"Player_{id_counter}")
            
            # Enregistrer le client
            with lock:
                client_id = id_counter
                id_counter += 1
                
                clients[client_socket] = {
                    'id': client_id,
                    'username': username,
                    'grid': self._create_empty_grid(),
                    'status': 'waiting_placement'
                }
            
            logger.info(f"Joueur {username} (ID: {client_id}) enregistré")
            
            # Envoyer une confirmation de login
            self._send_message(client_socket, {
                'type': 'login_success',
                'id': client_id,
                'message': f"Bienvenue {username}! Placez vos bateaux."
            })
            
            # Boucle principale de communication
            while self.running:
                message = self._receive_message(client_socket)
                if not message:
                    break
                
                # Traiter le message selon son type
                with lock:
                    client_info = clients[client_socket]
                    message_type = message.get('type')
                    
                    if message_type == 'place_ships':
                        # Recevoir le placement des bateaux
                        client_info['grid'] = message['grid']
                        client_info['status'] = 'ready'
                        
                        self._send_message(client_socket, {
                            'type': 'ships_placed',
                            'message': "Bateaux placés avec succès. En attente d'un adversaire."
                        })
                        
                        # Chercher un adversaire disponible
                        self._find_opponent(client_socket)
                    
                    elif message_type == 'fire_shot':
                        # Traiter un tir
                        if 'opponent' not in client_info or client_info.get('turn', False) is False:
                            self._send_message(client_socket, {
                                'type': 'error',
                                'message': "Ce n'est pas votre tour."
                            })
                            continue
                        
                        # Récupérer les coordonnées du tir
                        position = message['position']
                        row, column = position
                        
                        # Récupérer l'adversaire
                        opponent_socket = client_info['opponent']
                        opponent_info = clients[opponent_socket]
                        
                        # Traiter le tir sur la grille adverse
                        result = self._process_shot(opponent_info['grid'], row, column)
                        
                        if result == "already_fired":
                            self._send_message(client_socket, {
                                'type': 'error',
                                'message': "Vous avez déjà tiré à cette position."
                            })
                            continue
                        
                        # Vérifier si la partie est terminée
                        game_over = self._check_game_over(opponent_info['grid'])
                        
                        # Envoyer le résultat au tireur
                        self._send_message(client_socket, {
                            'type': 'shot_result',
                            'result': result,
                            'position': [row, column],
                            'game_over': game_over,
                            'opponent_grid': opponent_info['grid']
                        })
                        
                        # Envoyer le résultat à l'adversaire
                        self._send_message(opponent_socket, {
                            'type': 'opponent_shot',
                            'result': result,
                            'position': [row, column],
                            'game_over': game_over,
                            'my_grid': opponent_info['grid']
                        })
                        
                        if not game_over:
                            # Passer le tour
                            client_info['turn'] = False
                            opponent_info['turn'] = True
                            
                            # Informer l'adversaire que c'est son tour
                            self._send_message(opponent_socket, {
                                'type': 'your_turn',
                                'message': "C'est votre tour de tirer."
                            })
                        else:
                            # Fin de partie
                            client_info.pop('opponent', None)
                            opponent_info.pop('opponent', None)
                            client_info['status'] = 'waiting_placement'
                            opponent_info['status'] = 'waiting_placement'
                            
                            self._send_message(client_socket, {
                                'type': 'game_over',
                                'winner': True,
                                'message': "Félicitations ! Vous avez gagné !"
                            })
                            
                            self._send_message(opponent_socket, {
                                'type': 'game_over',
                                'winner': False,
                                'message': "Dommage, vous avez perdu. Votre adversaire a coulé tous vos bateaux."
                            })
                    
                    elif message_type == 'ready_for_new_game':
                        # Préparer une nouvelle partie
                        client_info['grid'] = self._create_empty_grid()
                        client_info['status'] = 'waiting_placement'
                        
                        self._send_message(client_socket, {
                            'type': 'place_ships_request',
                            'message': "Nouvelle partie! Placez vos bateaux."
                        })
        
        except Exception as e:
            logger.error(f"Erreur dans la gestion du client {addr}: {e}")
        
        finally:
            # Nettoyer à la déconnexion
            self._disconnect_client(client_socket)
    
    def _disconnect_client(self, client_socket):
        """
        Gérer la déconnexion d'un client
        
        Args:
            client_socket: Socket du client à déconnecter
        """
        with lock:
            if client_socket in clients:
                client_info = clients[client_socket]
                
                # Informer l'adversaire si nécessaire
                if 'opponent' in client_info and client_info['opponent'] in clients:
                    opponent_socket = client_info['opponent']
                    opponent_info = clients[opponent_socket]
                    
                    self._send_message(opponent_socket, {
                        'type': 'opponent_disconnected',
                        'message': f"{client_info['username']} s'est déconnecté. La partie est terminée."
                    })
                    
                    opponent_info.pop('opponent', None)
                
                logger.info(f"Client {client_info['username']} (ID: {client_info['id']}) déconnecté.")
                del clients[client_socket]
        
        try:
            client_socket.close()
        except:
            pass
    
    def _find_opponent(self, client_socket):
        """
        Trouver un adversaire disponible pour un client
        
        Args:
            client_socket: Socket du client cherchant un adversaire
        """
        client_info = clients[client_socket]
        
        if client_info['status'] != 'ready':
            return
        
        # Chercher un autre client prêt
        for other_socket, other_info in clients.items():
            if (other_socket != client_socket and 
                other_info['status'] == 'ready' and 
                'opponent' not in other_info):
                
                # Associer les deux clients
                client_info['opponent'] = other_socket
                other_info['opponent'] = client_socket
                
                # Tirer au sort qui commence
                first_player = random.choice([client_socket, other_socket])
                second_player = other_socket if first_player == client_socket else client_socket
                
                clients[first_player]['turn'] = True
                clients[second_player]['turn'] = False
                
                # Informer les deux joueurs du démarrage de la partie
                self._send_message(client_socket, {
                    'type': 'game_start',
                    'opponent': other_info['username'],
                    'first_player': first_player == client_socket,
                    'my_grid': client_info['grid'],
                    'opponent_grid': self._hide_ships(other_info['grid'])
                })
                
                self._send_message(other_socket, {
                    'type': 'game_start',
                    'opponent': client_info['username'],
                    'first_player': first_player == other_socket,
                    'my_grid': other_info['grid'],
                    'opponent_grid': self._hide_ships(client_info['grid'])
                })
                
                # Informer le premier joueur que c'est son tour
                self._send_message(first_player, {
                    'type': 'your_turn',
                    'message': "C'est votre tour de tirer."
                })
                
                logger.info(f"Nouvelle partie: {client_info['username']} vs {other_info['username']}")
                return
        
        # Si aucun adversaire n'est trouvé, informer le client qu'il doit attendre
        self._send_message(client_socket, {
            'type': 'waiting_opponent',
            'message': "En attente d'un adversaire..."
        })
    
    def _hide_ships(self, grid):
        """
        Cacher les bateaux d'une grille (remplacer 'B' par '~')
        
        Args:
            grid: Grille à modifier
            
        Returns:
            Copie de la grille avec les bateaux cachés
        """
        hidden_grid = {
            'matrix': [[cell if cell != SHIP else WATER for cell in row] for row in grid['matrix']],
            'ships': []  # Pas besoin d'envoyer les infos des bateaux
        }
        return hidden_grid
    
    def _send_message(self, client_socket, message):
        """
        Envoyer un message au client au format JSON
        
        Args:
            client_socket: Socket du client
            message: Message à envoyer (dictionnaire)
        """
        try:
            message_json = json.dumps(message)
            message_bytes = message_json.encode('utf-8')
            
            # Envoyer d'abord la taille du message
            size_bytes = len(message_bytes).to_bytes(4, byteorder='big')
            client_socket.sendall(size_bytes + message_bytes)
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message: {e}")
            self._disconnect_client(client_socket)
            return False
    
    def _receive_message(self, client_socket):
        """
        Recevoir un message du client au format JSON
        
        Args:
            client_socket: Socket du client
            
        Returns:
            Message reçu (dictionnaire) ou None en cas d'erreur
        """
        try:
            # Recevoir d'abord la taille du message
            size_bytes = client_socket.recv(4)
            if not size_bytes:
                return None
            
            message_size = int.from_bytes(size_bytes, byteorder='big')
            
            # Recevoir le message par morceaux si nécessaire
            message_bytes = b''
            remaining = message_size
            
            while remaining > 0:
                chunk = client_socket.recv(min(remaining, 4096))
                if not chunk:
                    return None
                message_bytes += chunk
                remaining -= len(chunk)
            
            # Convertir en JSON
            message_json = message_bytes.decode('utf-8')
            return json.loads(message_json)
        except Exception as e:
            logger.error(f"Erreur lors de la réception du message: {e}")
            return None
    
    def _create_empty_grid(self):
        """
        Créer une grille vide
        
        Returns:
            Grille vide
        """
        return {
            'matrix': [[WATER for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)],
            'ships': []
        }
    
    def _process_shot(self, grid, row, column):
        """
        Traiter un tir sur une grille
        
        Args:
            grid: Grille cible
            row, column: Coordonnées du tir
            
        Returns:
            Résultat du tir: "miss", "hit", "sunk" ou "already_fired"
        """
        # Vérifier si la case a déjà été ciblée
        if grid['matrix'][row][column] in [MISSED_SHOT, HIT_SHOT]:
            return "already_fired"
        
        # Vérifier si la case contient un bateau
        if grid['matrix'][row][column] == SHIP:
            # Marquer comme touché
            grid['matrix'][row][column] = HIT_SHOT
            
            # Vérifier si un bateau a été coulé
            for ship in grid['ships']:
                if [row, column] in ship['positions'] or (row, column) in ship['positions']:
                    # S'assurer que hits est une liste et enregistrer au bon format
                    if 'hits' not in ship:
                        ship['hits'] = []
                    
                    # Ajouter le hit (assurer la cohérence du format)
                    if isinstance(ship['positions'][0], list):
                        ship['hits'].append([row, column])
                    else:
                        ship['hits'].append((row, column))
                    
                    # Vérifier si le bateau est coulé
                    if len(ship['hits']) == ship['size']:
                        return "sunk"
                    else:
                        return "hit"
            
            return "hit"
        else:
            # Marqué comme manqué
            grid['matrix'][row][column] = MISSED_SHOT
            return "miss"
    
    def _check_game_over(self, grid):
        """
        Vérifier si tous les bateaux d'une grille sont coulés
        
        Args:
            grid: Grille à vérifier
            
        Returns:
            True si tous les bateaux sont coulés, False sinon
        """
        if not grid['ships']:
            return False
            
        for ship in grid['ships']:
            if 'hits' not in ship or len(ship['hits']) < ship['size']:
                return False
        return True


# Point d'entrée pour démarrer le serveur directement
if __name__ == "__main__":
    server = Server()
    try:
        if server.start():
            print("Serveur démarré avec succès. Appuyez sur Ctrl+C pour quitter.")
            # Garder le thread principal en vie
            while True:
                time.sleep(1)
        else:
            print("Erreur lors du démarrage du serveur.")
    except KeyboardInterrupt:
        print("\nArrêt du serveur...")
    finally:
        server.stop()