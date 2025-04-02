# server.py
import socket
import threading
import json
import random
import string
import time
from game.constants import DEFAULT_PORT, MAX_GAMES

class Game:
    """Représente une partie de bataille navale en cours"""
    
    def __init__(self, game_id):
        self.game_id = game_id
        self.players = {}  # id -> {socket, name, ready, grid, ships}
        self.current_player = None
        self.state = "waiting"  # "waiting", "playing", "finished"
        self.ai_difficulty = 2  # Difficulté par défaut pour l'IA (MOYEN)
        self.is_ai_game = False
        self.last_activity = time.time()
    
    def add_player(self, player_id, player_socket, player_name="Joueur"):
        """Ajoute un joueur à la partie"""
        if len(self.players) >= 2 and not self.is_ai_game:
            return False
        
        self.players[player_id] = {
            "socket": player_socket,
            "name": player_name,
            "ready": False,
            "grid": [[' ' for _ in range(10)] for _ in range(10)],
            "ships": []
        }
        
        return True
    
    def remove_player(self, player_id):
        """Retire un joueur de la partie"""
        if player_id in self.players:
            del self.players[player_id]
            
            # Si tous les joueurs sont partis, la partie est terminée
            if not self.players:
                self.state = "finished"
            
            return True
        
        return False
    
    def is_ready(self):
        """Vérifie si tous les joueurs sont prêts à jouer"""
        if len(self.players) < 2 and not self.is_ai_game:
            return False
        
        return all(player["ready"] for player in self.players.values())
    
    def set_player_ready(self, player_id):
        """Marque un joueur comme prêt à jouer"""
        if player_id in self.players:
            self.players[player_id]["ready"] = True
            
            # Si tous les joueurs sont prêts, commencer la partie
            if self.is_ready():
                self.start_game()
            
            return True
        
        return False
    
    def start_game(self):
        """Démarre la partie"""
        if self.state == "waiting" and self.is_ready():
            self.state = "playing"
            
            # Choisir le joueur qui commence
            self.current_player = random.choice(list(self.players.keys()))
            
            # Informer tous les joueurs du début de la partie
            for player_id, player in self.players.items():
                try:
                    message = {
                        "type": "game_started",
                        "starting_player": self.current_player,
                        "your_turn": player_id == self.current_player
                    }
                    self._send_to_player(player_id, message)
                except Exception as e:
                    print(f"Erreur lors du démarrage de la partie: {e}")
            
            return True
        
        return False
    
    def process_shot(self, player_id, row, col):
        """Traite un tir d'un joueur"""
        if self.state != "playing" or self.current_player != player_id:
            return {"valid": False, "reason": "Ce n'est pas votre tour"}
        
        # Trouver l'adversaire
        opponent_id = next((pid for pid in self.players.keys() if pid != player_id), None)
        
        if not opponent_id:
            return {"valid": False, "reason": "Aucun adversaire trouvé"}
        
        opponent = self.players[opponent_id]
        
        # Vérifier si la case a déjà été ciblée
        if opponent["grid"][row][col] in ['O', 'X']:
            return {"valid": False, "reason": "Case déjà ciblée"}
        
        # Déterminer le résultat du tir
        if opponent["grid"][row][col] == 'N':
            # Touché
            opponent["grid"][row][col] = 'X'
            
            # Vérifier si un navire est coulé
            ship_sunk = self._check_ship_sunk(opponent["grid"], opponent["ships"], row, col)
            
            # Vérifier si tous les navires sont coulés
            all_sunk = all(all(cell != 'N' for cell in row) for row in opponent["grid"])
            
            result = {
                "valid": True,
                "hit": True,
                "sunk": ship_sunk,
                "game_over": all_sunk
            }
            
            if all_sunk:
                self.state = "finished"
                self._send_game_over(player_id)
            else:
                # Changer de joueur
                self.current_player = opponent_id
        
        else:
            # Manqué
            opponent["grid"][row][col] = 'O'
            
            result = {
                "valid": True,
                "hit": False,
                "sunk": False,
                "game_over": False
            }
            
            # Changer de joueur
            self.current_player = opponent_id
        
        # Notifier les deux joueurs du résultat
        self._notify_shot_result(player_id, opponent_id, row, col, result)
        
        return result
    
    def _check_ship_sunk(self, grid, ships, row, col):
        """Vérifie si un navire a été coulé par le tir"""
        # Trouver le navire touché
        for ship in ships:
            is_hit = False
            
            if ship["orientation"] == 'H':
                if ship["row"] == row and ship["col"] <= col < ship["col"] + ship["size"]:
                    is_hit = True
            else:  # Vertical
                if ship["col"] == col and ship["row"] <= row < ship["row"] + ship["size"]:
                    is_hit = True
            
            if is_hit:
                # Vérifier si toutes les cases du navire sont touchées
                all_hit = True
                
                if ship["orientation"] == 'H':
                    for c in range(ship["col"], ship["col"] + ship["size"]):
                        if grid[ship["row"]][c] != 'X':
                            all_hit = False
                            break
                else:  # Vertical
                    for r in range(ship["row"], ship["row"] + ship["size"]):
                        if grid[r][ship["col"]] != 'X':
                            all_hit = False
                            break
                
                return all_hit
        
        return False
    
    def _notify_shot_result(self, shooter_id, target_id, row, col, result):
        """Notifie les joueurs du résultat d'un tir"""
        # Message pour le tireur
        shooter_message = {
            "type": "shot_result",
            "row": row,
            "col": col,
            "hit": result["hit"],
            "sunk": result["sunk"],
            "game_over": result["game_over"],
            "your_turn": False  # Le tour passe à l'adversaire
        }
        
        # Message pour la cible
        target_message = {
            "type": "opponent_shot",
            "row": row,
            "col": col,
            "hit": result["hit"],
            "sunk": result["sunk"],
            "game_over": result["game_over"],
            "your_turn": True  # C'est maintenant son tour
        }
        
        # Envoyer les messages
        self._send_to_player(shooter_id, shooter_message)
        self._send_to_player(target_id, target_message)
    
    def _send_game_over(self, winner_id):
        """Envoie un message de fin de partie à tous les joueurs"""
        for player_id, player in self.players.items():
            message = {
                "type": "game_over",
                "winner": winner_id,
                "you_won": player_id == winner_id
            }
            self._send_to_player(player_id, message)
    
    def _send_to_player(self, player_id, message):
        """Envoie un message à un joueur spécifique"""
        if player_id in self.players:
            try:
                data = json.dumps(message).encode('utf-8')
                message_size = len(data).to_bytes(4, byteorder='big')
                self.players[player_id]["socket"].sendall(message_size + data)
            except Exception as e:
                print(f"Erreur d'envoi au joueur {player_id}: {e}")
                # Le joueur sera déconnecté par le gestionnaire d'erreur du thread client
    
    def set_ships(self, player_id, ships):
        """Définit les positions des navires d'un joueur"""
        if player_id in self.players:
            # Enregistrer les navires
            self.players[player_id]["ships"] = ships
            
            # Marquer les positions des navires sur la grille
            grid = self.players[player_id]["grid"]
            
            for ship in ships:
                row, col = ship["row"], ship["col"]
                size, orientation = ship["size"], ship["orientation"]
                
                if orientation == 'H':
                    for c in range(col, col + size):
                        grid[row][c] = 'N'
                else:  # Vertical
                    for r in range(row, row + size):
                        grid[r][col] = 'N'
            
            # Marquer le joueur comme prêt
            self.players[player_id]["ready"] = True
            
            # Vérifier si tous les joueurs sont prêts
            if self.is_ready():
                self.start_game()
            
            return True
        
        return False
    
    def is_active(self, timeout=300):
        """Vérifie si la partie est active (dernière activité < timeout secondes)"""
        return time.time() - self.last_activity < timeout

class GameServer:
    """Serveur de jeu pour la bataille navale en ligne"""
    
    def __init__(self, host="0.0.0.0", port=DEFAULT_PORT):
        self.host = host
        self.port = port
        self.socket = None
        self.running = False
        self.clients = {}  # socket -> {id, game_id}
        self.games = {}    # game_id -> Game
        self.next_player_id = 1
    
    def start(self):
        """Démarre le serveur"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)
            self.running = True
            
            print(f"Serveur démarré sur {self.host}:{self.port}")
            
            # Démarrer le thread pour nettoyer les parties inactives
            cleanup_thread = threading.Thread(target=self._cleanup_inactive_games)
            cleanup_thread.daemon = True
            cleanup_thread.start()
            
            # Boucle principale d'acceptation des connexions
            while self.running:
                try:
                    client_socket, client_address = self.socket.accept()
                    print(f"Nouvelle connexion de {client_address[0]}:{client_address[1]}")
                    
                    # Créer un thread pour gérer ce client
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                
                except Exception as e:
                    if self.running:
                        print(f"Erreur d'acceptation: {e}")
                    else:
                        break
        
        except Exception as e:
            print(f"Erreur de démarrage du serveur: {e}")
        
        finally:
            self.stop()
    
    def stop(self):
        """Arrête le serveur"""
        self.running = False
        
        # Fermer toutes les connexions client
        for client_socket in list(self.clients.keys()):
            try:
                client_socket.close()
            except Exception:
                pass
        
        # Fermer la socket du serveur
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
        
        print("Serveur arrêté")
    
    def _handle_client(self, client_socket, client_address):
        """Gère un client connecté"""
        player_id = self._generate_player_id()
        self.clients[client_socket] = {"id": player_id, "game_id": None}
        
        try:
            while self.running:
                # Recevoir la taille du message
                size_data = self._recvall(client_socket, 4)
                if not size_data:
                    break
                
                message_size = int.from_bytes(size_data, byteorder='big')
                
                # Recevoir le message complet
                message_data = self._recvall(client_socket, message_size)
                if not message_data:
                    break
                
                # Décoder et traiter le message
                try:
                    message = json.loads(message_data.decode('utf-8'))
                    self._process_client_message(client_socket, player_id, message)
                except Exception as e:
                    print(f"Erreur de traitement du message: {e}")
        
        except Exception as e:
            print(f"Erreur de connexion avec {client_address}: {e}")
        
        finally:
            # Nettoyer quand le client se déconnecte
            self._client_disconnected(client_socket)
    
    def _recvall(self, sock, n):
        """
        Reçoit exactement n octets du socket
        
        Args:
            sock: Le socket à lire
            n: Nombre d'octets à recevoir
            
        Returns:
            bytes: Les données reçues ou None si la connexion est fermée
        """
        data = bytearray()
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return data
    
    def _process_client_message(self, client_socket, player_id, message):
        """
        Traite un message reçu d'un client
        
        Args:
            client_socket: Le socket du client
            player_id: L'identifiant du joueur
            message: Le message décodé
        """
        if "type" not in message:
            print("Message reçu sans type")
            return
        
        message_type = message["type"]
        
        if message_type == "create_game":
            self._create_game(client_socket, player_id)
        
        elif message_type == "join_game":
            game_id = message.get("game_id")
            if game_id:
                self._join_game(client_socket, player_id, game_id)
            else:
                self._send_error(client_socket, "ID de partie manquant")
        
        elif message_type == "play_ai":
            self._create_ai_game(client_socket, player_id)
        
        elif message_type == "shot":
            game_id = message.get("game_id")
            row = message.get("row")
            col = message.get("col")
            
            if game_id and row is not None and col is not None:
                if game_id in self.games:
                    game = self.games[game_id]
                    result = game.process_shot(player_id, row, col)
                    
                    if not result["valid"]:
                        self._send_error(client_socket, result.get("reason", "Tir invalide"))
                else:
                    self._send_error(client_socket, "Partie inexistante")
            else:
                self._send_error(client_socket, "Paramètres manquants")
        
        elif message_type == "ship_positions":
            game_id = message.get("game_id")
            ships = message.get("ships", [])
            
            if game_id and ships:
                if game_id in self.games:
                    game = self.games[game_id]
                    success = game.set_ships(player_id, ships)
                    
                    if success:
                        self._send_response(client_socket, {"type": "ships_set"})
                    else:
                        self._send_error(client_socket, "Impossible de définir les navires")
                else:
                    self._send_error(client_socket, "Partie inexistante")
            else:
                self._send_error(client_socket, "Paramètres manquants")
        
        elif message_type == "disconnect":
            self._client_disconnected(client_socket)
    
    def _create_game(self, client_socket, player_id):
        """Crée une nouvelle partie"""
        # Vérifier si le nombre maximum de parties est atteint
        if len(self.games) >= MAX_GAMES:
            self._send_error(client_socket, "Nombre maximum de parties atteint")
            return
        
        # Générer un ID de partie unique
        game_id = self._generate_game_id()
        
        # Créer la partie
        game = Game(game_id)
        game.add_player(player_id, client_socket)
        self.games[game_id] = game
        
        # Mettre à jour les informations du client
        self.clients[client_socket]["game_id"] = game_id
        
        # Envoyer la confirmation
        self._send_response(client_socket, {
            "type": "game_created",
            "game_id": game_id,
            "player_id": player_id
        })
    
    def _create_ai_game(self, client_socket, player_id):
        """Crée une partie contre l'IA"""
        # Vérifier si le nombre maximum de parties est atteint
        if len(self.games) >= MAX_GAMES:
            self._send_error(client_socket, "Nombre maximum de parties atteint")
            return
        
        # Générer un ID de partie unique
        game_id = self._generate_game_id()
        
        # Créer la partie
        game = Game(game_id)
        game.add_player(player_id, client_socket)
        game.is_ai_game = True
        
        # Ajouter l'IA comme second joueur
        ai_id = self._generate_player_id()
        game.add_player(ai_id, None, "IA")
        
        # Marquer l'IA comme prête (les navires seront placés automatiquement côté serveur)
        game.set_player_ready(ai_id)
        
        self.games[game_id] = game
        
        # Mettre à jour les informations du client
        self.clients[client_socket]["game_id"] = game_id
        
        # Envoyer la confirmation
        self._send_response(client_socket, {
            "type": "game_created",
            "game_id": game_id,
            "player_id": player_id,
            "is_ai_game": True
        })
    
    def _join_game(self, client_socket, player_id, game_id):
        """Rejoint une partie existante"""
        if game_id in self.games:
            game = self.games[game_id]
            
            if game.state == "waiting" and len(game.players) < 2:
                # Ajouter le joueur à la partie
                if game.add_player(player_id, client_socket):
                    # Mettre à jour les informations du client
                    self.clients[client_socket]["game_id"] = game_id
                    
                    # Envoyer la confirmation
                    self._send_response(client_socket, {
                        "type": "game_joined",
                        "game_id": game_id,
                        "player_id": player_id
                    })
                    
                    # Notifier l'autre joueur
                    for pid, player in game.players.items():
                        if pid != player_id and player["socket"]:
                            game._send_to_player(pid, {
                                "type": "player_joined",
                                "player_id": player_id
                            })
                else:
                    self._send_error(client_socket, "Impossible de rejoindre la partie")
            else:
                self._send_error(client_socket, "Partie complète ou déjà commencée")
        else:
            self._send_error(client_socket, "Partie introuvable")
    
    def _client_disconnected(self, client_socket):
        """Gère la déconnexion d'un client"""
        if client_socket in self.clients:
            player_info = self.clients[client_socket]
            player_id = player_info["id"]
            game_id = player_info["game_id"]
            
            # Retirer le joueur de sa partie éventuelle
            if game_id and game_id in self.games:
                game = self.games[game_id]
                game.remove_player(player_id)
                
                # Notifier les autres joueurs de la déconnexion
                for pid, player in game.players.items():
                    if player["socket"]:
                        game._send_to_player(pid, {
                            "type": "player_disconnected",
                            "player_id": player_id
                        })
                
                # Supprimer la partie si elle est vide ou terminée
                if game.state == "finished" or not game.players:
                    del self.games[game_id]
            
            # Retirer le client de la liste
            del self.clients[client_socket]
            
            # Fermer la connexion
            try:
                client_socket.close()
            except Exception:
                pass
    
    def _send_response(self, client_socket, message):
        """Envoie une réponse à un client"""
        try:
            data = json.dumps(message).encode('utf-8')
            message_size = len(data).to_bytes(4, byteorder='big')
            client_socket.sendall(message_size + data)
        except Exception as e:
            print(f"Erreur d'envoi de réponse: {e}")
            self._client_disconnected(client_socket)
    
    def _send_error(self, client_socket, error_message):
        """Envoie un message d'erreur à un client"""
        self._send_response(client_socket, {
            "type": "error",
            "message": error_message
        })
    
    def _generate_player_id(self):
        """Génère un ID de joueur unique"""
        player_id = self.next_player_id
        self.next_player_id += 1
        return player_id
    
    def _generate_game_id(self):
        """Génère un ID de partie unique (code à 6 caractères)"""
        while True:
            # Générer un code de 6 caractères (lettres et chiffres)
            chars = string.ascii_uppercase + string.digits
            game_id = ''.join(random.choice(chars) for _ in range(6))
            
            # Vérifier qu'il n'existe pas déjà
            if game_id not in self.games:
                return game_id
    
    def _cleanup_inactive_games(self):
        """Nettoie périodiquement les parties inactives"""
        while self.running:
            time.sleep(60)  # Vérifier toutes les minutes
            
            for game_id in list(self.games.keys()):
                game = self.games[game_id]
                if not game.is_active():
                    print(f"Suppression de la partie inactive {game_id}")
                    
                    # Notifier les joueurs encore connectés
                    for player_id, player in game.players.items():
                        if player["socket"]:
                            game._send_to_player(player_id, {
                                "type": "game_timeout",
                                "game_id": game_id
                            })
                    
                    # Supprimer la partie
                    del self.games[game_id]

# Fonction principale pour démarrer le serveur
def start_server(host="0.0.0.0", port=DEFAULT_PORT):
    server = GameServer(host, port)
    server.start()

if __name__ == "__main__":
    start_server()

