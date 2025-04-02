# ship_placement.py
import pygame
import math
import time
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GRID_BLUE, DARK_BLUE, 
    PLACEMENT_TIME, PLACEMENT_NAVIRES, JEU_SOLO, JEU_ONLINE
)
from ui.ui_elements import Button, TextBox, ProgressBar

class ShipPlacementScreen:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        
        # Polices
        self.title_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 24)
        self.small_font = pygame.font.SysFont("Arial", 18)
        
        # Boutons
        self.button_rotate = Button("Tourner (R)", (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT - 150), (180, 50))
        self.button_next = Button("→", (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 150), (50, 50))
        self.button_prev = Button("←", (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 150), (50, 50))
        self.button_random = Button("Aléatoire", (SCREEN_WIDTH // 2 + 150, SCREEN_HEIGHT - 150), (180, 50))
        self.button_start = Button("Commencer", (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80), (200, 50))
        
        # Barre de temps
        self.time_bar = ProgressBar((SCREEN_WIDTH // 2, 70), (600, 20), PLACEMENT_TIME)
        
        # Coordonnées de la grille
        self.grid_pos = (SCREEN_WIDTH // 2 - 200, 150)
        
        # État
        self.preview_pos = None
        self.placement_valid = False
    
    def draw(self, screen, background_drawer):
        """Dessine l'écran de placement des navires"""
        # Fond animé de la mer
        background_drawer()
        
        # Titre avec effet légèrement ondulant
        offset_y = 2 * math.sin(time.time() * 2)
        
        titre = self.title_font.render("PLACEMENT DES NAVIRES", True, WHITE)
        shadow = self.title_font.render("PLACEMENT DES NAVIRES", True, GRID_BLUE)
        screen.blit(shadow, (SCREEN_WIDTH // 2 - titre.get_width() // 2 + 2, 32 + offset_y))
        screen.blit(titre, (SCREEN_WIDTH // 2 - titre.get_width() // 2, 30 + offset_y))
        
        # Barre de temps restant
        self.time_bar.update(self.game_manager.get_remaining_placement_time())
        self.time_bar.draw(screen, True)
        
        # Temps restant en texte
        remaining_seconds = self.game_manager.get_remaining_placement_time() // 1000
        time_text = self.text_font.render(f"{remaining_seconds} secondes restantes", True, WHITE)
        screen.blit(time_text, (SCREEN_WIDTH // 2 - time_text.get_width() // 2, 90))
        
        # Afficher la grille du joueur
        self.game_manager.player.grid.draw(
            screen, 
            self.grid_pos,
            True,
            self.game_manager.player.get_current_ship(),
            self.preview_pos,
            self.placement_valid
        )
        
        # Informations sur le navire à placer
        current_ship = self.game_manager.player.get_current_ship()
        
        if current_ship:
            # Fond semi-transparent pour le texte
            info_surf = pygame.Surface((500, 35), pygame.SRCALPHA)
            info_surf.fill((0, 50, 100, 150))
            screen.blit(info_surf, (SCREEN_WIDTH // 2 - 250, 110))
            
            info = self.text_font.render(f"Placez le {current_ship.name} (taille: {current_ship.size})", True, WHITE)
            screen.blit(info, (SCREEN_WIDTH // 2 - info.get_width() // 2, 115))
            
            # Panneau d'instruction avec effet de brillance
            instruction_surf = pygame.Surface((600, 80), pygame.SRCALPHA)
            instruction_surf.fill((0, 30, 60, 180))
            pygame.draw.rect(instruction_surf, GRID_BLUE, (0, 0, 600, 80), 2, 10)
            screen.blit(instruction_surf, (SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT - 200))
            
            # Instructions
            instruction1 = self.small_font.render("Appuyez sur 'R' ou sur le bouton 'Tourner' pour changer l'orientation", True, WHITE)
            instruction2 = self.small_font.render("Utilisez les flèches pour choisir le navire à placer", True, WHITE)
            
            screen.blit(instruction1, (SCREEN_WIDTH // 2 - instruction1.get_width() // 2, SCREEN_HEIGHT - 190))
            screen.blit(instruction2, (SCREEN_WIDTH // 2 - instruction2.get_width() // 2, SCREEN_HEIGHT - 170))
            
            # Afficher l'orientation actuelle
            orientation_text = "Horizontale" if current_ship.orientation == 'H' else "Verticale"
            orientation = self.small_font.render(f"Orientation: {orientation_text}", True, WHITE)
            screen.blit(orientation, (SCREEN_WIDTH // 2 - orientation.get_width() // 2, SCREEN_HEIGHT - 220))
            
            # Boutons
            self.button_rotate.draw(screen)
            self.button_next.draw(screen)
            self.button_prev.draw(screen)
            self.button_random.draw(screen)
        else:
            # Tous les navires sont placés
            ready_text = self.text_font.render("Tous les navires sont placés, prêt à commencer !", True, (50, 255, 50))
            screen.blit(ready_text, (SCREEN_WIDTH // 2 - ready_text.get_width() // 2, SCREEN_HEIGHT - 180))
            
            # Bouton pour commencer la partie
            self.button_start.draw(screen, time.time())
    
    def handle_event(self, event):
        """Gère les événements de l'écran de placement"""
        current_ship = self.game_manager.player.get_current_ship()
        
        if current_ship:
            # Rotation avec la touche R
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.game_manager.player.rotate_current_ship()
            
            # Navigation entre les navires avec les flèches
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.game_manager.player.previous_ship()
                elif event.key == pygame.K_RIGHT:
                    self.game_manager.player.next_ship()
            
            # Clic pour placer un navire
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = pygame.mouse.get_pos()
                grid_x, grid_y = self.grid_pos
                
                # Vérifier si le clic est dans la grille
                cell_size = 40  # Même valeur que dans constants.py
                grid_width = grid_height = 10 * cell_size
                
                if (grid_x <= mouse_pos[0] < grid_x + grid_width and 
                    grid_y <= mouse_pos[1] < grid_y + grid_height):
                    # Convertir les coordonnées en indices de grille
                    col = (mouse_pos[0] - grid_x) // cell_size
                    row = (mouse_pos[1] - grid_y) // cell_size
                    
                    # Placer le navire s'il est dans une position valide
                    if self.placement_valid:
                        self.game_manager.player.place_current_ship(row, col, current_ship.orientation)
            
            # Vérifier les clics sur les boutons
            if self.button_rotate.check_click():
                self.game_manager.player.rotate_current_ship()
            
            if self.button_next.check_click():
                self.game_manager.player.next_ship()
            
            if self.button_prev.check_click():
                self.game_manager.player.previous_ship()
            
            if self.button_random.check_click():
                self._place_random()
        else:
            # Tous les navires sont placés
            if self.button_start.check_click():
                self.game_manager.start_game()
                if self.game_manager.is_online:
                    return JEU_ONLINE
                else:
                    return JEU_SOLO
        
        # Vérifier si le temps de placement est écoulé
        if self.game_manager.check_placement_timeout():
            if self.game_manager.is_online:
                return JEU_ONLINE
            else:
                return JEU_SOLO
        
        return PLACEMENT_NAVIRES
    
    def update(self):
        """Met à jour l'aperçu du placement des navires"""
        current_ship = self.game_manager.player.get_current_ship()
        if not current_ship:
            return
        
        # Obtenir la position de la souris
        mouse_pos = pygame.mouse.get_pos()
        grid_x, grid_y = self.grid_pos
        
        # Vérifier si la souris est sur la grille
        cell_size = 40  # Même valeur que dans constants.py
        grid_width = grid_height = 10 * cell_size
        
        if (grid_x <= mouse_pos[0] < grid_x + grid_width and 
            grid_y <= mouse_pos[1] < grid_y + grid_height):
            # Convertir les coordonnées en indices de grille
            col = (mouse_pos[0] - grid_x) // cell_size
            row = (mouse_pos[1] - grid_y) // cell_size
            
            # Mettre à jour la position de l'aperçu
            self.preview_pos = (row, col)
            
            # Vérifier si le placement est valide
            self.placement_valid = self.game_manager.player.grid.can_place_ship(
                current_ship.size, row, col, current_ship.orientation
            )
        else:
            self.preview_pos = None
    
    def _place_random(self):
        """Place aléatoirement le navire actuel"""
        import random
        
        current_ship = self.game_manager.player.get_current_ship()
        if not current_ship:
            return
        
        # Essayer 100 positions aléatoires
        for _ in range(100):
            orientation = random.choice(['H', 'V'])
            current_ship.orientation = orientation
            
            if orientation == 'H':
                row = random.randint(0, 9)
                col = random.randint(0, 10 - current_ship.size)
            else:
                row = random.randint(0, 10 - current_ship.size)
                col = random.randint(0, 9)
            
            # Essayer de placer le navire
            if self.game_manager.player.grid.can_place_ship(current_ship.size, row, col, orientation):
                self.game_manager.player.place_current_ship(row, col, orientation)
                break

