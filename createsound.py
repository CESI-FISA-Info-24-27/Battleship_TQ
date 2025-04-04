import wave
import struct
import numpy as np
import os
import math

# Créer le dossier assets/sounds si nécessaire
os.makedirs("assets/sounds", exist_ok=True)

def create_sound(filename, function, duration=0.5, sample_rate=44100):
    """
    Crée un fichier audio WAV
    
    Args:
        filename: Nom du fichier à créer
        function: Fonction qui génère les échantillons audio
        duration: Durée en secondes
        sample_rate: Taux d'échantillonnage
    """
    num_samples = int(duration * sample_rate)
    samples = []
    
    for i in range(num_samples):
        t = i / sample_rate
        value = function(t, i, num_samples)
        # Limiter les valeurs entre -32767 et 32767 pour le format 16-bit
        value = max(-32767, min(32767, value))
        samples.append(int(value))
    
    # Créer le fichier WAV
    filepath = os.path.join("assets", "sounds", filename)
    with wave.open(filepath, "wb") as file:
        file.setnchannels(1)
        file.setsampwidth(2)
        file.setframerate(sample_rate)
        for sample in samples:
            file.writeframes(struct.pack("<h", sample))
    
    print(f"Son créé: {filepath}")

# Fonction pour le son de démarrage
def start_sound(t, i, num_samples):
    # Un son de chime ascendant
    freqs = [440, 554, 659, 880]
    amplitude = 12000 * (1 - i / num_samples)  # Diminution progressive
    
    value = 0
    for idx, freq in enumerate(freqs):
        # Décaler les fréquences pour qu'elles commencent à des moments différents
        if t > idx * 0.1 and t < (idx * 0.1 + 0.3):
            value += amplitude * math.sin(2 * math.pi * freq * t)
    
    return value

# Fonction pour le son de tir
def fire_sound(t, i, num_samples):
    # Un son court avec une diminution rapide
    freq = 150 + 80 * (1 - t / 0.5)  # Diminution de la fréquence
    amplitude = 12000 * (1 - i / num_samples) ** 4  # Diminution rapide - valeur réduite
    
    # Ajouter du bruit pour un effet plus réaliste - valeur réduite
    noise = np.random.normal(0, 5000) * (1 - i / num_samples) ** 2
    
    return amplitude * math.sin(2 * math.pi * freq * t) + noise

# Fonction pour le son d'explosion
def explosion_sound(t, i, num_samples):
    # Un son plus grave avec du bruit
    base_freq = 100
    amplitude = 10000 * (1 - i / num_samples) ** 2  # Diminution moins rapide - valeur réduite
    
    # Plusieurs fréquences pour un son plus riche
    value = 0
    for mult in [1, 1.5, 2, 2.5]:
        value += amplitude * 0.25 * math.sin(2 * math.pi * base_freq * mult * t)
    
    # Beaucoup de bruit pour l'explosion - valeur réduite
    noise = np.random.normal(0, 8000) * (1 - i / num_samples) ** 1.5
    
    return value + noise

# Créer les fichiers son
create_sound("start.wav", start_sound, duration=1.2)
create_sound("fire.wav", fire_sound, duration=0.3)
create_sound("explosion.wav", explosion_sound, duration=0.7)

print("Tous les sons ont été créés dans le dossier assets/sounds/")