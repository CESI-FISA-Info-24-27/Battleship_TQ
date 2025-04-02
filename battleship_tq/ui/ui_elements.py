# ui_elements.py
import pygame
import math
import time
from game.constants import WHITE, DARK_BLUE, GRID_BLUE, LIGHT_BLUE

class Button:
    def __init__(self, text, pos, size=(300, 60), font_size=24, hover_effect=True):
        self.text = text
        self.x, self.y = pos
        self.width, self.height = size
        self.rect = pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)
        self.font_size = font_size
        self.hover_effect = hover_effect
        self.hovered = False
        self.clicked = False
        self.font = pygame.font.SysFont("Arial", self.font_size)
    
    def draw(self, screen, time_value=None):
        mouse_pos = pygame.mouse.get_pos()
        self.hovered = self.rect.collidepoint(mouse_pos)
        
        # Couleur du bouton
        color = GRID_BLUE if self.hovered else DARK_BLUE
        
        # Effet de pulsation pour les boutons avec hover_effect
        glow = 0
        if self.hover_effect:
            if self.hovered:
                glow = 30
            else:
                glow = (20 * (math.sin(time_value or time.time() * 3) + 1))
            
            # Effet de halo
            halo_surf = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
            pygame.draw.rect(halo_surf, (0, 120, 255, int(glow)), (0, 0, self.width + 20, self.height + 20), border_radius=15)
            screen.blit(halo_surf, (self.rect.x - 10, self.rect.y - 10))
        
        # Dessiner le bouton avec des bords arrondis
        pygame.draw.rect(screen, color, self.rect, 0, 12)
        pygame.draw.rect(screen, LIGHT_BLUE, self.rect, 2, 12)
        
        # Ajouter un effet de brillance quand survolé
        if self.hovered:
            highlight = pygame.Surface((self.width - 4, 10), pygame.SRCALPHA)
            highlight.fill((255, 255, 255, 90))
            screen.blit(highlight, (self.rect.left + 2, self.rect.top + 5))
        
        # Texte du bouton
        text_surface = self.font.render(self.text, True, WHITE)
        screen.blit(text_surface, (self.x - text_surface.get_width() // 2, self.y - text_surface.get_height() // 2))
    
    def check_click(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_click = pygame.mouse.get_pressed()[0]
        
        if self.rect.collidepoint(mouse_pos):
            if mouse_click and not self.clicked:
                self.clicked = True
                return True
            elif not mouse_click:
                self.clicked = False
        
        return False

class TextBox:
    def __init__(self, pos, size=(400, 80), font_size=24, bg_color=(0, 30, 60, 180), border_color=GRID_BLUE, border_radius=10):
        self.x, self.y = pos
        self.width, self.height = size
        self.bg_color = bg_color
        self.border_color = border_color
        self.border_radius = border_radius
        self.font = pygame.font.SysFont("Arial", font_size)
    
    def draw(self, screen, text, shadow=False, shadow_offset=(2, 2)):
        # Surface semi-transparente pour le fond
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        surf.fill(self.bg_color)
        pygame.draw.rect(surf, self.border_color, (0, 0, self.width, self.height), 2, self.border_radius)
        screen.blit(surf, (self.x - self.width // 2, self.y - self.height // 2))
        
        # Texte
        if shadow:
            text_shadow = self.font.render(text, True, (0, 0, 0))
            screen.blit(text_shadow, (self.x - text_shadow.get_width() // 2 + shadow_offset[0], 
                                     self.y - text_shadow.get_height() // 2 + shadow_offset[1]))
        
        text_surface = self.font.render(text, True, WHITE)
        screen.blit(text_surface, (self.x - text_surface.get_width() // 2, self.y - text_surface.get_height() // 2))

class ProgressBar:
    def __init__(self, pos, size=(300, 30), max_value=100, color=GRID_BLUE, bg_color=DARK_BLUE):
        self.x, self.y = pos
        self.width, self.height = size
        self.max_value = max_value
        self.value = max_value
        self.color = color
        self.bg_color = bg_color
    
    def update(self, value):
        self.value = max(0, min(value, self.max_value))
    
    def draw(self, screen, pulse=False):
        # Fond de la barre
        bg_rect = pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, self.width, self.height)
        pygame.draw.rect(screen, self.bg_color, bg_rect, 0, 5)
        pygame.draw.rect(screen, LIGHT_BLUE, bg_rect, 1, 5)
        
        # Portion remplie
        if self.value > 0:
            fill_width = int(self.width * (self.value / self.max_value))
            
            # Effet de pulsation quand le temps est faible
            pulse_effect = 0
            if pulse and self.value < self.max_value * 0.2:  # Moins de 20%
                pulse_effect = 5 * math.sin(time.time() * 5)
            
            fill_rect = pygame.Rect(self.x - self.width // 2, self.y - self.height // 2, 
                                   fill_width + pulse_effect, self.height)
            pygame.draw.rect(screen, self.color, fill_rect, 0, 5)

class AnimatedText:
    def __init__(self, font, duration=2.0):
        self.font = font
        self.message = ""
        self.color = WHITE
        self.active = False
        self.start_time = 0
        self.duration = duration  # secondes
    
    def start_animation(self, message, color=WHITE):
        self.message = message
        self.color = color
        self.active = True
        self.start_time = time.time()
    
    def draw(self, screen, screen_width, screen_height):
        if not self.active:
            return
        
        elapsed = time.time() - self.start_time
        
        if elapsed < self.duration:
            # Calcul de l'opacité (fondu entrant puis sortant)
            if elapsed < self.duration / 2:
                opacity = min(255, int(elapsed * 510 / self.duration))
            else:
                opacity = max(0, int(255 - (elapsed - self.duration / 2) * 510 / self.duration))
            
            # Surface semi-transparente pour le fond
            fond = pygame.Surface((screen_width, 150), pygame.SRCALPHA)
            fond.fill((0, 0, 0, min(200, opacity)))  # Fond noir semi-transparent
            
            # Calculer l'échelle avec effet de rebond
            scale = 1.0
            if elapsed < 0.3:
                scale = 0.5 + 1.5 * elapsed / 0.3  # Grandir rapidement
            elif elapsed < 0.5:
                scale = 1.0 + 0.2 * math.sin((elapsed - 0.3) * math.pi / 0.2)  # Petit rebond
            
            # Texte de l'animation
            texte = self.font.render(self.message, True, self.color)
            texte.set_alpha(opacity)
            
            # Appliquer l'échelle
            texte_scaled = pygame.transform.scale(texte, 
                                              (int(texte.get_width() * scale), 
                                               int(texte.get_height() * scale)))
            
            # Positionner au centre
            rect = texte_scaled.get_rect(center=(screen_width // 2, screen_height // 2))
            
            # Ajouter un halo autour du texte
            glow_surf = pygame.Surface((rect.width + 40, rect.height + 40), pygame.SRCALPHA)
            glow_color = (*self.color[:3], min(100, opacity))
            pygame.draw.ellipse(glow_surf, glow_color, 
                             (0, 0, rect.width + 40, rect.height + 40))
            
            # Afficher le fond
            screen.blit(fond, (0, screen_height // 2 - 75))
            
            # Afficher le halo puis le texte
            screen.blit(glow_surf, (rect.x - 20, rect.y - 20))
            screen.blit(texte_scaled, rect)
        else:
            # Fin de l'animation
            self.active = False
    
    def is_active(self):
        return self.active

