\ Model Logistique_Humanitaire
\ LP format - for model browsing. Use MPS format to capture full model detail.
Minimize
  100 n_W_Main_Zone_A_M_Std + 2 x_W_Main_Zone_A_M_Std_P_Eau
   + 2 x_W_Main_Zone_A_M_Std_P_Vaccin + 2 x_W_Main_Zone_A_M_Std_P_Riz
   + 150 n_W_Main_Zone_A_M_Frigo + 5047 x_W_Main_Zone_A_M_Frigo_P_Eau
   + 3 x_W_Main_Zone_A_M_Frigo_P_Vaccin
   + 5047 x_W_Main_Zone_A_M_Frigo_P_Riz + 200 n_W_Main_Zone_B_M_Std
   + 4 x_W_Main_Zone_B_M_Std_P_Eau + 4 x_W_Main_Zone_B_M_Std_P_Vaccin
   + 4 x_W_Main_Zone_B_M_Std_P_Riz + 300 n_W_Main_Zone_B_M_Frigo
   + 5050 x_W_Main_Zone_B_M_Frigo_P_Eau
   + 6 x_W_Main_Zone_B_M_Frigo_P_Vaccin
   + 5050 x_W_Main_Zone_B_M_Frigo_P_Riz + 500 n_W_Main_Zone_C_M_Std
   + 10 x_W_Main_Zone_C_M_Std_P_Eau + 10 x_W_Main_Zone_C_M_Std_P_Vaccin
   + 10 x_W_Main_Zone_C_M_Std_P_Riz + 750 n_W_Main_Zone_C_M_Frigo
   + 5059 x_W_Main_Zone_C_M_Frigo_P_Eau
   + 15 x_W_Main_Zone_C_M_Frigo_P_Vaccin
   + 5059 x_W_Main_Zone_C_M_Frigo_P_Riz + 120 n_W_Pharma_Zone_A_M_Std
   + 2 x_W_Pharma_Zone_A_M_Std_P_Eau + 2 x_W_Pharma_Zone_A_M_Std_P_Vaccin
   + 2 x_W_Pharma_Zone_A_M_Std_P_Riz + 180 n_W_Pharma_Zone_A_M_Frigo
   + 5047 x_W_Pharma_Zone_A_M_Frigo_P_Eau
   + 3 x_W_Pharma_Zone_A_M_Frigo_P_Vaccin
   + 5047 x_W_Pharma_Zone_A_M_Frigo_P_Riz + 220 n_W_Pharma_Zone_B_M_Std
   + 4 x_W_Pharma_Zone_B_M_Std_P_Eau + 4 x_W_Pharma_Zone_B_M_Std_P_Vaccin
   + 4 x_W_Pharma_Zone_B_M_Std_P_Riz + 330 n_W_Pharma_Zone_B_M_Frigo
   + 5050 x_W_Pharma_Zone_B_M_Frigo_P_Eau
   + 6 x_W_Pharma_Zone_B_M_Frigo_P_Vaccin
   + 5050 x_W_Pharma_Zone_B_M_Frigo_P_Riz + 450 n_W_Pharma_Zone_C_M_Std
   + 10 x_W_Pharma_Zone_C_M_Std_P_Eau + 10 x_W_Pharma_Zone_C_M_Std_P_Vaccin
   + 10 x_W_Pharma_Zone_C_M_Std_P_Riz + 650 n_W_Pharma_Zone_C_M_Frigo
   + 5058 x_W_Pharma_Zone_C_M_Frigo_P_Eau
   + 14 x_W_Pharma_Zone_C_M_Frigo_P_Vaccin
   + 5058 x_W_Pharma_Zone_C_M_Frigo_P_Riz + 100 manque_Zone_A_P_Eau
   + 100 manque_Zone_A_P_Vaccin + 100 manque_Zone_A_P_Riz
   + 100 manque_Zone_B_P_Eau + 100 manque_Zone_B_P_Vaccin
   + 100 manque_Zone_B_P_Riz + 100 manque_Zone_C_P_Eau
   + 100 manque_Zone_C_P_Vaccin + 100 manque_Zone_C_P_Riz
Subject To
 Demande_Zone_A_P_Eau: 2 x_W_Pharma_Zone_A_M_Std_P_Eau
   + 2 x_W_Pharma_Zone_A_M_Frigo_P_Eau + manque_Zone_A_P_Eau = 200
 Demande_Zone_A_P_Vaccin: 2 x_W_Pharma_Zone_A_M_Std_P_Vaccin
   + 2 x_W_Pharma_Zone_A_M_Frigo_P_Vaccin + manque_Zone_A_P_Vaccin = 50
 Demande_Zone_B_P_Eau: 2 x_W_Pharma_Zone_B_M_Std_P_Eau
   + 2 x_W_Pharma_Zone_B_M_Frigo_P_Eau + manque_Zone_B_P_Eau = 300
 Demande_Zone_C_P_Eau: 2 x_W_Pharma_Zone_C_M_Std_P_Eau
   + 2 x_W_Pharma_Zone_C_M_Frigo_P_Eau + manque_Zone_C_P_Eau = 100
 Demande_Zone_C_P_Vaccin: 2 x_W_Pharma_Zone_C_M_Std_P_Vaccin
   + 2 x_W_Pharma_Zone_C_M_Frigo_P_Vaccin + manque_Zone_C_P_Vaccin = 100
 Stock_W_Main_P_Eau: 3 x_W_Main_Zone_C_M_Std_P_Eau
   + 3 x_W_Main_Zone_C_M_Frigo_P_Eau <= 1000
 Stock_W_Main_P_Vaccin: 3 x_W_Main_Zone_C_M_Std_P_Vaccin
   + 3 x_W_Main_Zone_C_M_Frigo_P_Vaccin <= 0
 Stock_W_Main_P_Riz: 3 x_W_Main_Zone_C_M_Std_P_Riz
   + 3 x_W_Main_Zone_C_M_Frigo_P_Riz <= 500
 Stock_W_Pharma_P_Eau: 3 x_W_Pharma_Zone_C_M_Std_P_Eau
   + 3 x_W_Pharma_Zone_C_M_Frigo_P_Eau <= 200
 Stock_W_Pharma_P_Vaccin: 3 x_W_Pharma_Zone_C_M_Std_P_Vaccin
   + 3 x_W_Pharma_Zone_C_M_Frigo_P_Vaccin <= 300
 Stock_W_Pharma_P_Riz: 3 x_W_Pharma_Zone_C_M_Std_P_Riz
   + 3 x_W_Pharma_Zone_C_M_Frigo_P_Riz <= 0
 Capacite_W_Main_Zone_A_M_Std: - 40 n_W_Main_Zone_A_M_Std
   + 0.02 x_W_Main_Zone_A_M_Std_P_Eau
   + 0.005 x_W_Main_Zone_A_M_Std_P_Vaccin
   + 0.03 x_W_Main_Zone_A_M_Std_P_Riz <= 0
 Capacite_W_Main_Zone_A_M_Frigo: - 25 n_W_Main_Zone_A_M_Frigo
   + 0.02 x_W_Main_Zone_A_M_Frigo_P_Eau
   + 0.005 x_W_Main_Zone_A_M_Frigo_P_Vaccin
   + 0.03 x_W_Main_Zone_A_M_Frigo_P_Riz <= 0
 Capacite_W_Main_Zone_B_M_Std: - 40 n_W_Main_Zone_B_M_Std
   + 0.02 x_W_Main_Zone_B_M_Std_P_Eau
   + 0.005 x_W_Main_Zone_B_M_Std_P_Vaccin
   + 0.03 x_W_Main_Zone_B_M_Std_P_Riz <= 0
 Capacite_W_Main_Zone_B_M_Frigo: - 25 n_W_Main_Zone_B_M_Frigo
   + 0.02 x_W_Main_Zone_B_M_Frigo_P_Eau
   + 0.005 x_W_Main_Zone_B_M_Frigo_P_Vaccin
   + 0.03 x_W_Main_Zone_B_M_Frigo_P_Riz <= 0
 Capacite_W_Main_Zone_C_M_Std: - 40 n_W_Main_Zone_C_M_Std
   + 0.02 x_W_Main_Zone_C_M_Std_P_Eau
   + 0.005 x_W_Main_Zone_C_M_Std_P_Vaccin
   + 0.03 x_W_Main_Zone_C_M_Std_P_Riz <= 0
 Capacite_W_Main_Zone_C_M_Frigo: - 25 n_W_Main_Zone_C_M_Frigo
   + 0.02 x_W_Main_Zone_C_M_Frigo_P_Eau
   + 0.005 x_W_Main_Zone_C_M_Frigo_P_Vaccin
   + 0.03 x_W_Main_Zone_C_M_Frigo_P_Riz <= 0
 Capacite_W_Pharma_Zone_A_M_Std: - 40 n_W_Pharma_Zone_A_M_Std
   + 0.02 x_W_Pharma_Zone_A_M_Std_P_Eau
   + 0.005 x_W_Pharma_Zone_A_M_Std_P_Vaccin
   + 0.03 x_W_Pharma_Zone_A_M_Std_P_Riz <= 0
 Capacite_W_Pharma_Zone_A_M_Frigo: - 25 n_W_Pharma_Zone_A_M_Frigo
   + 0.02 x_W_Pharma_Zone_A_M_Frigo_P_Eau
   + 0.005 x_W_Pharma_Zone_A_M_Frigo_P_Vaccin
   + 0.03 x_W_Pharma_Zone_A_M_Frigo_P_Riz <= 0
 Capacite_W_Pharma_Zone_B_M_Std: - 40 n_W_Pharma_Zone_B_M_Std
   + 0.02 x_W_Pharma_Zone_B_M_Std_P_Eau
   + 0.005 x_W_Pharma_Zone_B_M_Std_P_Vaccin
   + 0.03 x_W_Pharma_Zone_B_M_Std_P_Riz <= 0
 Capacite_W_Pharma_Zone_B_M_Frigo: - 25 n_W_Pharma_Zone_B_M_Frigo
   + 0.02 x_W_Pharma_Zone_B_M_Frigo_P_Eau
   + 0.005 x_W_Pharma_Zone_B_M_Frigo_P_Vaccin
   + 0.03 x_W_Pharma_Zone_B_M_Frigo_P_Riz <= 0
 Capacite_W_Pharma_Zone_C_M_Std: - 40 n_W_Pharma_Zone_C_M_Std
   + 0.02 x_W_Pharma_Zone_C_M_Std_P_Eau
   + 0.005 x_W_Pharma_Zone_C_M_Std_P_Vaccin
   + 0.03 x_W_Pharma_Zone_C_M_Std_P_Riz <= 0
 Capacite_W_Pharma_Zone_C_M_Frigo: - 25 n_W_Pharma_Zone_C_M_Frigo
   + 0.02 x_W_Pharma_Zone_C_M_Frigo_P_Eau
   + 0.005 x_W_Pharma_Zone_C_M_Frigo_P_Vaccin
   + 0.03 x_W_Pharma_Zone_C_M_Frigo_P_Riz <= 0
 Flotte_M_Std: n_W_Main_Zone_A_M_Std + n_W_Main_Zone_B_M_Std
   + n_W_Main_Zone_C_M_Std + n_W_Pharma_Zone_A_M_Std
   + n_W_Pharma_Zone_B_M_Std + n_W_Pharma_Zone_C_M_Std <= 0
 Flotte_M_Frigo: n_W_Main_Zone_A_M_Frigo + n_W_Main_Zone_B_M_Frigo
   + n_W_Main_Zone_C_M_Frigo + n_W_Pharma_Zone_A_M_Frigo
   + n_W_Pharma_Zone_B_M_Frigo + n_W_Pharma_Zone_C_M_Frigo <= 12
 Secu_Veh_W_Main_Zone_A: x_W_Main_Zone_A_M_Std_P_Vaccin = 0
 Secu_Depot_W_Main: x_W_Main_Zone_A_M_Std_P_Vaccin = 0
 Secu_Depot_W_Main: x_W_Main_Zone_A_M_Frigo_P_Vaccin = 0
 Secu_Veh_W_Main_Zone_B: x_W_Main_Zone_B_M_Std_P_Vaccin = 0
 Secu_Depot_W_Main: x_W_Main_Zone_B_M_Std_P_Vaccin = 0
 Secu_Depot_W_Main: x_W_Main_Zone_B_M_Frigo_P_Vaccin = 0
 Secu_Veh_W_Main_Zone_C: x_W_Main_Zone_C_M_Std_P_Vaccin = 0
 Secu_Depot_W_Main: x_W_Main_Zone_C_M_Std_P_Vaccin = 0
 Secu_Depot_W_Main: x_W_Main_Zone_C_M_Frigo_P_Vaccin = 0
 Secu_Veh_W_Pharma_Zone_A: x_W_Pharma_Zone_A_M_Std_P_Vaccin = 0
 Secu_Veh_W_Pharma_Zone_B: x_W_Pharma_Zone_B_M_Std_P_Vaccin = 0
 Secu_Veh_W_Pharma_Zone_C: x_W_Pharma_Zone_C_M_Std_P_Vaccin = 0
Bounds
Generals
 n_W_Main_Zone_A_M_Std n_W_Main_Zone_A_M_Frigo n_W_Main_Zone_B_M_Std
 n_W_Main_Zone_B_M_Frigo n_W_Main_Zone_C_M_Std n_W_Main_Zone_C_M_Frigo
 n_W_Pharma_Zone_A_M_Std n_W_Pharma_Zone_A_M_Frigo n_W_Pharma_Zone_B_M_Std
 n_W_Pharma_Zone_B_M_Frigo n_W_Pharma_Zone_C_M_Std
 n_W_Pharma_Zone_C_M_Frigo
End
