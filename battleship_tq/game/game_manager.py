# game_manager.py
import random
import time
import pygame
import logging
import json
from game.constants import (
    PLACEMENT_TIME, TURN_TIME, MESSAGE_DURATION, 
    FACILE, MOYEN, DIFFICILE, NAVIRES
)
from game.player import Player
from game.ai_player import AIPlayer
from game.ship import Ship

# Configuration des logs
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

class GameManager:
    def __init__(self):
        self.player = Player("Joueur")
        self.opponent = None
        self.is_online = False
        self.network_client = None  # Référence au client réseau
        self.current_player = None  # "player" ou "opponent"
        self.game_state = "waiting"  # "waiting", "placement", "playing", "game_over"
        self.message = ""
        self.message_color = (255, 255, 255)
        self.message_start_time = 0
        self.placement_start_time = 0
        self.turn_start_time = 0
        self.winner = None
        self.difficulty = MOYEN
        self.last_network_message = None
    
    def start_solo_game(self, difficulty=MOYEN):
        """Démarre une partie solo contre un bot"""
        logging.info(f"Démarrage d'une partie solo - Difficulté : {difficulty}")
        # Réinitialiser le mode de jeu
        self.is_online = False
        self.network_client = None  # Important: libérer la référence au client réseau
        
        self.difficulty = difficulty
        self.opponent = AIPlayer(difficulty)
        self.player.reset()
        self.game_state = "placement"
        self.placement_start_time = pygame.time.get_ticks()
        self.message = ""
        self.winner = None
    
    def start_online_game(self, opponent_name="Adversaire"):
        """Démarre une partie en ligne"""
        logging.info(f"Démarrage d'une partie en ligne contre {opponent_name}")
        
        # Réinitialiser le jeu
        self.is_online = True
        
        # Créer un joueur opposant
        self.opponent = Player(opponent_name)
        
        # Réinitialiser le joueur
        self.player.reset()
        
        # Passer à l'état de placement des navires
        self.game_state = "placement"
        self.placement_start_time = pygame.time.get_ticks()
        
        # Réinitialiser les messages
        self.message = ""
        self.winner = None
        
        # Configurer le client réseau
        if self.network_client:
            # Définir le callback pour les messages réseau
            if hasattr(self.network_client, 'set_message_callback'):
                self.network_client.set_message_callback(self._handle_network_message)
            else:
                # Utiliser directement l'attribut message_callback
                self.network_client.message_callback = self._handle_network_message
            
            # Déterminer qui commence - basé sur qui est l'hôte, pas sur my_turn qui peut être désynchronisé
            if hasattr(self.network_client, 'is_host') and self.network_client.is_host:
                # L'hôte commence toujours
                self.current_player = "player"
                if hasattr(self.network_client, 'my_turn'):
                    self.network_client.my_turn = True
                logging.info("Hôte - Le joueur commence")
            else:
                # Le client ne commence jamais
                self.current_player = "opponent"
                if hasattr(self.network_client, 'my_turn'):
                    self.network_client.my_turn = False
                logging.info("Client - L'adversaire commence")
                
    def start_game(self):
        """Démarre la partie après le placement des navires"""
        logging.info("Démarrage de la partie après placement des navires")
        
        # Vérifier si les deux joueurs sont prêts
        if not self.player.ready:
            # Placement aléatoire des navires restants du joueur
            self._auto_place_player_ships()
        
        if isinstance(self.opponent, AIPlayer):
            # Pour le mode solo, placer les navires du bot
            bot_ships = [Ship(name, size) for name, size in NAVIRES.items()]
            self.opponent.place_ships(self.opponent.grid, bot_ships)
        
        # Déterminer aléatoirement qui commence en mode solo
        if not self.is_online:
            self.current_player = random.choice(["player", "opponent"])
        else:
            # En mode en ligne, on conserve la détermination faite dans start_online_game
            # Envoyer un message de début de jeu pour s'assurer que les deux clients sont synchronisés
            if hasattr(self.network_client, 'is_host') and self.network_client.is_host:
                self._send_game_start()
        
        self.game_state = "playing"
        self.turn_start_time = pygame.time.get_ticks()
        
        logging.info(f"Début de la partie - Joueur actuel : {self.current_player}")
        return self.current_player
    
    def _auto_place_player_ships(self):
        """Place automatiquement les navires restants du joueur"""
        logging.info("Placement automatique des navires du joueur")
        current_ship = self.player.get_current_ship()
        while current_ship:
            placed = False
            for _ in range(100):  # Essayer 100 fois maximum pour éviter les boucles infinies
                orientation = random.choice(['H', 'V'])
                current_ship.orientation = orientation
                
                if orientation == 'H':
                    row = random.randint(0, 9)
                    col = random.randint(0, 10 - current_ship.size)
                else:
                    row = random.randint(0, 10 - current_ship.size)
                    col = random.randint(0, 9)
                
                if self.player.place_current_ship(row, col, orientation):
                    placed = True
                    break
            
            if not placed:
                # Si après 100 essais on n'a pas pu placer le navire
                logging.warning(f"Impossible de placer le navire {current_ship.name}")
                self.player.current_ship_index += 1
            
            current_ship = self.player.get_current_ship()
        
        self.player.ready = True
    
    def process_player_shot(self, row, col):
        """Traite un tir du joueur humain"""
        logging.info(f"Tir du joueur en position ({row}, {col})")
        
        if self.game_state != "playing" or self.current_player != "player":
            logging.warning("Tir invalide - Pas le tour du joueur")
            return False, ""
        
        if pygame.time.get_ticks() - self.message_start_time < MESSAGE_DURATION:
            logging.warning("Tir invalide - Message actif")
            return False, "message_active"
        
        # Mode en ligne
        if self.is_online:
            # Vérifier si la case a déjà été tirée
            if self.opponent.grid.shots[row][col] != ' ':
                return False, "already_shot"
            
            # Marquer le tir localement avant d'envoyer
            self.opponent.grid.shots[row][col] = '?'  # Marquage temporaire

            # Créer le message de tir
            shot_message = {
                'type': 'shot',
                'row': row,
                'col': col
            }
            
            # Envoyer le tir à l'adversaire
            if self.network_client:
                sent_successfully = False
                
                # Essayer différentes méthodes d'envoi possibles
                if hasattr(self.network_client, 'send_message'):
                    try:
                        self.network_client.send_message(shot_message)
                        sent_successfully = True
                    except Exception as e:
                        logging.error(f"Erreur lors de l'envoi avec send_message: {e}")
                    
                # Si la méthode précédente n'existe pas ou a échoué, essayer send
                if not sent_successfully and hasattr(self.network_client, 'send'):
                    try:
                        self.network_client.send(shot_message)
                        sent_successfully = True
                    except Exception as e:
                        logging.error(f"Erreur lors de l'envoi avec send: {e}")
                
                # Si nous avons un attribut send_move, essayons-le
                if not sent_successfully and hasattr(self.network_client, 'send_move'):
                    try:
                        self.network_client.send_move((row, col))
                        sent_successfully = True
                    except Exception as e:
                        logging.error(f"Erreur lors de l'envoi avec send_move: {e}")
                
                if sent_successfully:
                    logging.info(f"Tir envoyé en ({row}, {col})")
                    
                    # Marquer que ce n'est plus notre tour de façon très claire
                    self.current_player = "opponent"
                    if hasattr(self.network_client, 'my_turn'):
                        self.network_client.my_turn = False
                        logging.info("Tour passé à l'adversaire")
                    
                    # Mettre à jour la barre de temps
                    self.turn_start_time = pygame.time.get_ticks()
                    
                    # Envoyer explicitement un message de changement de tour
                    self._send_turn_change()
                    
                    # Afficher un message pour indiquer qu'on a tiré
                    self.show_message("Tir effectué, attente du résultat...", (200, 200, 200))
                    
                    return True, "wait_response"
                else:
                    logging.error("Aucune méthode d'envoi de message fonctionnelle trouvée")
                    # Annuler le marquage temporaire
                    self.opponent.grid.shots[row][col] = ' '
                    return False, "network_error"
            else:
                logging.error("Erreur: Client réseau non disponible")
                # Annuler le marquage temporaire
                self.opponent.grid.shots[row][col] = ' '
                return False, "network_error"
        
        # Mode solo (code existant)
        result = self.player.make_shot(self.opponent.grid, row, col)
        
        if result == "already_shot" or result == "invalid":
            logging.warning(f"Tir invalide - {result}")
            return False, result
        
        # Afficher le message approprié
        if result == "hit":
            self.show_message("TOUCHÉ!", (255, 165, 0))
        elif result == "miss":
            self.show_message("MANQUÉ!", (135, 206, 250))
        elif result == "sunk":
            self.show_message("COULÉ!", (255, 50, 50))
        
        # Vérifier si le jeu est terminé
        if self.opponent.grid.are_all_ships_sunk():
            logging.info("Partie terminée - Joueur gagnant")
            self.game_state = "game_over"
            self.winner = "player"
            return True, "game_over"
        
        # Passer au tour de l'adversaire
        self.current_player = "opponent"
        self.turn_start_time = pygame.time.get_ticks()
        
        return True, result
    
    def process_ai_turn(self):
        """Exécute le tour de l'IA"""
        logging.info("Tour de l'IA")
        
        if self.game_state != "playing" or self.current_player != "opponent" or not isinstance(self.opponent, AIPlayer):
            logging.warning("Tour de l'IA invalide")
            return False, ""
        
        if pygame.time.get_ticks() - self.message_start_time < MESSAGE_DURATION:
            logging.warning("Tir de l'IA impossible - Message actif")
            return False, "message_active"
        
        # L'IA fait son tir
        row, col = self.opponent.make_shot(self.player.grid)
        result = self.player.grid.receive_shot(row, col)
        
        # Informer l'IA du résultat pour adapter sa stratégie
        self.opponent.process_shot_result(result, row, col)
        
        # Afficher le message approprié
        if result == "hit":
            self.show_message("TOUCHÉ!", (255, 165, 0))
        elif result == "miss":
            self.show_message("MANQUÉ!", (135, 206, 250))
        elif result == "sunk":
            self.show_message("COULÉ!", (255, 50, 50))
        
        # Vérifier si le jeu est terminé
        if self.player.grid.are_all_ships_sunk():
            logging.info("Partie terminée - IA gagnante")
            self.game_state = "game_over"
            self.winner = "opponent"
            return True, "game_over"
        
        # Passer au tour du joueur
        self.current_player = "player"
        self.turn_start_time = pygame.time.get_ticks()
        
        return True, result
    
    def _handle_network_message(self, message):
        """Gère les messages réseau reçus"""
        logging.info(f"Message réseau reçu: {message}")
        self.last_network_message = message
        
        # S'il s'agit d'un message "move" (format utilisé par battleship_connection.py)
        if isinstance(message, dict) and "move" in message:
            # Convertir au format attendu par notre logique
            row, col = message["move"]
            message = {
                'type': 'shot',
                'row': row,
                'col': col
            }
            logging.info(f"Message converti de format 'move' à format 'shot': {message}")
        
        # Traiter différents types de messages
        if isinstance(message, dict):
            message_type = message.get('type', '')
            
            if message_type == 'shot':
                row, col = message.get('row'), message.get('col')
                logging.info(f"Tir reçu de l'adversaire: ({row}, {col})")
                
                # Appliquer le tir sur notre grille
                result = self.player.grid.receive_shot(row, col)
                
                # Envoyer le résultat du tir
                self._send_shot_result(result, row, col)
                
                # Afficher le message approprié
                if result == "hit":
                    self.show_message("TOUCHÉ!", (255, 165, 0))
                elif result == "miss":
                    self.show_message("MANQUÉ!", (135, 206, 250))
                elif result == "sunk":
                    self.show_message("COULÉ!", (255, 50, 50))
                
                # Vérifier si le jeu est terminé
                if self.player.grid.are_all_ships_sunk():
                    logging.info("Partie terminée - Adversaire gagnant")
                    self.game_state = "game_over"
                    self.winner = "opponent"
                    
                    # Informer l'adversaire de la victoire
                    self._send_game_over("opponent")
                else:
                    # Passer le tour au joueur et envoyer une confirmation explicite
                    self.current_player = "player"
                    if self.network_client:
                        self.network_client.my_turn = True
                        logging.info("Mon tour activé suite à un tir adversaire")
                    self.turn_start_time = pygame.time.get_ticks()
                    # Pas besoin d'envoyer de confirmation, le résultat du tir sert de confirmation
            
            elif message_type == 'shot_result':
                result = message.get('result')
                row, col = message.get('row'), message.get('col')
                logging.info(f"Résultat du tir: {result} à ({row}, {col})")
                
                # Mettre à jour notre grille de tirs
                if result == "hit":
                    self.opponent.grid.shots[row][col] = 'X'
                    self.show_message("TOUCHÉ!", (255, 165, 0))
                elif result == "miss":
                    self.opponent.grid.shots[row][col] = 'O'
                    self.show_message("MANQUÉ!", (135, 206, 250))
                elif result == "sunk":
                    self.opponent.grid.shots[row][col] = 'X'
                    self.show_message("COULÉ!", (255, 50, 50))
                    
                    # Vérifier si tous les navires sont coulés
                    # Notez que cela suppose une logique côté serveur pour suivre les navires coulés
                    if message.get('all_sunk', False):
                        logging.info("Tous les navires adverses coulés - Victoire du joueur")
                        self.game_state = "game_over"
                        self.winner = "player"
                        return
                
                # Après un résultat de tir, c'est toujours le tour de l'adversaire
                # Ne pas changer l'état du tour ici, cela sera géré par turn_change
            
            elif message_type == 'turn_change':
                next_player = message.get('next_player')
                logging.info(f"Message de changement de tour reçu, prochain joueur: {next_player}")
                
                # Mettre à jour le tour en fonction du message
                if next_player == 'player':
                    self.current_player = "player"
                    if self.network_client:
                        self.network_client.my_turn = True
                    logging.info("C'est maintenant mon tour (message explicite)")
                elif next_player == 'opponent':
                    self.current_player = "opponent"
                    if self.network_client:
                        self.network_client.my_turn = False
                    logging.info("C'est maintenant le tour de l'adversaire (message explicite)")
            
            elif message_type == 'game_start':
                logging.info("Message de début de partie reçu")
                # Le client (non-hôte) reçoit ce message et confirme que c'est à l'hôte de commencer
                if not (hasattr(self.network_client, 'is_host') and self.network_client.is_host):
                    self.current_player = "opponent"
                    if self.network_client:
                        self.network_client.my_turn = False
                    logging.info("Tour initial: c'est l'hôte qui commence")
            
            elif message_type == 'game_over':
                winner = message.get('winner')
                logging.info(f"Message de fin de partie reçu: {winner}")
                
                self.game_state = "game_over"
                self.winner = winner
                
                # S'assurer que le client sait que la partie est terminée
                if self.network_client:
                    self.network_client.is_match_active = False
        else:
            logging.warning(f"Message reçu dans un format inconnu: {message}")
    
    def _send_shot(self, row, col):
        """Envoie un message de tir à l'adversaire"""
        if not self.is_online or not self.network_client:
            return False
        
        message = {
            'type': 'shot',
            'row': row,
            'col': col
        }
        
        sent_successfully = False
        
        # Essayer différentes méthodes d'envoi possibles
        if hasattr(self.network_client, 'send_message'):
            try:
                self.network_client.send_message(message)
                sent_successfully = True
            except Exception as e:
                logging.error(f"Erreur lors de l'envoi avec send_message: {e}")
        
        if not sent_successfully and hasattr(self.network_client, 'send'):
            try:
                self.network_client.send(message)
                sent_successfully = True
            except Exception as e:
                logging.error(f"Erreur lors de l'envoi avec send: {e}")
        
        if not sent_successfully and hasattr(self.network_client, 'send_move'):
            try:
                self.network_client.send_move((row, col))
                sent_successfully = True
            except Exception as e:
                logging.error(f"Erreur lors de l'envoi avec send_move: {e}")
        
        if sent_successfully:
            logging.info(f"Message de tir envoyé: ({row}, {col})")
            return True
        else:
            logging.error("Aucune méthode d'envoi de message fonctionnelle trouvée")
            return False
    
    def _send_shot_result(self, result, row, col):
        """Envoie le résultat d'un tir à l'adversaire"""
        if not self.is_online or not self.network_client:
            return False
        
        message = {
            'type': 'shot_result',
            'result': result,
            'row': row,
            'col': col,
            'your_turn': True  # Indique explicitement que c'est maintenant le tour de l'adversaire
        }
        
        sent_successfully = False
        
        # Essayer différentes méthodes d'envoi possibles
        if hasattr(self.network_client, 'send_message'):
            try:
                self.network_client.send_message(message)
                sent_successfully = True
            except Exception as e:
                logging.error(f"Erreur lors de l'envoi avec send_message: {e}")
        
        if not sent_successfully and hasattr(self.network_client, 'send'):
            try:
                self.network_client.send(message)
                sent_successfully = True
            except Exception as e:
                logging.error(f"Erreur lors de l'envoi avec send: {e}")
        
        if sent_successfully:
            logging.info(f"Résultat de tir envoyé: {result} à ({row}, {col})")
            
            # Après avoir envoyé le résultat, passer explicitement le tour au joueur adverse
            self._send_turn_change(next_player='player')
            
            return True
        else:
            logging.error("Aucune méthode d'envoi de message fonctionnelle trouvée")
            return False
    
    def _send_turn_change(self, next_player='opponent'):
        """Envoie un message pour signaler le changement de tour"""
        if not self.is_online or not self.network_client:
            return False
        
        message = {
            'type': 'turn_change',
            'next_player': next_player  # 'player' ou 'opponent'
        }
        
        sent_successfully = False
        
        # Essayer différentes méthodes d'envoi possibles
        if hasattr(self.network_client, 'send_message'):
            try:
                self.network_client.send_message(message)
                sent_successfully = True
            except Exception as e:
                logging.error(f"Erreur lors de l'envoi du changement de tour: {e}")
        
        if not sent_successfully and hasattr(self.network_client, 'send'):
            try:
                self.network_client.send(message)
                sent_successfully = True
            except Exception as e:
                logging.error(f"Erreur lors de l'envoi du changement de tour: {e}")
        
        if sent_successfully:
            logging.info(f"Message de changement de tour envoyé, prochain joueur: {next_player}")
            return True
        else:
            logging.error("Échec de l'envoi du message de changement de tour")
            return False
    
    def _send_game_start(self):
        """Envoie un message pour signaler le début de la partie"""
        if not self.is_online or not self.network_client:
            return False
        
        message = {
            'type': 'game_start',
            'host_starts': True
        }
        
        sent_successfully = False
        
        # Essayer différentes méthodes d'envoi possibles
        if hasattr(self.network_client, 'send_message'):
            try:
                self.network_client.send_message(message)
                sent_successfully = True
            except Exception as e:
                logging.error(f"Erreur lors de l'envoi du message de début de partie: {e}")
        
        if not sent_successfully and hasattr(self.network_client, 'send'):
            try:
                self.network_client.send(message)
                sent_successfully = True
            except Exception as e:
                logging.error(f"Erreur lors de l'envoi du message de début de partie: {e}")
        
        if sent_successfully:
            logging.info("Message de début de partie envoyé")
            return True
        else:
            logging.error("Échec de l'envoi du message de début de partie")
            return False
    
    def _send_game_over(self, winner):
        """Envoie un message de fin de partie à l'adversaire"""
        if not self.is_online or not self.network_client:
            return False
        
        message = {
            'type': 'game_over',
            'winner': winner
        }
        
        sent_successfully = False
        
        # Essayer différentes méthodes d'envoi possibles
        if hasattr(self.network_client, 'send_message'):
            try:
                self.network_client.send_message(message)
                sent_successfully = True
            except Exception as e:
                logging.error(f"Erreur lors de l'envoi avec send_message: {e}")
        
        if not sent_successfully and hasattr(self.network_client, 'send'):
            try:
                self.network_client.send(message)
                sent_successfully = True
            except Exception as e:
                logging.error(f"Erreur lors de l'envoi avec send: {e}")
        
        if sent_successfully:
            logging.info(f"Message de fin de partie envoyé, gagnant: {winner}")
            return True
        else:
            logging.error("Aucune méthode d'envoi de message fonctionnelle trouvée")
            return False
    
    def check_turn_timeout(self):
        """Vérifie si le temps du tour actuel est écoulé"""
        if self.game_state != "playing":
            return False
        
        current_time = pygame.time.get_ticks()
        
        if current_time - self.turn_start_time > TURN_TIME:
            # Exécuter un coup aléatoire pour le joueur qui a dépassé le temps
            if self.current_player == "player":
                # Trouver une case non ciblée aléatoirement
                valid_shots = []
                for row in range(10):
                    for col in range(10):
                        if self.opponent.grid.shots[row][col] == ' ':
                            valid_shots.append((row, col))
                
                if valid_shots:
                    row, col = random.choice(valid_shots)
                    self.process_player_shot(row, col)
            else:
                # L'IA joue automatiquement
                if isinstance(self.opponent, AIPlayer):
                    self.process_ai_turn()
                elif self.is_online:
                    # En mode réseau, on passe simplement au tour du joueur après timeout
                    self.current_player = "player"
                    if hasattr(self.network_client, 'my_turn'):
                        self.network_client.my_turn = True
                    self.turn_start_time = pygame.time.get_ticks()
                    self.show_message("Tour passé - Temps écoulé", (255, 100, 100))
                    # Informer l'adversaire du changement de tour
                    self._send_turn_change(next_player='player')
            
            return True
        
        return False
    
    def check_placement_timeout(self):
        """Vérifie si le temps de placement est écoulé"""
        if self.game_state != "placement":
            return False
        
        current_time = pygame.time.get_ticks()
        
        if current_time - self.placement_start_time > PLACEMENT_TIME:
            # Placement automatique des navires restants
            self.start_game()
            return True
        
        return False
    
    def show_message(self, message, color=(255, 255, 255)):
        """Affiche un message temporaire"""
        logging.info(f"Message affiché : {message}")
        self.message = message
        self.message_color = color
        self.message_start_time = pygame.time.get_ticks()
    
    def get_remaining_placement_time(self):
        """Retourne le temps restant pour le placement des navires"""
        if self.game_state != "placement":
            return 0
        
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.placement_start_time
        remaining = max(0, PLACEMENT_TIME - elapsed)
        
        return remaining
    
    def get_remaining_turn_time(self):
        """Retourne le temps restant pour le tour actuel"""
        if self.game_state != "playing":
            return 0
        
        current_time = pygame.time.get_ticks()
        elapsed = current_time - self.turn_start_time
        remaining = max(0, TURN_TIME - elapsed)
        
        return remaining
    
    def is_message_active(self):
        """Vérifie si un message est actuellement affiché"""
        current_time = pygame.time.get_ticks()
        return current_time - self.message_start_time < MESSAGE_DURATION
    
    def cleanup_network(self):
        """Nettoie les ressources réseau"""
        logging.info("Nettoyage des ressources réseau")
        if self.network_client:
            try:
                self.network_client.disconnect()
                logging.info("Client réseau déconnecté")
            except Exception as e:
                logging.error(f"Erreur lors de la déconnexion réseau: {e}")
            self.network_client = None