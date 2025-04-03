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
        self.title_font = pygame.font.SysFont("Arial", 48, bold=True)  # Agrandi
        self.text_font = pygame.font.SysFont("Arial", 28)  # Agrandi
        self.small_font = pygame.font.SysFont("Arial", 22)  # Agrandi
        self.animation_font = pygame.font.SysFont("Impact", 84, bold=True)  # Agrandi
        
        # Calculer les positions des grilles pour centrage
        grid_width = CELL_SIZE * 10  # Taille d'une grille
        total_grids_width = grid_width * 2 + 200  # Deux grilles avec un espace entre elles
        grid_start_x = (SCREEN_WIDTH - total_grids_width) // 2
        
        # Coordonnées des grilles
        self.player_grid_pos = (grid_start_x, 150)
        self.opponent_grid_pos = (grid_start_x + grid_width + 200, 150)  # 200 pixels d'espace entre les grilles
        
        # Animation de message
        self.animated_text = AnimatedText(self.animation_font)
        
        # Barre de temps
        self.time_bar = ProgressBar((SCREEN_WIDTH // 2, 90), (600, 25), TURN_TIME, GRID_BLUE, DARK_BLUE)  # Agrandi
    
    def draw(self, screen, background_drawer):
        """Dessine l'écran de jeu"""
        # Fond animé de la mer
        background_drawer()
        
        # Titre avec effet d'ombre
        titre = self.title_font.render("BATTLESHIP TQ", True, WHITE)
        shadow = self.title_font.render("BATTLESHIP TQ", True, GRID_BLUE)
        screen.blit(shadow, (SCREEN_WIDTH // 2 - titre.get_width() // 2 + 2, 32))
        screen.blit(titre, (SCREEN_WIDTH // 2 - titre.get_width() // 2, 30))
        
        # Barre de temps pour le tour actuel
        remaining_time = self.game_manager.get_remaining_turn_time()
        self.time_bar.update(remaining_time)
        self.time_bar.draw(screen, remaining_time < TURN_TIME * 0.3)  # Animation quand moins de 30% du temps
        
        # Message indiquant le tour actuel
        turn_text = "Votre tour" if self.game_manager.current_player == "player" else "Tour de l'adversaire"
        turn_color = GREEN if self.game_manager.current_player == "player" else LIGHT_BLUE
        
        turn_info = self.text_font.render(turn_text, True, turn_color)
        screen.blit(turn_info, (SCREEN_WIDTH // 2 - turn_info.get_width() // 2, 120))
        
        # Afficher les grilles
        grid_y = 150
        self.game_manager.player.grid.draw(screen, self.player_grid_pos, True)  # Grille du joueur
        self.game_manager.opponent.grid.draw(screen, self.opponent_grid_pos, False)  # Grille de l'adversaire (tirs du joueur)
        
        # Créer un panneau d'information entre les grilles
        info_panel_x = self.player_grid_pos[0] + 10 * CELL_SIZE + 20  # Juste après la 1ère grille
        info_panel_width = self.opponent_grid_pos[0] - info_panel_x - 20  # Largeur disponible entre les grilles
        info_panel_height = 10 * CELL_SIZE  # Même hauteur que les grilles
        
        info_panel = pygame.Surface((info_panel_width, info_panel_height), pygame.SRCALPHA)
        info_panel.fill((0, 30, 60, 180))
        pygame.draw.rect(info_panel, GRID_BLUE, (0, 0, info_panel_width, info_panel_height), 2, 10)
        screen.blit(info_panel, (info_panel_x, grid_y))
        
        # Afficher des statistiques dans le panneau central
        stats_y = grid_y + 20
        
        # Statistiques du joueur
        player_stats = [
            ("Navires restants:", f"{self.game_manager.player.get_ships_left()}/{len(self.game_manager.player.grid.ships)}", GREEN),
            ("Navires coulés:", f"{self.game_manager.player.grid.get_sunk_ships_count()}/{len(self.game_manager.player.grid.ships)}", RED)
        ]
        
        # Statistiques de l'adversaire
        opponent_stats = [
            ("Navires restants:", f"{len(self.game_manager.opponent.grid.ships) - self.game_manager.opponent.grid.get_sunk_ships_count()}/{len(self.game_manager.opponent.grid.ships)}", GREEN),
            ("Navires coulés:", f"{self.game_manager.opponent.grid.get_sunk_ships_count()}/{len(self.game_manager.opponent.grid.ships)}", RED)
        ]
        
        # Afficher les stats du joueur
        panel_center_x = info_panel_x + info_panel_width // 2
        title_text = self.text_font.render("STATISTIQUES", True, WHITE)
        screen.blit(title_text, (panel_center_x - title_text.get_width() // 2, stats_y))
        
        stats_y += 50
        player_title = self.text_font.render("VOUS", True, GREEN)
        screen.blit(player_title, (panel_center_x - player_title.get_width() // 2, stats_y))
        
        stats_y += 40
        for i, (label, value, color) in enumerate(player_stats):
            label_text = self.small_font.render(label, True, WHITE)
            value_text = self.small_font.render(value, True, color)
            
            x_offset = panel_center_x - (label_text.get_width() + value_text.get_width() + 10) // 2
            screen.blit(label_text, (x_offset, stats_y + i * 30))
            screen.blit(value_text, (x_offset + label_text.get_width() + 10, stats_y + i * 30))
        
        stats_y += 80
        opponent_title = self.text_font.render("ADVERSAIRE", True, LIGHT_BLUE)
        screen.blit(opponent_title, (panel_center_x - opponent_title.get_width() // 2, stats_y))
        
        stats_y += 40
        for i, (label, value, color) in enumerate(opponent_stats):
            label_text = self.small_font.render(label, True, WHITE)
            value_text = self.small_font.render(value, True, color)
            
            x_offset = panel_center_x - (label_text.get_width() + value_text.get_width() + 10) // 2
            screen.blit(label_text, (x_offset, stats_y + i * 30))
            screen.blit(value_text, (x_offset + label_text.get_width() + 10, stats_y + i * 30))
        
        # Légendes des grilles
        grid_titles = [
            ("VOTRE FLOTTE", (self.player_grid_pos[0] + 5 * CELL_SIZE, grid_y - 40)),
            ("TIRS SUR L'ADVERSAIRE", (self.opponent_grid_pos[0] + 5 * CELL_SIZE, grid_y - 40))
        ]
        
        for texte, pos in grid_titles:
            # Halo
            title_text = self.text_font.render(texte, True, WHITE)
            halo_surf = pygame.Surface((title_text.get_width() + 20, title_text.get_height() + 10), pygame.SRCALPHA)
            halo_surf.fill((0, 30, 60, 160))
            pygame.draw.rect(halo_surf, GRID_BLUE, (0, 0, title_text.get_width() + 20, title_text.get_height() + 10), 2, 8)
            screen.blit(halo_surf, (pos[0] - title_text.get_width() // 2 - 10, pos[1] - title_text.get_height() // 2 - 5))
            
            # Texte
            screen.blit(title_text, (pos[0] - title_text.get_width() // 2, pos[1] - title_text.get_height() // 2))
        
        # Panneau inférieur avec légende
        info_panel_bottom = pygame.Surface((SCREEN_WIDTH - 100, 100), pygame.SRCALPHA)
        info_panel_bottom.fill((0, 20, 40, 180))
        pygame.draw.rect(info_panel_bottom, GRID_BLUE, (0, 0, SCREEN_WIDTH - 100, 100), 2, 12)
        screen.blit(info_panel_bottom, (50, SCREEN_HEIGHT - 120))
        
        # Légende
        legende_y = SCREEN_HEIGHT - 100
        screen.blit(self.text_font.render("Légende:", True, WHITE), (70, legende_y))
        
        # Icônes de légende avec espacement plus grand
        legende_items = [
            ("Navire", DARK_BLUE, (250, legende_y + 15)),
            ("Touché", RED, (450, legende_y + 15)),
            ("Manqué", WATER_BLUE, (650, legende_y + 15)),
            ("Non tiré", WHITE, (850, legende_y + 15))
        ]
        
        for texte, couleur, (x, y) in legende_items:
            # Fond pour l'échantillon
            pygame.draw.rect(screen, couleur, (x, y, 30, 30))
            pygame.draw.rect(screen, WHITE, (x, y, 30, 30), 1)
            
            # Texte
            txt = self.small_font.render(texte, True, WHITE)
            screen.blit(txt, (x + 40, y + 5))
        
        # Afficher le message animé s'il est actif
        if self.game_manager.is_message_active():
            self.animated_text.start_animation(self.game_manager.message, self.game_manager.message_color)
        
        self.animated_text.draw(screen, SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Vérifier si le tour est écoulé et afficher un avertissement
        if self.game_manager.get_remaining_turn_time() < 5000 and self.game_manager.current_player == "player":  # 5 secondes
            warning_text = self.text_font.render("Attention ! Plus que quelques secondes pour jouer !", True, (255, 100, 50))
            # Animation de pulsation pour l'avertissement
            scale = 1.0 + 0.1 * math.sin(time.time() * 10)
            warning_scaled = pygame.transform.scale(warning_text, 
                                                 (int(warning_text.get_width() * scale), 
                                                  int(warning_text.get_height() * scale)))
            screen.blit(warning_scaled, 
                       (SCREEN_WIDTH // 2 - warning_scaled.get_width() // 2, 
                        SCREEN_HEIGHT - 150))
        
        # En mode en ligne, afficher l'état de la connexion
        if self.game_manager.is_online and self.game_manager.network_client:
            connection_status = self.game_manager.network_client.connection_status
            status_color = (50, 255, 100) if "Connecté" in connection_status else (255, 100, 100)
            status_text = self.small_font.render(f"État réseau: {connection_status}", True, status_color)
            screen.blit(status_text, (SCREEN_WIDTH - status_text.get_width() - 20, 20))
    
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