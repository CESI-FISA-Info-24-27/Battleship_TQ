# emprunt.py
# Loan Management (Composition)

from datetime import datetime, timedelta

class Emprunt:
    """
    Class representing a book loan by a user.
    Uses composition to link a book to a user.
    """
    
    def __init__(self, livre, utilisateur, duree_jours=14):
        """
        Initialize a new loan.
        
        Args:
            livre: The borrowed book
            utilisateur: The user borrowing the book
            duree_jours (int, optional): The loan duration in days, default is 14 days
        """
        self.__livre = livre
        self.__utilisateur = utilisateur
        self.__date_emprunt = datetime.now()
        self.__date_retour_prevue = self.__date_emprunt + timedelta(days=duree_jours)
        self.__date_retour_effective = None
        self.__actif = True
        
        # Mark the book as borrowed
        self.__livre.emprunter()
    
    @property
    def livre(self):
        """Returns the borrowed book."""
        return self.__livre
    
    @property
    def utilisateur(self):
        """Returns the user who borrowed the book."""
        return self.__utilisateur
    
    @property
    def date_emprunt(self):
        """Returns the loan date."""
        return self.__date_emprunt
    
    @property
    def date_retour_prevue(self):
        """Returns the expected return date."""
        return self.__date_retour_prevue
    
    @property
    def date_retour_effective(self):
        """Returns the actual return date if the book has been returned."""
        return self.__date_retour_effective
    
    @property
    def actif(self):
        """Returns True if the loan is still active, False otherwise."""
        return self.__actif
    
    def retourner(self):
        """
        Marks the book as returned and ends the loan.
        
        Returns:
            bool: True if the return was successful, False otherwise
        """
        if self.__actif:
            self.__livre.rendre()
            self.__date_retour_effective = datetime.now()
            self.__actif = False
            return True
        return False
    
    def est_en_retard(self):
        """
        Checks if the loan is overdue.
        
        Returns:
            bool: True if the loan is overdue, False otherwise
        """
        if not self.__actif:
            return False
        return datetime.now() > self.__date_retour_prevue
    
    def __str__(self):
        """
        Text representation of the loan.
        
        Returns:
            str: Description of the loan with dates and status
        """
        statut = "actif" if self.__actif else "retourné"
        if self.__actif:
            if self.est_en_retard():
                statut = "en retard"
            retour_info = f"à rendre avant le {self.__date_retour_prevue.strftime('%d/%m/%Y')}"
        else:
            retour_info = f"retourné le {self.__date_retour_effective.strftime('%d/%m/%Y')}"
        
        return f"Emprunt de '{self.__livre.titre}' par {self.__utilisateur.nom_complet} - {statut}, {retour_info}"
