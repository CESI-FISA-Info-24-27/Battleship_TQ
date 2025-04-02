import socket
import threading
import pickle
import time
import logging
import json
from ..game.game_state import GameState
from ..models.network_models import Action, GameStateUpdate
from ..utils.constants import DEFAULT_PORT

class Server:
    """
    Serveur pour gérer les connexions réseau du jeu de bataille navale
    """
    
    def __init__(self, host='0.0.0.0', port=DEFAULT_PORT):
        # Configuration du logging
        logging.basicConfig(
            level=logging.INFO, 
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Paramètres du serveur
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        
        # État du jeu et gestion des clients
        self.game_state = GameState()
        self.clients = []  # Liste des tuples (connexion, ID_joueur)
        self.lock = threading.Lock()  # Verrou pour modifications thread-safe
        
        # Compteur pour assigner des IDs uniques
        self.player_id_counter = 0
    
    def start(self):
        """
        Démarrer le serveur et écouter les connexions
        
        Returns:
            True si le démarrage est réussi, False sinon
        """
        try:
            # Créer le socket serveur
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            try:
                # Lier le socket à l'hôte et au port
                self.server_socket.bind((self.host, self.port))
                self.server_socket.listen(5)  # Accepter jusqu'à 5 connexions en attente
                self.running = True
                
                # Obtenir l'adresse IP locale de manière robuste
                try:
                    # Méthode 1 : Utiliser une connexion temporaire à un serveur externe
                    temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    temp_socket.connect(("8.8.8.8", 80))
                    local_ip = temp_socket.getsockname()[0]
                    temp_socket.close()
                except Exception:
                    # Méthode de repli
                    local_ip = socket.gethostbyname(socket.gethostname())
                
                self.logger.info(f"Serveur démarré sur {self.host}:{self.port}")
                self.logger.info(f"Adresse IP locale : {local_ip}:{self.port}")
                
                # Stocker l'IP locale pour affichage
                self.local_ip = local_ip
                
                # S'assurer que la liste des clients est vide au démarrage
                with self.lock:
                    self.clients = []
                
                # Démarrer un thread pour accepter les connexions
                accept_thread = threading.Thread(target=self._accept_connections)
                accept_thread.daemon = True
                accept_thread.start()
                
                return True
            
            except Exception as e:
                self.logger.error(f"Erreur de liaison du serveur : {e}")
                try:
                    self.server_socket.close()
                except:
                    pass
                return False
        
        except Exception as e:
            self.logger.error(f"Erreur de création du socket serveur : {e}")
            return False
    
    def stop(self):
        """
        Arrêter le serveur et fermer toutes les connexions
        """
        self.logger.info("Arrêt du serveur")
        self.running = False
        
        # Fermer toutes les connexions clients
        with self.lock:
            for conn, _ in self.clients:
                try:
                    conn.close()
                except:
                    pass
            
            self.clients = []
        
        # Fermer le socket serveur
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        self.logger.info("Serveur arrêté")
    
    def _is_connection_active(self, conn):
        """
        Vérifie si une connexion est toujours active
        
        Args:
            conn: Connexion socket à vérifier
            
        Returns:
            True si la connexion est active, False sinon
        """
        try:
            # Vérifier si le descripteur de fichier est valide
            return conn.fileno() != -1
        except:
            return False
    
    def _accept_connections(self):
        """
        Accepter les connexions des clients
        """
        # Timeout pour permettre des arrêts propres
        self.server_socket.settimeout(1.0)
        
        while self.running:
            try:
                # Accepter une nouvelle connexion
                conn, addr = self.server_socket.accept()
                self.logger.info(f"Nouvelle connexion de {addr}")
                
                # Attribuer un ID de joueur
                with self.lock:
                    # Nettoyer la liste des clients inactifs
                    self.clients = [(c, pid) for c, pid in self.clients if self._is_connection_active(c)]
                    
                    # Log du nombre de clients actuels
                    self.logger.info(f"Nombre de clients actuels: {len(self.clients)}")
                    
                    # Vérifier si on peut attribuer l'ID 0 ou 1
                    player_id = None
                    existing_ids = [pid for _, pid in self.clients]
                    
                    for possible_id in [0, 1]:
                        if possible_id not in existing_ids:
                            player_id = possible_id
                            break
                    
                    # Si les IDs 0 et 1 sont déjà pris, serveur complet
                    if player_id is None:
                        self.logger.warning(f"Tentative de connexion rejetée : serveur complet ({len(self.clients)} clients connectés)")
                        conn.send(pickle.dumps("SERVER_FULL"))
                        conn.close()
                        continue
                    
                    # Ajouter le client à la liste
                    self.clients.append((conn, player_id))
                    
                    # Envoyer l'ID de joueur
                    conn.send(pickle.dumps(player_id))
                    
                    # Démarrer un thread pour gérer ce client
                    handler_thread = threading.Thread(
                        target=self._handle_client,
                        args=(conn, player_id)
                    )
                    handler_thread.daemon = True
                    handler_thread.start()
            
            except socket.timeout:
                # Timeout normal, continuer la boucle
                continue
            
            except Exception as e:
                if self.running:
                    self.logger.error(f"Erreur lors de l'acceptation des connexions : {e}")
                    time.sleep(1)
    
    def _handle_client(self, conn, player_id):
        """
        Gérer la communication avec un client
        
        Args:
            conn: Connexion socket
            player_id: ID du joueur (0 ou 1)
        """
        conn.settimeout(0.5)  # Timeout pour éviter un blocage
        
        try:
            # Envoyer l'état initial du jeu
            self._send_game_state(conn)
            
            # Boucle principale de communication
            while self.running:
                try:
                    # Recevoir une action
                    data = conn.recv(4096)
                    
                    if not data:
                        self.logger.warning(f"Client {player_id} déconnecté (aucune donnée)")
                        break
                    
                    # Traiter l'action
                    action = pickle.loads(data)
                    self._process_action(action)
                    
                    # Diffuser l'état du jeu à tous les clients
                    self._broadcast_game_state()
                
                except socket.timeout:
                    # Timeout normal, continuer
                    continue
                
                except (ConnectionResetError, ConnectionAbortedError):
                    self.logger.warning(f"Réinitialisation de la connexion du client {player_id}")
                    break
                
                except Exception as e:
                    self.logger.error(f"Erreur lors de la réception des données du client {player_id} : {e}")
                    break
        
        except Exception as e:
            self.logger.error(f"Erreur lors de la gestion du client {player_id}: {e}")
        
        finally:
            # Nettoyer la connexion
            with self.lock:
                self.clients = [(c, pid) for c, pid in self.clients if c != conn]
            
            try:
                conn.close()
            except:
                pass
            
            self.logger.info(f"Client {player_id} déconnecté")
            
            # Si un joueur se déconnecte, réinitialiser l'état du jeu
            if self.running:
                self.logger.info("Un joueur s'est déconnecté, réinitialisation de l'état du jeu")
                with self.lock:
                    self.game_state.reset()
                    self._broadcast_game_state()
    
    def _process_action(self, action):
        """
        Traiter une action reçue d'un client
        
        Args:
            action: Objet Action
        """
        with self.lock:
            try:
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
                
                # Les messages de chat ne modifient pas l'état du jeu, ils sont simplement diffusés
                elif action.type == Action.CHAT_MESSAGE:
                    pass
            
            except Exception as e:
                self.logger.error(f"Erreur lors du traitement de l'action : {e}")
    
    def _send_game_state(self, conn):
        """
        Envoyer l'état actuel du jeu à un client
        
        Args:
            conn: Connexion socket
        """
        try:
            with self.lock:
                update = GameStateUpdate(self.game_state)
            conn.send(pickle.dumps(update))
        except Exception as e:
            self.logger.error(f"Erreur lors de l'envoi de l'état du jeu : {e}")
    
    def _broadcast_game_state(self):
        """
        Diffuser l'état du jeu à tous les clients connectés
        """
        with self.lock:
            update = GameStateUpdate(self.game_state)
            data = pickle.dumps(update)
            
            disconnect_list = []
            
            for conn, player_id in self.clients:
                try:
                    conn.send(data)
                except:
                    self.logger.warning(f"Échec de l'envoi de la mise à jour au joueur {player_id}")
                    disconnect_list.append((conn, player_id))
            
            # Supprimer les clients déconnectés
            for conn, player_id in disconnect_list:
                if (conn, player_id) in self.clients:
                    self.clients.remove((conn, player_id))
                try:
                    conn.close()
                except:
                    pass