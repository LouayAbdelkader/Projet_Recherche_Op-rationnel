#  Operations Decision  - Optimisation Logistique Humanitaire

##  Introduction

**Operations Decision Suite** est une application avancée d'optimisation logistique dédiée aux opérations humanitaires. Elle combine une interface moderne et intuitive avec la puissance du solveur **Gurobi** pour résoudre des problèmes complexes d’allocation de ressources sous contraintes multiples.

##  Fonctionnalités Clés

###  Interface Moderne & Intuitive
- Tableau de bord avec métriques en temps réel
- Visualisation graphique des flux logistiques
- Interface sombre moderne avec animations fluides
- Navigation par onglets intuitive

###  Optimisation Avancée
- Minimisation des coûts totaux (fixes, variables et pénalités)
- Gestion des contraintes de température (produits réfrigérés)
- Respect strict des délais de livraison
- Allocation optimale des véhicules disponibles

###  Visualisations Riches
- Graphe réseau interactif (entrepôts → zones)
- Graphiques circulaires et barres pour l’analyse
- Cartes KPI animées avec compteurs progressifs
- Logs détaillés avec horodatage

###  Gestion des Données
- Import/export de fichiers CSV
- Prévisualisation des données tabulaires
- Génération automatique de jeux de données démo
- Validation des données en temps réel

##  Architecture Technique

### Structure des Fichiers
```
operations-decision-suite/
├── frontend.py          # Interface graphique complète
├── backend.py           # Logique d'optimisation Gurobi
├── README.md            # Documentation (ce fichier)
├── produits.csv
├── vehicules_types.csv
├── entrepots.csv
├── demandes.csv
└── transport_couts.csv

```

### Technologies Utilisées
| Technologie   | Rôle                       | Version |
|---------------|----------------------------|---------|
| Python        | Langage principal          | 3.9+    |
| PySide6       | Interface graphique        | 6.5+    |
| Gurobi        | Solveur d’optimisation     | 10.0+   |
| Pandas        | Manipulation des données   | 2.0+    |
| PyQt6-Charts  | Visualisations graphiques  | 6.5+    |

##  Installation Rapide

### 1. Prérequis Système
- Python 3.9 ou supérieur
- 4 Go de RAM minimum
- Licence Gurobi valide (académique ou commerciale)

### 2. Installation des Dépendances
```bash
# Clonez le projet
git clone <votre-repo>
cd operations-decision-suite

# Installez les dépendances
pip install PySide6 pandas gurobipy PyQt6-Charts
```

### 3. Configuration de Gurobi
- Téléchargez Gurobi : [gurobi.com/download](https://www.gurobi.com/downloads/)
- Obtenez une licence :
  - Licence académique gratuite : [gurobi.com/academia](https://www.gurobi.com/academia)
  - Licence commerciale : usage professionnel
- Configurez la licence :
```bash

```

### 4. Lancement de l’Application
```bash
python main.py
```

##  Guide d’Utilisation

### Étape 1 : Lancement
- Exécutez `python main.py`
- Les fichiers CSV de démonstration sont générés automatiquement
- Sélectionnez **HUMANITAIRE** dans le launcher

### Étape 2 : Inspection des Données
- Onglet **DONNÉES**
- Visualisez :
  - Demandes clients
  - Stocks entrepôts
  - Types de véhicules
  - Catalogue produits
  - Coûts de transport
- Importez vos propres fichiers CSV

### Étape 3 : Configuration
- Onglet **OPTIMISATION & ANALYSE**
- Configurez la flotte :
  - Camion_Std : 10 unités
  - Camion_Frigo : 10 unités
  - Avion : 10 unités
- Paramètres de pénalités :
  - Retard : 500€ / unité
  - Mésusage : 50€ / unité

### Étape 4 : Exécution
- Cliquez sur **LANCER L’OPTIMISATION**
- Suivez la progression dans les logs
- Résultats en temps réel :
  - KPI animés
  - Graphiques mis à jour
  - Visualisation du réseau
  - Plan de transport détaillé

### Étape 5 : Analyse des Résultats
- **Tableau de Bord**
  - Coût total
  - Taux de service
  - Nombre de routes
  - Véhicules actifs
- **Réseau Logistique**
  - Entrepôts (rectangles bleus) → Zones (cercles rouges)
  - Couleurs selon type de transport :
    - Bleu : Camions frigorifiques
    - Violet : Avions
    - Gris : Camions standards
- **Plan de Transport**
  - Origine / Destination
  - Type et nombre de véhicules
  - Produits transportés
  - Quantités spécifiques

##  Modèle Mathématique

### Fonction Objectif
Minimiser :
```
Z = Σ(Cout_Fixe × n) + Σ(Cout_Var × x) + Σ(Penalite_Retard × x)
    + Σ(Penalite_Mesusage × x) + Σ(Penalite_Manque × d_manque)
```

### Variables de Décision
- `x[i,j,m,k]` : Quantité du produit k transportée de i à j avec le mode m  
- `n[i,j,m]` : Nombre de véhicules du mode m sur l'arc (i,j)  
- `d_manque[j,k]` : Quantité manquante du produit k dans la zone j  

### Contraintes Principales
1. **Satisfaction de la demande**
```
Σ x[i,j,m,k] + d_manque[j,k] = Demande[j,k]   ∀ j,k
```
2. **Limitation des stocks**
```
Σ x[i,j,m,k] ≤ Stock[i,k]   ∀ i,k
```
3. **Capacité des véhicules**
```
Σ (Volume[k] × x[i,j,m,k]) ≤ Capacite[m] × n[i,j,m]   ∀ i,j,m
```
4. **Contraintes de froid**
```
x[i,j,m,k] = 0   si Besoin_Froid[k]=1 et Est_Refrigere[m]=0
x[i,j,m,k] = 0   si Besoin_Froid[k]=1 et A_Chambre_Froide[i]=0
```
5. **Limitation de la flotte**
```
Σ n[i,j,m] ≤ Flotte_Disponible[m]   ∀ m
```
6. **Contraintes de temps**
```
x[i,j,m,k] = 0   si Temps_Transport[i,j,m] > Temps_Max[k,j]
```

---

