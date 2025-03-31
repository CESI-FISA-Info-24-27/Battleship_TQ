import os
import random
import time

class BatailleNavale:
    def __init__(self):
        # Taille de la grille
        self.taille_grille = 10
        
        # Initialisation des grilles
        self.grille_joueur = [[' ' for _ in range(self.taille_grille)] for _ in range(self.taille_grille)]
        self.grille_ordinateur = [[' ' for _ in range(self.taille_grille)] for _ in range(self.taille_grille)]
        self.grille_tirs_joueur = [[' ' for _ in range(self.taille_grille)] for _ in range(self.taille_grille)]
        self.grille_tirs_ordinateur = [[' ' for _ in range(self.taille_grille)] for _ in range(self.taille_grille)]
        
        # Définition des navires et leurs tailles
        self.navires = {
            'Porte-avions': 5,
            'Croiseur': 4,
            'Contre-torpilleur': 3,
            'Sous-marin': 3,
            'Torpilleur': 2
        }
        
        # Compteurs de navires coulés
        self.navires_coules_joueur = 0
        self.navires_coules_ordinateur = 0
        
        # Nombre total de navires
        self.total_navires = len(self.navires)
    
    def effacer_ecran(self):
        """Efface l'écran de la console"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def afficher_grilles(self):
        """Affiche les grilles de jeu"""
        self.effacer_ecran()
        
        print("\n" + "=" * 50)
        print("               BATAILLE NAVALE")
        print("=" * 50 + "\n")
        
        # En-tête de colonne
        print("   Votre flotte:               Vos tirs:")
        print("   A B C D E F G H I J         A B C D E F G H I J")
        
        # Affichage des deux grilles côte à côte
        for i in range(self.taille_grille):
            ligne_joueur = f"{i} |"
            ligne_tirs = f"{i} |"
            
            for j in range(self.taille_grille):
                ligne_joueur += f"{self.grille_joueur[i][j]}|"
                ligne_tirs += f"{self.grille_tirs_joueur[i][j]}|"
            
            print(f"{ligne_joueur}       {ligne_tirs}")
        
        print("\nLégende: N = Navire, X = Touché, O = Manqué")
        print("=" * 50 + "\n")
    
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
    
    def convertir_coordonnees(self, coordonnees):
        """Convertit les coordonnées entrées (ex: A5) en indices de grille (ligne, colonne)"""
        try:
            if len(coordonnees) < 2 or len(coordonnees) > 3:
                return None
            
            colonne = ord(coordonnees[0].upper()) - ord('A')
            ligne = int(coordonnees[1:])
            
            if 0 <= ligne < self.taille_grille and 0 <= colonne < self.taille_grille:
                return ligne, colonne
            else:
                return None
        except:
            return None
    
    def tir_joueur(self):
        """Gère le tir du joueur"""
        while True:
            try:
                coordonnees = input("Entrez les coordonnées de tir (ex: A5): ")
                position = self.convertir_coordonnees(coordonnees)
                
                if position is None:
                    print("Coordonnées invalides. Veuillez réessayer.")
                    continue
                
                ligne, colonne = position
                
                # Vérifier si déjà tiré à cet endroit
                if self.grille_tirs_joueur[ligne][colonne] != ' ':
                    print("Vous avez déjà tiré à cet endroit. Choisissez d'autres coordonnées.")
                    continue
                
                # Vérifier si touché ou manqué
                if self.grille_ordinateur[ligne][colonne] == 'N':
                    print("Touché !")
                    self.grille_tirs_joueur[ligne][colonne] = 'X'
                    
                    # Vérifier si le navire est coulé
                    if self.verifier_navire_coule(self.grille_ordinateur, self.grille_tirs_joueur, ligne, colonne):
                        print("Navire coulé !")
                        self.navires_coules_joueur += 1
                else:
                    print("Manqué !")
                    self.grille_tirs_joueur[ligne][colonne] = 'O'
                
                time.sleep(1)
                break
            except Exception as e:
                print(f"Erreur: {e}. Veuillez réessayer.")
    
    def tir_ordinateur(self):
        """Gère le tir de l'ordinateur"""
        print("\nL'ordinateur tire...")
        time.sleep(1)
        
        # Stratégie simple: tir aléatoire
        while True:
            ligne = random.randint(0, self.taille_grille - 1)
            colonne = random.randint(0, self.taille_grille - 1)
            
            # Vérifier si déjà tiré à cet endroit
            if self.grille_tirs_ordinateur[ligne][colonne] == ' ':
                # Vérifier si touché ou manqué
                if self.grille_joueur[ligne][colonne] == 'N':
                    print(f"L'ordinateur a touché votre navire en {chr(65 + colonne)}{ligne} !")
                    self.grille_joueur[ligne][colonne] = 'X'
                    self.grille_tirs_ordinateur[ligne][colonne] = 'X'
                    
                    # Vérifier si le navire est coulé
                    if self.verifier_navire_coule(self.grille_joueur, self.grille_tirs_ordinateur, ligne, colonne):
                        print("Un de vos navires a été coulé !")
                        self.navires_coules_ordinateur += 1
                else:
                    print(f"L'ordinateur a manqué en {chr(65 + colonne)}{ligne}.")
                    self.grille_tirs_ordinateur[ligne][colonne] = 'O'
                
                time.sleep(1)
                break
    
    def verifier_navire_coule(self, grille_navires, grille_tirs, ligne, colonne):
        """Vérifie si un navire est entièrement coulé"""
        # Cette fonction vérifie si toutes les cases d'un navire ont été touchées
        # Recherche horizontale
        debut_col = colonne
        while debut_col > 0 and (grille_navires[ligne][debut_col-1] == 'N' or grille_tirs[ligne][debut_col-1] == 'X'):
            debut_col -= 1
        
        fin_col = colonne
        while fin_col < self.taille_grille - 1 and (grille_navires[ligne][fin_col+1] == 'N' or grille_tirs[ligne][fin_col+1] == 'X'):
            fin_col += 1
        
        # Vérifier si toutes les cases horizontales sont touchées
        if debut_col != fin_col:
            for i in range(debut_col, fin_col + 1):
                if grille_tirs[ligne][i] != 'X':
                    return False
            return True
        
        # Recherche verticale
        debut_ligne = ligne
        while debut_ligne > 0 and (grille_navires[debut_ligne-1][colonne] == 'N' or grille_tirs[debut_ligne-1][colonne] == 'X'):
            debut_ligne -= 1
        
        fin_ligne = ligne
        while fin_ligne < self.taille_grille - 1 and (grille_navires[fin_ligne+1][colonne] == 'N' or grille_tirs[fin_ligne+1][colonne] == 'X'):
            fin_ligne += 1
        
        # Vérifier si toutes les cases verticales sont touchées
        if debut_ligne != fin_ligne:
            for i in range(debut_ligne, fin_ligne + 1):
                if grille_tirs[i][colonne] != 'X':
                    return False
            return True
        
        # Si c'est un navire de taille 1
        return True
    
    def verifier_fin_jeu(self):
        """Vérifie si le jeu est terminé"""
        return self.navires_coules_joueur == self.total_navires or self.navires_coules_ordinateur == self.total_navires
    
    def afficher_resultat(self):
        """Affiche le résultat final du jeu"""
        self.effacer_ecran()
        print("\n" + "=" * 50)
        print("               FIN DE PARTIE")
        print("=" * 50 + "\n")
        
        if self.navires_coules_joueur == self.total_navires:
            print("Félicitations ! Vous avez gagné !")
        else:
            print("Dommage, l'ordinateur a gagné.")
        
        print(f"\nScore final:")
        print(f"Vous avez coulé {self.navires_coules_joueur} navires sur {self.total_navires}.")
        print(f"L'ordinateur a coulé {self.navires_coules_ordinateur} navires sur {self.total_navires}.")
        
        print("\n" + "=" * 50)
    
    def jouer(self):
        """Méthode principale pour jouer au jeu"""
        # Placer les navires
        self.placer_navires_aleatoirement(self.grille_joueur)
        self.placer_navires_aleatoirement(self.grille_ordinateur)
        
        # Boucle principale du jeu
        while not self.verifier_fin_jeu():
            self.afficher_grilles()
            
            # Tour du joueur
            self.tir_joueur()
            
            # Vérifier si le joueur a gagné
            if self.navires_coules_joueur == self.total_navires:
                break
            
            # Tour de l'ordinateur
            self.tir_ordinateur()
        
        # Afficher le résultat final
        self.afficher_resultat()

# Démarrer le jeu
if __name__ == "__main__":
    print("Bienvenue dans le jeu de Bataille Navale !")
    print("Placez vos tirs en utilisant les coordonnées (ex: A5)")
    print("Appuyez sur Entrée pour commencer...")
    input()
    
    jeu = BatailleNavale()
    jeu.jouer()
    
    print("\nMerci d'avoir joué ! À bientôt !")