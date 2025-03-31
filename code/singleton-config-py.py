# singleton_config.py
# Singleton for library configuration

class ConfigurationBibliotheque:
    """
    Singleton class for library configuration.
    Ensures that only one configuration instance exists.
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """
        Implementation of the Singleton pattern ensuring that only 
        one instance of this class can be created.
        """
        if cls._instance is None:
            cls._instance = super(ConfigurationBibliotheque, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, nom="Bibliothèque Municipale", max_livres_defaut=1000, duree_emprunt_defaut=14):
        """
        Initializes the library configuration.
        Initializes only once, even if the instance is called multiple times.
        
        Args:
            nom (str, optional): The name of the library
            max_livres_defaut (int, optional): Default maximum book capacity
            duree_emprunt_defaut (int, optional): Default loan duration in days
        """
        if not self._initialized:
            self._nom = nom
            self._max_livres_defaut = max_livres_defaut
            self._duree_emprunt_defaut = duree_emprunt_defaut
            self._initialized = True
    
    @property
    
    @nom.setter
    def nom(self, nouveau_nom):
        """
        Définit un nouveau nom pour la bibliothèque.
        
        Args:
            nouveau_nom (str): Le nouveau nom de la bibliothèque
        """
        self._nom = nouveau_nom
    
    @max_livres_defaut.setter
    def max_livres_defaut(self, nouvelle_valeur):
        """
        Définit une nouvelle capacité maximale de livres par défaut.
        
        Args:
            nouvelle_valeur (int): La nouvelle capacité maximale
        """
        if nouvelle_valeur > 0:
            self._max_livres_defaut = nouvelle_valeur
    
    @duree_emprunt_defaut.setter
    def duree_emprunt_defaut(self, nouvelle_duree):
        """
        Définit une nouvelle durée d'emprunt par défaut.
        
        Args:
            nouvelle_duree (int): La nouvelle durée d'emprunt en jours
        """
        if nouvelle_duree > 0:
            self._duree_emprunt_defaut = nouvelle_duree
    
    def __str__(self):
        """
        Représentation textuelle de la configuration.
        
        Returns:
            str: Description de la configuration de la bibliothèque
        """
        return f"Configuration de {self._nom} - Capacité: {self._max_livres_defaut} livres, " \
               f"Durée d'emprunt par défaut: {self._duree_emprunt_defaut} jours"
