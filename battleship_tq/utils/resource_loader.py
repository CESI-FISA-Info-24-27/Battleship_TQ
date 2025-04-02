# resource_loader.py
import os
import sys
import pygame

class ResourceLoader:
    """Gestionnaire pour le chargement des ressources du jeu"""
    
    @staticmethod
    def resource_path(relative_path):
        """Obtient le chemin absolu d'une ressource, fonctionne avec PyInstaller"""
        try:
            # PyInstaller crée un répertoire temporaire et stocke le chemin dans _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        
        return os.path.join(base_path, relative_path)
    
    @staticmethod
    def load_sound(filename):
        """Charge un fichier son"""
        try:
            sound_path = ResourceLoader.resource_path(os.path.join('assets', 'sounds', filename))
            return pygame.mixer.Sound(sound_path)
        except Exception as e:
            print(f"Erreur lors du chargement du son {filename}: {e}")
            return None
    
    @staticmethod
    def load_image(filename):
        """Charge une image"""
        try:
            image_path = ResourceLoader.resource_path(os.path.join('assets', 'images', filename))
            return pygame.image.load(image_path).convert_alpha()
        except Exception as e:
            print(f"Erreur lors du chargement de l'image {filename}: {e}")
            return None
    
    @staticmethod
    def load_font(filename, size):
        """Charge une police personnalisée"""
        try:
            font_path = ResourceLoader.resource_path(os.path.join('assets', 'fonts', filename))
            return pygame.font.Font(font_path, size)
        except Exception as e:
            print(f"Erreur lors du chargement de la police {filename}: {e}")
            # Fallback sur une police système
            return pygame.font.SysFont("Arial", size)
    
    @staticmethod
    def init_sounds():
        """Initialise et retourne les sons du jeu"""
        try:
            pygame.mixer.init()
            sounds = {
                'hit': ResourceLoader.load_sound('hit.wav'),
                'miss': ResourceLoader.load_sound('miss.wav'),
                'sink': ResourceLoader.load_sound('sink.wav'),
                'menu': ResourceLoader.load_sound('menu.wav'),
                'game_start': ResourceLoader.load_sound('game_start.wav'),
                'game_over': ResourceLoader.load_sound('game_over.wav')
            }
            return sounds, True
        except Exception as e:
            print(f"Erreur lors de l'initialisation des sons: {e}")
            return {}, False

