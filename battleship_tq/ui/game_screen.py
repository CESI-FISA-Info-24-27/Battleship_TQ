# game_screen.py
import pygame
import math
import time
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GRID_BLUE, DARK_BLUE, LIGHT_BLUE,
    RED, GREEN, WATER_BLUE, TURN_TIME, JEU_SOLO, FIN_PARTIE
)
from ui.ui_elements import Button, TextBox, ProgressBar, AnimatedText

class GameScreen:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        
        # Polices
        self.title_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 24)
        self.small_font = pygame.font.SysFont("Arial", 18)
        self.animation_font = pygame.font.SysFont("Impact", 72, bold=True)
        
        # Coordonnées des grilles
        self.player_grid_pos = (150, 120)
        self.opponent_grid_pos = (SCREEN_WIDTH - 150 - 10 * 40, 120)  # 40 = CELL_SIZE
        
        # Animation de message
        self.animated_text = AnimatedText(self.animation_font)
        
        # Barre de temps
        self.time_bar = ProgressBar((SCREEN_WIDTH // 2, 70), (400, 20), TURN_TIME)
    
    def draw(self, screen, background_drawer):
        """Dessine l'écran de jeu"""
        # Fond animé de la mer
        background_drawer()
        
        # Titre
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
        screen.blit(turn_info, (SCREEN_WIDTH // 2 - turn_info.get_width() // 2, 90))
        
        # Afficher les grilles
        grid_y = 120
        self.game_manager.player.grid.draw(screen, self.player_grid_pos, True)  # Grille du joueur
        self.game_manager.opponent.grid.draw(screen, self.opponent_grid_pos, False)  # Grille de l'adversaire (tirs du joueur)
        
        # Légendes des grilles avec effet de halo
        for texte, pos in [
            ("Votre flotte", (150 + 200, grid_y - 30)),  # 200 = GRID_WIDTH / 2
            ("Tirs sur l'adversaire", (SCREEN_WIDTH - 150 - 200, grid_y - 30))
        ]:
            # Halo
            halo_surf = pygame.Surface((320, 40), pygame.SRCALPHA)
            halo_surf.fill((0, 30, 60, 160))
            pygame.draw.rect(halo_surf, GRID_BLUE, (0, 0, 320, 40), 2, 8)
            screen.blit(halo_surf, (pos[0] - 160, pos[1] - 20))
            
            # Texte
            txt = self.text_font.render(texte, True, WHITE)
            screen.blit(txt, (pos[0] - txt.get_width() // 2, pos[1] - txt.get_height() // 2))
        
        # Panneau inférieur avec légende et statistiques
        info_panel = pygame.Surface((SCREEN_WIDTH - 100, 150), pygame.SRCALPHA)
        info_panel.fill((0, 20, 40, 180))
        pygame.draw.rect(info_panel, GRID_BLUE, (0, 0, SCREEN_WIDTH - 100, 150), 2, 12)
        screen.blit(info_panel, (50, grid_y + 400 + 20))  # 400 = GRID_HEIGHT
        
        # Légende
        legende_y = grid_y + 400 + 35
        screen.blit(self.text_font.render("Légende:", True, WHITE), (70, legende_y))
        
        # Icônes de légende
        legende_items = [
            ("Navire", DARK_BLUE, (200, legende_y)),
            ("Touché", RED, (350, legende_y)),
            ("Manqué", WATER_BLUE, (500, legende_y))
        ]
        
        for texte, couleur, (x, y) in legende_items:
            # Fond pour l'échantillon
            pygame.draw.rect(screen, couleur, (x, y, 20, 20))
            pygame.draw.rect(screen, WHITE, (x, y, 20, 20), 1)
            
            # Texte
            txt = self.small_font.render(texte, True, WHITE)
            screen.blit(txt, (x + 30, y + 2))
        
        # Statistiques avec animation de nombre
        stats_y = legende_y + 50
        
        # Cadres pour les statistiques
        for i, (texte, valeur, couleur) in enumerate([
            ("Vos navires restants:", f"{self.game_manager.player.get_ships_left()}/{len(self.game_manager.player.grid.ships)}", GREEN),
            ("Navires ennemis coulés:", f"{self.game_manager.opponent.grid.get_sunk_ships_count()}/{len(self.game_manager.opponent.grid.ships)}", RED)
        ]):
            # Cadre avec pulsation pour les statistiques importantes
            pulse = 0
            if (i == 0 and self.game_manager.player.grid.get_sunk_ships_count() > 0) or (i == 1 and self.game_manager.opponent.grid.get_sunk_ships_count() > 0):
                pulse = 10 * math.sin(time.time() * 3)
            
            stat_rect = pygame.Rect(70, stats_y + i * 40, 300 + abs(pulse), 30)
            pygame.draw.rect(screen, DARK_BLUE, stat_rect, 0, 8)
            pygame.draw.rect(screen, couleur, stat_rect, 2, 8)
            
            # Texte
            screen.blit(self.text_font.render(texte, True, WHITE), (80, stats_y + 5 + i * 40))
            val_txt = self.text_font.render(valeur, True, couleur)
            screen.blit(val_txt, (300, stats_y + 5 + i * 40))
        
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
                        SCREEN_HEIGHT - 50))
    
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
                cell_size = 40  # Même valeur que dans constants.py
                grid_width = grid_height = 10 * cell_size
                
                if (grid_x <= mouse_pos[0] < grid_x + grid_width and 
                    grid_y <= mouse_pos[1] < grid_y + grid_height):
                    # Convertir les coordonnées en indices de grille
                    col = (mouse_pos[0] - grid_x) // cell_size
                    row = (mouse_pos[1] - grid_y) // cell_size
                    
                    # Effectuer le tir
                    self.game_manager.process_player_shot(row, col)
        
        # Si c'est le tour de l'IA et que c'est un jeu solo
        if self.game_manager.current_player == "opponent" and not self.game_manager.is_online:
            # L'IA joue automatiquement après un court délai
            pygame.time.delay(500)  # Pause de 500ms
            self.game_manager.process_ai_turn()
        
        # Vérifier si le temps du tour est écoulé
        self.game_manager.check_turn_timeout()
        
        return JEU_SOLO
    
    def update(self):
        """Met à jour les éléments de l'écran de jeu"""
        # Mettre à jour l'animation de message
        if not self.animated_text.is_active() and self.game_manager.is_message_active():
            self.animated_text.start_animation(self.game_manager.message, self.game_manager.message_color)

