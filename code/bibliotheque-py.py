# bibliotheque.py
# Main library management class

from singleton_config import ConfigurationBibliotheque
from emprunt import Emprunt

class Bibliotheque:
    """
    Main class managing the entire library system.
    Responsible for book management, users and loans.
    """
    
    def __init__(self):
        """
        Initializes a new library with default configurations.
        """
        self.__config = ConfigurationBibliotheque()
        self.__livres = []
        self.__utilisateurs = {}  # Dictionary with ID as key
        self.__emprunts = []
    
    @property
    def nom(self):
        """Returns the name of the library."""
        return self.__config.nom
    
    @property
    def nombre_livres(self):
        """Returns the number of books in the library."""
        return len(self.__livres)
    
    @property
    def nombre_utilisateurs(self):
        """Returns the number of registered users."""
        return len(self.__utilisateurs)
    
    @property
    def nombre_emprunts_actifs(self):
        """Returns the number of active loans."""
        return sum(1 for emprunt in self.__emprunts if emprunt.actif)
    
    def ajouter_livre(self, livre):
        """
        Adds a book to the library.
        
        Args:
            livre: The book to add
            
        Returns:
            bool: True if the addition was successful, False otherwise
        """
        if len(self.__livres) < self.__config.max_livres_defaut:
            self.__livres.append(livre)
            return True
        return False
    
    def enregistrer_utilisateur(self, utilisateur):
        """
        Registers a user in the library.
        
        Args:
            utilisateur: The user to register
            
        Returns:
            bool: True if the registration was successful, False otherwise
        """
        if utilisateur.id not in self.__utilisateurs:
            self.__utilisateurs[utilisateur.id] = utilisateur
            return True
        return False
    
    def rechercher_livre(self, titre=None, auteur=None, isbn=None):
        """
        Searches for books based on different criteria.
        
        Args:
            titre (str, optional): Title or part of title to search for
            auteur (str, optional): Author or part of author name to search for
            isbn (str, optional): Exact ISBN to search for
            
        Returns:
            list: List of books matching the criteria
        """
        resultats = []
        
        for livre in self.__livres:
            match = True
            
            if titre and titre.lower() not in livre.titre.lower():
                match = False
            if auteur and auteur.lower() not in livre.auteur.lower():
                match = False
            if isbn and livre.isbn != isbn:
                match = False
                
            if match:
                resultats.append(livre)
                
        return resultats
    
    def obtenir_utilisateur(self, id_utilisateur):
        """
        Retrieves a user by their ID.
        
        Args:
            id_utilisateur (str): The ID of the user to retrieve
            
        Returns:
            Utilisateur: The found user or None if not found
        """
        return self.__utilisateurs.get(id_utilisateur)
    
    def emprunter_livre(self, id_utilisateur, livre):
        """
        Allows a user to borrow a book.
        
        Args:
            id_utilisateur (str): The user's ID
            livre: The book to borrow
            
        Returns:
            Emprunt: The created loan or None if the loan could not be made
        """
        utilisateur = self.obtenir_utilisateur(id_utilisateur)
        
        if not utilisateur:
            print(f"Utilisateur avec ID {id_utilisateur} non trouvé.")
            return None
        
        if not livre.disponible:
            print(f"Le livre '{livre.titre}' n'est pas disponible.")
            return None
        
        # Vérifier si l'utilisateur peut emprunter plus de livres
        if len(utilisateur.emprunts) >= utilisateur.max_emprunts:
            print(f"L'utilisateur {utilisateur.nom_complet} a atteint sa limite d'emprunts.")
            return None
        
        # Créer l'emprunt
        emprunt = Emprunt(livre, utilisateur, self.__config.duree_emprunt_defaut)
        self.__emprunts.append(emprunt)
        
        # Ajouter l'emprunt à l'utilisateur
        utilisateur.ajouter_emprunt(emprunt)
        
        return emprunt
    
    def retourner_livre(self, emprunt):
        """
        Allows returning a borrowed book.
        
        Args:
            emprunt: The loan to complete
            
        Returns:
            bool: True if the return was successful, False otherwise
        """
        if emprunt not in self.__emprunts or not emprunt.actif:
            return False
        
        # Retourner le livre
        emprunt.retourner()
        
        # Supprimer l'emprunt de la liste de l'utilisateur
        emprunt.utilisateur.supprimer_emprunt(emprunt)
        
        return True
    
    def obtenir_livres_disponibles(self):
        """
        Returns the list of books available for loan.
        
        Returns:
            list: List of available books
        """
        return [livre for livre in self.__livres if livre.disponible]
    
    def obtenir_emprunts_utilisateur(self, id_utilisateur):
        """
        Returns the list of active loans for a user.
        
        Args:
            id_utilisateur (str): The user's ID
            
        Returns:
            list: List of active loans for the user
        """
        utilisateur = self.obtenir_utilisateur(id_utilisateur)
        if not utilisateur:
            return []
        
        return [emprunt for emprunt in utilisateur.emprunts if emprunt.actif]
    
    def obtenir_emprunts_en_retard(self):
        """
        Returns the list of overdue loans.
        
        Returns:
            list: List of overdue loans
        """
        return [emprunt for emprunt in self.__emprunts if emprunt.actif and emprunt.est_en_retard()]
    
    def __str__(self):
        """
        Text representation of the library.
        
        Returns:
            str: Description of the library with its statistics
        """
        return f"{self.nom} - {self.nombre_livres} livres, {self.nombre_utilisateurs} utilisateurs, " \
               f"{self.nombre_emprunts_actifs} emprunts actifs"
