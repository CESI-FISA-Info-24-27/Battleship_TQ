# game_timer.py
import pygame

class GameTimer:
    """Classe pour gérer les minuteurs dans le jeu"""
    
    def __init__(self, duration=0):
        """
        Initialise un minuteur
        
        Args:
            duration (int): Durée en millisecondes
        """
        self.duration = duration
        self.start_time = 0
        self.paused_time = 0
        self.paused = False
        self.running = False
    
    def start(self, duration=None):
        """Démarre le minuteur"""
        if duration is not None:
            self.duration = duration
        
        self.start_time = pygame.time.get_ticks()
        self.paused = False
        self.running = True
    
    def pause(self):
        """Met en pause le minuteur"""
        if self.running and not self.paused:
            self.paused_time = pygame.time.get_ticks()
            self.paused = True
    
    def resume(self):
        """Reprend le minuteur après une pause"""
        if self.running and self.paused:
            elapsed_pause = pygame.time.get_ticks() - self.paused_time
            self.start_time += elapsed_pause
            self.paused = False
    
    def reset(self):
        """Réinitialise le minuteur"""
        self.running = False
        self.paused = False
    
    def get_time_left(self):
        """Renvoie le temps restant en millisecondes"""
        if not self.running:
            return 0
        
        if self.paused:
            elapsed = self.paused_time - self.start_time
        else:
            elapsed = pygame.time.get_ticks() - self.start_time
        
        time_left = max(0, self.duration - elapsed)
        return time_left
    
    def is_expired(self):
        """Vérifie si le temps est écoulé"""
        return self.running and self.get_time_left() == 0

