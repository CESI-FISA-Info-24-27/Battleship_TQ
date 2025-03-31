# livre.py
# Book Class (Encapsulation)

class Livre:
    """
    Class representing a book in the library.
    Encapsulates book attributes and controls access to availability state.
    """
    
    def __init__(self, titre, auteur, isbn=None):
        """
        Initialize a new book with a title, author and optional ISBN identifier.
        
        Args:
            titre (str): The book title
            auteur (str): The book author
            isbn (str, optional): The ISBN number of the book
        """
        self.__titre = titre
        self.__auteur = auteur
        self.__isbn = isbn
        self.__disponible = True  # Par défaut, un livre est disponible
    
    # Getters and setters for controlled access to attributes
    @property
    def titre(self):
        return self.__titre
    
    @property
    def auteur(self):
        return self.__auteur
    
    @property
    def isbn(self):
        return self.__isbn
    
    @property
    def disponible(self):
        return self.__disponible
    
    def emprunter(self):
        """
        Attempts to set the book to a borrowed state.
        
        Returns:
            bool: True if the borrowing was successful, False otherwise
        """
        if self.__disponible:
            self.__disponible = False
            return True
        return False
    
    def rendre(self):
        """
        Sets the book back to available state.
        """
        self.__disponible = True
    
    def __str__(self):
        """
        Text representation of the book.
        
        Returns:
            str: Description of the book with its availability status
        """
        statut = "disponible" if self.__disponible else "emprunté"
        return f"'{self.__titre}' par {self.__auteur} ({statut})"
