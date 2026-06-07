# backend_telecoms_final.py
import pandas as pd
import networkx as nx
from gurobipy import Model, GRB, quicksum

def solve_telecom_model(params, file_paths):
    """
    params: dict { budget, alpha }
    file_paths: dict { antennes, frequences, interferences }
    """

    gurobi_logs = []

    # -------------------
    # Chargement et validation des CSV
    # -------------------
    try:
        antennes_df = pd.read_csv(file_paths['antennes'])
        freqs_df = pd.read_csv(file_paths['frequences'])
        edges_df = pd.read_csv(file_paths['interferences'])
    except Exception as e:
        raise ValueError(f"Erreur chargement CSV: {str(e)}")

    # Colonnes antennes
    V = antennes_df['ID'].astype(str).tolist()
    demand = dict(zip(antennes_df['ID'], antennes_df.get('demande', [1]*len(V))))

    # Colonnes fréquences
    Colors = freqs_df['channel_index'].astype(str).tolist()
    capacities = dict(zip(Colors, freqs_df.get('capacity', [GRB.INFINITY]*len(Colors))))
    costs = dict(zip(Colors, freqs_df.get('cost', [0]*len(Colors))))
    availability = dict(zip(Colors, freqs_df.get('available', [True]*len(Colors))))

    # Graphe d'interférences
    G = nx.Graph()
    G.add_nodes_from(V)
    for _, row in edges_df.iterrows():
        u, v = str(row['ant1']), str(row['ant2'])
        if u in V and v in V:
            G.add_edge(u, v)

    # -------------------
    # Modèle Gurobi
    # -------------------
    m = Model("Telecoms_Frequency_Allocation")
    m.Params.LogToConsole = 0  # désactiver logs bruts

    # Variables
    x = {(v, k): m.addVar(vtype=GRB.BINARY, name=f"x_{v}_{k}") for v in V for k in Colors}
    y = {k: m.addVar(vtype=GRB.BINARY, name=f"y_{k}") for k in Colors}

    # Contraintes
    for v in V:
        m.addConstr(quicksum(x[v, k] for k in Colors) == 1, name=f"one_freq_{v}")
    for u, v_ in G.edges():
        for k in Colors:
            m.addConstr(x[u, k] + x[v_, k] <= 1, name=f"interf_{u}_{v_}_{k}")
    for v in V:
        for k in Colors:
            m.addConstr(x[v, k] <= y[k], name=f"act_{v}_{k}")
    for k in Colors:
        m.addConstr(quicksum(x[v, k] for v in V) >= y[k], name=f"no_ghost_{k}")

    """Colors_sorted = sorted(Colors)
    for i in range(len(Colors_sorted) - 1):
        m.addConstr(y[Colors_sorted[i]] >= y[Colors_sorted[i + 1]], name=f"sym_{i}")
    if V and Colors_sorted:
        m.addConstr(x[V[0], Colors_sorted[0]] == 1, name="anchor")
    """
    for k in Colors:
        if capacities[k] < GRB.INFINITY:
            m.addConstr(quicksum(demand[v] * x[v, k] for v in V) <= capacities[k], name=f"cap_{k}")
    for k in Colors:
        if not availability[k]:
            m.addConstr(y[k] == 0)
            for v in V:
                m.addConstr(x[v, k] == 0)
    budget = params.get('budget', GRB.INFINITY)
    if budget < GRB.INFINITY:
        m.addConstr(quicksum(costs[k] * y[k] for k in Colors) <= budget)

    # Fonction objectif
    alpha = params.get('alpha', 0)
    alpha = float(alpha)
    m.setObjective(quicksum(costs[k] * y[k] for k in Colors) + alpha * quicksum(y[k] for k in Colors), GRB.MINIMIZE)

    # -------------------
    # Optimisation
    # -------------------
    m.optimize()

    # Logs synthétiques
    gurobi_logs.append(f"Status Gurobi: {m.Status}")
    gurobi_logs.append(f"Valeur objectif: {m.ObjVal if m.Status == GRB.OPTIMAL else 'N/A'}")
    gurobi_logs.append(f"Temps calcul: {m.Runtime:.2f}s")
    gurobi_logs.append(f"Nœuds explorés: {m.NodeCount}")

    if m.Status != GRB.OPTIMAL:
        return {
            "status": "non_optimal",
            "gurobi_logs": gurobi_logs
        }

    # -------------------
    # Extraction solution
    # -------------------
    solution = {v: k for v in V for k in Colors if x[v, k].X > 0.5}
    y_sol = {k: int(y[k].X) for k in Colors}

    # Détails antennes
    antennes_details = []
    for v in V:
        for k in Colors:
            if x[v, k].X > 0.5:
                row = antennes_df[antennes_df['ID'] == v]
                x_coord = row['x'].iloc[0] if 'x' in row.columns else 0
                y_coord = row['y'].iloc[0] if 'y' in row.columns else 0
                antennes_details.append({
                    "id": v,
                    "frequence": k,
                    "cout": costs.get(k, 0),
                    "x": float(x_coord),
                    "y": float(y_coord),
                    "demande": int(demand.get(v, 1))
                })
                break

    return {
        "status": "optimal",
        "solution": solution,
        "y": y_sol,
        "cout_total": float(m.ObjVal),
        "antennes_details": antennes_details,
        "gurobi_logs": gurobi_logs,
        "metriques": {
            "nb_antennes": len(V),
            "nb_frequences_utilisees": sum(y_sol.values()),
            "temps_calcul": m.Runtime,
            "noeuds_explores": m.NodeCount,
            "iterations": m.IterCount
        }
    }
