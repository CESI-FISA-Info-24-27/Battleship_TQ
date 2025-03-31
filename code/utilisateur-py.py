# utilisateur.py
# User Class (Inheritance and Polymorphism)

from abc import ABC, abstractmethod

class Utilisateur(ABC):
    """
    Abstract class representing a library user.
    Serves as a base for specific user types (students, professors).
    """
    
    def __init__(self, nom, prenom, id_utilisateur):
        """
        Initialize a new user.
        
        Args:
            nom (str): User's last name
            prenom (str): User's first name
            id_utilisateur (str): Unique identifier for the user
        """
        self._nom = nom
        self._prenom = prenom
        self._id = id_utilisateur
        self._emprunts = []  # List of active loans
    
    @property
    def nom_complet(self):
        """Returns the full name of the user."""
        return f"{self._prenom} {self._nom}"
    
    @property
    def id(self):
        """Returns the user's identifier."""
        return self._id
    
    @property
    def emprunts(self):
        """Returns the list of user's loans."""
        return self._emprunts
    
    def ajouter_emprunt(self, emprunt):
        """
        Adds a loan to the user's loan list.
        
        Args:
            emprunt: The loan to add
            
        Returns:
            bool: True if the addition was successful, False otherwise (if limit reached)
        """
        if len(self._emprunts) < self.max_emprunts:
            self._emprunts.append(emprunt)
            return True
        return False
    
    def supprimer_emprunt(self, emprunt):
        """
        Removes a loan from the user's loan list.
        
        Args:
            emprunt: The loan to remove
        """
        if emprunt in self._emprunts:
            self._emprunts.remove(emprunt)
    
    @abstractmethod
    def max_emprunts(self):
        """
        Abstract method that defines the maximum number of allowed loans.
        Must be implemented by derived classes.
        """
        pass
    
    def __str__(self):
        """
        Text representation of the user.
        
        Returns:
            str: Description of the user with their number of loans
        """
        return f"{self.nom_complet} (ID: {self._id}) - {len(self._emprunts)}/{self.max_emprunts} emprunts"


class Etudiant(Utilisateur):
    """
    Class representing a student, a specific type of library user.
    Inherits from the User class.
    """
    
    def __init__(self, nom, prenom, id_utilisateur, niveau_etude):
        """
        Initialise un nouvel étudiant.
        
        Args:
            nom (str): Nom de l'étudiant
            prenom (str): Prénom de l'étudiant
            id_utilisateur (str): Identifiant unique de l'étudiant
            niveau_etude (str): Niveau d'étude de l'étudiant (Licence, Master, Doctorat)
        """
        super().__init__(nom, prenom, id_utilisateur)
        self._niveau_etude = niveau_etude
    
    @property
    def niveau_etude(self):
        """Retourne le niveau d'étude de l'étudiant."""
        return self._niveau_etude
    
    @property
    def max_emprunts(self):
        """
        Implémentation de la méthode abstraite qui définit le nombre maximum d'emprunts permis.
        Un étudiant peut emprunter 3 livres maximum.
        
        Returns:
            int: Le nombre maximum d'emprunts permis
        """
        return 3
    
    def __str__(self):
        """
        Représentation textuelle de l'étudiant.
        
        Returns:
            str: Description de l'étudiant avec son niveau d'étude et ses emprunts
        """
        return f"Étudiant: {super().__str__()} - Niveau: {self._niveau_etude}"


class Professeur(Utilisateur):
    """
    Classe représentant un professeur, un type spécifique d'utilisateur de la bibliothèque.
    Hérite de la classe Utilisateur.
    """
    
    def __init__(self, nom, prenom, id_utilisateur, departement):
        """
        Initialise un nouveau professeur.
        
        Args:
            nom (str): Nom du professeur
            prenom (str): Prénom du professeur
            id_utilisateur (str): Identifiant unique du professeur
            departement (str): Département auquel appartient le professeur
        """
        super().__init__(nom, prenom, id_utilisateur)
        self._departement = departement
    
    @property
    def departement(self):
        """Retourne le département du professeur."""
        return self._departement
    
    @property
    def max_emprunts(self):
        """
        Implémentation de la méthode abstraite qui définit le nombre maximum d'emprunts permis.
        Un professeur peut emprunter 10 livres maximum.
        
        Returns:
            int: Le nombre maximum d'emprunts permis
        """
        return 10
    
    def __str__(self):
        """
        Représentation textuelle du professeur.
        
        Returns:
            str: Description du professeur avec son département et ses emprunts
        """
        return f"Professeur: {super().__str__()} - Département: {self._departement}"
