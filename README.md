# Système de Gestion de Bibliothèque en POO

## Présentation du Projet

Ce mini-projet implémente un système de gestion de bibliothèque avancé en Programmation Orientée Objet (POO) avec Python. Le système permet de gérer un catalogue de livres, des utilisateurs et le processus d'emprunt/retour en appliquant les principes fondamentaux de la POO.

## Principes de POO Appliqués

### 1. Encapsulation
- Mise en œuvre dans la classe `Livre`
- Attributs privés avec accès contrôlé via des propriétés
- Les modifications d'état (emprunt/retour) ne sont possibles que par des méthodes dédiées

### 2. Héritage et Polymorphisme
- Classe abstraite de base `Utilisateur` définissant une interface générique
- Classes enfants `Etudiant` et `Professeur` héritant de cette classe de base
- Implémentation polymorphique de la propriété `max_emprunts` qui retourne des valeurs différentes selon le type d'utilisateur

### 3. Composition
- La classe `Emprunt` crée des relations entre les livres et les utilisateurs
- Elle gère le cycle de vie des emprunts sans coupler fortement les classes `Livre` et `Utilisateur`

### 4. Classes Abstraites
- Utilisation du module `ABC` de Python pour créer des classes abstraites
- Force l'implémentation des méthodes requises dans les classes enfants

### 5. Design Patterns
- **Pattern Singleton** : Implémenté dans la classe `ConfigurationBibliotheque` pour assurer une configuration globale unique
- **Pattern Factory** : Utilisé dans `FactoryUtilisateurs` pour créer différents types d'utilisateurs sans exposer les constructeurs

## Structure du Projet

- **livre.py** : Classe Livre avec encapsulation de l'état de disponibilité
- **utilisateur.py** : Classe abstraite Utilisateur avec les classes enfants Etudiant et Professeur
- **emprunt.py** : Classe Emprunt qui gère la relation livre-utilisateur
- **bibliotheque.py** : Classe principale de gestion de la bibliothèque
- **singleton_config.py** : Singleton pour la configuration de la bibliothèque
- **factory_utilisateurs.py** : Factory pour créer différents types d'utilisateurs
- **main.py** : Fichier d'exécution principal démontrant le système

## Fonctionnalités Implémentées

### Gestion des Livres
- Ajout de livres au catalogue de la bibliothèque
- Recherche de livres par titre, auteur ou ISBN
- Suivi de la disponibilité des livres

### Gestion des Utilisateurs
- Enregistrement de différents types d'utilisateurs (étudiants et professeurs)
- Application de limites d'emprunt différentes selon le type d'utilisateur
- Suivi de l'historique d'emprunt des utilisateurs

### Système d'Emprunt
- Traitement des emprunts et retours de livres
- Suivi des dates d'emprunt et dates d'échéance
- Identification des emprunts en retard

### Configuration
- Source unique de configuration pour les paramètres de la bibliothèque
- Durées d'emprunt et limites de capacité configurables

## Comment Utiliser

1. Initialiser une bibliothèque avec `Bibliotheque()`
2. Ajouter des livres avec `ajouter_livre()`
3. Enregistrer des utilisateurs via la factory avec `FactoryUtilisateurs.creer_utilisateur()`
4. Traiter les emprunts avec `emprunter_livre()`
5. Gérer les retours avec `retourner_livre()`
