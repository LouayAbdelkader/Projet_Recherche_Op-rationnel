# backend_complete.py
import pandas as pd
import gurobipy as gp
from gurobipy import GRB
import io
import sys
import traceback

def solve_airline_model(params, file_paths):
    """
    Fonction qui exécute le modèle Gurobi pour l'affectation des avions et surclassement.
    Retourne un dictionnaire structuré avec :
    - KPIs détaillés
    - Détails des routes et affectations
    - Logs Gurobi
    """

    try:
        # -----------------------------
        # 1. Chargement des données
        # -----------------------------
        df_avions = pd.read_csv(file_paths['avions'])
        df_vols = pd.read_csv(file_paths['vols'])

        # Listes d'indices
        A = df_avions['AvionID'].tolist()
        V = df_vols['VolID'].tolist()

        # Paramètres par avion
        K_eco = df_avions.set_index('AvionID')['K_eco'].to_dict()
        K_bus = df_avions.set_index('AvionID')['K_bus'].to_dict()
        C_op = df_avions.set_index('AvionID')['C_op'].to_dict()
        H_max = df_avions.set_index('AvionID')['H_max'].to_dict()
        E_CO2 = df_avions.set_index('AvionID')['E_CO2'].to_dict()
        TypeAvion = df_avions.set_index('AvionID')['Type'].to_dict()

        # Paramètres par vol
        P_eco = df_vols.set_index('VolID')['P_eco'].to_dict()
        P_bus = df_vols.set_index('VolID')['P_bus'].to_dict()
        Duree_Vol = df_vols.set_index('VolID')['Duree'].to_dict()
        Route = df_vols.set_index('VolID')['Route'].to_dict()

        # -----------------------------
        # 2. Matrices selon le modèle
        # -----------------------------
        t, c, s, compat = {}, {}, {}, {}
        for i in A:
            for j in V:
                t[i,j] = Duree_Vol[j]
                c[i,j] = 200 + (K_bus[i]*10)  # coût fixe

                # Satisfaction prédéfinie par avion
                if i == 1: base_sat = 70
                elif i == 2: base_sat = 75
                elif i == 3: base_sat = 78
                elif i == 4: base_sat = 82
                elif i == 5: base_sat = 88
                elif i == 6: base_sat = 92
                else: base_sat = 80

                # Variation selon vol pour plus de réalisme
                vol_variation = (j % 5) * 2  # 0 à 8 points
                s[i,j] = min(100, max(60, base_sat + vol_variation))

                compat[i,j] = 1  # Compatible par défaut (à ajuster si besoin)

        # Conflits temporels fictifs (exemple)
        C_conflit = [(1,2), (3,4)]

        # -----------------------------
        # 3. Paramètres depuis l'UI
        # -----------------------------
        C_up = params.get('cost_upgrade', 50)
        Q_CO2_max = params.get('max_co2', 5000)
        w1 = params.get('w1', 0.5)
        w2 = params.get('w2', 0.3)
        w3 = params.get('w3', 0.2)

        # -----------------------------
        # 4. Capture logs Gurobi
        # -----------------------------
        old_stdout = sys.stdout
        sys.stdout = log_capture = io.StringIO()

        # -----------------------------
        # 5. Définition du modèle
        # -----------------------------
        model = gp.Model("Airline_Optimization")
        model.setParam('OutputFlag', 1)

        # Variables
        x = model.addVars(A, V, vtype=GRB.BINARY, name="x")
        u = model.addVars(V, vtype=GRB.INTEGER, lb=0, name="u")

        # -----------------------------
        # 6. Fonction Objectif
        # -----------------------------
        cost_part = gp.quicksum((c[i,j] + C_op[i]*t[i,j]) * x[i,j] for i in A for j in V) + \
                    gp.quicksum(C_up * u[j] for j in V)
        satisfaction_part = gp.quicksum(s[i,j]*x[i,j] for i in A for j in V)
        time_part = gp.quicksum(t[i,j]*x[i,j] for i in A for j in V)

        model.setObjective(w1*cost_part - w2*satisfaction_part + w3*time_part, GRB.MINIMIZE)

        # -----------------------------
        # 7. Contraintes
        # -----------------------------

        # 7.1 Unicité des vols
        for j in V:
            model.addConstr(gp.quicksum(x[i,j] for i in A) == 1, name=f"unicite_{j}")

        # 7.2 Capacité Business
        for j in V:
            model.addConstr(P_bus[j] + u[j] <= gp.quicksum(K_bus[i]*x[i,j] for i in A), name=f"cap_bus_{j}")

        # 7.3 Capacité Éco
        for j in V:
            model.addConstr(P_eco[j] - u[j] <= gp.quicksum(K_eco[i]*x[i,j] for i in A), name=f"cap_eco_{j}")

        # 7.4 Limitation du surclassement
        for j in V:
            model.addConstr(u[j] <= P_eco[j], name=f"lim_up_{j}")

        # 7.5 Conflits temporels
        for i in A:
            for (j,k) in C_conflit:
                if j in V and k in V:
                    model.addConstr(x[i,j] + x[i,k] <= 1, name=f"conflit_{i}_{j}_{k}")

        # 7.6 Heures max par avion
        for i in A:
            model.addConstr(gp.quicksum(t[i,j]*x[i,j] for j in V) <= H_max[i], name=f"hmax_{i}")

        # 7.7 Quota CO2
        model.addConstr(gp.quicksum(t[i,j]*E_CO2[i]*x[i,j] for i in A for j in V) <= Q_CO2_max, name="co2_max")

        # -----------------------------
        # 8. Optimisation
        # -----------------------------
        model.optimize()

        # Restaurer stdout et récupérer logs
        sys.stdout = old_stdout
        gurobi_logs = log_capture.getvalue().split("\n")

        # -----------------------------
        # 9. Récupération des résultats
        # -----------------------------
        if model.status == GRB.OPTIMAL:
            res_routes = []
            total_upgrades = 0
            total_satisfaction = 0
            total_time = 0
            total_cost = 0
            total_co2 = 0
            plane_usage = {}
            hours_by_plane_type = {}
            total_hours = 0

            for j in V:
                assigned_plane = -1
                satisfaction_vol = 0
                time_vol = 0
                cost_vol = 0
                co2_vol = 0

                for i in A:
                    if x[i,j].X > 0.5:
                        assigned_plane = i
                        plane_type = TypeAvion[i]
                        plane_usage[plane_type] = plane_usage.get(plane_type,0)+1
                        vol_duree = t[i,j]
                        satisfaction_vol = s[i,j]
                        time_vol = t[i,j]
                        cost_vol = c[i,j] + C_op[i]*t[i,j]
                        co2_vol = E_CO2[i]*t[i,j]

                        hours_by_plane_type[plane_type] = hours_by_plane_type.get(plane_type,0)+time_vol
                        total_satisfaction += satisfaction_vol
                        total_time += time_vol
                        total_cost += cost_vol
                        total_co2 += co2_vol
                        total_hours += vol_duree
                        break

                nb_up = int(u[j].X)
                total_upgrades += nb_up

                res_routes.append({
                    "vol_id": j,
                    "route": Route[j],
                    "avion": TypeAvion[assigned_plane],
                    "avion_id": assigned_plane,
                    "duree": Duree_Vol[j],
                    "demande_eco": P_eco[j],
                    "demande_bus": P_bus[j],
                    "surclassement": nb_up,
                    "satisfaction": satisfaction_vol,
                    "cout_vol": cost_vol,
                    "co2_vol": co2_vol
                })

            total_cost += total_upgrades * C_up
            satisfaction_moyenne = total_satisfaction / len(V) if len(V) > 0 else 0
            objective_value = model.objVal

            return {
                "status": "optimal",
                "kpis": {
                    "cout": total_cost,
                    "objective_value": objective_value,
                    "upgrades": total_upgrades,
                    "co2": total_co2,
                    "vols_ok": len(V),
                    "satisfaction": total_satisfaction,
                    "temps_total": total_time,
                    "cout_moyen": total_cost/len(V) if len(V)>0 else 0,
                    "satisfaction_moyenne": satisfaction_moyenne
                },
                "routes": res_routes,
                "usage": plane_usage,
                "hours_by_plane": hours_by_plane_type,
                "logs": gurobi_logs
            }
        else:
            return {
                "status": "infeasible",
                "message": "Aucune solution trouvée (modèle infaisable)",
                "logs": gurobi_logs
            }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Erreur: {str(e)}",
            "logs": [f"Erreur: {str(e)}", traceback.format_exc()]
        }

# -----------------------------
# Fin du code backend_complete.py
# -----------------------------
