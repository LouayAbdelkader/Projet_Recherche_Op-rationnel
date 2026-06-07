# Airline Fleet Optimizer

## 📋 Vue d'ensemble

Airline Fleet Optimizer est une application d'optimisation de flotte aérienne qui combine une interface utilisateur moderne avec un solveur d'optimisation Gurobi afin de résoudre des problèmes d'affectation d'avions aux vols tout en optimisant les coûts, la satisfaction client et les contraintes opérationnelles.

---

##  Lancement de l'application

### Option 1 : Via le lanceur principal
Exécuter l'application depuis le dossier parent :

```bash
python main.py -> Sélectionner l'option 2 (Transport) dans l'interface du launcher 
```

### Option 2 : Directement via l'interface
Lancer directement l'interface graphique :

```bash
python frontend.py
```

---

## Structure des fichiers

```
Projet/
├── main.py              # Point d'entrée principal
├── launcher.py          # Module de lancement
├── backend.py           # Modèle d'optimisation Gurobi
├── frontend.py          # Interface graphique (PySide6)
├── avions.csv           # Données des avions
├── vols.csv             # Données des vols
└── Readme.md            # Documentation du projet
```

---

##  Dépendances

### Environnement requis
- Python 3.8 ou plus

### Bibliothèques Python

```bash
pip install PySide6 pandas gurobipy
```

 **Important** :  
Gurobi nécessite une licence valide. Une licence académique gratuite est disponible sur :  
-> https://www.gurobi.com/academia/academic-program-and-licenses/

---

##  Fonctionnalités principales

### 1. Interface multi-onglets
- **Données** : Chargement et prévisualisation des fichiers CSV
- **Optimisation** : KPIs, résultats détaillés et logs Gurobi
- **Réseau** : Visualisation graphique des affectations avion → vol

### 2. Optimisation avec Gurobi
- Minimisation des coûts
- Maximisation de la satisfaction client
- Optimisation du temps de vol
- Respect des contraintes opérationnelles

### 3. Visualisations
- Diagrammes circulaires (utilisation des avions)
- Histogrammes (surclassements)
- Graphe réseau interactif
- Mise à jour en temps réel des indicateurs

### 4. Gestion des données
- Chargement dynamique des CSV
- Validation automatique des formats
- Affichage tabulaire des données

---

##  Paramètres de configuration

### Pondérations (priorités)
- **Coût**
- **Satisfaction**
- **Temps de vol**

### Paramètres globaux
- Coût par surclassement
- Quota maximal d’émissions CO₂

---

##  Format des fichiers de données

### avions.csv (exemple)

```csv
AvionID,Type,K_eco,K_bus,C_op,E_CO2,H_max
1,A220,90,8,650,10,13
2,A320,120,18,600,18,14
```

**Description des colonnes**
- `AvionID` : Identifiant de l’avion
- `Type` : Modèle
- `K_eco` : Capacité économique
- `K_bus` : Capacité affaires
- `C_op` : Coût opérationnel par heure
- `E_CO2` : Émissions CO₂ par heure
- `H_max` : Heures de vol maximales par jour

---

### vols.csv (exemple)

```csv
VolID,Route,P_eco,P_bus,Duree
101,Tunis-Paris,100,15,4.6
102,Paris-Londres,110,20,3.4
```

**Description des colonnes**
- `VolID` : Identifiant du vol
- `Route` : Trajet
- `P_eco` : Demande économique
- `P_bus` : Demande affaires
- `Duree` : Durée du vol (heures)

---

##  Logique d'optimisation

### Fonction objectif

```
Minimiser : w1 × Coûts − w2 × Satisfaction + w3 × Temps
```

### Contraintes principales
1. Chaque vol est affecté à un seul avion
2. Respect des capacités par classe
3. Surclassement limité par la demande économique
4. Heures de vol ≤ H_max
5. Respect du quota CO₂
6. Gestion des conflits temporels

---

##  Interface utilisateur

### Design
- Thème sombre professionnel
- Animations fluides
- Cartes et indicateurs visuels
- Interface responsive

### Palette de couleurs
- Fond : `#121218`
- Panneaux : `#1e1e24`
- Accent : `#5c7cfa`
- Texte : `#ffffff`

---

##  Résultats et indicateurs

### KPIs
- Coût total
- Satisfaction moyenne
- Nombre de surclassements
- Émissions CO₂
- Nombre de vols couverts

### Visualisation
- Détails par vol
- Graphiques analytiques
- Graphe global des affectations
- Logs détaillés du solveur Gurobi

---

##  Développement et extensions

### Ajouter une fonctionnalité
1. Modifier `backend.py`
2. Adapter `frontend.py`
3. Mettre à jour les fichiers CSV si nécessaire

### Extensions possibles
- Nouvelles contraintes
- Autres modèles de satisfaction
- Export PDF / Excel
- Scénarios multi-journées

---

##  Dépannage

### Problèmes courants

**Gurobi non installé**
```bash
pip install gurobipy
```

**Fichiers CSV introuvables**
- Vérifier les chemins
- Utiliser le sélecteur de fichiers

**Modèle irréalisable**
- Contraintes trop strictes
- Données incompatibles

**Interface ne s’affiche pas**
```bash
pip install PySide6
```

---

##  Journal des versions

### Version 1.0
- Interface graphique complète
- Modèle Gurobi intégré
- Visualisations avancées
- Gestion dynamique des données

---


##  Support

- Consulter les logs Gurobi
- Vérifier les formats CSV
- Contacter l’équipe de développement

---

**Note** : Une licence Gurobi valide est obligatoire pour exécuter l’optimisation. Une licence académique gratuite est disponible pour les étudiants et enseignants.
