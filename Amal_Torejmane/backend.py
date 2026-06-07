# backend.py
import os
import pandas as pd
import gurobipy as gp
from gurobipy import GRB

# --- GESTION DES CHEMINS ---
# Récupère le dossier où se trouve ce fichier (backend.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def get_csv_path(filename):
    """Retourne le chemin absolu vers un fichier CSV dans ce dossier."""
    return os.path.join(BASE_DIR, filename)

def get_default_paths():
    """Retourne un dictionnaire avec les chemins complets des fichiers."""
    return {
        'produits': get_csv_path("produits.csv"),
        'vehicules': get_csv_path("vehicules_types.csv"),
        'entrepots': get_csv_path("entrepots.csv"),
        'demandes': get_csv_path("demandes.csv"),
        'transport': get_csv_path("transport_couts.csv")
    }

# --- GÉNÉRATION DES DONNÉES ---
def generer_csv_demo():
    """Génère les fichiers CSV par défaut s'ils n'existent pas dans le dossier du module."""
    
    # On vérifie si le premier fichier existe via son chemin absolu
    if os.path.exists(get_csv_path("produits.csv")): return
    
    # Produits
    pd.DataFrame({
        "ID_Produit": ["Eau", "Vaccins", "Riz", "Lait"],
        "Volume_m3": [0.02, 0.005, 0.03, 0.1],
        "Besoin_Froid": [0, 1, 0, 0]
    }).to_csv(get_csv_path("produits.csv"), index=False)
    
    # Véhicules
    pd.DataFrame({
        "ID_Mode": ["Camion_Std", "Camion_Frigo", "Avion"],
        "Capacite_max": [5, 8, 5],
        "Est_Refrigere": [0, 1, 0]
    }).to_csv(get_csv_path("vehicules_types.csv"), index=False)
    
    # Entrepôts
    pd.DataFrame({
        "ID_Entrepot": ["Depot_Central", "Depot_Central", "Depot_Pharma", "Depot_Pharma"],
        "ID_Produit": ["Eau", "Riz", "Vaccins", "Eau"],
        "Stock": [1000, 500, 300, 100],
        "A_Chambre_Froide": [0, 0, 1, 1] 
    }).to_csv(get_csv_path("entrepots.csv"), index=False)
    
    # Demandes
    pd.DataFrame({
        "ID_Zone": ["Zone_A", "Zone_A", "Zone_B", "Zone_B", "Zone_C"],
        "ID_Produit": ["Eau", "Vaccins", "Eau", "Vaccins", "Lait"],
        "Quantite": [200, 50, 300, 100, 20],
        "Temps_Max_h": [24, 24, 48, 48, 12],
        "Penalite_Unit_Manque": [1000, 10000, 1000, 10000, 5000]
    }).to_csv(get_csv_path("demandes.csv"), index=False)
    
    # Transport
    data = [
        ["Depot_Central", "Zone_A", "Camion_Std", 100, 2, 4],
        ["Depot_Central", "Zone_B", "Camion_Std", 200, 4, 8],
        ["Depot_Central", "Zone_C", "Camion_Std", 500, 10, 15],
        ["Depot_Central", "Zone_C", "Avion", 1000, 20, 2],
        ["Depot_Pharma", "Zone_A", "Camion_Frigo", 150, 3, 4],
        ["Depot_Pharma", "Zone_B", "Camion_Frigo", 300, 6, 8],
        ["Depot_Pharma", "Zone_C", "Camion_Frigo", 750, 15, 15],
        ["Depot_Pharma", "Zone_C", "Avion", 1200, 25, 2]
    ]
    pd.DataFrame(data, columns=["Origine", "Destination", "ID_Mode", "Cout_Fixe", "Cout_Var", "Temps_h"]).to_csv(get_csv_path("transport_couts.csv"), index=False)

# --- LOGIQUE D'OPTIMISATION ---
def solve_model(user_params, file_paths):
    """Logique d'optimisation Gurobi avec retour structuré."""
    try:
        # Vérification des fichiers avec les chemins fournis
        for name, path in file_paths.items():
            if not os.path.exists(path): 
                return {"status": "error", "message": f"Fichier {name} introuvable au chemin : {path}"}

        df_prod = pd.read_csv(file_paths['produits']).set_index("ID_Produit")
        df_veh = pd.read_csv(file_paths['vehicules']).set_index("ID_Mode")
        df_stock = pd.read_csv(file_paths['entrepots'])
        df_dem = pd.read_csv(file_paths['demandes'])
        df_trans = pd.read_csv(file_paths['transport'])

        K, M = df_prod.index.tolist(), df_veh.index.tolist()
        I, J = df_stock["ID_Entrepot"].unique().tolist(), df_dem["ID_Zone"].unique().tolist()
        
        K_froid = df_prod[df_prod["Besoin_Froid"] == 1].index.tolist()
        M_froid = df_veh[df_veh["Est_Refrigere"] == 1].index.tolist()
        I_froid = df_stock[df_stock["A_Chambre_Froide"] == 1]["ID_Entrepot"].unique().tolist()

        v_k, V_m = df_prod["Volume_m3"].to_dict(), df_veh["Capacite_max"].to_dict()
        stock_dict = df_stock.set_index(["ID_Entrepot", "ID_Produit"])["Stock"].to_dict()
        dem_dict = df_dem.set_index(["ID_Zone", "ID_Produit"])["Quantite"].to_dict()
        tmax_dict = df_dem.set_index(["ID_Zone", "ID_Produit"])["Temps_Max_h"].to_dict()
        penalite_manque = df_dem.set_index(["ID_Zone", "ID_Produit"])["Penalite_Unit_Manque"].to_dict()

        m = gp.Model("Logistics")
        m.setParam('OutputFlag', 1)

        x, n, d_manque = {}, {}, {}
        Arcs = []
        for _, row in df_trans.iterrows():
            i, j, mode = row["Origine"], row["Destination"], row["ID_Mode"]
            Arcs.append((i, j, mode))
            n[i, j, mode] = m.addVar(vtype=GRB.INTEGER)
            for k in K: x[i, j, mode, k] = m.addVar(vtype=GRB.CONTINUOUS)

        for j in J:
            for k in K: d_manque[j, k] = m.addVar(vtype=GRB.CONTINUOUS)

        # Calcul des composantes du coût
        cout_fixe, cout_var, cout_retard, cout_mesusage, cout_manque = 0, 0, 0, 0, 0
        
        for _, row in df_trans.iterrows():
            i, j, mode = row["Origine"], row["Destination"], row["ID_Mode"]
            cout_fixe += row["Cout_Fixe"] * n[i, j, mode]
            for k in K:
                cout_var += row["Cout_Var"] * x[i, j, mode, k]
                if row["Temps_h"] > tmax_dict.get((j, k), 9999):
                    cout_retard += user_params['penalites']['Retard'] * x[i, j, mode, k]
                if mode in M_froid and k not in K_froid:
                    cout_mesusage += user_params['penalites']['Mesusage'] * x[i, j, mode, k]
        
        for j in J:
            for k in K: 
                cout_manque += penalite_manque.get((j, k), 10000) * d_manque[j, k]

        obj = cout_fixe + cout_var + cout_retard + cout_mesusage + cout_manque
        m.setObjective(obj, GRB.MINIMIZE)

        # Contraintes
        for j in J:
            for k in K:
                if dem_dict.get((j, k), 0) > 0:
                    m.addConstr(gp.quicksum(x[i, j, mode, k] for (i, jl, mode) in Arcs if jl == j) + d_manque[j, k] == dem_dict[(j, k)])

        for i in I:
            for k in K:
                m.addConstr(gp.quicksum(x[i, j, mode, k] for (il, j, mode) in Arcs if il == i) <= stock_dict.get((i, k), 0))

        for (i, j, mode) in Arcs:
            m.addConstr(gp.quicksum(v_k[k] * x[i, j, mode, k] for k in K) <= V_m[mode] * n[i, j, mode])

        for mode in M:
            m.addConstr(gp.quicksum(n[i, j, ml] for (i, j, ml) in Arcs if ml == mode) <= user_params['flotte'].get(mode, 0))

        for (i, j, mode) in Arcs:
            for k in K:
                if k in K_froid and mode not in M_froid: m.addConstr(x[i, j, mode, k] == 0)
                if k in K_froid and i not in I_froid: m.addConstr(x[i, j, mode, k] == 0)

        m.optimize()

        if m.status == GRB.OPTIMAL:
            # Construction du résultat structuré
            result = {
                "status": "optimal",
                "cout_total": m.objVal,
                "routes": [],
                "manques": [],
                "metriques": {},
                "utilisation_vehicules": {}
            }
            
            # Routes et livraisons
            total_livraisons = 0
            for (i, j, mode) in Arcs:
                if n[i, j, mode].X > 0.5:
                    route = {
                        "origine": i,
                        "destination": j,
                        "mode": mode,
                        "nb_vehicules": int(n[i, j, mode].X),
                        "produits": []
                    }
                    for k in K:
                        if x[i, j, mode, k].X > 0.01:
                            route["produits"].append({
                                "nom": k,
                                "quantite": round(x[i, j, mode, k].X, 1)
                            })
                            total_livraisons += x[i, j, mode, k].X
                    result["routes"].append(route)
            
            # Manques
            demande_totale = sum(dem_dict.values())
            for j in J:
                for k in K:
                    if d_manque[j, k].X > 0.1:
                        result["manques"].append({
                            "zone": j,
                            "produit": k,
                            "quantite": round(d_manque[j, k].X, 1)
                        })
            
            total_manques = sum(item["quantite"] for item in result["manques"])
            taux_satisfaction = ((demande_totale - total_manques) / demande_totale * 100) if demande_totale > 0 else 100
            
            # Utilisation des véhicules
            for mode in M:
                utilise = sum(int(n[i, j, ml].X) for (i, j, ml) in Arcs if ml == mode)
                disponible = user_params['flotte'].get(mode, 0)
                result["utilisation_vehicules"][mode] = {
                    "utilise": utilise,
                    "disponible": disponible,
                    "taux": (utilise / disponible * 100) if disponible > 0 else 0
                }
            
            # Métriques
            result["metriques"] = {
                "demande_totale": demande_totale,
                "livraisons_totales": total_livraisons,
                "manques_totaux": total_manques,
                "taux_satisfaction": taux_satisfaction,
                "nb_routes": len(result["routes"]),
                "nb_vehicules_total": sum(r["nb_vehicules"] for r in result["routes"])
            }
            
            return result
        else:
            return {"status": "error", "message": "Pas de solution possible."}
            
    except Exception as e:
        return {"status": "error", "message": f"Erreur: {str(e)}"}