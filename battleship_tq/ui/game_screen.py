# game_screen.py
import pygame
import math
import time
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GRID_BLUE, DARK_BLUE, LIGHT_BLUE,
    RED, GREEN, WATER_BLUE, TURN_TIME, JEU_SOLO, FIN_PARTIE, CELL_SIZE
)
from ui.ui_elements import Button, TextBox, ProgressBar, AnimatedText

class GameScreen:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        
        # Polices
        self.title_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 24)
        self.small_font = pygame.font.SysFont("Arial", 18)
        self.animation_font = pygame.font.SysFont("Impact", 64, bold=True)
        
        # Calculer les positions des grilles pour éviter le chevauchement
        self.calculate_grid_positions()
        
        # Animation de message
        self.animated_text = AnimatedText(self.animation_font)
        
        # Barre de temps
        self.time_bar = ProgressBar((SCREEN_WIDTH // 2, 50), (400, 20), TURN_TIME)
    
    def calculate_grid_positions(self):
        """Calcule les positions optimales des grilles pour éviter le chevauchement"""
        grid_width = CELL_SIZE * 10  # Taille d'une grille
        
        # Calculer la séparation minimale pour avoir suffisamment d'espace pour les labels et statistiques
        min_separation = 120
        
        # Vérifier si la fenêtre est assez large pour afficher les deux grilles côte à côte
        available_width = SCREEN_WIDTH - 120  # 60 pixels de marge de chaque côté
        
        if available_width >= (2 * grid_width + min_separation):
            # Cas standard: afficher les grilles côte à côte
            left_grid_x = (SCREEN_WIDTH - (2 * grid_width + min_separation)) // 2
            right_grid_x = left_grid_x + grid_width + min_separation
            
            self.player_grid_pos = (left_grid_x, 120)
            self.opponent_grid_pos = (right_grid_x, 120)
            
            # Position du panneau central
            self.center_panel_pos = (left_grid_x + grid_width, 120)
            self.center_panel_width = min_separation
            self.layout_type = "horizontal"
        else:
            # Si la fenêtre est trop étroite, ajuster pour une mise en page plus compacte
            # Utiliser toute la largeur disponible
            margin = 40
            grid_spacing = (SCREEN_WIDTH - 2 * margin - 2 * grid_width) // 3
            
            self.player_grid_pos = (margin + grid_spacing, 120)
            self.opponent_grid_pos = (SCREEN_WIDTH - margin - grid_spacing - grid_width, 120)
            
            # Panneau central plus étroit
            self.center_panel_pos = (SCREEN_WIDTH // 2 - 50, 120)
            self.center_panel_width = 100
            self.layout_type = "compact"
    
    def draw(self, screen, background_drawer):
        """Dessine l'écran de jeu"""
        # Fond animé de la mer
        background_drawer()
        
        # Titre
        titre = self.title_font.render("BATTLESHIP TQ", True, WHITE)
        shadow = self.title_font.render("BATTLESHIP TQ", True, GRID_BLUE)
        screen.blit(shadow, (SCREEN_WIDTH // 2 - titre.get_width() // 2 + 2, 22))
        screen.blit(titre, (SCREEN_WIDTH // 2 - titre.get_width() // 2, 20))
        
        # Barre de temps pour le tour actuel
        remaining_time = self.game_manager.get_remaining_turn_time()
        self.time_bar.update(remaining_time)
        self.time_bar.draw(screen, remaining_time < TURN_TIME * 0.3)
        
        # Message indiquant le tour actuel
        turn_text = "Votre tour" if self.game_manager.current_player == "player" else "Tour de l'adversaire"
        turn_color = GREEN if self.game_manager.current_player == "player" else LIGHT_BLUE
        
        turn_info = self.text_font.render(turn_text, True, turn_color)
        screen.blit(turn_info, (SCREEN_WIDTH // 2 - turn_info.get_width() // 2, 75))
        
        # Afficher les grilles
        grid_y = 120
        self.game_manager.player.grid.draw(screen, self.player_grid_pos, True)  # Grille du joueur
        self.game_manager.opponent.grid.draw(screen, self.opponent_grid_pos, False)  # Grille de l'adversaire
        
        # Légendes des grilles
        grid_titles = [
            ("VOTRE FLOTTE", (self.player_grid_pos[0] + 5 * CELL_SIZE, grid_y - 40)),
            ("TIRS SUR L'ADVERSAIRE", (self.opponent_grid_pos[0] + 5 * CELL_SIZE, grid_y - 40))
        ]
        
        for texte, pos in grid_titles:
            # Panel de fond pour le titre
            title_text = self.text_font.render(texte, True, WHITE)
            panel_width = title_text.get_width() + 20
            panel_height = title_text.get_height() + 10
            
            title_panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
            title_panel.fill((0, 30, 60, 180))
            pygame.draw.rect(title_panel, GRID_BLUE, (0, 0, panel_width, panel_height), 2, 5)
            
            screen.blit(title_panel, (pos[0] - panel_width // 2, pos[1] - panel_height // 2))
            screen.blit(title_text, (pos[0] - title_text.get_width() // 2, pos[1] - title_text.get_height() // 2))
        
        # Statistiques sous chaque grille
        self._draw_statistics(screen)
        
        # Panneau inférieur avec légende
        bottom_panel_y = grid_y + 10 * CELL_SIZE + 30
        
        # Vérifier si l'espace est suffisant pour le panneau inférieur
        if bottom_panel_y + 80 < SCREEN_HEIGHT - 20:
            info_panel = pygame.Surface((SCREEN_WIDTH - 80, 70), pygame.SRCALPHA)
            info_panel.fill((0, 20, 40, 180))
            pygame.draw.rect(info_panel, GRID_BLUE, (0, 0, SCREEN_WIDTH - 80, 70), 2, 10)
            screen.blit(info_panel, (40, bottom_panel_y))
            
            # Légende
            legende_y = bottom_panel_y + 10
            screen.blit(self.text_font.render("Légende:", True, WHITE), (60, legende_y))
            
            # Icônes de légende
            legende_items = [
                ("Navire", WHITE, (220, legende_y + 10)),
                ("Touché", RED, (350, legende_y + 10)),
                ("Manqué", WATER_BLUE, (480, legende_y + 10)),
                ("En attente", YELLOW, (610, legende_y + 10))
            ]
            
            for texte, couleur, (x, y) in legende_items:
                # Carré de couleur
                pygame.draw.rect(screen, couleur, (x, y, 20, 20), 0 if texte != "Manqué" else 2)
                
                # Texte
                txt = self.small_font.render(texte, True, WHITE)
                screen.blit(txt, (x + 30, y + 2))
        
        # Afficher le message animé s'il est actif
        if self.game_manager.is_message_active():
            self.animated_text.start_animation(self.game_manager.message, self.game_manager.message_color)
        
        self.animated_text.draw(screen, SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Vérifier si le tour est écoulé et afficher un avertissement
        if self.game_manager.get_remaining_turn_time() < 5000 and self.game_manager.current_player == "player":
            warning_text = self.small_font.render("Attention ! Plus que quelques secondes pour jouer !", True, (255, 100, 50))
            screen.blit(warning_text, (SCREEN_WIDTH // 2 - warning_text.get_width() // 2, SCREEN_HEIGHT - 50))
        
        # En mode en ligne, afficher l'état de la connexion
        if self.game_manager.is_online and self.game_manager.network_client:
            connection_status = self.game_manager.network_client.connection_status
            status_color = (50, 255, 100) if "Connecté" in connection_status else (255, 100, 100)
            status_text = self.small_font.render(f"État: {connection_status}", True, status_color)
            screen.blit(status_text, (SCREEN_WIDTH - status_text.get_width() - 10, 10))
    
    def _draw_statistics(self, screen):
        """Dessine les statistiques de jeu sous chaque grille"""
        # Position verticale des statistiques
        stats_y = self.player_grid_pos[1] + 10 * CELL_SIZE + 10
        
        # Statistiques du joueur
        player_stats = [
            (f"Restants: {self.game_manager.player.get_ships_left()}/{len(self.game_manager.player.grid.ships)}", GREEN),
            (f"Coulés: {self.game_manager.player.grid.get_sunk_ships_count()}/{len(self.game_manager.player.grid.ships)}", RED)
        ]
        
        # Statistiques de l'adversaire
        opponent_stats = [
            (f"Restants: {len(self.game_manager.opponent.grid.ships) - self.game_manager.opponent.grid.get_sunk_ships_count()}/{len(self.game_manager.opponent.grid.ships)}", GREEN),
            (f"Coulés: {self.game_manager.opponent.grid.get_sunk_ships_count()}/{len(self.game_manager.opponent.grid.ships)}", RED)
        ]
        
        # Panneaux de statistiques
        self._draw_stats_panel(screen, "VOTRE FLOTTE", player_stats, 
                             (self.player_grid_pos[0] + 5 * CELL_SIZE, stats_y))
        
        self._draw_stats_panel(screen, "FLOTTE ENNEMIE", opponent_stats, 
                             (self.opponent_grid_pos[0] + 5 * CELL_SIZE, stats_y))
    
    def _draw_stats_panel(self, screen, title, stats, position):
        """Dessine un panneau de statistiques"""
        x, y = position
        
        # Taille du panneau
        panel_width = 200
        panel_height = 70
        
        # Fond du panneau
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((0, 30, 60, 180))
        pygame.draw.rect(panel, GRID_BLUE, (0, 0, panel_width, panel_height), 1, 5)
        
        # Positions
        title_y = 10
        stats_y = 35
        
        # Titre
        title_text = self.small_font.render(title, True, WHITE)
        panel.blit(title_text, (panel_width // 2 - title_text.get_width() // 2, title_y))
        
        # Stats
        for i, (text, color) in enumerate(stats):
            stat_text = self.small_font.render(text, True, color)
            panel.blit(stat_text, (panel_width // 2 - stat_text.get_width() // 2, stats_y + i * 20))
        
        # Afficher le panneau
        screen.blit(panel, (x - panel_width // 2, y))
    
    def handle_event(self, event):
        """Gère les événements de l'écran de jeu"""
        # Si le jeu est terminé, passer à l'écran de fin
        if self.game_manager.game_state == "game_over":
            return FIN_PARTIE
        
        # Ne pas permettre d'action pendant l'affichage d'un message
        if self.game_manager.is_message_active() or self.animated_text.is_active():
            return JEU_SOLO
        
        # Si c'est le tour du joueur
        if self.game_manager.current_player == "player":
            # Clic pour tirer
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                grid_x, grid_y = self.opponent_grid_pos
                
                # Vérifier si le clic est dans la grille de l'adversaire
                grid_width = grid_height = 10 * CELL_SIZE
                
                if (grid_x <= mouse_pos[0] < grid_x + grid_width and 
                    grid_y <= mouse_pos[1] < grid_y + grid_height):
                    # Convertir les coordonnées en indices de grille
                    col = (mouse_pos[0] - grid_x) // CELL_SIZE
                    row = (mouse_pos[1] - grid_y) // CELL_SIZE
                    
                    # Effectuer le tir
                    self.game_manager.process_player_shot(row, col)
        
        # Si c'est le tour de l'IA et que c'est un jeu solo
        if self.game_manager.current_player == "opponent" and not self.game_manager.is_online:
            # L'IA joue automatiquement après un court délai
            pygame.time.delay(500)  # Pause de 500ms
            self.game_manager.process_ai_turn()
        
        # Vérifier si le temps du tour est écoulé
        self.game_manager.check_turn_timeout()
        
        return JEU_SOLO if not self.game_manager.is_online else "jeu_online"
    
    def update(self):
        """Met à jour les éléments de l'écran de jeu"""
        # Mettre à jour l'animation de message
        if not self.animated_text.is_active() and self.game_manager.is_message_active():
            self.animated_text.start_animation(self.game_manager.message, self.game_manager.message_color)