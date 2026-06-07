import gurobipy as gp
from gurobipy import GRB
import numpy as np



def solve_budget_constrained_median(distances, demands, station_costs, budget, max_stations=None, capacities=None, max_distance=None):
    """
    Résout le problème de localisation de stations sous contrainte budgétaire
    (Similaire au problème de "Location Allocation" ou "Uncapacitated Facility Location").
    
    Args:
        distances (list): Matrice des distances entre les zones (n x n)
        demands (list): Liste des demandes pour chaque zone
        station_costs (list): Coût d'installation d'une station pour chaque zone candidate
        budget (float): Budget total disponible
        max_stations (int, optional): Nombre MAX de stations (remplace p, est optionnel).
        capacities (list, optional): Capacités maximales par station
        max_distance (float, optional): Distance maximale autorisée
    
    Returns:
        dict: Solution contenant stations ouvertes, assignations, coût total et valeur objective
    """
    try:
        n = len(distances)  # Nombre de zones
        
        # Vérification des données d'entrée
        if n == 0 or len(station_costs) != n:
            raise ValueError("Données d'entrée invalides (distances ou coûts)")
        
        # Création du modèle
        model = gp.Model("budget_constrained_median")
        
        # Variables de décision
        # x_j = 1 si on ouvre une station au site j
        x = model.addVars(n, vtype=GRB.BINARY, name="x")
        
        # y_ij = 1 si la zone i est assignée à la station j
        y = model.addVars(n, n, vtype=GRB.BINARY, name="y")
        
        # Fonction objectif: Minimiser la distance totale pondérée par la demande
        objective = gp.quicksum(
            demands[i] * distances[i][j] * y[i, j]
            for i in range(n)
            for j in range(n)
        )
        model.setObjective(objective, GRB.MINIMIZE)
        
        # --- Contraintes ---
        
        # Contrainte 1: Chaque zone doit être assignée à exactement une station
        for i in range(n):
            model.addConstr(
                gp.quicksum(y[i, j] for j in range(n)) == 1,
                name=f"Assignation_zone_{i}"
            )
        
        # Contrainte 2: On ne peut assigner une zone qu'à une station ouverte
        for i in range(n):
            for j in range(n):
                model.addConstr(
                    y[i, j] <= x[j],
                    name=f"Station_ouverte_{i}_{j}"
                )
        
        # Contrainte 3 (NOUVELLE): Contrainte de Budget
        # La somme des coûts des stations ouvertes ne doit pas dépasser le budget
        model.addConstr(
            gp.quicksum(station_costs[j] * x[j] for j in range(n)) <= budget,
            name="Budget_Max"
        )
        
        # Contrainte 4 (Optionnelle): Nombre MAX de stations
        if max_stations is not None and max_stations > 0:
            model.addConstr(
                gp.quicksum(x[j] for j in range(n)) <= max_stations,
                name="Max_Stations"
            )
        
        # Contrainte 5: Capacités des stations
        if capacities is not None and len(capacities) == n:
            for j in range(n):
                model.addConstr(
                    gp.quicksum(demands[i] * y[i, j] for i in range(n)) <= capacities[j] * x[j],
                    name=f"Capacite_station_{j}"
                )
        
        # Contrainte 6: Distance maximale
        if max_distance is not None and max_distance > 0:
            for i in range(n):
                for j in range(n):
                    if distances[i][j] > max_distance:
                        model.addConstr(
                            y[i, j] == 0,
                            name=f"Distance_max_{i}_{j}"
                        )
        
        # Paramètres du solveur
        model.setParam('OutputFlag', 0)
        model.setParam('TimeLimit', 300)
        
        # Résolution
        model.optimize()
        
        # Vérification et récupération de la solution
        if model.status == GRB.OPTIMAL or (model.status == GRB.TIME_LIMIT and model.SolCount > 0):
            stations_ouvertes = [j for j in range(n) if x[j].X > 0.5]
            
            assignations = {}
            for i in range(n):
                for j in range(n):
                    if y[i, j].X > 0.5:
                        assignations[i] = j
                        break
            
            cout_total = sum(station_costs[j] for j in stations_ouvertes)

            return {
                'objective_value': model.objVal,
                'stations_ouvertes': stations_ouvertes,
                'assignations': assignations,
                'cout_total': cout_total, # NOUVEAU
                'budget_initial': budget,  # NOUVEAU
                'model_status': 'Optimal' if model.status == GRB.OPTIMAL else 'TimeLimit'
            }
        
        else:
            return None
            
    except gp.GurobiError as e:
        raise Exception(f"Erreur Gurobi: {e}")
    except Exception as e:
        raise Exception(f"Erreur inattendue: {e}")

def solve_p_median(distances, demands, p, capacities=None, max_distance=None):
    """
    Résout le problème p-median pour la localisation de stations de recharge.
    
    Args:
        distances (list): Matrice des distances entre les zones (n x n)
        demands (list): Liste des demandes pour chaque zone
        p (int): Nombre de stations à ouvrir
        capacities (list, optional): Capacités maximales par station
        max_distance (float, optional): Distance maximale autorisée
    
    Returns:
        dict: Solution contenant stations ouvertes, assignations et valeur objective
    """
    try:
        n = len(distances)  # Nombre de zones
        
        # Vérification des données d'entrée
        if n == 0:
            raise ValueError("Aucune donnée fournie")
        
        if p <= 0 or p > n:
            raise ValueError(f"Le nombre de stations p doit être entre 1 et {n}")
        
        # Création du modèle
        model = gp.Model("p_median_stations_recharge")
        
        # Variables de décision
        # x_j = 1 si on ouvre une station au site j
        x = model.addVars(n, vtype=GRB.BINARY, name="x")
        
        # y_ij = 1 si la zone i est assignée à la station j
        y = model.addVars(n, n, vtype=GRB.BINARY, name="y")
        
        # Fonction objectif: Minimiser la distance totale
        objective = gp.quicksum(
            demands[i] * distances[i][j] * y[i, j]
            for i in range(n)
            for j in range(n)
        )
        model.setObjective(objective, GRB.MINIMIZE)
        
        # Contrainte 1: Chaque zone doit être assignée à exactement une station
        for i in range(n):
            model.addConstr(
                gp.quicksum(y[i, j] for j in range(n)) == 1,
                name=f"Assignation_zone_{i}"
            )
        
        # Contrainte 2: On ne peut assigner une zone qu'à une station ouverte
        for i in range(n):
            for j in range(n):
                model.addConstr(
                    y[i, j] <= x[j],
                    name=f"Station_ouverte_{i}_{j}"
                )
        
        # Contrainte 3: Exactement p stations doivent être ouvertes
        model.addConstr(
            gp.quicksum(x[j] for j in range(n)) == p,
            name="Nombre_stations"
        )
        
        # Contrainte 4: Capacités des stations (complexité 1)
        if capacities is not None:
            for j in range(n):
                model.addConstr(
                    gp.quicksum(demands[i] * y[i, j] for i in range(n)) <= capacities[j] * x[j],
                    name=f"Capacite_station_{j}"
                )
        
        # Contrainte 5: Distance maximale (complexité 2)
        if max_distance is not None:
            for i in range(n):
                for j in range(n):
                    if distances[i][j] > max_distance:
                        model.addConstr(
                            y[i, j] == 0,
                            name=f"Distance_max_{i}_{j}"
                        )
        
        # Paramètres du solveur
        model.setParam('OutputFlag', 0)  # Désactive la sortie console de Gurobi
        model.setParam('TimeLimit', 300)  # Limite de temps de 5 minutes
        
        # Résolution
        model.optimize()
        
        # Vérification de la solution
        if model.status == GRB.OPTIMAL:
            # Récupération des résultats
            stations_ouvertes = [j for j in range(n) if x[j].X > 0.5]
            
            assignations = {}
            for i in range(n):
                for j in range(n):
                    if y[i, j].X > 0.5:
                        assignations[i] = j
                        break
            
            return {
                'objective_value': model.objVal,
                'stations_ouvertes': stations_ouvertes,
                'assignations': assignations,
                'model_status': 'Optimal'
            }
        
        elif model.status == GRB.TIME_LIMIT and model.SolCount > 0:
            # Solution réalisable trouvée mais pas optimale (délai dépassé)
            stations_ouvertes = [j for j in range(n) if x[j].X > 0.5]
            
            assignations = {}
            for i in range(n):
                for j in range(n):
                    if y[i, j].X > 0.5:
                        assignations[i] = j
                        break
            
            return {
                'objective_value': model.objVal,
                'stations_ouvertes': stations_ouvertes,
                'assignations': assignations,
                'model_status': 'TimeLimit'
            }
        
        else:
            print(f"Statut du modèle: {model.status}")
            return None
            
    except gp.GurobiError as e:
        print(f"Erreur Gurobi: {e}")
        return None
    except Exception as e:
        print(f"Erreur inattendue: {e}")
        return None