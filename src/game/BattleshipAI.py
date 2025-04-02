import random

class BattleshipAI:
    def __init__(self, difficulty='expert'):
        """
        Initialise l'IA de Bataille Navale avec un niveau de difficulté.
        
        :param difficulty: Niveau de difficulté ('facile', 'moyenne', 'difficile', 'expert')
        """
        self.difficulty = difficulty.lower()
        self.ship_sizes = [5, 4, 3, 3, 2]  # Tailles standard des navires
        self.remaining_ships = self.ship_sizes.copy()

    def choose_target(self, board):
        """
        Choisit une cible en fonction du niveau de difficulté.
        
        :param board: Le plateau de jeu
        :return: Coordonnées (x, y) de la cible
        """
        if self.difficulty == 'facile':
            return self._random_target(board)
        elif self.difficulty == 'moyenne':
            return self._medium_strategy(board)
        elif self.difficulty == 'difficile':
            return self._hard_strategy(board)
        elif self.difficulty == 'expert':
            return self._expert_strategy(board)

    def _random_target(self, board):
        """
        Stratégie de ciblage aléatoire.
        
        :param board: Le plateau de jeu
        :return: Coordonnées (x, y) d'une case non touchée
        """
        width, height = len(board.grid[0]), len(board.grid)
        available = [
            (x, y) for x in range(width) for y in range(height)
            if not any(sx == x and sy == y for sx, sy, _ in board.shots)
        ]
        return random.choice(available) if available else None

    def _medium_strategy(self, board):
        """
        Stratégie de ciblage en damier.
        
        :param board: Le plateau de jeu
        :return: Coordonnées (x, y) d'une case non touchée
        """
        width, height = len(board.grid[0]), len(board.grid)
        available = [
            (x, y) for x in range(width) for y in range(height)
            if (x + y) % 2 == 0 and not any(sx == x and sy == y for sx, sy, _ in board.shots)
        ]
        if not available:
            return self._random_target(board)
        return random.choice(available)

    def _hard_strategy(self, board):
        """
        Stratégie de chasse directionnelle améliorée.
        
        :param board: Le plateau de jeu
        :return: Coordonnées (x, y) d'une cible stratégique
        """
        target = self._hunt_directional(board)
        return target or self._medium_strategy(board)

    def _expert_strategy(self, board):
        """
        Stratégie experte combinant chasse directionnelle et probabilités.
        
        :param board: Le plateau de jeu
        :return: Coordonnées (x, y) de la cible optimale
        """
        # Priorité : chasse directionnelle intelligente
        target = self._hunt_directional(board)
        if target:
            return target
        
        # Sinon : grille de probabilité pondérée
        return self._calculate_weighted_probability_grid(board)

    def _hunt_directional(self, board):
        """
        Méthode de chasse directionnelle basée sur les hits précédents.
        
        :param board: Le plateau de jeu
        :return: Coordonnées (x, y) d'une cible directionnelle, ou None
        """
        hits = [(x, y) for x, y, hit in board.shots if hit]
        tried = {(x, y) for x, y, _ in board.shots}

        # Grouper les hits connectés
        for hit in hits[::-1]:
            connected = self._connected_hits(hit, hits)
            if len(connected) == 1:
                return self._target_adjacent(connected[0], tried)
            else:
                # Déduire la direction
                dx = connected[1][0] - connected[0][0]
                dy = connected[1][1] - connected[0][1]
                last = connected[-1]
                for i in range(1, 5):  # Avancer dans la direction
                    nx, ny = last[0] + dx * i, last[1] + dy * i
                    if not (0 <= nx < len(board.grid[0]) and 0 <= ny < len(board.grid)):
                        break
                    if (nx, ny) in tried:
                        break
                    return (nx, ny)
                
                # Essayer l'autre sens
                first = connected[0]
                for i in range(1, 5):
                    nx, ny = first[0] - dx * i, first[1] - dy * i
                    if not (0 <= nx < len(board.grid[0]) and 0 <= ny < len(board.grid)):
                        break
                    if (nx, ny) in tried:
                        break
                    return (nx, ny)
        return None

    def _target_adjacent(self, cell, tried):
        """
        Trouve une case adjacente non touchée.
        
        :param cell: Cellule de référence
        :param tried: Ensemble des cases déjà essayées
        :return: Coordonnées (x, y) d'une case adjacente
        """
        x, y = cell
        for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
            nx, ny = x + dx, y + dy
            if (0 <= nx < 10 and 0 <= ny < 10) and (nx, ny) not in tried:
                return (nx, ny)
        return None

    def _connected_hits(self, origin, hits):
        """
        Retourne tous les hits connectés en ligne (horizontale ou verticale).
        
        :param origin: Point de départ
        :param hits: Liste de tous les hits
        :return: Liste des hits connectés
        """
        connected = [origin]
        directions = [(1, 0), (0, 1)]
        for dx, dy in directions:
            for sign in [1, -1]:
                x, y = origin
                while True:
                    x += dx * sign
                    y += dy * sign
                    if (x, y) in hits:
                        connected.append((x, y))
                    else:
                        break
        connected.sort()
        return connected

    def _calculate_weighted_probability_grid(self, board):
        """
        Calcule une grille de probabilités pondérées pour le ciblage.
        
        :param board: Le plateau de jeu
        :return: Coordonnées (x, y) de la case la plus probable
        """
        width, height = len(board.grid[0]), len(board.grid)
        prob = [[0 for _ in range(width)] for _ in range(height)]
        shots = {(x, y) for x, y, _ in board.shots}
        hits = {(x, y) for x, y, hit in board.shots if hit}

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

        # Booster les cases autour des hits
        for x, y in hits:
            for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < width and 0 <= ny < height and (nx, ny) not in shots:
                    prob[ny][nx] += 5

        max_val = max(max(row) for row in prob)
        best = [(x, y) for y in range(height) for x in range(width) if prob[y][x] == max_val]
        return random.choice(best) if best else self._random_target(board)

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