import socket
import threading
import requests
import json
import time

class BattleshipConnection:
    def __init__(self, username, port, matchmaking_url):
        self.username = username
        self.port = port
        self.matchmaking_url = matchmaking_url
        self.opponent = None
        self.match_code = None
        self.is_match_active = False
        self.my_turn = False  # Indicateur pour savoir si c'est le tour du joueur
        self.game_board = {}  # Pour suivre les positions des navires et les tirs
        self.moves = []  # Liste des coups effectués
        self.winner = None
        self.message_callback = None
        self.is_host = False
        self.socket = None
        self.last_network_message = None
        
        # Automatically register with the server
        self.auto_register()

    def auto_register(self):
        """Auto-register the player with the server"""
        try:
            print(f"Tentative d'enregistrement de {self.username} sur {self.matchmaking_url}...")
            response = requests.post(f"{self.matchmaking_url}/auto_join", json={
                "username": self.username, 
                "port": self.port
            })
            if response.status_code == 200:
                print(f"✅ {self.username} enregistré sur le serveur.")
                return True
            else:
                print(f"❌ Impossible de s'enregistrer sur le serveur: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Erreur de connexion au serveur: {e}")
            return False

    def create_match(self, match_code):
        """Create a new match with the given code"""
        try:
            print(f"Création d'un match avec le code: {match_code}")
            response = requests.post(f"{self.matchmaking_url}/create_match", json={
                "player_id": self.username,
                "code": match_code
            })
            print(f"Réponse: {response.status_code} - {response.text}")
            
            if response.status_code == 200:
                self.match_code = match_code
                self.is_host = True
                print(f"✅ Match créé avec le code {match_code}. En attente d'un adversaire...")
                
                # Polling pour vérifier si quelqu'un a rejoint
                for _ in range(60):  # 60 secondes maximum d'attente
                    time.sleep(1)
                    try:
                        status_response = requests.get(f"{self.matchmaking_url}/match_status", params={"code": match_code})
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            print(f"Statut du match: {status_data}")
                            
                            if status_data.get("status") == "active":
                                self.opponent = status_data.get("opponent")
                                self.is_match_active = True
                                self.my_turn = False  # Le créateur joue en second
                                print(f"✅ {self.opponent} a rejoint le match!")
                                return True
                    except Exception as e:
                        print(f"Erreur lors de la vérification du statut: {e}")
                
                print("⌛ Délai d'attente dépassé, aucun adversaire n'a rejoint.")
                return False
            else:
                print(f"❌ Impossible de créer le match: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Erreur lors de la création du match: {e}")
            return False

    def propose_match(self, target_username, match_code=None):
        """Propose a match to another player"""
        if not match_code:
            match_code = f"{self.username}_{int(time.time())}"
            
        data = {
            "from": self.username,
            "to": target_username,
            "code": match_code
        }

        try:
            print(f"Envoi d'une proposition de match à {target_username} avec le code {match_code}...")
            response = requests.post(f"{self.matchmaking_url}/propose_match", json=data)
            print(f"Réponse: {response.status_code} - {response.text}")
            
            if response.status_code == 200:
                print(f"📨 Demande de match envoyée à {target_username}.")
                self.match_code = match_code
                self.opponent = target_username
                self.is_host = True
                
                # Attendre que l'adversaire accepte
                print("En attente de confirmation...")
                for _ in range(30):  # 30 secondes maximum
                    time.sleep(1)
                    # Vérifier si le match est actif 
                    # (Cette logique peut être améliorée avec un endpoint spécifique)
                    try:
                        match_response = requests.get(f"{self.matchmaking_url}/match_status", 
                                                   params={"code": match_code})
                        if match_response.status_code == 200:
                            match_data = match_response.json()
                            if match_data.get("status") == "active":
                                self.is_match_active = True
                                print(f"✅ {target_username} a accepté le match!")
                                return True
                    except Exception as e:
                        print(f"Erreur lors de la vérification du statut: {e}")
                        
                print("⌛ Délai d'attente dépassé. Pas de réponse.")
                return False
            else:
                print(f"❌ Impossible d'envoyer la demande de match: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Erreur d'envoi de la demande: {e}")
            return False

    def join_match(self, match_code):
        """Join a match with the provided code"""
        try:
            print(f"Tentative de rejoindre le match avec le code: {match_code}")
            response = requests.post(f"{self.matchmaking_url}/join_match", json={
                "player_id": self.username, 
                "code": match_code
            })
            
            print(f"Réponse du serveur: Code {response.status_code}")
            print(f"Contenu de la réponse: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                players = data.get('players', [])
                if len(players) == 2:
                    self.opponent = players[0] if players[1] == self.username else players[1]
                    print(f"✅ Match rejoint avec le code {match_code}. Adversaire: {self.opponent}.")
                    self.match_code = match_code
                    self.is_match_active = True
                    self.is_host = False
                    self.my_turn = True  # Le joueur qui rejoint commence
                    return True
                else:
                    print(f"⚠️ Format de réponse inattendu: {data}")
                    return False
            else:
                print(f"❌ Impossible de rejoindre le match: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Erreur de connexion au match: {e}")
            return False

    def start_socket_listener(self):
        """Start listening for game messages from the opponent"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server_socket.bind(("0.0.0.0", self.port))
            server_socket.listen(1)
            server_socket.settimeout(1.0)  # Timeout pour vérifier régulièrement l'état du match
            
            print(f"🔍 Écoute sur le port {self.port} pour les coups adverses...")
            
            while self.is_match_active and not self.winner:
                try:
                    conn, addr = server_socket.accept()
                    data = conn.recv(1024).decode()
                    conn.close()
                    
                    if data:
                        self.handle_opponent_move(data)
                        self.my_turn = True  # C'est à nouveau notre tour
                except socket.timeout:
                    continue  # Continuer la boucle en cas de timeout
                except Exception as e:
                    print(f"⚠️ Erreur de réception: {e}")
        except Exception as e:
            print(f"❌ Erreur d'initialisation du socket: {e}")
        finally:
            server_socket.close()
            print("Socket d'écoute fermé.")

    def send_move(self, move):
        """Send a move to the opponent via their server"""
        if not self.opponent:
            print("⚠️ Aucun adversaire connu.")
            return False
            
        try:
            # Récupérer la liste des joueurs pour trouver l'IP et le port de l'adversaire
            print(f"Récupération des informations sur l'adversaire {self.opponent}...")
            r = requests.get(f"{self.matchmaking_url}/players")
            if r.status_code != 200:
                print(f"❌ Impossible de récupérer la liste des joueurs: {r.text}")
                return False
                
            players = r.json()
            print(f"Joueurs connectés: {len(players)}")
            for p in players:
                print(f"- {p.get('username')}: {p.get('ip')}:{p.get('port')}")
                
            target = next((p for p in players if p.get("username") == self.opponent), None)
            
            if not target:
                print(f"❌ Adversaire '{self.opponent}' introuvable dans la liste des joueurs.")
                return False
                
            ip, port = target.get("ip"), int(target.get("port"))
            print(f"Envoi du coup à {self.opponent} ({ip}:{port})...")
            
            # Envoyer le coup
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(5.0)  # 5 secondes de timeout
            client_socket.connect((ip, port))
            client_socket.send(json.dumps({"move": list(move)}).encode())
            client_socket.close()
            
            print(f"🎯 Coup envoyé en {move}")
            return True
        except Exception as e:
            print(f"❌ Erreur d'envoi du coup: {e}")
            return False

    def handle_opponent_move(self, data):
        """Handle the opponent's move"""
        try:
            move_data = json.loads(data)
            move = tuple(move_data["move"])
            print(f"📥 Coup reçu: {move}")
            
            # Mettre à jour le plateau de jeu
            self.update_game_board(move, opponent=True)
            
            # Si un callback de message est défini, on l'appelle
            if self.message_callback:
                self.message_callback(move_data)
                
        except Exception as e:
            print(f"❌ Erreur de traitement du coup adverse: {e}")

    def update_game_board(self, move, opponent=False):
        """Update the game board with the given move"""
        if opponent:
            # L'adversaire a joué sur notre grille
            if self.game_board.get(move) == "SHIP":
                self.game_board[move] = "HIT"
                print(f"💥 TOUCHÉ en {move} !")
            else:
                self.game_board[move] = "MISS"
                print(f"💦 MANQUÉ en {move}")
        else:
            # On place un navire ou on joue sur la grille adverse
            self.game_board[move] = "SHIP"
            print(f"🚢 Navire placé en {move}")
        
        self.moves.append(move)
        self.check_victory()

    def check_victory(self):
        """Check if the game is won"""
        hits = [pos for pos, val in self.game_board.items() if val == "HIT"]
        ships = [pos for pos, val in self.game_board.items() if val == "SHIP"]
        
        # Si on a 3 navires touchés, l'adversaire gagne
        if len(hits) >= 3:
            self.winner = self.opponent
            self.end_game()
            return True
            
        return False

    def start_game(self):
        """Start the game after both players are ready"""
        if not self.is_match_active:
            print("⚠️ Aucun match actif.")
            return False
            
        # Démarrer le thread d'écoute des coups adverses
        listener_thread = threading.Thread(target=self.start_socket_listener)
        listener_thread.daemon = True
        listener_thread.start()
        
        print(f"🎮 Partie démarrée contre {self.opponent}.")
        return True

    def end_game(self):
        """End the game and record the result"""
        if not self.winner:
            print("⚠️ Fin de partie sans gagnant.")
            return False
            
        loser = self.username if self.winner == self.opponent else self.opponent
        
        try:
            print(f"Envoi du résultat au serveur: {self.winner} a gagné contre {loser}")
            response = requests.post(f"{self.matchmaking_url}/match_result", json={
                "winner": self.winner,
                "loser": loser
            })
            
            if response.status_code == 200:
                print(f"🏆 Résultat enregistré: {self.winner} a gagné !")
                self.is_match_active = False
                return True
            else:
                print(f"❌ Impossible d'enregistrer le résultat: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Erreur d'enregistrement du résultat: {e}")
            return False
    
    def set_message_callback(self, callback):
        """Définit un callback pour les messages entrants (pour compatibilité avec NetworkClient)"""
        print(f"Définition du callback de message: {callback}")
        self.message_callback = callback
    
    def send_message(self, message):
        """Send a message to the server (for compatibility with NetworkClient)"""
        print(f"Tentative d'envoi de message (compatibilité): {message}")
        # Cette fonction existe pour la compatibilité avec le code existant
        return True
    
    # Modification à apporter à network/battleship_connection.py
# Ajouter la propriété connection_status pour compatibilité

class BattleshipConnection:
    def __init__(self, username, port, matchmaking_url):
        self.username = username
        self.port = port
        self.matchmaking_url = matchmaking_url
        self.opponent = None
        self.match_code = None
        self.is_match_active = False
        self.my_turn = False  # Indicateur pour savoir si c'est le tour du joueur
        self.game_board = {}  # Pour suivre les positions des navires et les tirs
        self.moves = []  # Liste des coups effectués
        self.winner = None
        self.message_callback = None
        self.is_host = False
        self.socket = None
        self.last_network_message = None
        # Ajout d'une propriété connection_status pour compatibilité avec NetworkClient
        self.connection_status = "Non connecté"
        
        # Automatically register with the server
        self.auto_register()
        
    # Après auto_register, ajouter cette mise à jour du statut
    def auto_register(self):
        """Auto-register the player with the server"""
        try:
            print(f"Tentative d'enregistrement de {self.username} sur {self.matchmaking_url}...")
            response = requests.post(f"{self.matchmaking_url}/auto_join", json={
                "username": self.username, 
                "port": self.port
            })
            if response.status_code == 200:
                print(f"✅ {self.username} enregistré sur le serveur.")
                self.connection_status = "Connecté au serveur"
                return True
            else:
                print(f"❌ Impossible de s'enregistrer sur le serveur: {response.text}")
                self.connection_status = f"Erreur d'enregistrement: {response.text}"
                return False
        except Exception as e:
            print(f"❌ Erreur de connexion au serveur: {e}")
            self.connection_status = f"Erreur de connexion: {e}"
            return False
            
    # Mettre à jour les méthodes qui modifient l'état de la connexion
    def create_match(self, match_code):
        """Create a new match with the given code"""
        try:
            print(f"Création d'un match avec le code: {match_code}")
            self.connection_status = "Création d'un match..."
            response = requests.post(f"{self.matchmaking_url}/create_match", json={
                "player_id": self.username,
                "code": match_code
            })
            print(f"Réponse: {response.status_code} - {response.text}")
            
            if response.status_code == 200:
                self.match_code = match_code
                self.is_host = True
                self.connection_status = f"Match créé avec le code {match_code}. En attente d'un adversaire..."
                print(f"✅ Match créé avec le code {match_code}. En attente d'un adversaire...")
                
                # Polling pour vérifier si quelqu'un a rejoint
                for _ in range(60):  # 60 secondes maximum d'attente
                    time.sleep(1)
                    try:
                        status_response = requests.get(f"{self.matchmaking_url}/match_status", params={"code": match_code})
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            print(f"Statut du match: {status_data}")
                            
                            if status_data.get("status") == "active":
                                self.opponent = status_data.get("opponent")
                                self.is_match_active = True
                                self.my_turn = self.is_host  # Le créateur commence
                                self.connection_status = f"Connecté à {self.opponent}"
                                print(f"✅ {self.opponent} a rejoint le match!")
                                return True
                    except Exception as e:
                        print(f"Erreur lors de la vérification du statut: {e}")
                
                self.connection_status = "Délai d'attente dépassé, aucun adversaire n'a rejoint."
                print("⌛ Délai d'attente dépassé, aucun adversaire n'a rejoint.")
                return False
            else:
                self.connection_status = f"Erreur: {response.text}"
                print(f"❌ Impossible de créer le match: {response.text}")
                return False
        except Exception as e:
            self.connection_status = f"Erreur: {str(e)}"
            print(f"❌ Erreur lors de la création du match: {e}")
            return False

    def join_match(self, match_code):
        """Join a match with the provided code"""
        try:
            print(f"Tentative de rejoindre le match avec le code: {match_code}")
            self.connection_status = "Tentative de rejoindre le match..."
            response = requests.post(f"{self.matchmaking_url}/join_match", json={
                "player_id": self.username, 
                "code": match_code
            })
            
            print(f"Réponse du serveur: Code {response.status_code}")
            print(f"Contenu de la réponse: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                players = data.get('players', [])
                if len(players) == 2:
                    self.opponent = players[0] if players[1] == self.username else players[1]
                    self.connection_status = f"Connecté à {self.opponent}"
                    print(f"✅ Match rejoint avec le code {match_code}. Adversaire: {self.opponent}.")
                    self.match_code = match_code
                    self.is_match_active = True
                    self.is_host = False
                    self.my_turn = not self.is_host  # Celui qui rejoint commence en second
                    return True
                else:
                    self.connection_status = "Format de réponse inattendu"
                    print(f"⚠️ Format de réponse inattendu: {data}")
                    return False
            else:
                self.connection_status = f"Erreur: {response.text}"
                print(f"❌ Impossible de rejoindre le match: {response.text}")
                return False
        except Exception as e:
            self.connection_status = f"Erreur: {str(e)}"
            print(f"❌ Erreur de connexion au match: {e}")
            return False
            
    def disconnect(self):
        """Disconnect from the server (for compatibility with NetworkClient)"""
        print("Déconnexion du serveur...")
        self.connection_status = "Déconnexion..."
        self.is_match_active = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        # Notifier le serveur de la déconnexion
        try:
            requests.post(f"{self.matchmaking_url}/disconnect", json={"username": self.username})
            self.connection_status = "Déconnecté"
            print("✅ Déconnexion réussie")
        except Exception as e:
            self.connection_status = f"Erreur de déconnexion: {str(e)}"
            print(f"⚠️ Erreur lors de la notification de déconnexion: {e}")
    
    def set_message_callback(self, callback):
        """Définit un callback pour les messages entrants"""
        print(f"Définition du callback de message pour BattleshipConnection")
        self.message_callback = callback
