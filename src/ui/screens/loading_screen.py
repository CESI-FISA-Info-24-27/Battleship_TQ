import pygame
import sys
import os
import time
import math
import random
from src.utils.constants import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, BLUE, LIGHT_BLUE, DARK_BLUE, RED, GREEN, YELLOW, FPS, TITLE, GRAY

class LoadingScreen:
    """Écran de chargement avec animation rétro de bataille navale"""
    
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.clock = game.clock
        self.start_time = time.time()
        self.max_duration = 5  # 5 secondes maximum
        
        # Polices
        self.title_font = pygame.font.Font(None, 72)
        self.subtitle_font = pygame.font.Font(None, 32)
        self.loading_font = pygame.font.Font(None, 24)
        
        # Couleurs
        self.background_color = (10, 30, 60)  # Bleu marine profond
        self.grid_color = (20, 50, 80)  # Bleu un peu plus clair pour la grille
        
        # Animation de vague
        self.wave_offset = 0
        self.wave_speed = 2
        
        # Barre de chargement
        self.loading_progress = 0
        self.loading_width = SCREEN_WIDTH * 0.7
        self.loading_height = 30
        self.loading_x = (SCREEN_WIDTH - self.loading_width) / 2
        self.loading_y = SCREEN_HEIGHT * 0.7
        
        # Animation de bateaux
        self.ships = [
            {
                'x': SCREEN_WIDTH * 0.2,
                'y': SCREEN_HEIGHT * 0.4,
                'width': 70,
                'height': 20,
                'color': RED,
                'accent_color': (180, 50, 50),
                'direction': 1,
                'has_fired': False,
                'fire_time': 0,
                'offset_y': 0
            },
            {
                'x': SCREEN_WIDTH * 0.8,
                'y': SCREEN_HEIGHT * 0.4,
                'width': 70,
                'height': 20,
                'color': BLUE,
                'accent_color': LIGHT_BLUE,
                'direction': -1,
                'has_fired': False,
                'fire_time': 0,
                'offset_y': 0
            }
        ]
        
        # Projectiles
        self.projectiles = []
        
        # Explosions
        self.explosions = []
        
        # Textes aléatoires pour le chargement
        self.loading_texts = [
            "Préparation des navires...",
            "Chargement des canons...",
            "Recrutement des marins...",
            "Déploiement de la flotte...",
            "Scan des eaux ennemies...",
            "Calibration des radars...",
            "Traçage des coordonnées...",
            "Armement des torpilles...",
            "Mise à jour des cartes..."
        ]
        self.current_text = random.choice(self.loading_texts)
        self.text_timer = 0
        self.text_change_interval = 60  # Frames avant changement de texte
        
        # Jouer un son de démarrage
        self._play_start_sound()
        
    def _play_start_sound(self):
        """Joue un son de démarrage"""
        try:
            if pygame.mixer.get_init():
                sound_path = os.path.join("assets", "sounds", "start.wav")
                if os.path.exists(sound_path):
                    start_sound = pygame.mixer.Sound(sound_path)
                    start_sound.play()
        except:
            pass
    
    def update(self):
        """Mise à jour de l'état de l'écran de chargement"""
        # Calculer la progression basée sur le temps écoulé
        elapsed_time = time.time() - self.start_time
        self.loading_progress = min(1.0, elapsed_time / self.max_duration)
        
        # Animer la vague
        self.wave_offset += self.wave_speed
        
        # Mettre à jour les textes de chargement
        self.text_timer += 1
        if self.text_timer >= self.text_change_interval:
            self.text_timer = 0
            self.current_text = random.choice(self.loading_texts)
        
        # Mettre à jour les bateaux
        for ship in self.ships:
            # Oscillation légère des bateaux
            ship['offset_y'] = math.sin(time.time() * 2) * 2.5
            
            # Tir aléatoire
            if not ship['has_fired'] and random.random() < 0.02:
                ship['has_fired'] = True
                ship['fire_time'] = time.time()
                
                # Position de départ du projectile
                if ship['direction'] > 0:
                    start_x = ship['x'] + ship['width'] + 5
                else:
                    start_x = ship['x'] - 5
                
                start_y = ship['y'] + ship['height'] / 2
                
                # Ajouter le projectile
                self.projectiles.append({
                    'x': start_x,
                    'y': start_y,
                    'dx': ship['direction'] * 6,
                    'dy': random.uniform(-0.3, 0.3),
                    'color': ship['color'],
                    'size': 4
                })
                
                # Jouer un son de tir
                self._play_fire_sound()
        
        # Vérifier si les bateaux peuvent tirer à nouveau
        for ship in self.ships:
            if ship['has_fired'] and time.time() - ship['fire_time'] > 1:
                ship['has_fired'] = False
        
        # Mettre à jour les projectiles
        new_projectiles = []
        for projectile in self.projectiles:
            projectile['x'] += projectile['dx']
            projectile['y'] += projectile['dy']
            
            # Vérifier collision avec les bateaux
            hit = False
            for ship in self.ships:
                if (projectile['dx'] * ship['direction'] < 0 and  # Vérifie que le projectile va vers le bateau
                    ship['x'] <= projectile['x'] <= ship['x'] + ship['width'] and
                    ship['y'] <= projectile['y'] <= ship['y'] + ship['height']):
                    
                    # Créer une explosion
                    self.explosions.append({
                        'x': projectile['x'],
                        'y': projectile['y'],
                        'size': 5,
                        'max_size': 20,
                        'growth': 1.5,
                        'color': YELLOW
                    })
                    
                    # Jouer un son d'explosion
                    self._play_explosion_sound()
                    hit = True
                    break
            
            # Vérifier sortie de l'écran
            if (0 <= projectile['x'] <= SCREEN_WIDTH and 
                0 <= projectile['y'] <= SCREEN_HEIGHT and
                not hit):
                new_projectiles.append(projectile)
        
        self.projectiles = new_projectiles
        
        # Mettre à jour les explosions
        new_explosions = []
        for explosion in self.explosions:
            explosion['size'] += explosion['growth']
            if explosion['size'] < explosion['max_size']:
                new_explosions.append(explosion)
        
        self.explosions = new_explosions
        
        # Vérifier si le chargement est terminé
        if self.loading_progress >= 1.0:
            return True
            
        return False
    
    def _play_fire_sound(self):
        """Joue un son de tir"""
        try:
            if pygame.mixer.get_init():
                sound_path = os.path.join("assets", "sounds", "fire.wav")
                if os.path.exists(sound_path):
                    fire_sound = pygame.mixer.Sound(sound_path)
                    fire_sound.set_volume(0.3)
                    fire_sound.play()
        except:
            pass
    
    def _play_explosion_sound(self):
        """Joue un son d'explosion"""
        try:
            if pygame.mixer.get_init():
                sound_path = os.path.join("assets", "sounds", "explosion.wav")
                if os.path.exists(sound_path):
                    explosion_sound = pygame.mixer.Sound(sound_path)
                    explosion_sound.set_volume(0.4)
                    explosion_sound.play()
        except:
            pass
    
    def _draw_stylized_ship(self, ship):
        """Dessine un bateau plus stylisé"""
        # Appliquer l'oscillation
        y = ship['y'] + ship['offset_y']
        
        # Base du navire (coque)
        ship_rect = pygame.Rect(ship['x'], y, ship['width'], ship['height'])
        pygame.draw.rect(self.screen, ship['color'], ship_rect, border_radius=8)
        
        # Parties additionnelles pour rendre le bateau plus détaillé
        if ship['direction'] > 0:  # Navire orienté vers la droite
            # Proue du navire (forme triangulaire à l'avant)
            bow_points = [
                (ship['x'] + ship['width'], y + ship['height'] // 2),  # Point avant
                (ship['x'] + ship['width'] - 10, y),                   # Haut
                (ship['x'] + ship['width'] - 10, y + ship['height'])   # Bas
            ]
            pygame.draw.polygon(self.screen, ship['accent_color'], bow_points)
            
            # Structure supérieure (cabine/passerelle)
            cabin_rect = pygame.Rect(
                ship['x'] + ship['width'] // 3, 
                y - ship['height'] // 2,
                ship['width'] // 3,
                ship['height'] // 2
            )
            pygame.draw.rect(self.screen, ship['accent_color'], cabin_rect, border_radius=3)
            
            # Petite structure secondaire
            small_cabin = pygame.Rect(
                ship['x'] + ship['width'] // 5,
                y - ship['height'] // 4,
                ship['width'] // 6,
                ship['height'] // 4
            )
            pygame.draw.rect(self.screen, ship['accent_color'], small_cabin, border_radius=2)
            
            # Canon
            canon_length = ship['width'] // 4
            canon_height = ship['height'] // 3
            canon_rect = pygame.Rect(
                ship['x'] + ship['width'] - 5,
                y + ship['height'] // 3,
                canon_length,
                canon_height
            )
            pygame.draw.rect(self.screen, BLACK, canon_rect, border_radius=2)
            
        else:  # Navire orienté vers la gauche
            # Proue du navire (forme triangulaire à l'avant)
            bow_points = [
                (ship['x'], y + ship['height'] // 2),  # Point avant
                (ship['x'] + 10, y),                   # Haut
                (ship['x'] + 10, y + ship['height'])   # Bas
            ]
            pygame.draw.polygon(self.screen, ship['accent_color'], bow_points)
            
            # Structure supérieure (cabine/passerelle)
            cabin_rect = pygame.Rect(
                ship['x'] + ship['width'] // 3, 
                y - ship['height'] // 2,
                ship['width'] // 3,
                ship['height'] // 2
            )
            pygame.draw.rect(self.screen, ship['accent_color'], cabin_rect, border_radius=3)
            
            # Petite structure secondaire
            small_cabin = pygame.Rect(
                ship['x'] + ship['width'] // 2,
                y - ship['height'] // 4,
                ship['width'] // 6,
                ship['height'] // 4
            )
            pygame.draw.rect(self.screen, ship['accent_color'], small_cabin, border_radius=2)
            
            # Canon
            canon_length = ship['width'] // 4
            canon_height = ship['height'] // 3
            canon_rect = pygame.Rect(
                ship['x'] - canon_length + 5,
                y + ship['height'] // 3,
                canon_length,
                canon_height
            )
            pygame.draw.rect(self.screen, BLACK, canon_rect, border_radius=2)
            
        # Détails supplémentaires communs
        # Ligne de flottaison
        pygame.draw.line(
            self.screen,
            (200, 200, 200),
            (ship['x'], y + ship['height'] - 2),
            (ship['x'] + ship['width'], y + ship['height'] - 2),
            1
        )
        
        # Petits hublots
        num_portholes = 3
        porthole_radius = 2
        for i in range(num_portholes):
            porthole_x = ship['x'] + ship['width'] * (i + 1) / (num_portholes + 1)
            porthole_y = y + ship['height'] // 2
            pygame.draw.circle(self.screen, WHITE, (int(porthole_x), int(porthole_y)), porthole_radius)
    
    def render(self):
        """Affiche l'écran de chargement"""
        # Fond
        self.screen.fill(self.background_color)
        
        # Dessiner une grille pour simuler un radar/carte marine
        grid_size = 40
        for x in range(0, SCREEN_WIDTH, grid_size):
            pygame.draw.line(self.screen, self.grid_color, (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, grid_size):
            pygame.draw.line(self.screen, self.grid_color, (0, y), (SCREEN_WIDTH, y), 1)
        
        # Dessiner quelques points comme des étoiles/radar
        for i in range(50):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            size = random.randint(1, 3)
            brightness = random.randint(150, 255)
            pygame.draw.circle(self.screen, (brightness, brightness, brightness), (x, y), size)
        
        # Dessiner les bateaux stylisés
        for ship in self.ships:
            self._draw_stylized_ship(ship)
        
        # Dessiner les projectiles
        for projectile in self.projectiles:
            pygame.draw.circle(
                self.screen,
                projectile['color'],
                (int(projectile['x']), int(projectile['y'])),
                projectile['size']
            )
            
            # Traînée simple du projectile
            for i in range(5):
                trail_x = int(projectile['x'] - projectile['dx'] * i * 0.2)
                trail_y = int(projectile['y'] - projectile['dy'] * i * 0.2)
                trail_size = projectile['size'] * (5 - i) / 7
                pygame.draw.circle(
                    self.screen,
                    projectile['color'],
                    (trail_x, trail_y),
                    trail_size
                )
        
        # Dessiner les explosions
        for explosion in self.explosions:
            pygame.draw.circle(
                self.screen,
                explosion['color'],
                (int(explosion['x']), int(explosion['y'])),
                int(explosion['size'])
            )
            
            # Cercle intérieur blanc
            if explosion['size'] > 5:
                inner_size = explosion['size'] * 0.6
                pygame.draw.circle(
                    self.screen,
                    WHITE,
                    (int(explosion['x']), int(explosion['y'])),
                    int(inner_size)
                )
        
        # Titre
        title_text = self.title_font.render(TITLE, True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 5))
        self.screen.blit(title_text, title_rect)
        
        # Sous-titre
        subtitle_text = self.subtitle_font.render("Préparez-vous pour la bataille!", True, LIGHT_BLUE)
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH // 2, title_rect.bottom + 20))
        self.screen.blit(subtitle_text, subtitle_rect)
        
        # Cadre de la barre de chargement
        loading_frame = pygame.Rect(
            self.loading_x - 5,
            self.loading_y - 5,
            self.loading_width + 10,
            self.loading_height + 10
        )
        pygame.draw.rect(self.screen, WHITE, loading_frame, 2, border_radius=10)
        
        # Fond de la barre de chargement
        loading_bg = pygame.Rect(
            self.loading_x,
            self.loading_y,
            self.loading_width,
            self.loading_height
        )
        pygame.draw.rect(self.screen, (5, 20, 50), loading_bg, border_radius=8)
        
        # Barre de chargement
        wave_width = int(self.loading_width * self.loading_progress)
        if wave_width > 0:
            progress_rect = pygame.Rect(
                self.loading_x,
                self.loading_y,
                wave_width,
                self.loading_height
            )
            # Utiliser une couleur dégradée
            progress_color = (30, 100, 200)
            pygame.draw.rect(self.screen, progress_color, progress_rect, border_radius=8)
        
        # Pourcentage et texte
        percentage = int(self.loading_progress * 100)
        percentage_text = self.loading_font.render(f"{percentage}%", True, WHITE)
        percentage_rect = percentage_text.get_rect(midright=(self.loading_x + self.loading_width + 40, self.loading_y + self.loading_height / 2))
        self.screen.blit(percentage_text, percentage_rect)
        
        loading_text = self.loading_font.render(self.current_text, True, LIGHT_BLUE)
        loading_rect = loading_text.get_rect(center=(
            self.loading_x + self.loading_width / 2,  # Centré horizontalement dans la barre
            self.loading_y + self.loading_height / 2  # Centré verticalement dans la barre
        ))
        self.screen.blit(loading_text, loading_rect)
        
        # Version
        version_text = pygame.font.Font(None, 20).render("v1.0", True, GRAY)
        version_rect = version_text.get_rect(bottomright=(SCREEN_WIDTH - 10, SCREEN_HEIGHT - 10))
        self.screen.blit(version_text, version_rect)
        
        # Instructions
        instructions_text = self.loading_font.render("Appuyez sur ESPACE pour passer", True, (150, 150, 150))
        instructions_rect = instructions_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
        self.screen.blit(instructions_text, instructions_rect)
        
        pygame.display.flip()
    
    def run(self):
        """Exécuter l'écran de chargement complet"""
        # Boucle principale de l'écran de chargement
        while True:
            # Gérer les événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    # Permettre de sauter l'écran de chargement avec Espace ou Entrée
                    if event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                        return
            
            # Mettre à jour l'état
            if self.update():
                # Animation terminée, sortir de la boucle
                break
            
            # Afficher l'écran de chargement
            self.render()
            
            # Limiter la fréquence d'images
            self.clock.tick(FPS)