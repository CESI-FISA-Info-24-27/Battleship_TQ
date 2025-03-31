# main.py
# Main execution file for the library management system

from bibliotheque import Bibliotheque
from livre import Livre
from factory_utilisateurs import FactoryUtilisateurs
from singleton_config import ConfigurationBibliotheque

def main():
    # Library initialization and configuration
    config = ConfigurationBibliotheque(
        nom="Bibliothèque Universitaire de Paris",
        max_livres_defaut=5000,
        duree_emprunt_defaut=21
    )
    
    print("Configuration de la bibliothèque :")
    print(config)
    print("\n" + "="*50 + "\n")
    
    # Création d'une bibliothèque
    bibliotheque = Bibliotheque()
    print(f"Bibliothèque créée : {bibliotheque}")
    
    # Ajout de quelques livres
    livres = [
        Livre("Le Petit Prince", "Antoine de Saint-Exupéry", "978-2-07-040850-4"),
        Livre("1984", "George Orwell", "978-2-07-036822-8"),
        Livre("Harry Potter à l'école des sorciers", "J.K. Rowling", "978-2-07-054090-1"),
        Livre("L'Étranger", "Albert Camus", "978-2-07-036002-4"),
        Livre("Les Misérables", "Victor Hugo", "978-2-253-09634-8"),
        Livre("Fondation", "Isaac Asimov", "978-2-07-045416-1"),
    ]
    
    for livre in livres:
        bibliotheque.ajouter_livre(livre)
    
    print(f"\nAjout de {len(livres)} livres à la bibliothèque.")
    
    # Création de quelques utilisateurs via la factory
    factory = FactoryUtilisateurs()
    
    utilisateurs = [
        factory.creer_utilisateur("etudiant", "Dupont", "Marie", "E001", niveau_etude="Licence"),
        factory.creer_utilisateur("etudiant", "Martin", "Lucas", "E002", niveau_etude="Master"),
        factory.creer_utilisateur("professeur", "Dubois", "Sophie", "P001", departement="Littérature"),
        factory.creer_utilisateur("professeur", "Leroy", "Pierre", "P002", departement="Sciences"),
    ]
    
    for utilisateur in utilisateurs:
        bibliotheque.enregistrer_utilisateur(utilisateur)
        print(f"Utilisateur enregistré : {utilisateur}")
    
    print("\n" + "="*50 + "\n")
    
    # Emprunts de livres
    print("Emprunts de livres :")
    
    # Premier utilisateur emprunte deux livres
    emprunt1 = bibliotheque.emprunter_livre("E