import pygame
import sys
import os
import time
import random
import math
from pygame.locals import *

# Initialisation de Pygame
pygame.init()
pygame.font.init()

# Constantes
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
GRID_SIZE = 10
CELL_SIZE = 40
MARGIN = 60
GRID_WIDTH = CELL_SIZE * GRID_SIZE
GRID_HEIGHT = CELL_SIZE * GRID_SIZE

# Couleurs améliorées
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_BLUE = (0, 30, 60)      # Fond plus foncé
GRID_BLUE = (0, 120, 215)    # Grille plus visible
LIGHT_BLUE = (135, 206, 250) # Bleu clair pour les éléments interactifs
DEEP_BLUE = (0, 50, 100)     # Bleu profond pour les navires
WATER_BLUE = (10, 75, 120)   # Couleur de l'eau
RED = (255, 50, 50)          # Rouge plus vif pour les coups
GREEN = (50, 255, 100)       # Vert plus vif
YELLOW = (255, 255, 0)       # Jaune pour les notifications
ORANGE = (255, 165, 0)       # Orange pour certains éléments visuels

# Difficulté
FACILE = 1
MOYEN = 2
DIFFICILE = 3

class BatailleNavale:
    def __init__(self):
        # Initialisation de la fenêtre
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Bataille Navale Solo")
        self.clock = pygame.time.Clock()
        
        # Chargement des polices
        self.title_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.text_font = pygame.font.SysFont("Arial", 24)
        self.small_font = pygame.font.SysFont("Arial", 18)
        self.animation_font = pygame.font.SysFont("Impact", 72, bold=True)
        
        # Taille de la grille
        self.taille_grille = GRID_SIZE
        
        # Initialisation des grilles
        self.reset_game()
        
        # État du jeu
        self.etat = 'menu'  # menu, placement, jeu, fin
        self.difficulte = MOYEN
        self.placement_navire_actuel = None
        self.placement_orientation = 'H'
        self.dernier_tir_bot = None
        self.tirs_reussis_bot = []
        self.direction_chasse = None
        
        # Variables pour l'animation
        self.animation_active = False
        self.animation_message = ""
        self.animation_couleur = WHITE
        self.animation_debut = 0
        self.animation_duree = 2.0  # 2 secondes
        
        # Initialisation des sons (sans essayer de les charger pour éviter les erreurs)
        self.sound_hit = None
        self.sound_miss = None
        self.sound_sink = None
        
        # Essayer de charger les sons si possible
        try:
            pygame.mixer.init()
            self.sound_hit = pygame.mixer.Sound(self.resource_path('assets/hit.wav'))
            self.sound_miss = pygame.mixer.Sound(self.resource_path('assets/miss.wav'))
            self.sound_sink = pygame.mixer.Sound(self.resource_path('assets/sink.wav'))
            self.sons_actifs = True
        except Exception as e:
            print(f"Erreur lors du chargement des sons: {e}")
            self.sons_actifs = False
    
    def resource_path(self, relative_path):
        try:
            # PyInstaller crée un répertoire temporaire et stocke le chemin dans _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        
        return os.path.join(base_path, relative_path)
    
    def reset_game(self):
        # Initialisation des grilles
        self.grille_joueur = [[' ' for _ in range(self.taille_grille)] for _ in range(self.taille_grille)]
        self.grille_bot = [[' ' for _ in range(self.taille_grille)] for _ in range(self.taille_grille)]
        self.grille_tirs_joueur = [[' ' for _ in range(self.taille_grille)] for _ in range(self.taille_grille)]
        self.grille_tirs_bot = [[' ' for _ in range(self.taille_grille)] for _ in range(self.taille_grille)]
        
        # Définition des navires et leurs tailles
        self.navires = {
            'Porte-avions': 5,
            'Croiseur': 4,
            'Contre-torpilleur': 3,
            'Sous-marin': 3,
            'Torpilleur': 2
        }
        
        # Liste des navires pour le placement
        self.navires_a_placer = list(self.navires.items())
        self.navire_index = 0
        
        # Compteurs de navires coulés
        self.navires_coules_joueur = 0
        self.navires_coules_bot = 0
        
        # Nombre total de navires
        self.total_navires = len(self.navires)
        
        # Réinitialiser les variables de jeu
        self.dernier_tir_bot = None
        self.tirs_reussis_bot = []
        self.direction_chasse = None
    
    def dessiner_fond_marin(self):
        # Dessiner un fond noir pour l'océan
        self.screen.fill(BLACK)
        
        # Ajouter des effets d'ondulation sous-marine (vagues légères)
        for y in range(0, SCREEN_HEIGHT, 20):
            amplitude = 5
            frequence = 0.05
            for x in range(0, SCREEN_WIDTH, 4):
                offset = amplitude * math.sin(frequence * x + time.time())
                pygame.draw.line(self.screen, DARK_BLUE, (x, y + offset), (x, y + 10 + offset), 2)
    
    def dessiner_bateau(self, x, y, taille, orientation, couleur=DEEP_BLUE, contour=True):
        """Dessine un bateau stylisé"""
        # Taille du bateau
        if orientation == 'H':
            width = CELL_SIZE * taille
            height = CELL_SIZE
            rect = pygame.Rect(x, y, width, height)
            
            # Corps du bateau
            pygame.draw.rect(self.screen, couleur, rect, 0 if not contour else 2)
            
            # Pont supérieur
            pont_height = height // 2
            pygame.draw.rect(self.screen, 
                            (min(255, couleur[0] + 40), min(255, couleur[1] + 40), min(255, couleur[2] + 40)),
                            (x + width//10, y + height//4, width - width//5, pont_height), 
                            0 if not contour else 1)
            
            # Cabine
            if taille >= 3:
                pygame.draw.rect(self.screen, 
                                (min(255, couleur[0] + 30), min(255, couleur[1] + 30), min(255, couleur[2] + 30)),
                                (x + width//3, y + 2, width//3, height//2), 
                                0 if not contour else 1)
        else:  # Vertical
            width = CELL_SIZE
            height = CELL_SIZE * taille
            rect = pygame.Rect(x, y, width, height)
            
            # Corps du bateau
            pygame.draw.rect(self.screen, couleur, rect, 0 if not contour else 2)
            
            # Pont supérieur
            pygame.draw.rect(self.screen, 
                            (min(255, couleur[0] + 40), min(255, couleur[1] + 40), min(255, couleur[2] + 40)),
                            (x + width//4, y + height//10, width//2, height - height//5), 
                            0 if not contour else 1)
            
            # Cabine
            if taille >= 3:
                pygame.draw.rect(self.screen, 
                                (min(255, couleur[0] + 30), min(255, couleur[1] + 30), min(255, couleur[2] + 30)),
                                (x + 2, y + height//3, width//2, height//3), 
                                0 if not contour else 1)
    
    def afficher_menu(self):
        self.dessiner_fond_marin()
        
        # Titre avec effet de flottement
        offset_y = 5 * math.sin(time.time() * 2)
        titre = self.title_font.render("BATAILLE NAVALE", True, WHITE)
        shadow = self.title_font.render("BATAILLE NAVALE", True, GRID_BLUE)
        self.screen.blit(shadow, (SCREEN_WIDTH // 2 - titre.get_width() // 2 + 3, 103 + offset_y))
        self.screen.blit(titre, (SCREEN_WIDTH // 2 - titre.get_width() // 2, 100 + offset_y))
        
        # Boutons avec effet de lueur
        glow = (20 * (math.sin(time.time() * 3) + 1)) # 0-40 pulsing value
        boutons = [
            ("Jouer", (SCREEN_WIDTH // 2, 300)),
            ("Difficulté: " + self.obtenir_nom_difficulte(), (SCREEN_WIDTH // 2, 380)),
            ("Quitter", (SCREEN_WIDTH // 2, 460))
        ]
        
        for texte, pos in boutons:
            # Effet de halo
            halo_surf = pygame.Surface((320, 80), pygame.SRCALPHA)
            pygame.draw.rect(halo_surf, (0, 120, 255, int(glow)), (0, 0, 320, 80), border_radius=15)
            self.screen.blit(halo_surf, (pos[0] - 160, pos[1] - 40))
            
            self.afficher_bouton(texte, pos)
        
        # Décoration: petits bateaux animés sur l'eau
        self.dessiner_decorations()
        
        pygame.display.flip()
    
    def dessiner_decorations(self):
        # Dessiner quelques bateaux décoratifs qui se déplacent lentement
        t = time.time()
        
        # Premier petit bateau
        x1 = (t * 20) % (SCREEN_WIDTH + 100) - 50
        self.dessiner_bateau(x1, 550, 3, 'H', LIGHT_BLUE)
        
        # Deuxième petit bateau dans l'autre sens
        x2 = SCREEN_WIDTH - ((t * 15) % (SCREEN_WIDTH + 100) - 50)
        self.dessiner_bateau(x2, 650, 2, 'H', DEEP_BLUE)
    
    def obtenir_nom_difficulte(self):
        if self.difficulte == FACILE:
            return "Facile"
        elif self.difficulte == MOYEN:
            return "Moyen"
        else:
            return "Difficile"
    
    def afficher_bouton(self, texte, pos, largeur=300, hauteur=60):
        x, y = pos
        rect = pygame.Rect(x - largeur // 2, y - hauteur // 2, largeur, hauteur)
        
        # Vérifier si la souris est sur le bouton
        souris_pos = pygame.mouse.get_pos()
        survol = rect.collidepoint(souris_pos)
        
        # Couleur du bouton
        couleur = GRID_BLUE if survol else DARK_BLUE
        
        # Dessiner le bouton avec des bords arrondis
        pygame.draw.rect(self.screen, couleur, rect, 0, 12)
        pygame.draw.rect(self.screen, LIGHT_BLUE, rect, 2, 12)
        
        # Ajouter un effet de brillance quand survolé
        if survol:
            highlight = pygame.Surface((largeur - 4, 10), pygame.SRCALPHA)
            highlight.fill((255, 255, 255, 90))
            self.screen.blit(highlight, (rect.left + 2, rect.top + 5))
        
        # Texte du bouton
        texte_surface = self.text_font.render(texte, True, WHITE)
        self.screen.blit(texte_surface, (x - texte_surface.get_width() // 2, y - texte_surface.get_height() // 2))
        
        return rect
    
    def afficher_ecran_placement(self):
        self.dessiner_fond_marin()
        
        # Titre avec effet légèrement ondulant
        offset_y = 2 * math.sin(time.time() * 2)
        titre = self.title_font.render("PLACEMENT DES NAVIRES", True, WHITE)
        shadow = self.title_font.render("PLACEMENT DES NAVIRES", True, GRID_BLUE)
        self.screen.blit(shadow, (SCREEN_WIDTH // 2 - titre.get_width() // 2 + 2, 32 + offset_y))
        self.screen.blit(titre, (SCREEN_WIDTH // 2 - titre.get_width() // 2, 30 + offset_y))
        
        # Afficher la grille du joueur
        self.afficher_grille(self.grille_joueur, (SCREEN_WIDTH // 2 - GRID_WIDTH // 2, 120), True)
        
        # Informations sur le navire à placer
        if self.navire_index < len(self.navires_a_placer):
            nom, taille = self.navires_a_placer[self.navire_index]
            
            # Fond semi-transparent pour le texte
            info_surf = pygame.Surface((500, 35), pygame.SRCALPHA)
            info_surf.fill((0, 50, 100, 150))
            self.screen.blit(info_surf, (SCREEN_WIDTH // 2 - 250, 80))
            
            info = self.text_font.render(f"Placez le {nom} (taille: {taille})", True, WHITE)
            self.screen.blit(info, (SCREEN_WIDTH // 2 - info.get_width() // 2, 85))
            
            # Panneau d'instruction avec effet de brillance
            instruction_surf = pygame.Surface((550, 80), pygame.SRCALPHA)
            instruction_surf.fill((0, 30, 60, 180))
            pygame.draw.rect(instruction_surf, GRID_BLUE, (0, 0, 550, 80), 2, 10)
            self.screen.blit(instruction_surf, (SCREEN_WIDTH // 2 - 275, GRID_HEIGHT + 150))
            
            # Instructions
            instruction = self.small_font.render("Appuyez sur 'R' pour changer l'orientation", True, WHITE)
            self.screen.blit(instruction, (SCREEN_WIDTH // 2 - instruction.get_width() // 2, GRID_HEIGHT + 160))
            
            # Afficher l'orientation actuelle
            orientation = self.small_font.render(f"Orientation: {'Horizontale' if self.placement_orientation == 'H' else 'Verticale'}", True, WHITE)
            self.screen.blit(orientation, (SCREEN_WIDTH // 2 - orientation.get_width() // 2, GRID_HEIGHT + 190))
        else:
            # Bouton pour commencer la partie avec animation
            glow = (20 * (math.sin(time.time() * 3) + 1))
            halo_surf = pygame.Surface((320, 80), pygame.SRCALPHA)
            pygame.draw.rect(halo_surf, (0, 120, 255, int(glow)), (0, 0, 320, 80), border_radius=15)
            self.screen.blit(halo_surf, (SCREEN_WIDTH // 2 - 160, GRID_HEIGHT + 150))
            
            rect = self.afficher_bouton("Commencer la partie", (SCREEN_WIDTH // 2, GRID_HEIGHT + 180))
            
            if pygame.mouse.get_pressed()[0] and rect.collidepoint(pygame.mouse.get_pos()):
                self.placer_navires_aleatoirement(self.grille_bot)
                self.etat = 'jeu'
        
        pygame.display.flip()
    
    def afficher_ecran_jeu(self):
        self.dessiner_fond_marin()
        
        # Titre
        titre = self.title_font.render("BATAILLE NAVALE", True, WHITE)
        shadow = self.title_font.render("BATAILLE NAVALE", True, GRID_BLUE)
        self.screen.blit(shadow, (SCREEN_WIDTH // 2 - titre.get_width() // 2 + 2, 32))
        self.screen.blit(titre, (SCREEN_WIDTH // 2 - titre.get_width() // 2, 30))
        
        # Afficher les grilles
        grid_y = 120
        self.afficher_grille(self.grille_joueur, (150, grid_y), True)  # Grille du joueur
        self.afficher_grille(self.grille_tirs_joueur, (SCREEN_WIDTH - 150 - GRID_WIDTH, grid_y), False)  # Grille des tirs du joueur
        
        # Légendes des grilles avec effet de halo
        for texte, pos in [
            ("Votre flotte", (150 + GRID_WIDTH // 2, grid_y - 30)),
            ("Vos tirs", (SCREEN_WIDTH - 150 - GRID_WIDTH // 2, grid_y - 30))
        ]:
            # Halo
            halo_surf = pygame.Surface((200, 40), pygame.SRCALPHA)
            halo_surf.fill((0, 30, 60, 160))
            pygame.draw.rect(halo_surf, GRID_BLUE, (0, 0, 200, 40), 2, 8)
            self.screen.blit(halo_surf, (pos[0] - 100, pos[1] - 20))
            
            # Texte
            txt = self.text_font.render(texte, True, WHITE)
            self.screen.blit(txt, (pos[0] - txt.get_width() // 2, pos[1] - txt.get_height() // 2))
        
        # Panneau inférieur avec légende et statistiques
        info_panel = pygame.Surface((SCREEN_WIDTH - 100, 150), pygame.SRCALPHA)
        info_panel.fill((0, 20, 40, 180))
        pygame.draw.rect(info_panel, GRID_BLUE, (0, 0, SCREEN_WIDTH - 100, 150), 2, 12)
        self.screen.blit(info_panel, (50, grid_y + GRID_HEIGHT + 20))
        
        # Légende
        legende_y = grid_y + GRID_HEIGHT + 35
        self.screen.blit(self.text_font.render("Légende:", True, WHITE), (70, legende_y))
        
        # Icônes de légende
        legende_items = [
            ("Navire", DEEP_BLUE, (200, legende_y)),
            ("Touché", RED, (350, legende_y)),
            ("Manqué", WATER_BLUE, (500, legende_y))
        ]
        
        for texte, couleur, (x, y) in legende_items:
            # Fond pour l'échantillon
            pygame.draw.rect(self.screen, couleur, (x, y, 20, 20))
            pygame.draw.rect(self.screen, WHITE, (x, y, 20, 20), 1)
            
            # Texte
            txt = self.small_font.render(texte, True, WHITE)
            self.screen.blit(txt, (x + 30, y + 2))
        
        # Statistiques avec animation de nombre
        stats_y = legende_y + 50
        
        # Cadres pour les statistiques
        for i, (texte, valeur, couleur) in enumerate([
            ("Vos navires coulés:", f"{self.navires_coules_joueur}/{self.total_navires}", RED),
            ("Navires ennemis coulés:", f"{self.navires_coules_bot}/{self.total_navires}", GREEN)
        ]):
            # Cadre avec pulsation pour les statistiques importantes
            pulse = 0
            if (i == 0 and self.navires_coules_joueur > 0) or (i == 1 and self.navires_coules_bot > 0):
                pulse = 10 * math.sin(time.time() * 3)
            
            stat_rect = pygame.Rect(70, stats_y + i * 40, 300 + abs(pulse), 30)
            pygame.draw.rect(self.screen, DARK_BLUE, stat_rect, 0, 8)
            pygame.draw.rect(self.screen, couleur, stat_rect, 2, 8)
            
            # Texte
            self.screen.blit(self.text_font.render(texte, True, WHITE), (80, stats_y + 5 + i * 40))
            val_txt = self.text_font.render(valeur, True, couleur)
            self.screen.blit(val_txt, (300, stats_y + 5 + i * 40))
        
        # Afficher l'animation si active
        if self.animation_active:
            self.afficher_animation()
        
        pygame.display.flip()
    
    def afficher_ecran_fin(self):
        self.dessiner_fond_marin()
        
        # Titre avec effet de pulsation
        scale = 1.0 + 0.05 * math.sin(time.time() * 2)
        titre = self.title_font.render("FIN DE PARTIE", True, WHITE)
        titre_scaled = pygame.transform.scale(titre, 
                                            (int(titre.get_width() * scale), 
                                             int(titre.get_height() * scale)))
        self.screen.blit(titre_scaled, 
                        (SCREEN_WIDTH // 2 - titre_scaled.get_width() // 2, 
                         100 - (titre_scaled.get_height() - titre.get_height()) // 2))
        
        # Panneau de résultat
        result_panel = pygame.Surface((500, 300), pygame.SRCALPHA)
        result_panel.fill((0, 20, 40, 200))
        pygame.draw.rect(result_panel, GRID_BLUE, (0, 0, 500, 300), 3, 15)
        self.screen.blit(result_panel, (SCREEN_WIDTH // 2 - 250, 170))
        
        # Résultat avec effet de brillance
        if self.navires_coules_joueur == self.total_navires:
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
        
        self.screen.blit(glow_surf, 
                       (SCREEN_WIDTH // 2 - resultat.get_width() // 2 - glow_size, 
                        200 - glow_size))
        self.screen.blit(resultat, (SCREEN_WIDTH // 2 - resultat.get_width() // 2, 200))
        
        # Score avec animation
        score_y = 280
        for i, (texte, valeur, couleur) in enumerate([
            ("Vos navires coulés:", f"{self.navires_coules_joueur}/{self.total_navires}", RED),
            ("Navires ennemis coulés:", f"{self.navires_coules_bot}/{self.total_navires}", GREEN)
        ]):
            y_offset = 3 * math.sin(time.time() * 2 + i)
            
            txt = self.text_font.render(texte, True, WHITE)
            val = self.text_font.render(valeur, True, couleur)
            
            self.screen.blit(txt, (SCREEN_WIDTH // 2 - 170, score_y + i * 40 + y_offset))
            self.screen.blit(val, (SCREEN_WIDTH // 2 + 100, score_y + i * 40 + y_offset))
        
        # Boutons avec effet de pulsation
        glow = (30 * (math.sin(time.time() * 2) + 1))
        for texte, y in [("Rejouer", 450), ("Menu principal", 530)]:
            # Effet de halo
            halo_surf = pygame.Surface((320, 80), pygame.SRCALPHA)
            pygame.draw.rect(halo_surf, (0, 120, 255, int(glow)), (0, 0, 320, 80), border_radius=15)
            self.screen.blit(halo_surf, (SCREEN_WIDTH // 2 - 160, y - 40))
            
            rect = self.afficher_bouton(texte, (SCREEN_WIDTH // 2, y))
            
            # Gestion des clics sur les boutons
            if pygame.mouse.get_pressed()[0]:
                pos = pygame.mouse.get_pos()
                if rect.collidepoint(pos):
                    if texte == "Rejouer":
                        self.reset_game()
                        self.etat = 'placement'
                        time.sleep(0.2)  # Éviter les clics multiples
                    else:
                        self.reset_game()
                        self.etat = 'menu'
                        time.sleep(0.2)  # Éviter les clics multiples
        
        pygame.display.flip()

    def afficher_grille(self, grille, position, est_joueur=False):
        x_start, y_start = position
    
        # Dessiner le fond de la grille (fond marin sombre)
        pygame.draw.rect(self.screen, DARK_BLUE, (x_start, y_start, GRID_WIDTH, GRID_HEIGHT))
        pygame.draw.rect(self.screen, GRID_BLUE, (x_start, y_start, GRID_WIDTH, GRID_HEIGHT), 3)
    
        # Dessiner les lignes de la grille
        for i in range(1, self.taille_grille):
            # Lignes horizontales avec effet d'ondulation
            offset = 1 * math.sin(time.time() * 2 + i * 0.2)
            pygame.draw.line(self.screen, GRID_BLUE, 
                           (x_start, y_start + i * CELL_SIZE + offset),
                           (x_start + GRID_WIDTH, y_start + i * CELL_SIZE + offset), 1)
        
            # Lignes verticales
            pygame.draw.line(self.screen, GRID_BLUE, 
                           (x_start + i * CELL_SIZE, y_start),
                           (x_start + i * CELL_SIZE, y_start + GRID_HEIGHT), 1)
    
        # Dessiner les cellules et les navires
        for i in range(self.taille_grille):
            for j in range(self.taille_grille):
                cell_x = x_start + j * CELL_SIZE
                cell_y = y_start + i * CELL_SIZE
                cell_rect = pygame.Rect(cell_x, cell_y, CELL_SIZE, CELL_SIZE)
            
                # Déterminer l'orientation du navire (si applicable)
                orientation = None
                taille = 0
            
                if grille[i][j] == 'N' and est_joueur:
                    # Déterminer l'orientation en vérifiant les cellules adjacentes
                    # Horizontal si des navires à droite ou à gauche
                    if (j < self.taille_grille-1 and grille[i][j+1] in ['N', 'X']) or \
                       (j > 0 and grille[i][j-1] in ['N', 'X']):
                        orientation = 'H'
                    
                        # Compter la taille du navire horizontal
                        debut = j
                        while debut > 0 and grille[i][debut-1] in ['N', 'X']:
                            debut -= 1
                    
                        fin = j
                        while fin < self.taille_grille-1 and grille[i][fin+1] in ['N', 'X']:
                            fin += 1
                    
                        taille = fin - debut + 1
                    
                        # Dessiner le bateau seulement depuis le début
                        if j == debut:
                            self.dessiner_bateau(cell_x, cell_y, taille, 'H', DEEP_BLUE)
                    # Vertical si des navires en haut ou en bas
                    elif (i < self.taille_grille-1 and grille[i+1][j] in ['N', 'X']) or \
                         (i > 0 and grille[i-1][j] in ['N', 'X']):
                        orientation = 'V'
                    
                        # Compter la taille du navire vertical
                        debut = i
                        while debut > 0 and grille[debut-1][j] in ['N', 'X']:
                            debut -= 1
                    
                        fin = i
                        while fin < self.taille_grille-1 and grille[fin+1][j] in ['N', 'X']:
                            fin += 1
                    
                        taille = fin - debut + 1
                    
                        # Dessiner le bateau seulement depuis le début
                        if i == debut:
                            self.dessiner_bateau(cell_x, cell_y, taille, 'V', DEEP_BLUE)
                    else:
                        # Navire de taille 1 ou isolé
                        pygame.draw.rect(self.screen, DEEP_BLUE, cell_rect)
                        # Détails du bateau
                        pygame.draw.rect(self.screen, LIGHT_BLUE, 
                                       (cell_x + 5, cell_y + 5, CELL_SIZE - 10, CELL_SIZE - 10), 1)
            
                elif grille[i][j] == 'X':
                    # Explosion pour les cases touchées
                    pygame.draw.rect(self.screen, RED, cell_rect)
                    for k in range(3):  # Plusieurs lignes pour l'effet d'explosion
                        angle = k * 60 + time.time() * 50 % 360  # Animation de rotation
                        length = CELL_SIZE * 0.4
                        center_x, center_y = cell_x + CELL_SIZE // 2, cell_y + CELL_SIZE // 2
                        end_x = center_x + length * math.cos(math.radians(angle))
                        end_y = center_y + length * math.sin(math.radians(angle))
                        pygame.draw.line(self.screen, YELLOW, (center_x, center_y), (end_x, end_y), 3)
                
                    # X au centre
                    pygame.draw.line(self.screen, BLACK, 
                                   (cell_x + 5, cell_y + 5), 
                                   (cell_x + CELL_SIZE - 5, cell_y + CELL_SIZE - 5), 2)
                    pygame.draw.line(self.screen, BLACK, 
                                   (cell_x + CELL_SIZE - 5, cell_y + 5), 
                                   (cell_x + 5, cell_y + CELL_SIZE - 5), 2)
            
                elif grille[i][j] == 'O':
                    # Effet d'éclaboussure pour les tirs manqués
                    center_x, center_y = cell_x + CELL_SIZE // 2, cell_y + CELL_SIZE // 2
                
                    # Cercle d'eau
                    pygame.draw.circle(self.screen, WATER_BLUE, (center_x, center_y), CELL_SIZE // 3)
                    pygame.draw.circle(self.screen, LIGHT_BLUE, (center_x, center_y), CELL_SIZE // 3, 1)
                
                    # Éclaboussures animées
                    for k in range(4):
                        angle = k * 90 + time.time() * 30 % 360
                        dist = 2 * math.sin(time.time() * 5 + k) + 5
                        splash_x = center_x + dist * math.cos(math.radians(angle))
                        splash_y = center_y + dist * math.sin(math.radians(angle))
                        pygame.draw.circle(self.screen, LIGHT_BLUE, (splash_x, splash_y), 3)
    
        # Afficher les lettres (A-J) pour les colonnes avec effet d'ondulation
        for j in range(self.taille_grille):
            lettre = chr(65 + j)
            offset_y = 3 * math.sin(time.time() * 2 + j * 0.3)
            texte = self.small_font.render(lettre, True, WHITE)
            self.screen.blit(texte, (x_start + j * CELL_SIZE + CELL_SIZE // 2 - texte.get_width() // 2, 
                                 y_start - 25 + offset_y))
    
        # Afficher les chiffres (0-9) pour les lignes avec effet de pulsation
        for i in range(self.taille_grille):
            scale = 1.0 + 0.1 * math.sin(time.time() * 1.5 + i * 0.2)
            texte = self.small_font.render(str(i), True, WHITE)
            texte_scaled = pygame.transform.scale(texte, 
                                               (int(texte.get_width() * scale), 
                                                int(texte.get_height() * scale)))
            self.screen.blit(texte_scaled, 
                           (x_start - 25, 
                            y_start + i * CELL_SIZE + CELL_SIZE // 2 - texte_scaled.get_height() // 2))
    
        # Si on est en phase de placement, afficher l'aperçu du navire
        if self.etat == 'placement' and self.navire_index < len(self.navires_a_placer) and est_joueur:
            pos_souris = pygame.mouse.get_pos()
            cell_x = (pos_souris[0] - x_start) // CELL_SIZE
            cell_y = (pos_souris[1] - y_start) // CELL_SIZE
        
            if 0 <= cell_x < self.taille_grille and 0 <= cell_y < self.taille_grille:
                _, taille = self.navires_a_placer[self.navire_index]
            
                # Vérifier si le placement est valide
                placement_valide = self.verifier_placement_valide(cell_y, cell_x, taille, self.placement_orientation)
            
                # Afficher l'aperçu
                couleur = GREEN if placement_valide else RED
            
                # Dessiner l'aperçu du bateau
                if self.placement_orientation == 'H':
                    if placement_valide:
                        # Dessiner un bateau complet
                        self.dessiner_bateau(x_start + cell_x * CELL_SIZE, y_start + cell_y * CELL_SIZE, 
                                         taille, 'H', couleur, True)
                    else:
                        # Juste un rectangle rouge si invalide
                        for i in range(min(taille, self.taille_grille - cell_x)):
                            rect = pygame.Rect(x_start + (cell_x + i) * CELL_SIZE, 
                                             y_start + cell_y * CELL_SIZE, 
                                             CELL_SIZE, CELL_SIZE)
                            pygame.draw.rect(self.screen, couleur, rect, 3)
                else:  # Vertical
                    if placement_valide:
                        # Dessiner un bateau complet
                        self.dessiner_bateau(x_start + cell_x * CELL_SIZE, y_start + cell_y * CELL_SIZE, 
                                         taille, 'V', couleur, True)
                    else:
                        # Juste un rectangle rouge si invalide
                        for i in range(min(taille, self.taille_grille - cell_y)):
                            rect = pygame.Rect(x_start + cell_x * CELL_SIZE, 
                                             y_start + (cell_y + i) * CELL_SIZE, 
                                             CELL_SIZE, CELL_SIZE)
                            pygame.draw.rect(self.screen, couleur, rect, 3)

    def afficher_animation(self):
        """Affiche une animation au milieu de l'écran"""
        # Calculer le temps écoulé depuis le début de l'animation
        temps_ecoule = time.time() - self.animation_debut
    
        if temps_ecoule < self.animation_duree:
            # Calcul de l'opacité (fondu entrant puis sortant)
            if temps_ecoule < self.animation_duree / 2:
                opacite = min(255, int(temps_ecoule * 510 / self.animation_duree))
            else:
                opacite = max(0, int(255 - (temps_ecoule - self.animation_duree / 2) * 510 / self.animation_duree))
        
            # Surface semi-transparente pour le fond
            fond = pygame.Surface((SCREEN_WIDTH, 150), pygame.SRCALPHA)
            fond.fill((0, 0, 0, min(200, opacite)))  # Fond noir semi-transparent
        
            # Calculer l'échelle avec effet de rebond
            scale = 1.0
            if temps_ecoule < 0.3:
                scale = 0.5 + 1.5 * temps_ecoule / 0.3  # Grandir rapidement
            elif temps_ecoule < 0.5:
                scale = 1.0 + 0.2 * math.sin((temps_ecoule - 0.3) * math.pi / 0.2)  # Petit rebond
        
            # Texte de l'animation
            texte = self.animation_font.render(self.animation_message, True, self.animation_couleur)
            texte.set_alpha(opacite)
        
            # Appliquer l'échelle
            texte_scaled = pygame.transform.scale(texte, 
                                             (int(texte.get_width() * scale), 
                                              int(texte.get_height() * scale)))
        
            # Positionner au centre
            rect = texte_scaled.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        
            # Ajouter un halo autour du texte
            glow_surf = pygame.Surface((rect.width + 40, rect.height + 40), pygame.SRCALPHA)
            glow_color = (*self.animation_couleur[:3], min(100, opacite))
            pygame.draw.ellipse(glow_surf, glow_color, 
                             (0, 0, rect.width + 40, rect.height + 40))
        
            # Afficher le fond
            self.screen.blit(fond, (0, SCREEN_HEIGHT // 2 - 75))
        
            # Afficher le halo puis le texte
            self.screen.blit(glow_surf, (rect.x - 20, rect.y - 20))
            self.screen.blit(texte_scaled, rect)
        else:
            # Fin de l'animation
            self.animation_active = False

    def demarrer_animation(self, message, couleur):
        """Démarre une animation avec le message et la couleur spécifiés"""
        self.animation_active = True
        self.animation_message = message
        self.animation_couleur = couleur
        self.animation_debut = time.time()

    def verifier_placement_valide(self, ligne, colonne, taille, orientation):
        """Vérifie si le placement d'un navire est valide"""
        if orientation == 'H':
            if colonne + taille > self.taille_grille:
                return False
        
            # Vérifier si l'emplacement est libre
            for i in range(taille):
                if self.grille_joueur[ligne][colonne + i] != ' ':
                    return False
        
            return True
    
        else:  # Vertical
            if ligne + taille > self.taille_grille:
                return False
        
            # Vérifier si l'emplacement est libre
            for i in range(taille):
                if self.grille_joueur[ligne + i][colonne] != ' ':
                    return False
        
            return True

    def placer_navire(self, ligne, colonne, taille, orientation):
        """Place un navire sur la grille"""
        if orientation == 'H':
            for i in range(taille):
                self.grille_joueur[ligne][colonne + i] = 'N'
        else:  # Vertical
            for i in range(taille):
                self.grille_joueur[ligne + i][colonne] = 'N'

    def placer_navires_aleatoirement(self, grille):
        """Place aléatoirement les navires sur la grille"""
        for nom_navire, taille in self.navires.items():
            placement_valide = False
        
            while not placement_valide:
                # Choix aléatoire de l'orientation (0: horizontal, 1: vertical)
                orientation = random.randint(0, 1)
            
                if orientation == 0:  # Horizontal
                    x = random.randint(0, self.taille_grille - 1)
                    y = random.randint(0, self.taille_grille - taille)
                
                    # Vérifier si l'emplacement est libre
                    libre = True
                    for i in range(taille):
                        if grille[x][y + i] != ' ':
                            libre = False
                            break
                
                    # Placer le navire si l'emplacement est libre
                    if libre:
                        for i in range(taille):
                            grille[x][y + i] = 'N'
                        placement_valide = True
            
                else:  # Vertical
                    x = random.randint(0, self.taille_grille - taille)
                    y = random.randint(0, self.taille_grille - 1)
                
                    # Vérifier si l'emplacement est libre
                    libre = True
                    for i in range(taille):
                        if grille[x + i][y] != ' ':
                            libre = False
                            break
                
                    # Placer le navire si l'emplacement est libre
                    if libre:
                        for i in range(taille):
                            grille[x + i][y] = 'N'
                        placement_valide = True

    def tir_joueur(self, ligne, colonne):
        """Gère le tir du joueur"""
        # Vérifier si déjà tiré à cet endroit
        if self.grille_tirs_joueur[ligne][colonne] != ' ':
            return False
    
        # Vérifier si touché ou manqué
        if self.grille_bot[ligne][colonne] == 'N':
            self.grille_tirs_joueur[ligne][colonne] = 'X'
            self.grille_bot[ligne][colonne] = 'X'  # Marquer aussi comme touché sur la grille du bot
        
            # Jouer le son si disponible
            if self.sons_actifs and self.sound_hit:
                self.sound_hit.play()
        
            # Vérifier si le navire est coulé
            if self.verifier_navire_coule(self.grille_bot, ligne, colonne):
                self.navires_coules_bot += 1
            
                # Animation
                self.demarrer_animation("COULÉ !", (255, 50, 50))
            
                # Jouer le son si disponible
                if self.sons_actifs and self.sound_sink:
                    self.sound_sink.play()
            else:
                # Animation
                self.demarrer_animation("TOUCHÉ !", (255, 165, 0))
        else:
            self.grille_tirs_joueur[ligne][colonne] = 'O'
        
            # Animation
            self.demarrer_animation("MANQUÉ !", LIGHT_BLUE)
        
            # Jouer le son si disponible
            if self.sons_actifs and self.sound_miss:
                self.sound_miss.play()
    
        return True

    def tir_bot(self):
        """Gère le tir du bot selon la difficulté"""
        resultat = None
    
        if self.difficulte == FACILE:
            resultat = self.tir_bot_facile()
        elif self.difficulte == MOYEN:
            resultat = self.tir_bot_moyen()
        else:
            resultat = self.tir_bot_difficile()
    
        return resultat

    def verifier_navire_coule_depuis_dernier_tir(self):
        """Vérifie si le dernier tir du bot a coulé un navire"""
        if self.dernier_tir_bot:
            ligne, colonne = self.dernier_tir_bot
            return self.verifier_navire_coule(self.grille_joueur, ligne, colonne)
        return False

    def tir_bot_facile(self):
        """Stratégie de tir facile : complètement aléatoire"""
        while True:
            ligne = random.randint(0, self.taille_grille - 1)
            colonne = random.randint(0, self.taille_grille - 1)
        
            # Vérifier si déjà tiré à cet endroit
            if self.grille_tirs_bot[ligne][colonne] == ' ':
                return self.executer_tir_bot(ligne, colonne)

    def tir_bot_moyen(self):
        """Stratégie de tir moyen : aléatoire + cibler les cases adjacentes aux coups réussis"""
        # Si le dernier tir a touché un navire, essayer de tirer autour
        if self.dernier_tir_bot and self.grille_tirs_bot[self.dernier_tir_bot[0]][self.dernier_tir_bot[1]] == 'X':
            ligne, colonne = self.dernier_tir_bot
        
            # Directions possibles (haut, droite, bas, gauche)
            directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
            random.shuffle(directions)
        
            for dx, dy in directions:
                nouvelle_ligne, nouvelle_colonne = ligne + dx, colonne + dy
            
                # Vérifier si la case est valide et n'a pas déjà été ciblée
                if (0 <= nouvelle_ligne < self.taille_grille and 
                    0 <= nouvelle_colonne < self.taille_grille and 
                    self.grille_tirs_bot[nouvelle_ligne][nouvelle_colonne] == ' '):
                    return self.executer_tir_bot(nouvelle_ligne, nouvelle_colonne)
    
        # Si pas de coup précédent réussi ou pas de cible valide, tir aléatoire
        return self.tir_bot_facile()

    def tir_bot_difficile(self):
        """Stratégie de tir difficile : ciblage intelligent + mémorisation"""
        # Si on a des tirs réussis non explorés complètement, continuer la chasse
        if self.tirs_reussis_bot:
            ligne, colonne = self.tirs_reussis_bot[0]
        
            # Si on a une direction de chasse, continuer dans cette direction
            if self.direction_chasse:
                dx, dy = self.direction_chasse
                nouvelle_ligne, nouvelle_colonne = ligne + dx, colonne + dy
            
                # Vérifier si la case est valide
                if (0 <= nouvelle_ligne < self.taille_grille and 
                    0 <= nouvelle_colonne < self.taille_grille and 
                    self.grille_tirs_bot[nouvelle_ligne][nouvelle_colonne] == ' '):
                    resultat = self.executer_tir_bot(nouvelle_ligne, nouvelle_colonne)
                
                    # Si le tir est réussi, continuer dans cette direction
                    if resultat == 'touche':
                        return resultat
                    else:
                        # Sinon, inverser la direction
                        self.direction_chasse = (-dx, -dy)
                        return resultat
            
                # Si on atteint une limite dans cette direction, inverser la direction
                self.direction_chasse = (-dx, -dy)
                nouvelle_ligne, nouvelle_colonne = self.tirs_reussis_bot[0][0] + self.direction_chasse[0], self.tirs_reussis_bot[0][1] + self.direction_chasse[1]
            
                # Vérifier si la nouvelle case est valide
                if (0 <= nouvelle_ligne < self.taille_grille and 
                    0 <= nouvelle_colonne < self.taille_grille and 
                    self.grille_tirs_bot[nouvelle_ligne][nouvelle_colonne] == ' '):
                    return self.executer_tir_bot(nouvelle_ligne, nouvelle_colonne)
            
                # Si on ne peut pas continuer dans les deux directions, passer à un autre tir réussi ou tirer aléatoirement
                self.tirs_reussis_bot.pop(0)
                self.direction_chasse = None
                return self.tir_bot_difficile()
        
            # Si on n'a pas de direction, essayer les 4 directions
            directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
            random.shuffle(directions)
        
            for dx, dy in directions:
                nouvelle_ligne, nouvelle_colonne = ligne + dx, colonne + dy
            
                if (0 <= nouvelle_ligne < self.taille_grille and 
                    0 <= nouvelle_colonne < self.taille_grille and 
                    self.grille_tirs_bot[nouvelle_ligne][nouvelle_colonne] == ' '):
                    resultat = self.executer_tir_bot(nouvelle_ligne, nouvelle_colonne)
                
                    if resultat == 'touche':
                        self.direction_chasse = (dx, dy)
                
                    return resultat
        
            # Si aucune des directions n'est valide, passer à un autre tir réussi ou tirer aléatoirement
            self.tirs_reussis_bot.pop(0)
            return self.tir_bot_difficile()
    
        # Tir intelligent en priorité sur les cases en damier pour optimiser la recherche
        cases_damier = []
        for i in range(self.taille_grille):
            for j in range(self.taille_grille):
                if (i + j) % 2 == 0 and self.grille_tirs_bot[i][j] == ' ':
                    cases_damier.append((i, j))
    
        if cases_damier and random.random() < 0.7:  # 70% de chance d'utiliser la stratégie du damier
            ligne, colonne = random.choice(cases_damier)
            return self.executer_tir_bot(ligne, colonne)
    
        # Sinon, tir aléatoire sur une case non ciblée
        cases_disponibles = []
        for i in range(self.taille_grille):
            for j in range(self.taille_grille):
                if self.grille_tirs_bot[i][j] == ' ':
                    cases_disponibles.append((i, j))
    
        if cases_disponibles:
            ligne, colonne = random.choice(cases_disponibles)
            return self.executer_tir_bot(ligne, colonne)
    
        return None  # Aucune case disponible (ne devrait pas arriver)

    def executer_tir_bot(self, ligne, colonne):
        """Exécute le tir du bot aux coordonnées spécifiées"""
        self.dernier_tir_bot = (ligne, colonne)
    
        # Vérifier si touché ou manqué
        if self.grille_joueur[ligne][colonne] == 'N':
            self.grille_tirs_bot[ligne][colonne] = 'X'
            self.grille_joueur[ligne][colonne] = 'X'  # Marquer aussi comme touché sur la grille du joueur
        
            # Jouer le son si disponible
            if self.sons_actifs and self.sound_hit:
                self.sound_hit.play()
        
            # Ajouter aux tirs réussis pour la stratégie difficile
            if self.difficulte == DIFFICILE:
                self.tirs_reussis_bot.append((ligne, colonne))
        
            # Vérifier si le navire est coulé
            if self.verifier_navire_coule(self.grille_joueur, ligne, colonne):
                self.navires_coules_joueur += 1
            
                # Jouer le son si disponible
                if self.sons_actifs and self.sound_sink:
                    self.sound_sink.play()
            
                # Si en mode difficile, retirer les cases de ce navire de la liste des tirs réussis
                if self.difficulte == DIFFICILE:
                    self.tirs_reussis_bot = []
                    self.direction_chasse = None
        
            return 'touche'
        else:
            self.grille_tirs_bot[ligne][colonne] = 'O'
        
            # Jouer le son si disponible
            if self.sons_actifs and self.sound_miss:
                self.sound_miss.play()
            
            return 'manque'

    def verifier_navire_coule(self, grille, ligne, colonne):
        """Vérifie si un navire est entièrement coulé"""
        # Recherche horizontale
        debut_col = colonne
        while debut_col > 0 and (grille[ligne][debut_col-1] == 'N' or grille[ligne][debut_col-1] == 'X'):
            debut_col -= 1
    
        fin_col = colonne
        while fin_col < self.taille_grille - 1 and (grille[ligne][fin_col+1] == 'N' or grille[ligne][fin_col+1] == 'X'):
            fin_col += 1
    
        # Vérifier si toutes les cases horizontales sont touchées
        if debut_col != fin_col:
            for i in range(debut_col, fin_col + 1):
                if grille[ligne][i] == 'N':  # S'il reste une partie non touchée
                    return False
            return True
    
        # Recherche verticale
        debut_ligne = ligne
        while debut_ligne > 0 and (grille[debut_ligne-1][colonne] == 'N' or grille[debut_ligne-1][colonne] == 'X'):
            debut_ligne -= 1
    
        fin_ligne = ligne
        while fin_ligne < self.taille_grille - 1 and (grille[fin_ligne+1][colonne] == 'N' or grille[fin_ligne+1][colonne] == 'X'):
            fin_ligne += 1
    
        # Vérifier si toutes les cases verticales sont touchées
        if debut_ligne != fin_ligne:
            for i in range(debut_ligne, fin_ligne + 1):
                if grille[i][colonne] == 'N':  # S'il reste une partie non touchée
                    return False
            return True
    
        # Si c'est un navire de taille 1
        return True
    def verifier_fin_jeu(self):
       """Vérifie si le jeu est terminé"""
       return self.navires_coules_joueur == self.total_navires or self.navires_coules_bot == self.total_navires

    def gerer_evenements(self):
       """Gère les événements Pygame"""
       for event in pygame.event.get():
           if event.type == QUIT:
               pygame.quit()
               sys.exit()
       
           elif event.type == KEYDOWN:
               # Changer l'orientation pendant le placement
               if self.etat == 'placement' and event.key == K_r:
                   self.placement_orientation = 'V' if self.placement_orientation == 'H' else 'H'
       
           elif event.type == MOUSEBUTTONDOWN and event.button == 1:  # Clic gauche
               if self.etat == 'menu':
                   self.gerer_clic_menu()
               elif self.etat == 'placement':
                   self.gerer_clic_placement()
               elif self.etat == 'jeu':
                   self.gerer_clic_jeu()

    def gerer_clic_menu(self):
       """Gère les clics sur le menu principal"""
       x, y = pygame.mouse.get_pos()
   
       # Vérifier les boutons
       bouton_jouer = pygame.Rect(SCREEN_WIDTH // 2 - 150, 300 - 30, 300, 60)
       bouton_difficulte = pygame.Rect(SCREEN_WIDTH // 2 - 150, 380 - 30, 300, 60)
       bouton_quitter = pygame.Rect(SCREEN_WIDTH // 2 - 150, 460 - 30, 300, 60)
   
       if bouton_jouer.collidepoint(x, y):
           self.etat = 'placement'
       elif bouton_difficulte.collidepoint(x, y):
           # Changer de difficulté
           if self.difficulte == FACILE:
               self.difficulte = MOYEN
           elif self.difficulte == MOYEN:
               self.difficulte = DIFFICILE
           else:
               self.difficulte = FACILE
       elif bouton_quitter.collidepoint(x, y):
           pygame.quit()
           sys.exit()

    def gerer_clic_placement(self):
       """Gère les clics pendant la phase de placement"""
       if self.navire_index >= len(self.navires_a_placer):
           return
   
       x, y = pygame.mouse.get_pos()
       grid_x = SCREEN_WIDTH // 2 - GRID_WIDTH // 2
       grid_y = 120
   
       # Vérifier si le clic est dans la grille
       if not (grid_x <= x < grid_x + GRID_WIDTH and grid_y <= y < grid_y + GRID_HEIGHT):
           return
   
       # Convertir les coordonnées du clic en indices de grille
       cell_x = (x - grid_x) // CELL_SIZE
       cell_y = (y - grid_y) // CELL_SIZE
   
       # Récupérer le navire à placer
       nom, taille = self.navires_a_placer[self.navire_index]
   
       # Vérifier si le placement est valide
       if self.verifier_placement_valide(cell_y, cell_x, taille, self.placement_orientation):
           # Placer le navire
           self.placer_navire(cell_y, cell_x, taille, self.placement_orientation)
       
           # Passer au navire suivant
           self.navire_index += 1

    def gerer_clic_jeu(self):
       """Gère les clics pendant la phase de jeu"""
       if self.verifier_fin_jeu():
           self.etat = 'fin'
           return
   
       x, y = pygame.mouse.get_pos()
       grid_x = SCREEN_WIDTH - 150 - GRID_WIDTH
       grid_y = 120
   
       # Vérifier si le clic est dans la grille des tirs
       if not (grid_x <= x < grid_x + GRID_WIDTH and grid_y <= y < grid_y + GRID_HEIGHT):
           return
   
       # Convertir les coordonnées du clic en indices de grille
       cell_x = (x - grid_x) // CELL_SIZE
       cell_y = (y - grid_y) // CELL_SIZE
   
       # Effectuer le tir du joueur
       if self.tir_joueur(cell_y, cell_x):
           # Vérifier si le jeu est terminé après le tir du joueur
           if self.verifier_fin_jeu():
               self.etat = 'fin'
               return
       
           # Tour du bot
           time.sleep(0.5)  # Petite pause pour montrer le résultat du tir du joueur
           self.tir_bot()
       
           # Vérifier si le jeu est terminé après le tir du bot
           if self.verifier_fin_jeu():
               self.etat = 'fin'

    def jouer(self):
        """Boucle principale du jeu"""
        while True:
            self.gerer_evenements()

            if self.etat == 'menu':
                self.afficher_menu()
            elif self.etat == 'placement':
                self.afficher_ecran_placement()
            elif self.etat == 'jeu':
                self.afficher_ecran_jeu()
            elif self.etat == 'fin':
                self.afficher_ecran_fin()

            self.clock.tick(60)


    # ------------------------------
    # Point d'entrée du programme
    # ------------------------------
if __name__ == "__main__":
    jeu = BatailleNavale()
    jeu.jouer()

