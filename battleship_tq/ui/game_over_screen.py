# game_over_screen.py
import pygame
import math
import time
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GRID_BLUE, DARK_BLUE, RED, GREEN,
    MENU_PRINCIPAL, PLACEMENT_NAVIRES
)
from ui.ui_elements import Button, TextBox

class GameOverScreen:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        
        # Polices
        self.title_font = pygame.font.SysFont("Arial", 48, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 24)
        
        # Boutons
        self.button_play_again = Button("Rejouer", (SCREEN_WIDTH // 2, 450))
        self.button_main_menu = Button("Menu principal", (SCREEN_WIDTH // 2, 530))
    
    def draw(self, screen, background_drawer):
        """Dessine l'écran de fin de partie"""
        # Fond animé de la mer
        background_drawer()
        
        # Titre avec effet de pulsation
        scale = 1.0 + 0.05 * math.sin(time.time() * 2)
        titre = self.title_font.render("FIN DE PARTIE", True, WHITE)
        titre_scaled = pygame.transform.scale(titre, 
                                           (int(titre.get_width() * scale), 
                                            int(titre.get_height() * scale)))
        screen.blit(titre_scaled, 
                   (SCREEN_WIDTH // 2 - titre_scaled.get_width() // 2, 
                    100 - (titre_scaled.get_height() - titre.get_height()) // 2))
        
        # Panneau de résultat
        result_panel = pygame.Surface((500, 300), pygame.SRCALPHA)
        result_panel.fill((0, 20, 40, 200))
        pygame.draw.rect(result_panel, GRID_BLUE, (0, 0, 500, 300), 3, 15)
        screen.blit(result_panel, (SCREEN_WIDTH // 2 - 250, 170))
        
        # Résultat avec effet de brillance
        if self.game_manager.winner == "opponent":
            resultat = self.title_font.render("Vous avez perdu !", True, RED)
            glow_color = (255, 0, 0, 50)
        else:
            resultat = self.title_font.render("Vous avez gagné !", True, GREEN)
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
                    200 - glow_size))
        screen.blit(resultat, (SCREEN_WIDTH // 2 - resultat.get_width() // 2, 200))
        
        # Score avec animation
        score_y = 280
        for i, (texte, valeur, couleur) in enumerate([
            ("Vos navires coulés:", f"{self.game_manager.player.grid.get_sunk_ships_count()}/{len(self.game_manager.player.grid.ships)}", RED),
            ("Navires ennemis coulés:", f"{self.game_manager.opponent.grid.get_sunk_ships_count()}/{len(self.game_manager.opponent.grid.ships)}", GREEN)
        ]):
            y_offset = 3 * math.sin(time.time() * 2 + i)
            
            txt = self.text_font.render(texte, True, WHITE)
            val = self.text_font.render(valeur, True, couleur)
            
            screen.blit(txt, (SCREEN_WIDTH // 2 - 170, score_y + i * 40 + y_offset))
            screen.blit(val, (SCREEN_WIDTH // 2 + 100, score_y + i * 40 + y_offset))
        
        # Boutons avec effet de pulsation
        glow = (30 * (math.sin(time.time() * 2) + 1))
        
        # Dessiner les boutons
        self.button_play_again.draw(screen, time.time())
        self.button_main_menu.draw(screen, time.time())
    
    def handle_event(self, event):
        """Gère les événements de l'écran de fin de partie"""
        if self.button_play_again.check_click():
            self.game_manager.start_solo_game(self.game_manager.difficulty)
            return PLACEMENT_NAVIRES
        
        if self.button_main_menu.check_click():
            return MENU_PRINCIPAL
        
        return "fin_partie"

