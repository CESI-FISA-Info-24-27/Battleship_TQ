# Configuration globale du jeu
import os

# Chemin vers les assets
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")

# Configuration des logs
DEBUG = True  # Mettre à False pour désactiver les logs de debug

# Configuration réseau avancée
NETWORK_TIMEOUT = 10  # Timeout en secondes pour les connexions réseau

def get_asset_path(folder, filename):
    """
    Obtient le chemin complet vers un fichier d'assets
    
    Args:
        folder: Dossier dans assets (images, sounds, etc.)
        filename: Nom du fichier
        
    Returns:
        Chemin complet vers le fichier
    """
    return os.path.join(ASSETS_DIR, folder, filename)

def setup_directories():
    """
    Crée les dossiers nécessaires s'ils n'existent pas
    """
    # Crée le dossier assets et ses sous-dossiers s'ils n'existent pas
    for folder in ["fonts", "images", "sounds"]:
        path = os.path.join(ASSETS_DIR, folder)
        if not os.path.exists(path):
            os.makedirs(path)