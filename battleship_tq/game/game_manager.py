# game_manager.py
import random
import time
import pygame
from game.constants import (PLACEMENT_TIME, TURN_TIME, MESSAGE_DURATION, 
                           FACILE, MOYEN, DIFFICILE, NAVIRES)
from game.player import Player
from game.ai_player import AIPlayer
from game.ship import Ship

class GameManager:
    def __init__(self):
        self.player = Player("Joueur")
        self.opponent = None
        self.is_online = False
        self.current_player = None  # "player" ou "opponent"
        self.game_state = "waiting"  # "waiting", "placement", "playing", "game_over"
        self.message = ""
        self.message_color = (255, 255, 255)
        self.message_start_time = 0
        self.placement_start_time = 0
        self.turn_start_time = 0
        self.winner = None
        self.difficulty = MOYEN
    
    def start_solo_game(self, difficulty=MOYEN):
        """Démarre une partie solo contre un bot"""
        self.is_online = False
        self.difficulty = difficulty
        self.opponent = AIPlayer(difficulty)
        self.player.reset()
        self.game_state = "placement"
        self.placement_start_time = pygame.time.get_ticks()
        self.message = ""
        self.winner = None
    
    def start_online_game(self, opponent_name="Adversaire"):
        """Démarre une partie en ligne"""
        self.is_online = True
        self.opponent = Player(opponent_name)
        self.player.reset()
        self.game_state = "placement"
        self.placement_start_time = pygame.time.get_ticks()
        self.message = ""
        self.winner = None
    
    def start_game(self):
        """Démarre la partie après le placement des navires"""
        # Vérifier si les deux joueurs sont prêts
        if not self.player.ready:
            # Placement aléatoire des navires restants du joueur
            self._auto_place_player_ships()
        
        if isinstance(self.opponent, AIPlayer):
            # Pour le mode solo, placer les navires du bot
            bot_ships = [Ship(name, size) for name, size in NAVIRES.items()]
            self.opponent.place_ships(self.opponent.grid, bot_ships)
        
        # Déterminer aléatoirement qui commence
        self.current_player = random.choice(["player", "opponent"])
        self.game_state = "playing"
        self.turn_start_time = pygame.time.get_ticks()
        
        return self.current_player
    
    def _auto_place_player_ships(self):
        """Place automatiquement les navires restants du joueur"""
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
                # Si après 100 essais on n'a pas pu placer le navire, c'est qu'il y a un problème
                # Réinitialiser la grille pourrait être une solution, mais ici on va juste ignorer ce navire
                self.player.current_ship_index += 1
            
            current_ship = self.player.get_current_ship()
        
        self.player.ready = True
    
    def process_player_shot(self, row, col):
        """Traite un tir du joueur humain"""
        if self.game_state != "playing" or self.current_player != "player":
            return False, ""
        
        if pygame.time.get_ticks() - self.message_start_time < MESSAGE_DURATION:
            return False, "message_active"  # Ne pas permettre d'action pendant l'affichage d'un message
        
        result = self.player.make_shot(self.opponent.grid, row, col)
        
        if result == "already_shot" or result == "invalid":
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
            self.game_state = "game_over"
            self.winner = "player"
            return True, "game_over"
        
        # Passer au tour de l'adversaire
        self.current_player = "opponent"
        self.turn_start_time = pygame.time.get_ticks()
        
        return True, result
    
    def process_ai_turn(self):
        """Exécute le tour de l'IA"""
        if self.game_state != "playing" or self.current_player != "opponent" or not isinstance(self.opponent, AIPlayer):
            return False, ""
        
        if pygame.time.get_ticks() - self.message_start_time < MESSAGE_DURATION:
            return False, "message_active"  # Ne pas permettre d'action pendant l'affichage d'un message
        
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
            self.game_state = "game_over"
            self.winner = "opponent"
            return True, "game_over"
        
        # Passer au tour du joueur
        self.current_player = "player"
        self.turn_start_time = pygame.time.get_ticks()
        
        return True, result
    
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
                self.process_ai_turn()
            
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

