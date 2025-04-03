import random
import math

class BattleshipAI:
    """
    IA avancée pour Bataille Navale avec plusieurs niveaux de sophistication
    """
    
    def __init__(self, difficulty='expert'):
        """
        Initialise l'IA de Bataille Navale avec un niveau de difficulté sophistiqué.
        
        :param difficulty: Niveau de difficulté ('facile', 'moyenne', 'difficile', 'expert')
        """
        self.difficulty = difficulty.lower()
        
        # Configuration des navires standard
        self.ship_sizes = [5, 4, 3, 3, 2]
        self.ship_names = ["Porte-avion", "Croiseur", "Contre-torpilleur", "Sous-marin", "Torpilleur"]
        
        # État de la partie
        self.remaining_ships = self.ship_sizes.copy()
        self.ship_locations = []  # Connaissances accumulées sur les positions probables
        self.hit_history = []  # Historique complet des hits
        self.hunt_mode = False
        self.target_ship = None
        
        # Paramètres avancés de l'IA
        self.memory_depth = 10  # Nombre de tirs à mémoriser
        self.prediction_confidence = {}  # Confiance dans les prédictions de positions
        
    def choose_target(self, board):
        """
        Sélectionne une cible en fonction du niveau de difficulté.
        
        :param board: Le plateau de jeu
        :return: Coordonnées (x, y) de la cible
        """
        # Réinitialiser les prédictions si nécessaire
        self._update_game_state(board)
        
        # Stratégies par difficulté
        if self.difficulty == 'facile':
            return self._facile_strategy(board)
        elif self.difficulty == 'moyenne':
            return self._moyenne_strategy(board)
        elif self.difficulty == 'difficile':
            return self._difficile_strategy(board)
        else:  # mode expert par défaut
            return self._expert_strategy(board)
    
    def _facile_strategy(self, board):
        """
        Stratégie de tir totalement aléatoire.
        
        :param board: Le plateau de jeu
        :return: Coordonnées (x, y) d'une case non touchée
        """
        width, height = len(board.grid[0]), len(board.grid)
        available = [
            (x, y) for x in range(width) for y in range(height)
            if not any(sx == x and sy == y for sx, sy, _ in board.shots)
        ]
        return random.choice(available) if available else None
    
    def _moyenne_strategy(self, board):
        """
        Stratégie de tir en damier avec légère intelligence.
        
        :param board: Le plateau de jeu
        :return: Coordonnées (x, y) d'une case non touchée
        """
        width, height = len(board.grid[0]), len(board.grid)
        
        # Tirs en damier préférentiel
        damier_cells = [
            (x, y) for x in range(width) for y in range(height)
            if (x + y) % 2 == 0 and not any(sx == x and sy == y for sx, sy, _ in board.shots)
        ]
        
        if damier_cells:
            return random.choice(damier_cells)
        
        # Fallback sur aléatoire
        return self._facile_strategy(board)
    
    def _difficile_strategy(self, board):
        """
        Stratégie de tir intelligente avec chasse directionnelle.
        
        :param board: Le plateau de jeu
        :return: Coordonnées (x, y) de la cible
        """
        # Priorité : terminer un navire en cours
        hits = [shot for shot in board.shots if shot[2]]
        
        if hits:
            # Essayer de terminer le dernier navire touché
            last_hit = hits[-1]
            target = self._hunt_around_hit(board, last_hit)
            if target:
                return target
        
        # Stratégie probabiliste basique
        return self._calculate_moderate_probability_grid(board)
    
    def _expert_strategy(self, board):
        """
        Stratégie de tir ultra-sophistiquée avec prédiction avancée.
        
        :param board: Le plateau de jeu
        :return: Coordonnées (x, y) de la cible optimale
        """
        # Étape 1 : Analyse des navires restants
        remaining_ship_sizes = sorted(self.remaining_ships, reverse=True)
        
        # Étape 2 : Analyse des hits précédents
        hits = [shot for shot in board.shots if shot[2]]
        
        # Étape 3 : Mode chasse intelligente
        if hits:
            # Priorité absolue : terminer un navire en cours
            for hit in reversed(hits):
                target = self._advanced_hunt_mode(board, hit)
                if target:
                    return target
        
        # Étape 4 : Prédiction probabiliste multi-niveaux
        probability_grid = self._create_ultimate_probability_grid(board, remaining_ship_sizes)
        
        # Étape 5 : Sélection de la meilleure cible
        best_targets = self._select_optimal_targets(probability_grid, board)
        
        # Étape 6 : Stratégie de sélection finale
        return self._strategic_target_selection(best_targets, board)
    
    def _advanced_hunt_mode(self, board, last_hit):
        """
        Mode de chasse avancé pour terminer un navire avec une stratégie intelligente.
        
        :param board: Le plateau de jeu
        :param last_hit: Dernier tir réussi
        :return: Coordonnées (x, y) de la cible
        """
        x, y, _ = last_hit
        width, height = len(board.grid[0]), len(board.grid)
        shots = {(sx, sy) for sx, sy, _ in board.shots}
        hits = {(sx, sy) for sx, sy, hit in board.shots if hit}
        
        # Déterminer la direction du navire
        def _get_ship_direction(hits):
            """Trouver la direction du navire basée sur les hits adjacents"""
            horizontal_hits = [h for h in hits if any((h[0]+1, h[1]) in hits or (h[0]-1, h[1]) in hits)]
            vertical_hits = [h for h in hits if any((h[0], h[1]+1) in hits or (h[0], h[1]-1) in hits)]
            
            return 'horizontal' if len(horizontal_hits) > len(vertical_hits) else 'vertical'
        
        # Filtrer les hits autour du dernier hit
        adjacent_hits = {
            (x+dx, y+dy) for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]
            if (x+dx, y+dy) in hits
        }
        
        # Si plusieurs hits adjacents, déterminer la direction
        if len(adjacent_hits) > 0:
            direction = _get_ship_direction(hits)
            
            if direction == 'horizontal':
                directions = [(1,0), (-1,0)]
            else:
                directions = [(0,1), (0,-1)]
        else:
            # Si pas de hit adjacent, tester toutes les directions
            directions = [(1,0), (-1,0), (0,1), (0,-1)]
        
        # Trouver les cibles potentielles dans les directions
        potential_targets = []
        for dx, dy in directions:
            # Chercher jusqu'à la longueur du plus grand navire restant
            max_search_distance = max(self.remaining_ships) if self.remaining_ships else 5
            
            for i in range(1, max_search_distance + 1):
                nx, ny = x + dx * i, y + dy * i
                
                # Vérifier que la case est dans la grille et n'a pas été touchée
                if (0 <= nx < width and 0 <= ny < height and 
                    (nx, ny) not in shots):
                    potential_targets.append((nx, ny))
                else:
                    break
        
        # Randomiser légèrement pour éviter la prévisibilité
        if potential_targets:
            # Donner plus de poids aux cibles les plus proches
            weights = [max(len(potential_targets) - abs(px - x) - abs(py - y), 1) for px, py in potential_targets]
            return random.choices(potential_targets, weights=weights)[0]
        
        return None
    
    def _create_ultimate_probability_grid(self, board, ship_sizes):
        """
        Crée une grille de probabilités ultra-sophistiquée.
        
        :param board: Le plateau de jeu
        :param ship_sizes: Tailles des navires restants
        :return: Grille de probabilités
        """
        width, height = len(board.grid[0]), len(board.grid)
        prob_grid = [[0 for _ in range(width)] for _ in range(height)]
        shots = {(x, y) for x, y, _ in board.shots}
        hits = {(x, y) for x, y, hit in board.shots if hit}
        
        # Calcul probabiliste basé sur plusieurs facteurs
        for ship_size in ship_sizes:
            for y in range(height):
                for x in range(width):
                    # Vérification horizontale
                    if x + ship_size <= width:
                        cells = [(x + i, y) for i in range(ship_size)]
                        if all((cx, cy) not in shots or (cx, cy) in hits for cx, cy in cells):
                            for cx, cy in cells:
                                prob_grid[cy][cx] += ship_size * 3
                    
                    # Vérification verticale
                    if y + ship_size <= height:
                        cells = [(x, y + i) for i in range(ship_size)]
                        if all((cx, cy) not in shots or (cx, cy) in hits for cx, cy in cells):
                            for cx, cy in cells:
                                prob_grid[cy][cx] += ship_size * 3
        
        # Bonus pour les cases adjacentes aux hits
        for x, y in hits:
            for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in shots:
                    prob_grid[ny][nx] += 10
        
        # Bonus zones centrales
        center_x, center_y = width // 2, height // 2
        for y in range(height):
            for x in range(width):
                dist_to_center = math.sqrt((x - center_x)**2 + (y - center_y)**2)
                prob_grid[y][x] += max(0, 10 - dist_to_center)
        
        return prob_grid
    
    def _select_optimal_targets(self, probability_grid, board):
        """
        Sélectionne les meilleures cibles selon la grille de probabilités.
        
        :param probability_grid: Grille de probabilités
        :param board: Le plateau de jeu
        :return: Liste des meilleures cibles
        """
        width, height = len(board.grid[0]), len(board.grid)
        shots = {(x, y) for x, y, _ in board.shots}
        
        # Trouver les cibles non touchées avec la probabilité maximale
        max_prob = max(max(row) for row in probability_grid)
        best_targets = [
            (x, y) for y in range(height) 
            for x in range(width) 
            if probability_grid[y][x] == max_prob and (x, y) not in shots
        ]
        
        return best_targets
    
    def _strategic_target_selection(self, best_targets, board):
        """
        Sélection stratégique finale parmi les meilleures cibles.
        
        :param best_targets: Liste des meilleures cibles
        :param board: Le plateau de jeu
        :return: Coordonnées (x, y) de la cible
        """
        # Si plusieurs cibles optimales, appliquer des critères de départage
        if len(best_targets) > 1:
            # Critères de départage : proximité des hits précédents
            hits = [shot for shot in board.shots if shot[2]]
            
            if hits:
                last_hit = hits[-1]
                best_targets.sort(key=lambda t: math.sqrt((t[0] - last_hit[0])**2 + (t[1] - last_hit[1])**2))
        
        return random.choice(best_targets)
    
    def _calculate_moderate_probability_grid(self, board):
        """
        Calcul de probabilité niveau intermédiaire.
        
        :param board: Le plateau de jeu
        :return: Coordonnées (x, y) de la cible
        """
        width, height = len(board.grid[0]), len(board.grid)
        prob = [[0 for _ in range(width)] for _ in range(height)]
        shots = {(x, y) for x, y, _ in board.shots}
        hits = {(x, y) for x, y, hit in board.shots if hit}
        
        # Calcul probabiliste simple
        for ship_size in self.remaining_ships:
            for y in range(height):
                for x in range(width):
                    # Horizontal
                    if x + ship_size <= width:
                        cells = [(x + i, y) for i in range(ship_size)]
                        if all((cx, cy) not in shots or (cx, cy) in hits for cx, cy in cells):
                            for cx, cy in cells:
                                if (cx, cy) not in shots:
                                    prob[cy][cx] += 2
                    
                    # Vertical
                    if y + ship_size <= height:
                        cells = [(x, y + i) for i in range(ship_size)]
                        if all((cx, cy) not in shots or (cx, cy) in hits for cx, cy in cells):
                            for cx, cy in cells:
                                if (cx, cy) not in shots:
                                    prob[cy][cx] += 2
        
        max_val = max(max(row) for row in prob)
        best = [(x, y) for y in range(height) for x in range(width) if prob[y][x] == max_val]
        return random.choice(best)
    
    def _update_game_state(self, board):
        """
        Met à jour l'état global du jeu.
        
        :param board: Le plateau de jeu
        """
        # Mettre à jour les navires restants
        sunk_ships = [ship for ship in self.ship_sizes if sum(1 for shot in board.shots if shot[2]) >= ship]
        for ship in sunk_ships:
            if ship in self.remaining_ships:
                self.remaining_ships.remove(ship)
        
        # Mémoriser l'historique des hits
        hits = [shot for shot in board.shots if shot[2]]
        self.hit_history = hits[-self.memory_depth:]
    
    def update_ship_status(self, ships_sunk):
        """
        Met à jour le statut des navires coulés.
        
        :param ships_sunk: Liste des tailles de navires coulés
        """
        for ship_size in ships_sunk:
            if ship_size in self.remaining_ships:
                self.remaining_ships.remove(ship_size)
    
    def reset(self):
        """
        Réinitialise l'état de l'IA.
        """
        self.remaining_ships = self.ship_sizes.copy()
        self.ship_locations = []
        self.hit_history = []
        self.hunt_mode = False
        self.target_ship = None
        self.prediction_confidence = {}