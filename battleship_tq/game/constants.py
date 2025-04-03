# constants.py
import pygame

# Écran
SCREEN_WIDTH = 1600  # Augmenté de 1200 à 1600
SCREEN_HEIGHT = 900  # Augmenté de 800 à 900
GRID_SIZE = 10
CELL_SIZE = 50  # Augmenté de 40 à 50
MARGIN = 80    # Augmenté de 60 à 80
GRID_WIDTH = CELL_SIZE * GRID_SIZE
GRID_HEIGHT = CELL_SIZE * GRID_SIZE

# Couleurs
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_BLUE = (0, 30, 60)      # Fond plus foncé
GRID_BLUE = (0, 120, 215)    # Grille plus visible
LIGHT_BLUE = (135, 206, 250) # Bleu clair pour les éléments interactifs
DEEP_BLUE = (220, 220, 220)  # Modifié pour être gris clair (bateaux)
WATER_BLUE = (10, 75, 120)   # Couleur de l'eau
RED = (255, 50, 50)          # Rouge plus vif pour les coups
GREEN = (50, 255, 100)       # Vert plus vif
YELLOW = (255, 255, 0)       # Jaune pour les notifications
ORANGE = (255, 165, 0)       # Orange pour certains éléments visuels

# Difficulté
FACILE = 1
MOYEN = 2
DIFFICILE = 3

# États du jeu
MENU_PRINCIPAL = "menu_principal"
MENU_DIFFICULTE = "menu_difficulte"
PLACEMENT_NAVIRES = "placement_navires"
JEU_SOLO = "jeu_solo"
JEU_ONLINE = "jeu_online"
MENU_ONLINE = "menu_online"
FIN_PARTIE = "fin_partie"

# Navires
NAVIRES = {
    'Porte-avions': 5,
    'Croiseur': 4,
    'Contre-torpilleur': 3,
    'Sous-marin': 3,
    'Torpilleur': 2
}

# Temporisateurs
PLACEMENT_TIME = 60 * 1000  # 60 secondes en millisecondes
TURN_TIME = 30 * 1000       # 30 secondes en millisecondes
MESSAGE_DURATION = 1500     # 1.5 secondes en millisecondes

# Réseau
DEFAULT_PORT = 5555
MAX_GAMES = 5              # Nombre maximum de parties simultanées sur le serveur