import random
import math

class BattleshipAI:
    """
    Intelligence artificielle avancée pour le jeu de Bataille Navale avec plusieurs niveaux de difficulté.
    """
    
    def __init__(self, difficulty='expert'):
        """
        Initialise l'IA de Bataille Navale avec un niveau de difficulté.
        
        :param difficulty: Niveau de difficulté ('facile', 'moyenne', 'difficile', 'expert')
        """
        self.difficulty = difficulty.lower()
        self.ship_sizes = [5, 4, 3, 3, 2]  # Tailles standard des navires
        self.remaining_ships = self.ship_sizes.copy()
        
        # Historique des tirs et des résultats
        self.shots_history = []
        self.last_successful_hit = None
        self.current_hunt_mode = False
        self.hunt_targets = []
        
        # Mémoire des tirs réussis pour les stratégies avancées
        self.successful_hits = []
        self.ship_hits = {}  # Groupes de hits par navire potentiel
        
        # État de la grille de probabilité
        self.probability_grid = None
        
        # Constantes pour les stratégies de tir
        self.BOARD_SIZE = 10

    def choose_target(self, board):
        """
        Choisit une cible en fonction du niveau de difficulté.
        
        :param board: Le plateau de jeu
        :return: Coordonnées (x, y) de la cible
        """
        # Mettre à jour notre historique des tirs
        self._update_history(board)
        
        if self.difficulty == 'facile':
            return self._easy_strategy(board)
        elif self.difficulty == 'moyenne':
            return self._medium_strategy(board)
        elif self.difficulty == 'difficile':
            return self._hard_strategy(board)
        elif self.difficulty == 'expert':
            return self._expert_strategy(board)
        else:
            # Fallback sur la stratégie moyenne si la difficulté n'est pas reconnue
            print(f"Difficulté non reconnue: {self.difficulty}, fallback sur 'moyenne'")
            return self._medium_strategy(board)
    
    def _update_history(self, board):
        """
        Met à jour l'historique des tirs basé sur l'état actuel du plateau.
        
        :param board: Le plateau de jeu
        """
        # Récupérer tous les tirs effectués
        all_shots = []
        hit_shots = []
        
        # Convertir les shots du board en liste pour notre usage interne
        if hasattr(board, 'shots'):
            for x, y, hit in board.shots:
                shot = (x, y)
                all_shots.append(shot)
                if hit:
                    hit_shots.append(shot)
        
        # Mettre à jour notre liste interne de tirs réussis
        self.successful_hits = hit_shots
        self.shots_history = all_shots
        
        # Grouper les hits par navires potentiels
        self._group_hits_by_ships()
    
    def _group_hits_by_ships(self):
        """
        Groupe les hits en navires potentiels selon leur proximité.
        """
        # Réinitialiser les groupes
        self.ship_hits = {}
        
        # Fonction pour trouver les hits adjacents
        def find_adjacent_hits(start_hit, all_hits, ship_group):
            adjacent_directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            for dx, dy in adjacent_directions:
                nx, ny = start_hit[0] + dx, start_hit[1] + dy
                adjacent_hit = (nx, ny)
                if adjacent_hit in all_hits and adjacent_hit not in ship_group:
                    ship_group.append(adjacent_hit)
                    find_adjacent_hits(adjacent_hit, all_hits, ship_group)
        
        # Copie des hits pour modification
        hits_to_process = self.successful_hits.copy()
        group_id = 0
        
        # Tant qu'il reste des hits à traiter
        while hits_to_process:
            start_hit = hits_to_process[0]
            ship_group = [start_hit]
            hits_to_process.remove(start_hit)
            
            # Trouver tous les hits adjacents
            find_adjacent_hits(start_hit, self.successful_hits, ship_group)
            
            # Retirer tous les hits trouvés de la liste à traiter
            for hit in ship_group:
                if hit in hits_to_process:
                    hits_to_process.remove(hit)
            
            # Enregistrer le groupe
            self.ship_hits[group_id] = ship_group
            group_id += 1
    
    def _easy_strategy(self, board):
        """
        Stratégie facile : tirs complètement aléatoires.
        
        :param board: Le plateau de jeu
        :return: Coordonnées (x, y) d'une case non touchée
        """
        available = [
            (x, y) for x in range(self.BOARD_SIZE) for y in range(self.BOARD_SIZE)
            if (x, y) not in self.shots_history
        ]
        
        return random.choice(available) if available else None
    
    def _medium_strategy(self, board):
        """
        Stratégie moyenne : tirs en damier + chasse basique.
        
        :param board: Le plateau de jeu
        :return: Coordonnées (x, y) d'une case non touchée
        """
        # Si on a touché un navire, tenter de cibler autour du hit
        if self.successful_hits:
            target = self._basic_hunt_mode(board)
            if target:
                return target
        
        # Sinon, utiliser un pattern en damier
        checkerboard = [
            (x, y) for x in range(self.BOARD_SIZE) for y in range(self.BOARD_SIZE)
            if (x + y) % 2 == 0 and (x, y) not in self.shots_history
        ]
        
        if checkerboard:
            return random.choice(checkerboard)
        
        # Si le damier est épuisé, tirer aléatoirement
        return self._easy_strategy(board)
    
    def _hard_strategy(self, board):
        """
        Stratégie difficile : damier intelligent + chasse améliorée + probabilités.
        
        :param board: Le plateau de jeu
        :return: Coordonnées (x, y) d'une cible stratégique
        """
        # Si nous avons des hits, passer en mode chasse
        if self.successful_hits:
            target = self._advanced_hunt_mode(board, self.successful_hits)
            if target:
                return target
        
        # Calculer une grille de probabilité simple
        self._calculate_probability_grid(board)
        
        # Combiner damier et probabilités
        checkerboard_with_prob = []
        for x in range(self.BOARD_SIZE):
            for y in range(self.BOARD_SIZE):
                if (x + y) % 2 == 0 and (x, y) not in self.shots_history:
                    # Donner un score basé sur la position et la probabilité
                    score = self.probability_grid[y][x]
                    checkerboard_with_prob.append(((x, y), score))
        
        if checkerboard_with_prob:
            # Sélectionner avec un biais vers les scores élevés
            sorted_targets = sorted(checkerboard_with_prob, key=lambda t: t[1], reverse=True)
            # Prendre parmi les 30% meilleurs scores
            top_n = max(1, len(sorted_targets) // 3)
            return sorted_targets[random.randint(0, top_n-1)][0]
        
        # Fallback sur stratégie moyenne
        return self._medium_strategy(board)
    
    def _expert_strategy(self, board):
        """
        Stratégie experte : analyse approfondie du plateau, mémoire des patterns.
        
        :param board: Le plateau de jeu
        :return: Coordonnées (x, y) de la cible optimale
        """
        # Si nous avons des hits, utiliser la chasse la plus sophistiquée
        if self.successful_hits:
            # Analyser les groupes de hits
            for group_id, hits in self.ship_hits.items():
                # Si le groupe contient plusieurs hits, chercher à le compléter
                if len(hits) >= 2:
                    target = self._predict_ship_position(hits, self.shots_history)
                    if target:
                        return target
            
            # Si aucun groupe ne donne de cible évidente, chasse avancée sur tous les hits
            target = self._advanced_hunt_mode(board, self.successful_hits)
            if target:
                return target
        
        # Calculer une grille de probabilité avancée
        probability_grid = self._calculate_advanced_probability_grid(board)
        
        # Trouver la case avec la plus haute probabilité
        max_prob = 0
        best_targets = []
        
        for y in range(self.BOARD_SIZE):
            for x in range(self.BOARD_SIZE):
                if (x, y) not in self.shots_history:
                    prob = probability_grid[y][x]
                    if prob > max_prob:
                        max_prob = prob
                        best_targets = [(x, y)]
                    elif prob == max_prob:
                        best_targets.append((x, y))
        
        if best_targets:
            return random.choice(best_targets)
        
        # Fallback sur la stratégie difficile
        return self._hard_strategy(board)
    
    def _basic_hunt_mode(self, board):
        """
        Mode de chasse basique : tir autour des hits.
        
        :param board: Le plateau de jeu
        :return: Coordonnées d'une cible ou None
        """
        # Cibler autour du dernier hit réussi
        for hit in self.successful_hits:
            adjacent_cells = [
                (hit[0] + dx, hit[1] + dy) 
                for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]
            ]
            
            valid_targets = [
                cell for cell in adjacent_cells
                if 0 <= cell[0] < self.BOARD_SIZE and 0 <= cell[1] < self.BOARD_SIZE
                and cell not in self.shots_history
            ]
            
            if valid_targets:
                return random.choice(valid_targets)
        
        return None
    
    def _advanced_hunt_mode(self, board, hits):
        """
        Mode de chasse avancé pour cibler les cases adjacentes aux hits.
        
        :param board: Le plateau de jeu
        :param hits: Liste des hits non coulés
        :return: Coordonnées de la cible ou None
        """
        # Vérifier si hits est non vide
        if not hits:
            return None
        
        # Convertir tous les éléments de hits en tuples pour garantir la cohérence
        hits = [tuple(h) if isinstance(h, list) else h for h in hits]
        
        # Déterminer la direction probable du navire
        direction = self._get_ship_direction(hits)
        
        # Trouver les extrémités des séquences de hits
        if direction == 'horizontal':
            # Trouver les extrémités horizontales
            for group_id, group_hits in self.ship_hits.items():
                if len(group_hits) < 2:
                    continue
                    
                # Trier par coordonnée x
                sorted_hits = sorted(group_hits, key=lambda h: h[0])
                leftmost = sorted_hits[0]
                rightmost = sorted_hits[-1]
                
                # Vérifier à gauche
                left_target = (leftmost[0] - 1, leftmost[1])
                if (0 <= left_target[0] < self.BOARD_SIZE and 
                    left_target not in self.shots_history):
                    return left_target
                
                # Vérifier à droite
                right_target = (rightmost[0] + 1, rightmost[1])
                if (right_target[0] < self.BOARD_SIZE and 
                    right_target not in self.shots_history):
                    return right_target
                    
        elif direction == 'vertical':
            # Trouver les extrémités verticales
            for group_id, group_hits in self.ship_hits.items():
                if len(group_hits) < 2:
                    continue
                
                # Trier par coordonnée y
                sorted_hits = sorted(group_hits, key=lambda h: h[1])
                topmost = sorted_hits[0]
                bottommost = sorted_hits[-1]
                
                # Vérifier en haut
                top_target = (topmost[0], topmost[1] - 1)
                if (0 <= top_target[1] < self.BOARD_SIZE and 
                    top_target not in self.shots_history):
                    return top_target
                
                # Vérifier en bas
                bottom_target = (bottommost[0], bottommost[1] + 1)
                if (bottom_target[1] < self.BOARD_SIZE and 
                    bottom_target not in self.shots_history):
                    return bottom_target
        
        # Si aucune extrémité n'est valide ou si la direction est inconnue,
        # essayer toutes les cases adjacentes
        for hit in hits:
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            
            # Si direction connue, prioritiser cette direction
            if direction == 'horizontal':
                directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
            elif direction == 'vertical':
                directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            
            for dx, dy in directions:
                target = (hit[0] + dx, hit[1] + dy)
                if (0 <= target[0] < self.BOARD_SIZE and 
                    0 <= target[1] < self.BOARD_SIZE and 
                    target not in self.shots_history):
                    return target
        
        return None
    
    def _predict_ship_position(self, hits, shots):
        """
        Prédit la position probable d'un navire à partir de hits alignés.
        
        :param hits: Liste des hits pour un navire potentiel
        :param shots: Liste de tous les tirs effectués
        :return: Coordonnées cible ou None
        """
        if len(hits) < 2:
            return None
        
        # Déterminer si les hits sont alignés horizontalement ou verticalement
        xs = [h[0] for h in hits]
        ys = [h[1] for h in hits]
        
        # Vérifier l'alignement horizontal
        if len(set(ys)) == 1:  # Tous les y sont identiques
            y = ys[0]
            min_x = min(xs)
            max_x = max(xs)
            
            # Vérifier s'il y a des "trous" dans la séquence
            for x in range(min_x, max_x + 1):
                if (x, y) not in hits and (x, y) not in shots:
                    return (x, y)
            
            # Essayer d'étendre à gauche
            if min_x > 0 and (min_x - 1, y) not in shots:
                return (min_x - 1, y)
                
            # Essayer d'étendre à droite
            if max_x < self.BOARD_SIZE - 1 and (max_x + 1, y) not in shots:
                return (max_x + 1, y)
                
        # Vérifier l'alignement vertical
        elif len(set(xs)) == 1:  # Tous les x sont identiques
            x = xs[0]
            min_y = min(ys)
            max_y = max(ys)
            
            # Vérifier s'il y a des "trous" dans la séquence
            for y in range(min_y, max_y + 1):
                if (x, y) not in hits and (x, y) not in shots:
                    return (x, y)
            
            # Essayer d'étendre en haut
            if min_y > 0 and (x, min_y - 1) not in shots:
                return (x, min_y - 1)
                
            # Essayer d'étendre en bas
            if max_y < self.BOARD_SIZE - 1 and (x, max_y + 1) not in shots:
                return (x, max_y + 1)
        
        return None
    
    def _get_ship_direction(self, hits):
        """
        Déterminer la direction probable d'un navire à partir des hits.
        
        :param hits: Liste des coordonnées de hits
        :return: 'horizontal', 'vertical' ou None si indéterminé
        """
        if len(hits) < 2:
            return None
        
        # Vérifier que hits est bien une liste de coordonnées
        if not all(isinstance(h, tuple) or isinstance(h, list) for h in hits):
            print(f"ERREUR: hits contient un élément non valide: {hits}")
            return None
        
        # Vérifier s'il y a une continuité horizontale
        horizontal_hits = []
        for h in hits:
            adjacent_horizontal = False
            for dx in [-1, 1]:
                adjacent_pos = (h[0] + dx, h[1])
                if adjacent_pos in hits:
                    adjacent_horizontal = True
                    break
            if adjacent_horizontal:
                horizontal_hits.append(h)
        
        # Vérifier s'il y a une continuité verticale
        vertical_hits = []
        for h in hits:
            adjacent_vertical = False
            for dy in [-1, 1]:
                adjacent_pos = (h[0], h[1] + dy)
                if adjacent_pos in hits:
                    adjacent_vertical = True
                    break
            if adjacent_vertical:
                vertical_hits.append(h)
        
        # Déterminer la direction probable
        if len(horizontal_hits) > len(vertical_hits):
            return 'horizontal'
        elif len(vertical_hits) > len(horizontal_hits):
            return 'vertical'
        else:
            return None  # Direction indéterminée
    
    def _calculate_probability_grid(self, board):
        """
        Calcule une grille de probabilité simple pour le ciblage.
        
        :param board: Le plateau de jeu
        :return: Coordonnées (x, y) de la case à plus forte probabilité
        """
        # Initialiser la grille de probabilité
        prob_grid = [[0 for _ in range(self.BOARD_SIZE)] for _ in range(self.BOARD_SIZE)]
        
        # Pour chaque navire restant, calculer les placements possibles
        for ship_size in self.remaining_ships:
            # Essayer tous les placements horizontaux
            for y in range(self.BOARD_SIZE):
                for x in range(self.BOARD_SIZE - ship_size + 1):
                    valid = True
                    for i in range(ship_size):
                        if (x + i, y) in self.shots_history:
                            valid = False
                            break
                    
                    if valid:
                        for i in range(ship_size):
                            prob_grid[y][x + i] += 1
            
            # Essayer tous les placements verticaux
            for x in range(self.BOARD_SIZE):
                for y in range(self.BOARD_SIZE - ship_size + 1):
                    valid = True
                    for i in range(ship_size):
                        if (x, y + i) in self.shots_history:
                            valid = False
                            break
                    
                    if valid:
                        for i in range(ship_size):
                            prob_grid[y + i][x] += 1
        
        # Stocker la grille pour référence future
        self.probability_grid = prob_grid
        
        # Trouver les coordonnées avec la plus haute probabilité
        max_prob = 0
        best_targets = []
        
        for y in range(self.BOARD_SIZE):
            for x in range(self.BOARD_SIZE):
                if (x, y) not in self.shots_history and prob_grid[y][x] > max_prob:
                    max_prob = prob_grid[y][x]
                    best_targets = [(x, y)]
                elif (x, y) not in self.shots_history and prob_grid[y][x] == max_prob:
                    best_targets.append((x, y))
        
        if best_targets:
            return random.choice(best_targets)
        
        # Si aucune cible n'est trouvée, revenir à une sélection aléatoire
        return self._easy_strategy(board)
    
    def _calculate_advanced_probability_grid(self, board):
        """
        Calcule une grille de probabilité avancée pour le ciblage expert.
        
        :param board: Le plateau de jeu
        :return: Grille de probabilité
        """
        # Initialiser la grille de probabilité
        prob_grid = [[0 for _ in range(self.BOARD_SIZE)] for _ in range(self.BOARD_SIZE)]
        
        # Pour chaque navire restant, calculer les placements possibles
        for ship_size in self.remaining_ships:
            # Essayer tous les placements horizontaux
            for y in range(self.BOARD_SIZE):
                for x in range(self.BOARD_SIZE - ship_size + 1):
                    placement = [(x + i, y) for i in range(ship_size)]
                    
                    # Vérifier si le placement est valide
                    valid = True
                    contains_hit = False
                    
                    for pos in placement:
                        # Si on a déjà tiré et manqué, ce n'est pas valide
                        if pos in self.shots_history and pos not in self.successful_hits:
                            valid = False
                            break
                        
                        # Si le placement contient un hit, c'est un bonus
                        if pos in self.successful_hits:
                            contains_hit = True
                    
                    if valid:
                        # Bonus si le placement contient un hit existant
                        weight = 2 if contains_hit else 1
                        
                        for pos in placement:
                            if pos not in self.shots_history:
                                prob_grid[pos[1]][pos[0]] += weight
            
            # Essayer tous les placements verticaux
            for x in range(self.BOARD_SIZE):
                for y in range(self.BOARD_SIZE - ship_size + 1):
                    placement = [(x, y + i) for i in range(ship_size)]
                    
                    # Vérifier si le placement est valide
                    valid = True
                    contains_hit = False
                    
                    for pos in placement:
                        # Si on a déjà tiré et manqué, ce n'est pas valide
                        if pos in self.shots_history and pos not in self.successful_hits:
                            valid = False
                            break
                        
                        # Si le placement contient un hit, c'est un bonus
                        if pos in self.successful_hits:
                            contains_hit = True
                    
                    if valid:
                        # Bonus si le placement contient un hit existant
                        weight = 2 if contains_hit else 1
                        
                        for pos in placement:
                            if pos not in self.shots_history:
                                prob_grid[pos[1]][pos[0]] += weight
        
        # Mettre en évidence les cellules adjacentes aux hits
        for hit in self.successful_hits:
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = hit[0] + dx, hit[1] + dy
                if (0 <= nx < self.BOARD_SIZE and 0 <= ny < self.BOARD_SIZE and 
                    (nx, ny) not in self.shots_history):
                    prob_grid[ny][nx] += 3
        
        # Bonus pour les cellules dans l'alignement de hits consécutifs
        for group_id, group_hits in self.ship_hits.items():
            if len(group_hits) >= 2:
                direction = self._get_ship_direction(group_hits)
                
                if direction == 'horizontal':
                    min_x = min(h[0] for h in group_hits)
                    max_x = max(h[0] for h in group_hits)
                    y = group_hits[0][1]  # Tous les y sont identiques
                    
                    # Bonus à gauche
                    if min_x > 0 and (min_x - 1, y) not in self.shots_history:
                        prob_grid[y][min_x - 1] += 5
                    
                    # Bonus à droite
                    if max_x < self.BOARD_SIZE - 1 and (max_x + 1, y) not in self.shots_history:
                        prob_grid[y][max_x + 1] += 5
                
                elif direction == 'vertical':
                    min_y = min(h[1] for h in group_hits)
                    max_y = max(h[1] for h in group_hits)
                    x = group_hits[0][0]  # Tous les x sont identiques
                    
                    # Bonus en haut
                    if min_y > 0 and (x, min_y - 1) not in self.shots_history:
                        prob_grid[min_y - 1][x] += 5
                    
                    # Bonus en bas
                    if max_y < self.BOARD_SIZE - 1 and (x, max_y + 1) not in self.shots_history:
                        prob_grid[max_y + 1][x] += 5
        
        return prob_grid
    
    def update_ship_status(self, ships_sunk):
        """
        Met à jour le statut des navires coulés.
        
        :param ships_sunk: Liste des tailles de navires coulés
        """
        for s in ships_sunk:
            if s in self.remaining_ships:
                self.remaining_ships.remove(s)
    
    def reset(self):
        """
        Réinitialise l'état de l'IA.
        """
        self.remaining_ships = self.ship_sizes.copy()
        self.shots_history = []
        self.successful_hits = []
        self.ship_hits = {}
        self.probability_grid = None