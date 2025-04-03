# client.py
import socket
import threading
import json
import random
import string
import logging
import time

class NetworkClient:
    """Client réseau pour le jeu de bataille navale"""
    
    ERROR_CODES = {
        'NOT_FOUND': "Code de partie invalide",
        'FULL': "La partie est déjà complète",
        'IN_PROGRESS': "La partie est déjà en cours",
        'NETWORK_ERROR': "Erreur de connexion réseau",
        'CONNECTION_REFUSED': "Connexion refusée par l'hôte",
        'TIMEOUT': "Délai de connexion dépassé"
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
        self.receiver_thread = None
        self.running = False
        self.cleanup_lock = threading.Lock()  # Verrou pour les opérations de nettoyage
        
        # Configuration du logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger('NetworkClient')
        self.logger.info("Nouveau client réseau initialisé")
    
    def _get_local_ip(self):
        """Obtient l'adresse IP locale"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération de l'IP locale: {e}")
            return 'localhost'
    
    def generate_game_code(self):
        """Génère un code de partie unique basé sur l'IP"""
        try:
            # Utiliser l'IP locale pour générer un code plus facile à reconnaître
            ip_parts = self.host.split('.')
            
            # S'assurer que nous avons assez de parties d'IP
            while len(ip_parts) < 4:
                ip_parts.append("00")
            
            # Prendre les deux premiers caractères de chaque partie de l'IP pour les 3 premières parties
            # Format: XX-XX-XX-XX où XX sont des caractères de l'IP, sauf la dernière partie qui est aléatoire
            code_parts = []
            
            # Pour les 3 premières parties, utiliser l'IP
            for i in range(3):
                # Prendre 2 chiffres de l'IP (avec padding si nécessaire)
                part = ip_parts[i].zfill(2)[:2]
                code_parts.append(part)
            
            # Pour la dernière partie, générer des caractères aléatoires
            chars = string.ascii_uppercase + string.digits
            random_part = ''.join(random.choice(chars) for _ in range(2))
            code_parts.append(random_part)
            
            # Joindre les parties avec des tirets
            game_code = '-'.join(code_parts)
            
            self.logger.info(f"Code de partie généré: {game_code} pour l'IP {self.host}")
            return game_code
        except Exception as e:
            self.logger.error(f"Erreur lors de la génération du code de partie: {e}")
            # En cas d'erreur, générer un code entièrement aléatoire
            code_parts = []
            chars = string.ascii_uppercase + string.digits
            for _ in range(4):
                code_parts.append(''.join(random.choice(chars) for _ in range(2)))
            return '-'.join(code_parts)
    
    def create_game(self):
        """Crée une partie en attente"""
        try:
            # Fermer toute connexion existante
            self.disconnect()
            
            # Générer un code de partie unique
            self.game_code = self.generate_game_code()
            
            # Créer un socket serveur
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            self.server_socket.settimeout(1.0)  # Timeout pour permettre de quitter proprement
            
            self.is_host = True
            self.connection_status = "En attente de connexion"
            self.running = True
            
            # Thread pour attendre la connexion du client
            self.connection_thread = threading.Thread(target=self._wait_for_connection)
            self.connection_thread.daemon = True
            self.connection_thread.start()
            
            self.logger.info(f"Partie créée avec le code {self.game_code} sur {self.host}:{self.port}")
            return self.game_code
        except Exception as e:
            self.logger.error(f"Erreur de création de partie: {e}")
            self.connection_status = f"Erreur de création: {e}"
            return None
    
    def _wait_for_connection(self):
        """Thread d'attente de connexion pour l'hôte"""
        try:
            self.logger.info("En attente de connexion client...")
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    self.logger.info(f"Connexion acceptée de {client_address}")
                    
                    with self.cleanup_lock:  # Protection pour les modifications critiques
                        # Vérifier la connexion
                        self.socket = client_socket
                        self.connected = True
                        self.connection_status = f"Connecté à {client_address[0]}"
                        
                        # Démarrer le thread de réception des messages
                        self._start_receiver_thread()
                        
                        # Signaler la connexion réussie
                        self.connection_event.set()
                    break
                except socket.timeout:
                    # Simple timeout, continuer à attendre
                    continue
                except Exception as e:
                    if self.running:
                        self.logger.error(f"Erreur d'attente de connexion: {e}")
                        self.connection_status = f"Erreur de connexion: {e}"
                        self.connection_event.set()
                        break
        except Exception as e:
            if self.running:
                self.logger.error(f"Erreur dans le thread d'attente: {e}")
                self.connection_status = f"Erreur de connexion: {e}"
                self.connection_event.set()
    
    def _extract_ip_from_code(self, game_code):
        """Extrait une adresse IP partielle du code de partie"""
        try:
            # Format attendu: XX-XX-XX-XX ou XX-XX-XX-
            parts = game_code.split('-')
            
            # Vérifier si nous avons au moins 3 parties (nécessaires pour l'extraction IP)
            if len(parts) < 3:
                self.logger.error(f"Format de code incorrect pour extraction IP: {game_code}")
                return None
            
            # Vérifier que les parties principales ont 2 caractères
            for i in range(3):  # Vérifier les 3 premières parties
                if i < len(parts) and len(parts[i]) != 2:
                    self.logger.error(f"Partie {i+1} du code incorrect: {parts[i]}")
                    return None
            
            # Récupérer les segments d'IP (approximatif)
            # On considère que la première partie est généralement 192 pour les réseaux locaux privés
            first_segment = "192"  # Valeur par défaut pour les réseaux locaux courants
            
            # On peut aussi essayer de détecter si on est dans d'autres types de réseaux privés
            local_ip = self._get_local_ip()
            if local_ip.startswith("10."):
                first_segment = "10"
            elif local_ip.startswith("172."):
                first_segment = "172"
                
            ip_parts = [first_segment]
            
            # Ajouter les segments basés sur le code
            # Le code XX-XX-XX représente les octets partiels
            for i in range(3):
                if i < len(parts):
                    # Convertir en valeur numérique si possible
                    try:
                        # Si c'est numérique, utiliser directement
                        val = int(parts[i])
                        ip_parts.append(str(val))
                    except ValueError:
                        # Sinon, baser sur la valeur ASCII des caractères
                        # Convertir les lettres/chiffres en valeurs numériques (simple hachage)
                        char_sum = sum(ord(c) for c in parts[i]) % 255
                        ip_parts.append(str(char_sum))
            
            # Construire l'adresse IP approximative (les 3 premiers octets)
            # Le dernier octet sera scanné dans la méthode _scan_local_network
            base_ip = '.'.join(ip_parts[:3])
            
            self.logger.info(f"IP base extraite du code: {base_ip}")
            return base_ip
        except Exception as e:
            self.logger.error(f"Erreur lors de l'extraction de l'IP depuis le code: {e}")
            return None
    
    def _scan_local_network(self, base_ip, game_code):
        """Analyse le réseau local pour trouver l'hôte du jeu"""
        self.logger.info(f"Recherche de l'hôte sur le réseau local avec base IP: {base_ip}")
        
        # Si l'utilisateur a fourni l'IP directement
        if socket.gethostbyname_ex(socket.gethostname())[2]:
            local_ips = socket.gethostbyname_ex(socket.gethostname())[2]
            self.logger.info(f"IPs locales détectées: {local_ips}")
        
        # Examen des 255 dernières adresses possibles (dernier octet)
        found_ip = None
        for i in range(1, 255):
            ip = f"{base_ip}.{i}"
            try:
                # Tenter une connexion rapide pour voir si le port est ouvert
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_socket.settimeout(0.05)  # Timeout court
                result = test_socket.connect_ex((ip, self.port))
                test_socket.close()
                
                if result == 0:
                    # Le port est ouvert, tenter de vérifier le code de partie
                    self.logger.info(f"Port ouvert trouvé sur {ip}:{self.port}")
                    found_ip = ip
                    break
            except Exception:
                continue
        
        return found_ip
    
    def join_game(self, game_code, server_host=None):
        """Rejoint une partie via son code"""
        try:
            # S'assurer que nous sommes déconnectés de toute session précédente
            self.disconnect()
            
            # Validation et normalisation du code
            if not game_code:
                self.logger.warning("Code de partie vide")
                return False, 'NOT_FOUND'
            
            # Normaliser le format du code (gestion des formats partiels)
            parts = game_code.split('-')
            
            # Vérifier si le code a au moins 3 parties (nécessaire pour extraction IP)
            if len(parts) < 3:
                self.logger.warning(f"Format de code invalide (nombre de parties insuffisant): {game_code}")
                return False, 'NOT_FOUND'
            
            # Vérifier que les parties principales ont 2 caractères
            if any(len(part) != 2 for part in parts[:3]):
                self.logger.warning(f"Format de code invalide (longueur des parties): {game_code}")
                return False, 'NOT_FOUND'
            
            # Ajouter la quatrième partie si nécessaire
            normalized_code = game_code
            if len(parts) == 3:
                # Ajouter un tiret final pour signaler la quatrième partie
                normalized_code += "-"
            
            # Utiliser le code normalisé
            self.game_code = normalized_code
            
            # Si l'hôte n'est pas spécifié, essayer de le déterminer depuis le code
            if not server_host:
                base_ip = self._extract_ip_from_code(normalized_code)
                if not base_ip:
                    self.logger.error(f"Impossible d'extraire l'IP du code: {normalized_code}")
                    return False, 'NOT_FOUND'
                
                server_host = self._scan_local_network(base_ip, normalized_code)
                if not server_host:
                    self.logger.error(f"Hôte non trouvé sur le réseau pour le code: {normalized_code}")
                    return False, 'NOT_FOUND'
            
            self.logger.info(f"Tentative de connexion à l'hôte: {server_host}:{self.port}")
            
            # Créer une connexion
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5.0)  # 5 secondes de timeout
            try:
                self.socket.connect((server_host, self.port))
            except ConnectionRefusedError:
                self.logger.error(f"Connexion refusée par {server_host}:{self.port}")
                return False, 'CONNECTION_REFUSED'
            except socket.timeout:
                self.logger.error(f"Délai de connexion dépassé pour {server_host}:{self.port}")
                return False, 'TIMEOUT'
            
            # Établir la connexion
            with self.cleanup_lock:  # Protection pour les modifications critiques
                self.game_code = normalized_code
                self.is_host = False
                self.connected = True
                self.connection_status = f"Connecté à {server_host}"
                self.running = True
                
                # Démarrer le thread de réception des messages
                self._start_receiver_thread()
            
            self.logger.info(f"Connecté avec succès à la partie: {normalized_code}")
            return True, None
        except Exception as e:
            self.logger.error(f"Erreur de connexion: {e}")
            self.connection_status = f"Erreur de connexion: {e}"
            return False, 'NETWORK_ERROR'
    
    def _start_receiver_thread(self):
        """Démarre le thread de réception des messages"""
        if self.receiver_thread and self.receiver_thread.is_alive():
            return
        
        self.running = True
        self.receiver_thread = threading.Thread(target=self._message_receiver)
        self.receiver_thread.daemon = True
        self.receiver_thread.start()
    
    def _message_receiver(self):
        """Thread de réception des messages"""
        self.logger.info("Thread de réception démarré")
        buffer = ""
        
        while self.running and self.connected:
            try:
                # Recevoir des données
                data = self.socket.recv(1024)
                if not data:
                    self.logger.warning("Connexion fermée par l'hôte distant")
                    break
                
                # Ajouter au buffer et traiter les messages complets
                buffer += data.decode('utf-8')
                
                # Traiter chaque message terminé par un saut de ligne
                while '\n' in buffer:
                    message_str, buffer = buffer.split('\n', 1)
                    try:
                        message = json.loads(message_str)
                        # Appeler le callback si défini
                        if self.message_callback:
                            self.message_callback(message)
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Erreur de décodage JSON: {e}")
            except (ConnectionResetError, ConnectionAbortedError, ConnectionRefusedError):
                self.logger.warning("Connexion réinitialisée ou interrompue")
                break
            except socket.timeout:
                # Simple timeout, continuer
                continue
            except Exception as e:
                self.logger.error(f"Erreur de réception: {e}")
                break
        
        # Fermer proprement en cas d'erreur
        if self.connected:
            self.logger.info("Fermeture de la connexion depuis le thread de réception")
            self.disconnect()
    
    def wait_for_connection(self, timeout=None):
        """Attend la connexion avec un timeout optionnel"""
        return self.connection_event.wait(timeout)
    
    def send_message(self, message):
        """Envoie un message au serveur"""
        if not self.connected:
            self.logger.warning("Tentative d'envoi alors que non connecté")
            return False
        
        try:
            encoded_message = json.dumps(message).encode('utf-8')
            self.socket.sendall(encoded_message + b'\n')
            return True
        except Exception as e:
            self.logger.error(f"Erreur d'envoi: {e}")
            self.disconnect()
            return False
    
    def receive_message(self):
        """Reçoit un message du serveur (méthode synchrone - à éviter)"""
        if not self.connected:
            return None
        
        try:
            data = self.socket.recv(1024).decode('utf-8')
            return json.loads(data) if data else None
        except Exception as e:
            self.logger.error(f"Erreur de réception synchrone: {e}")
            self.disconnect()
            return None
    
    def set_message_callback(self, callback):
        """Définit un callback pour les messages entrants"""
        self.message_callback = callback
    
    def disconnect(self):
        """Ferme la connexion"""
        with self.cleanup_lock:  # Protection pour les opérations critiques
            # D'abord marquer comme non actif pour arrêter les threads
            self.running = False
            self.connected = False
            self.connection_status = "Déconnecté"
            
            # Fermer le socket client
            if self.socket:
                try:
                    self.socket.shutdown(socket.SHUT_RDWR)
                except:
                    pass  # Ignorer les erreurs si déjà fermé
                    
                try:
                    self.socket.close()
                except Exception as e:
                    self.logger.error(f"Erreur lors de la fermeture du socket: {e}")
                self.socket = None
            
            # Fermer le socket serveur
            if self.server_socket:
                try:
                    self.server_socket.close()
                except Exception as e:
                    self.logger.error(f"Erreur lors de la fermeture du socket serveur: {e}")
                self.server_socket = None
            
            # Réinitialiser les états
            self.game_code = None
            self.is_host = False
            self.connection_event.clear()
            
            # Attendre un peu pour laisser les threads se terminer
            time.sleep(0.1)
            
            self.logger.info("Déconnexion complète effectuée")
        
    def is_connected(self):
        """Vérifie si le client est connecté"""
        return self.connected