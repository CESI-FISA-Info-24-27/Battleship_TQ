# ship_placement.py
import pygame
import math
import time
from game.constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, GRID_BLUE, DARK_BLUE, 
    PLACEMENT_TIME, PLACEMENT_NAVIRES, JEU_SOLO, JEU_ONLINE, CELL_SIZE
)
from ui.ui_elements import Button, TextBox, ProgressBar

class ShipPlacementScreen:
    def __init__(self, game_manager):
        self.game_manager = game_manager
        
        # Polices
        self.title_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 24)
        self.small_font = pygame.font.SysFont("Arial", 18)
        
        # Calculer la position centrée de la grille
        grid_width = CELL_SIZE * 10
        self.grid_pos = (SCREEN_WIDTH // 2 - grid_width // 2, 150)
        
        # Boutons
        btn_y = SCREEN_HEIGHT - 150  # Position verticale des boutons
        self.button_rotate = Button("Tourner (R)", (SCREEN_WIDTH // 2 - 250, btn_y), (180, 50), 22)
        self.button_next = Button("→", (SCREEN_WIDTH // 2 + 50, btn_y), (50, 50), 28)
        self.button_prev = Button("←", (SCREEN_WIDTH // 2 - 50, btn_y), (50, 50), 28)
        self.button_random = Button("Aléatoire", (SCREEN_WIDTH // 2 + 250, btn_y), (180, 50), 22)
        self.button_start = Button("Commencer", (SCREEN_WIDTH // 2, SCREEN_HEIGHT - 80), (250, 50), 24)
        
        # Barre de temps
        self.time_bar = ProgressBar((SCREEN_WIDTH // 2, 100), (600, 20), PLACEMENT_TIME)
        
        # État
        self.preview_pos = None
        self.placement_valid = False
    
    def draw(self, screen, background_drawer):
        """Dessine l'écran de placement des navires"""
        # Fond animé
        background_drawer()
        
        # Titre avec effet légèrement ondulant
        offset_y = 2 * math.sin(time.time() * 2)
        
        titre = self.title_font.render("PLACEMENT DES NAVIRES", True, WHITE)
        shadow = self.title_font.render("PLACEMENT DES NAVIRES", True, GRID_BLUE)
        screen.blit(shadow, (SCREEN_WIDTH // 2 - titre.get_width() // 2 + 2, 42 + offset_y))
        screen.blit(titre, (SCREEN_WIDTH // 2 - titre.get_width() // 2, 40 + offset_y))
        
        # Barre de temps restant
        self.time_bar.update(self.game_manager.get_remaining_placement_time())
        self.time_bar.draw(screen, self.game_manager.get_remaining_placement_time() < PLACEMENT_TIME * 0.3)
        
        # Temps restant en texte
        remaining_seconds = self.game_manager.get_remaining_placement_time() // 1000
        time_text = self.text_font.render(f"{remaining_seconds} secondes restantes", True, WHITE)
        screen.blit(time_text, (SCREEN_WIDTH // 2 - time_text.get_width() // 2, 120))
        
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
            # Créer un panneau d'information pour les navires à placer
            ships_panel_width = 300
            ships_panel_height = SCREEN_HEIGHT - 300
            
            # Positionnement du panneau (à droite de la grille)
            panel_x = self.grid_pos[0] + 10 * CELL_SIZE + 20
            
            # Vérifier si le panneau tient dans l'écran
            if panel_x + ships_panel_width > SCREEN_WIDTH:
                # Si pas assez d'espace à droite, mettre le panneau à gauche
                panel_x = self.grid_pos[0] - ships_panel_width - 20
            
            if panel_x < 0:
                # Si toujours pas assez d'espace, réduire la taille du panneau
                panel_x = 10
                ships_panel_width = self.grid_pos[0] - 30
            
            panel_y = 150
            
            # Dessiner le panneau des navires
            info_panel = pygame.Surface((ships_panel_width, ships_panel_height), pygame.SRCALPHA)
            info_panel.fill((0, 30, 60, 180))
            pygame.draw.rect(info_panel, GRID_BLUE, (0, 0, ships_panel_width, ships_panel_height), 2, 10)
            screen.blit(info_panel, (panel_x, panel_y))
            
            # Titre du panneau
            panel_title = self.text_font.render("NAVIRES À PLACER", True, WHITE)
            screen.blit(panel_title, (panel_x + ships_panel_width // 2 - panel_title.get_width() // 2, panel_y + 15))
            
            # Liste des navires à placer avec leur statut
            ships_y = panel_y + 60
            for i, ship in enumerate(self.game_manager.player.ships_to_place):
                # Déterminer si le navire est placé, en cours ou en attente
                if i < self.game_manager.player.current_ship_index:
                    status = "✓"  # Placé
                    color = (50, 255, 100)
                elif i == self.game_manager.player.current_ship_index:
                    status = "▶"  # En cours
                    color = (255, 255, 0)
                else:
                    status = "◯"  # En attente
                    color = WHITE
                
                # Texte du navire
                ship_name = f"{status} {ship.name} ({ship.size} cases)"
                ship_text = self.small_font.render(ship_name, True, color)
                
                # Effet de highlight pour le navire actuel
                if i == self.game_manager.player.current_ship_index:
                    highlight = pygame.Surface((ships_panel_width - 20, 25), pygame.SRCALPHA)
                    highlight.fill((255, 255, 0, 30))
                    screen.blit(highlight, (panel_x + 10, ships_y + i * 30 - 2))
                
                screen.blit(ship_text, (panel_x + 20, ships_y + i * 30))
            
            # Informations sur le navire actuel
            ship_info_y = ships_y + len(self.game_manager.player.ships_to_place) * 30 + 30
            info_title = self.text_font.render("NAVIRE ACTUEL", True, WHITE)
            screen.blit(info_title, (panel_x + ships_panel_width // 2 - info_title.get_width() // 2, ship_info_y))
            
            # Nom et taille du navire
            ship_info_y += 35
            ship_name = self.text_font.render(current_ship.name, True, (255, 255, 0))
            ship_name_width = ship_name.get_width()
            
            # Limiter la largeur du texte si nécessaire
            if ship_name_width > ships_panel_width - 40:
                # Réduire la taille de la police pour le nom
                smaller_font = pygame.font.SysFont("Arial", 20)
                ship_name = smaller_font.render(current_ship.name, True, (255, 255, 0))
            
            screen.blit(ship_name, (panel_x + ships_panel_width // 2 - ship_name.get_width() // 2, ship_info_y))
            
            ship_info_y += 30
            ship_size = self.small_font.render(f"Taille: {current_ship.size} cases", True, WHITE)
            screen.blit(ship_size, (panel_x + ships_panel_width // 2 - ship_size.get_width() // 2, ship_info_y))
            
            # Orientation actuelle
            ship_info_y += 25
            orientation_text = "Horizontale" if current_ship.orientation == 'H' else "Verticale"
            orientation = self.small_font.render(f"Orientation: {orientation_text}", True, WHITE)
            screen.blit(orientation, (panel_x + ships_panel_width // 2 - orientation.get_width() // 2, ship_info_y))
            
            # Instructions
            ship_info_y += 50
            instructions_title = self.text_font.render("INSTRUCTIONS", True, WHITE)
            screen.blit(instructions_title, (panel_x + ships_panel_width // 2 - instructions_title.get_width() // 2, ship_info_y))
            
            instructions = [
                "1. Placez tous les navires",
                "2. Utilisez 'R' pour tourner",
                "3. Cliquez sur la grille pour placer",
                "4. Utilisez les flèches ← → pour",
                "   changer de navire"
            ]
            
            for i, instruction in enumerate(instructions):
                instr_text = self.small_font.render(instruction, True, WHITE)
                screen.blit(instr_text, (panel_x + 20, ship_info_y + 30 + i * 25))
            
            # Panneau d'instruction en bas
            instruction_panel_y = SCREEN_HEIGHT - 200
            
            # Vérifier si l'espace est suffisant
            if instruction_panel_y > panel_y + 350:
                instruction_surf = pygame.Surface((600, 50), pygame.SRCALPHA)
                instruction_surf.fill((0, 30, 60, 180))
                pygame.draw.rect(instruction_surf, GRID_BLUE, (0, 0, 600, 50), 2, 8)
                screen.blit(instruction_surf, (SCREEN_WIDTH // 2 - 300, instruction_panel_y))
                
                # Instructions pour les contrôles
                instruction_text = self.small_font.render("Utilisez 'R' pour tourner et les flèches pour changer de navire", True, WHITE)
                screen.blit(instruction_text, (SCREEN_WIDTH // 2 - instruction_text.get_width() // 2, instruction_panel_y + 15))
            
            # Boutons
            self.button_rotate.draw(screen)
            self.button_next.draw(screen)
            self.button_prev.draw(screen)
            self.button_random.draw(screen)
        else:
            # Tous les navires sont placés
            ready_panel = pygame.Surface((600, 70), pygame.SRCALPHA)
            ready_panel.fill((0, 50, 0, 180))
            pygame.draw.rect(ready_panel, (50, 255, 100), (0, 0, 600, 70), 2, 10)
            screen.blit(ready_panel, (SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT - 180))
            
            ready_text = self.text_font.render("Tous les navires sont placés, prêt à commencer !", True, (50, 255, 50))
            screen.blit(ready_text, (SCREEN_WIDTH // 2 - ready_text.get_width() // 2, SCREEN_HEIGHT - 150))
            
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
                grid_width = grid_height = 10 * CELL_SIZE
                
                if (grid_x <= mouse_pos[0] < grid_x + grid_width and 
                    grid_y <= mouse_pos[1] < grid_y + grid_height):
                    # Convertir les coordonnées en indices de grille
                    col = (mouse_pos[0] - grid_x) // CELL_SIZE
                    row = (mouse_pos[1] - grid_y) // CELL_SIZE
                    
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
        grid_width = grid_height = 10 * CELL_SIZE
        
        if (grid_x <= mouse_pos[0] < grid_x + grid_width and 
            grid_y <= mouse_pos[1] < grid_y + grid_height):
            # Convertir les coordonnées en indices de grille
            col = (mouse_pos[0] - grid_x) // CELL_SIZE
            row = (mouse_pos[1] - grid_y) // CELL_SIZE
            
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