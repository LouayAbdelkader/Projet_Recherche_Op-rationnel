
# Projet Recherche Opérationnelle - Application 2

**REPUBLIQUE TUNISIENNE**  
Ministère de l’Enseignement Supérieur et de la Recherche Scientifique  
Université de Carthage  
Institut National des Sciences Appliquées et de Technologie  

**Spécialité : RT3**  
**Enseignante : Mme. Imen Ajili**  
**Année Universitaire : 2025 / 2026**

---

## Équipe de développement

| Membre | Problème traité |
|--------|----------------|
| Amal Torjmen | Transport / Acheminement de l’aide alimentaire |
| Mohamed Louay Abdelkader | Affectation des avions aux vols (surclassement) |
| Nour Besrour | Coloriage de graphe / Allocation de fréquences radio |
| Nour Smadhi | Localisation (P-Median) / Stations de recharge électrique |
| Baya Bouzouita | Set Covering / Planification du personnel 24h/24 |

---

## Problèmes d’optimisation implémentés

1. **Logistique Humanitaire** – Transport multi‑modes de l’aide vers zones sinistrées  
2. **Affectation Avions & Surclassement** – Optimisation de flotte aérienne  
3. **Allocation de fréquences radio** – Coloriage de graphe sans interférence  
4. **P‑Median** – Localisation optimale de stations de recharge électrique  
5. **Set Covering** – Planification minimale du personnel en station‑service 24h/24

---

## Prérequis

- Python 3.8 ou supérieur
- Bibliothèques : `PyQt5`, `pandas`, `numpy`, `gurobipy` (avec licence Gurobi académique ou valide)
- Fichiers CSV d’exemple fournis dans le dossier `data/`

---

## Installation et exécution

1. **Cloner ou extraire** l’archive du projet dans un dossier.
2. **Installer les dépendances** (de préférence dans un environnement virtuel) :
   ```bash
   pip install -r requirements.txt
   ```
3. **Lancer l’application** :

> Pour lancer l'interface de notre Application, il suffit de lancer le fichier `main.py` du dossier parent (celui‑là).  
> **« Vous pouvez madame choisir le modèle que vous voulez exécuter. »**

```bash
python main.py
```

---

## Utilisation

1. À l’accueil, sélectionnez l’un des cinq problèmes dans le menu principal.
2. Pour chaque problème :
   - **Onglet Données** : importez/modifiez les fichiers CSV (stocks, demandes, trajets, etc.).
   - **Onglet Optimisation** : paramétrez les poids, budgets, pénalités, puis lancez le calcul.
   - **Onglet Résultats / Visualisation** : consultez les KPIs, graphiques, graphes bipartis ou cartes géographiques.
3. Export possible des résultats et logs.

---

## Structure du projet

```
.
├── main.py                 # Point d’entrée unique de l’application
├── requirements.txt
├── README.md
├── interface/              # Modules PyQt5 pour chaque problème
├── models/                 # Modèles mathématiques (gurobipy)
├── data/                   # Fichiers CSV d’exemple
└── utils/                  # Fonctions partagées (lecture CSV, logs)
```

---

## Remarque

- Tous les problèmes utilisent **Gurobi** comme solveur.  
  En cas d’absence de licence, le modèle affichera un message d’erreur.
- Les données d’exemple sont fournies pour chaque cas d’usage (transport, avions, fréquences, p‑median, set covering).

---

**Pour toute question relative à l’exécution, veuillez contacter l’équipe projet.**  
