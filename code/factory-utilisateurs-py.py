# factory_utilisateurs.py
# Factory for creating users

from utilisateur import Etudiant, Professeur

class FactoryUtilisateurs:
    """
    Factory class for creating different types of users.
    Follows the Factory pattern to hide implementation details of the classes.
    """
    
    @staticmethod
    def creer_utilisateur(type_utilisateur, nom, prenom, id_utilisateur, **kwargs):
        """
        Creates and returns a new user of the specified type.
        
        Args:
            type_utilisateur (str): The type of user to create ('etudiant' or 'professeur')
            nom (str): Last name of the user
            prenom (str): First name of the user
            id_utilisateur (str): Unique identifier for the user
            **kwargs: Arguments specific to the user type
                - niveau_etude (str): For students
                - departement (str): For professors
        
        Returns:
            Utilisateur: An instance of the appropriate class
            
        Raises:
            ValueError: If the user type is unknown
        """
        if type_utilisateur.lower() == 'etudiant':
            niveau_etude = kwargs.get('niveau_etude', 'Non spécifié')
            return Etudiant(nom, prenom, id_utilisateur, niveau_etude)
        
        elif type_utilisateur.lower() == 'professeur':
            departement = kwargs.get('departement', 'Non spécifié')
            return Professeur(nom, prenom, id_utilisateur, departement)
        
        else:
            raise ValueError(f"Type d'utilisateur inconnu: {type_utilisateur}")
