# Application d’Optimisation de Stations de Recharge Électrique

## Description
Application de bureau dédiée à l’optimisation du placement de stations de recharge pour véhicules électriques. Le logiciel aide les planificateurs urbains et les entreprises de services publics à déterminer des emplacements optimaux tout en respectant des contraintes budgétaires et opérationnelles.

---

## Fonctionnalités

### 1. Gestion des données
- Importation de matrices de distance depuis des fichiers CSV
- Génération de données d’exemple avec distances aléatoires entre zones
- Saisie manuelle des données via des tableaux interactifs
- Support de différents types de zones :
  - Demande forte
  - Demande moyenne
  - Demande faible

### 2. Moteur d’optimisation
Résolution d’un problème d’optimisation permettant de déterminer :
- Les zones devant accueillir des stations de recharge
- L’affectation des zones aux stations
- La minimisation de la distance totale dans les limites du budget

Contraintes prises en compte :
- Contraintes budgétaires
- Nombre maximum de stations
- Distance de service maximale
- Limites de capacité des stations

### 3. Interface utilisateur
- **Tableau des distances** : affichage des distances entre toutes les zones
- **Contrôles des paramètres** : budget, limites de stations, contraintes
- **Visualisation interactive** :
  - Emplacements des zones (colorées selon le type de demande)
  - Stations sélectionnées (marqueurs en forme de pentagone jaune)
  - Lignes d’affectation entre zones et stations
- **Affichage des résultats** :
  - Indicateurs de performance clés (KPIs)
  - Liste des stations sélectionnées avec leurs coûts
  - Rapport d’affectation des zones
  - Journaux d’optimisation

---

## Installation

### Prérequis
- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)

### Dépendances
Installer les paquets requis :

```bash
pip install PySide6 numpy matplotlib
```

### Structure des fichiers

```text
project/
├── main.py                    # Point d’entrée principal
├── gui_controller.py          # Contrôleur de l’interface
├── worker_thread.py           # Thread d’optimisation
├── custom_widgets.py          # Widgets personnalisés
├── constants.py               # Constantes et styles
├── ui/
│   └── main_window.ui         # Fichier UI principal
└── README.md                  # Ce fichier
```

---

## Utilisation

### 1. Lancement de l’application

```bash
python main.py
```

### 2. Chargement des données
- Cliquer sur **Importer** pour charger un fichier CSV
- Ou cliquer sur **Générer** pour créer des données d’exemple

### 3. Configuration des paramètres
- Définir le budget disponible
- Spécifier le nombre maximum de stations
- Activer ou désactiver les contraintes de distance et de capacité
- Ajuster les valeurs des contraintes selon les besoins

### 4. Exécution de l’optimisation
- Cliquer sur **LANCER L’OPTIMISATION**
- Attendre la fin du calcul (le bouton est désactivé pendant l’exécution)
- Consulter les résultats dans les différents onglets

### 5. Interprétation des résultats
- **Tableau de bord** : KPIs principaux (distance totale, stations, budget)
- **Liste des stations** : stations sélectionnées avec coûts et types
- **Affectations** : détail des zones servies par chaque station
- **Graphique** : visualisation spatiale de la solution
- **Journaux** : détails techniques de l’optimisation

---

## Format des fichiers CSV

### Structure acceptée
- Matrice carrée de distances (n × n)
- Séparateur : virgule (,) ou point-virgule (;)
- En-têtes optionnels
- Valeurs numériques uniquement
- Diagonale contenant des zéros ou laissée vide

### Exemple

```text
Zone 1,Zone 2,Zone 3
0,15.2,25.7
15.2,0,18.3
25.7,18.3,0
```

---

## Architecture technique

### Composants principaux
- **GUIController** : contrôleur principal de l’interface
- **OptimizationThread** : exécution asynchrone de l’optimisation
- **Custom Widgets** : widgets personnalisés pour une interface moderne
- **Intégration Matplotlib** : visualisation des solutions

### Technologies utilisées
- Frontend : PySide6 (Qt for Python)
- Visualisation : Matplotlib
- Calculs : NumPy
- Optimisation : solveur mathématique implémenté dans `worker_thread.py`

---

## Personnalisation

### Types de zones
- Forte : coût 5000 €, demande élevée
- Moyenne : coût 3000 €, demande moyenne
- Faible : coût 1500 €, demande faible

### Paramètres par défaut
- Budget initial : 20 000 €
- Distance maximale : configurable
- Capacité par station : configurable

---

## Débogage

### Messages de log
L’application génère des messages détaillés dans la console concernant :
- Le chargement de l’interface
- L’importation des données
- La progression de l’optimisation
- Les erreurs éventuelles

### Problèmes courants
- **Fichier CSV non reconnu** : vérifier le format et le séparateur
- **Optimisation trop longue** : réduire le nombre de zones
- **Graphique non affiché** : vérifier l’installation de Matplotlib

---

## Performance

### Recommandations
- Nombre optimal de zones : 10 à 50
- Temps d’optimisation proportionnel au carré du nombre de zones
- Utilisation mémoire modérée

### Optimisations internes
- Calcul asynchrone dans un thread séparé
- Mise à jour incrémentale de l’interface
- Mise en cache des données intermédiaires

---

## Licence
Ce projet est fourni à des fins éducatives et professionnelles. Pour toute utilisation commerciale, contacter l’auteur.

---

## Support
Pour toute question technique :
- Consulter l’onglet **Journaux**
- Vérifier la console Python pour les erreurs détaillées
- S’assurer que toutes les dépendances sont correctement installées

