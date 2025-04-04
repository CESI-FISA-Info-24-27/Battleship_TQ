# game_over_screen.py
import pygame
import math
import time
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GRID_BLUE, DARK_BLUE, RED, GREEN,
    MENU_PRINCIPAL, PLACEMENT_NAVIRES, FIN_PARTIE
)
from ui.ui_elements import Button, TextBox

class GameOverScreen:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        
        # Polices
        self.title_font = pygame.font.SysFont("Arial", 64, bold=True)  # Agrandi
        self.subtitle_font = pygame.font.SysFont("Arial", 48, bold=True)  # Agrandi
        self.text_font = pygame.font.SysFont("Arial", 28)  # Agrandi
        
        # Boutons
        self.button_play_again = Button("Rejouer", (SCREEN_WIDTH // 2, 650), (300, 80), 32)  # Agrandi
        self.button_main_menu = Button("Menu principal", (SCREEN_WIDTH // 2, 750), (300, 80), 32)  # Agrandi
    
    def draw(self, screen, background_drawer):
        """Dessine l'écran de fin de partie"""
        # Fond animé de la mer
        background_drawer()
        
        # Panneau pour le titre
        title_panel = pygame.Surface((800, 120), pygame.SRCALPHA)
        title_panel.fill((0, 30, 60, 180))
        pygame.draw.rect(title_panel, GRID_BLUE, (0, 0, 800, 120), 3, 15)
        screen.blit(title_panel, (SCREEN_WIDTH // 2 - 400, 100))
        
        # Titre avec effet de pulsation
        scale = 1.0 + 0.05 * math.sin(time.time() * 2)
        titre = self.title_font.render("FIN DE PARTIE", True, WHITE)
        titre_scaled = pygame.transform.scale(titre, 
                                           (int(titre.get_width() * scale), 
                                            int(titre.get_height() * scale)))
        screen.blit(titre_scaled, 
                   (SCREEN_WIDTH // 2 - titre_scaled.get_width() // 2, 
                    130 - (titre_scaled.get_height() - titre.get_height()) // 2))
        
        # Grand panneau de résultat
        result_panel = pygame.Surface((800, 400), pygame.SRCALPHA)
        result_panel.fill((0, 20, 40, 200))
        pygame.draw.rect(result_panel, GRID_BLUE, (0, 0, 800, 400), 3, 15)
        screen.blit(result_panel, (SCREEN_WIDTH // 2 - 400, 250))
        
        # Résultat avec effet de brillance
        if self.game_manager.winner == "opponent":
            resultat = self.subtitle_font.render("Vous avez perdu !", True, RED)
            glow_color = (255, 0, 0, 50)
        else:
            resultat = self.subtitle_font.render("Vous avez gagné !", True, GREEN)
            glow_color = (0, 255, 0, 50)
        
        # Effet de halo pour le texte de résultat
        glow_size = 10 + 5 * math.sin(time.time() * 3)
        glow_surf = pygame.Surface((resultat.get_width() + glow_size * 2, 
                                  resultat.get_height() + glow_size * 2), 
                                 pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, glow_color, 
                         (0, 0, resultat.get_width() + glow_size * 2, 
                          resultat.get_height() + glow_size * 2))
        
        screen.blit(glow_surf, 
                   (SCREEN_WIDTH // 2 - resultat.get_width() // 2 - glow_size, 
                    280 - glow_size))
        screen.blit(resultat, (SCREEN_WIDTH // 2 - resultat.get_width() // 2, 280))
        
        # Panneau statistiques
        stats_panel_y = 350
        stats_panel = pygame.Surface((700, 250), pygame.SRCALPHA)
        stats_panel.fill((0, 30, 60, 180))
        pygame.draw.rect(stats_panel, GRID_BLUE, (0, 0, 700, 250), 2, 10)
        screen.blit(stats_panel, (SCREEN_WIDTH // 2 - 350, stats_panel_y))
        
        # Titre du panneau statistiques
        stats_title = self.text_font.render("STATISTIQUES DE LA PARTIE", True, WHITE)
        screen.blit(stats_title, (SCREEN_WIDTH // 2 - stats_title.get_width() // 2, stats_panel_y + 20))
        
        # Score avec animation
        score_y = stats_panel_y + 70
        
        # Données des joueurs
        player_stats = [
            ("Vos navires coulés:", f"{self.game_manager.player.grid.get_sunk_ships_count()}/{len(self.game_manager.player.grid.ships)}", RED),
            ("Navires ennemis coulés:", f"{self.game_manager.opponent.grid.get_sunk_ships_count()}/{len(self.game_manager.opponent.grid.ships)}", GREEN)
        ]
        
        # Afficher les statistiques avec une animation
        for i, (texte, valeur, couleur) in enumerate(player_stats):
            y_offset = 3 * math.sin(time.time() * 2 + i)
            
            # Fond pour la ligne de stats
            stat_line = pygame.Surface((650, 40), pygame.SRCALPHA)
            stat_line.fill((0, 0, 0, 50))
            screen.blit(stat_line, (SCREEN_WIDTH // 2 - 325, score_y + i * 60 + y_offset - 5))
            
            # Texte et valeur
            txt = self.text_font.render(texte, True, WHITE)
            val = self.text_font.render(valeur, True, couleur)
            
            screen.blit(txt, (SCREEN_WIDTH // 2 - 270, score_y + i * 60 + y_offset))
            screen.blit(val, (SCREEN_WIDTH // 2 + 170, score_y + i * 60 + y_offset))
        
        # Animation de particules pour célébrer la victoire si le joueur a gagné
        if self.game_manager.winner == "player":
            self._draw_celebration_particles(screen)
        
        # Boutons avec effet de pulsation
        self.button_play_again.draw(screen, time.time())
        self.button_main_menu.draw(screen, time.time())
    
    def _draw_celebration_particles(self, screen):
        """Dessine des particules d'animation pour célébrer la victoire"""
        num_particles = 50
        for i in range(num_particles):
            # Position basée sur le temps et l'indice
            angle = (time.time() * 0.5 + i * 0.1) % (2 * math.pi)
            distance = 200 + 100 * math.sin(time.time() + i * 0.2)
            x = SCREEN_WIDTH // 2 + distance * math.cos(angle)
            y = 350 + distance * math.sin(angle)
            
            # Taille et couleur
            size = 3 + 2 * math.sin(time.time() * 2 + i)
            hue = (time.time() * 50 + i * 10) % 360
            
            # Convertir HSV en RGB pour la couleur
            h = hue / 60
            c = 255
            x_val = c * (1 - abs(h % 2 - 1))
            
            if 0 <= h < 1:
                r, g, b = c, x_val, 0
            elif 1 <= h < 2:
                r, g, b = x_val, c, 0
            elif 2 <= h < 3:
                r, g, b = 0, c, x_val
            elif 3 <= h < 4:
                r, g, b = 0, x_val, c
            elif 4 <= h < 5:
                r, g, b = x_val, 0, c
            else:
                r, g, b = c, 0, x_val
            
            # Dessiner la particule
            pygame.draw.circle(screen, (int(r), int(g), int(b)), (int(x), int(y)), int(size))
    
    def handle_event(self, event):
        """Gère les événements de l'écran de fin de partie"""
        if self.button_play_again.check_click():
            # Si on était en mode online, déconnexion propre
            if self.game_manager.is_online and self.game_manager.network_client:
                try:
                    self.game_manager.network_client.disconnect()
                except Exception as e:
                    print(f"Erreur lors de la déconnexion: {e}")
                
            # Commencer une nouvelle partie (solo si on vient d'une partie online)
            self.game_manager.start_solo_game(self.game_manager.difficulty)
            return PLACEMENT_NAVIRES
    
        if self.button_main_menu.check_click():
            # Si on était en mode online, déconnexion propre
            if self.game_manager.is_online and self.game_manager.network_client:
                try:
                    self.game_manager.network_client.disconnect()
                    self.game_manager.network_client = None  # Libérer la référence
                    self.game_manager.is_online = False  # Réinitialiser l'état online
                except Exception as e:
                    print(f"Erreur lors de la déconnexion: {e}")
                
            # Réinitialiser certains états du jeu pour éviter des problèmes
            self.game_manager.winner = None
            self.game_manager.game_state = "waiting"
        
            return MENU_PRINCIPAL
    
        return FIN_PARTIE