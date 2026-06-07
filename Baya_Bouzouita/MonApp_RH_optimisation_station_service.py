#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys, os
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QFileDialog,
                             QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                             QTableWidget, QTableWidgetItem, QTabWidget, QSpinBox,
                             QGroupBox, QCheckBox, QMessageBox, QLineEdit)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from gurobipy import Model, GRB, quicksum
from matplotlib.backends.backend_pdf import PdfPages

# -----------------------------
# Shifts et jours
# -----------------------------
shifts = ['shift1','shift2','shift3','shift4']
shift_times = {
    "shift1": "00:00-06:00",
    "shift2": "06:00-12:00",
    "shift3": "12:00-18:00",
    "shift4": "18:00-24:00"
}
days = ['Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche']

# -----------------------------
# Lecture fichier Excel
# -----------------------------
def read_input_file(path):
    df = pd.read_excel(path)
    required = ['subset_id','elements','shifts','role']
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Le fichier doit contenir : {', '.join(required)}")
    subsets = {}
    universe = set()
    costs = {}
    for _, row in df.iterrows():
        sid = str(row['subset_id']).strip()
        elems = [x.strip() for x in str(row['elements']).replace(';',',').split(',') if x.strip()!=""]
        shifts_emp = [x.strip() for x in str(row['shifts']).replace(';',',').split(',') if x.strip()!=""]
        role = str(row['role']).strip()
        for day in days:
            for e in elems:
                for sh in shifts_emp:
                    universe.add(f"{e}_{sh}_{day}")
        subsets[sid] = {'elements': elems, 'shifts': shifts_emp, 'role': role}
        costs[sid] = float(row['cost']) if 'cost' in df.columns and not pd.isna(row['cost']) else 1.0
    return sorted(list(universe)), subsets, costs

# -----------------------------
# Solveur PLME réaliste
# -----------------------------
def solve_set_cover_plme(universe, subsets, costs, rh_constraints=None, max_tasks_per_shift=1.0, max_nuits=2):
    U = universe
    S = list(subsets.keys())
    covers = {e: [] for e in U}
    for j in S:
        for day in days:
            for e in subsets[j]['elements']:
                for sh in subsets[j]['shifts']:
                    task = f"{e}_{sh}_{day}"
                    if task in U:
                        covers[task].append(j)

    m = Model("SetCoverPLME")
    m.setParam("OutputFlag", 0)
    x = {j: m.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=1, name=f"x_{j}") for j in S}

    slack_vars = {}
    penalties = {}

    # Couverture des tâches
    for e in U:
        slack = m.addVar(lb=0, name=f"slack_cover_{e}")
        slack_vars[f"slack_cover_{e}"] = slack
        penalties[f"slack_cover_{e}"] = 100
        m.addConstr(quicksum(x[j] for j in covers[e]) + slack >= 1)

    # Disponibilité employés
    if rh_constraints and 'availability' in rh_constraints:
        for j, avail in rh_constraints['availability'].items():
            if j in x and not avail:
                m.addConstr(x[j]==0)

    # Objectif
    obj = quicksum((costs.get(j,1.0))*x[j] for j in S) + quicksum(slack_vars[k]*penalties[k] for k in slack_vars)
    m.setObjective(obj, GRB.MINIMIZE)

    if rh_constraints:
        if 'TimeLimit' in rh_constraints:
            m.setParam('TimeLimit', float(rh_constraints['TimeLimit']))
        if 'MIPGap' in rh_constraints:
            m.setParam('MIPGap', float(rh_constraints['MIPGap']))

    m.optimize()

    if m.status in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
        chosen = [j for j in S if x[j].X > 1e-6]
        xvals = {j: x[j].X for j in S}
        return chosen, xvals, m.ObjVal
    else:
        raise ValueError(f"Aucune solution réalisable trouvée. Statut Gurobi: {m.status}")

# -----------------------------
# Thème sombre
# -----------------------------
def apply_dark_theme(app):
    app.setStyleSheet("""
        QWidget {
            background-color: #121212;
            color: #EDEDED;
            font-size: 13px;
        }

        QPushButton {
            background-color: #2A2A2A;
            border: 1px solid #3C3C3C;
            padding: 6px;
            border-radius: 4px;
        }
        QPushButton:hover {
            background-color: #3A3A3A;
        }

        QLineEdit, QSpinBox, QTableWidget, QPlainTextEdit, QTextEdit, QComboBox {
            background-color: #1E1E1E;
            border: 1px solid #3C3C3C;
            padding: 4px;
            color: #EDEDED;
            selection-background-color: #3D6DCC;
            selection-color: #FFFFFF;
        }

        QTabWidget::pane {
            border: 1px solid #3C3C3C;
        }

        QTabBar::tab {
            background: #2A2A2A;
            padding: 8px;
            margin: 2px;
            color: #EDEDED;
        }
        QTabBar::tab:selected {
            background: #3A3A3A;
            border-bottom: 2px solid #3D6DCC;
        }

        QTableWidget {
            gridline-color: #3C3C3C;
        }

        QHeaderView::section {
            background-color: #2A2A2A;
            color: #EDEDED;
            border: 1px solid #3C3C3C;
            padding: 4px;
        }

        QScrollBar:vertical, QScrollBar:horizontal {
            background: #1E1E1E;
            border: none;
        }

        QScrollBar::handle {
            background: #3A3A3A;
            border-radius: 4px;
        }

        QScrollBar::handle:hover {
            background: #4A4A4A;
        }
    """)
# -----------------------------
# Fenêtre principale
# -----------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Station-service Optimisation RH 24h")
        self.resize(1366,768)
        self.setMinimumSize(1200, 700)
        self.universe = []
        self.subsets = {}
        self.costs = {}
        self.rh_constraints = {}
        self.solution = None
        self.solution_before = None
        self.graph_compact = True  # par défaut, graphe compact
        self.initUI()

    def initUI(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.tab_import = QWidget(); self.tabs.addTab(self.tab_import,"Données / Import"); self._init_tab_import()
        self.tab_rh = QWidget(); self.tabs.addTab(self.tab_rh,"Contraintes RH"); self._init_tab_rh()
        self.tab_res = QWidget(); self.tabs.addTab(self.tab_res,"Résultat / Optimisation"); self._init_tab_result()
        self.tab_cover = QWidget(); self.tabs.addTab(self.tab_cover,"Couverture des employés"); self._init_tab_cover()
        self.tab_vis = QWidget(); self.tabs.addTab(self.tab_vis,"Visualisation"); self._init_tab_vis()

    # -----------------------------
    # Tab Import
    # -----------------------------
    def _init_tab_import(self):
        layout = QVBoxLayout(); self.tab_import.setLayout(layout)
        h = QHBoxLayout()
        btn_load = QPushButton("Charger fichier Excel"); btn_load.clicked.connect(self.load_file)
        h.addWidget(btn_load)
        self.lbl_file = QLabel("Aucun fichier chargé"); h.addWidget(self.lbl_file)
        h.addStretch(); layout.addLayout(h)
        self.table = QTableWidget(); layout.addWidget(self.table)
        help_lbl = QLabel("Format Excel: subset_id | elements | shifts | role | cost(optionnel)")
        layout.addWidget(help_lbl)

    # -----------------------------
    # Tab RH
    # -----------------------------
    def _init_tab_rh(self):
        layout = QVBoxLayout(); self.tab_rh.setLayout(layout)
        self.grp_avail = QGroupBox("Disponibilité des employés")
        layout_avail = QVBoxLayout(); self.grp_avail.setLayout(layout_avail)
        self.chk_avail = {}
        layout.addWidget(self.grp_avail)
        self.grp_shifts = QGroupBox("Contraintes par shift / rôle")
        layout_shifts = QVBoxLayout(); self.grp_shifts.setLayout(layout_shifts)
        layout.addWidget(self.grp_shifts)
        self.spin_table = {}
        for rlabel in ["Min total","Max total","Min caissier","Min pompiste","Min responsable"]:
            h = QHBoxLayout(); layout_shifts.addLayout(h)
            h.addWidget(QLabel(rlabel))
            for s in shifts:
                spin = QSpinBox(); spin.setMaximum(50); h.addWidget(spin)
                self.spin_table[(rlabel,s)] = spin
        bottom = QHBoxLayout()
        bottom.addWidget(QLabel("TimeLimit (s):")); self.le_time = QLineEdit("10"); self.le_time.setMaximumWidth(80); bottom.addWidget(self.le_time)
        bottom.addSpacing(20)
        bottom.addWidget(QLabel("MIPGap:")); self.le_gap = QLineEdit("0.0"); self.le_gap.setMaximumWidth(80); bottom.addWidget(self.le_gap)
        bottom.addStretch()
        layout.addLayout(bottom)

    # -----------------------------
    # Tab Résultat
    # -----------------------------
    def _init_tab_result(self):
        layout = QVBoxLayout(); self.tab_res.setLayout(layout)
        top_bar=QHBoxLayout()
        btn_run=QPushButton("Lancer l'optimisation"); btn_run.clicked.connect(self.run_optimization)
        top_bar.addWidget(btn_run); top_bar.addStretch(); layout.addLayout(top_bar)
        self.lbl_obj=QLabel("Valeur objectif: -"); layout.addWidget(self.lbl_obj)
        self.lbl_open=QLabel("Employés choisis: -"); layout.addWidget(self.lbl_open)
        self.txt_assign=QTableWidget(); self.txt_assign.setColumnCount(2); self.txt_assign.setHorizontalHeaderLabels(["Tâche","Assigné à"])
        layout.addWidget(self.txt_assign)

    # -----------------------------
    # Tab Couverture
    # -----------------------------
    def _init_tab_cover(self):
        layout = QVBoxLayout(); self.tab_cover.setLayout(layout)
        self.fig_cover, self.ax_cover = plt.subplots(figsize=(10,6))
        self.canvas_cover = FigureCanvas(self.fig_cover)
        layout.addWidget(self.canvas_cover)

    # -----------------------------
    # Tab Visualisation
    # -----------------------------
    def _init_tab_vis(self):
        layout = QVBoxLayout(); self.tab_vis.setLayout(layout)
        self.fig_vis, self.ax_vis = plt.subplots(figsize=(12,8))
        self.canvas_vis = FigureCanvas(self.fig_vis)
        layout.addWidget(self.canvas_vis)
        # Boutons pour basculer compact/complet
        btn_toggle = QPushButton("Basculer graphe compact/complet")
        btn_toggle.clicked.connect(self.toggle_graph_mode)
        layout.addWidget(btn_toggle)
        btn_update = QPushButton("Actualiser graphe")
        btn_update.clicked.connect(self.plot_bipartite_graph)
        layout.addWidget(btn_update)

    # -----------------------------
    # Toggle mode graphe
    # -----------------------------
    def toggle_graph_mode(self):
        self.graph_compact = not self.graph_compact
        self.plot_bipartite_graph()

    # -----------------------------
    # Charger fichier
    # -----------------------------
    def load_file(self):
        path,_=QFileDialog.getOpenFileName(self,"Choisir fichier","","Excel Files (*.xlsx)")
        if not path: return
        try:
            self.universe, self.subsets, self.costs = read_input_file(path)
            self.lbl_file.setText(os.path.basename(path))
            self.load_availability_controls()
            self.load_table()
            QMessageBox.information(self,"Fichier chargé",f"{len(self.subsets)} sous-ensembles lus, {len(self.universe)} éléments.")
        except Exception as e:
            QMessageBox.critical(self,"Erreur lecture fichier",str(e))

    def load_table(self):
        self.table.setColumnCount(4); self.table.setHorizontalHeaderLabels(["Employé","Tâches","Shifts","Role"])
        self.table.setRowCount(len(self.subsets))
        for i,(sid,val) in enumerate(self.subsets.items()):
            self.table.setItem(i,0,QTableWidgetItem(sid))
            self.table.setItem(i,1,QTableWidgetItem(", ".join(val['elements'])))
            self.table.setItem(i,2,QTableWidgetItem(", ".join(val['shifts'])))
            self.table.setItem(i,3,QTableWidgetItem(val['role']))
        self.table.resizeColumnsToContents()

    def load_availability_controls(self):
        for i in reversed(range(self.grp_avail.layout().count())):
            w = self.grp_avail.layout().itemAt(i).widget()
            if w: w.setParent(None)
        self.chk_avail = {}
        for sid in self.subsets:
            chk = QCheckBox(sid); chk.setChecked(True); self.grp_avail.layout().addWidget(chk); self.chk_avail[sid] = chk

    # -----------------------------
    # Lancer optimisation
    # -----------------------------
    def run_optimization(self):
        if not self.subsets:
            QMessageBox.warning(self,"Aucune donnée","Charge d'abord un fichier Excel."); return
        avail = {sid:chk.isChecked() for sid,chk in self.chk_avail.items()}
        self.rh_constraints['availability'] = avail
        try: tl=float(self.le_time.text())
        except: tl=10.0
        try: mg=float(self.le_gap.text())
        except: mg=0.0
        self.rh_constraints['TimeLimit']=tl; self.rh_constraints['MIPGap']=mg

        # Stocker solution avant contraintes si nécessaire
        self.solution_before = None
        try:
            chosen, xvals, obj = solve_set_cover_plme(self.universe,self.subsets,self.costs)
            self.solution_before = {'chosen':chosen,'xvals':xvals,'obj':obj}
        except: pass

        # Appliquer contraintes RH
        try:
            chosen, xvals, obj = solve_set_cover_plme(self.universe,self.subsets,self.costs,self.rh_constraints)
            self.solution = {'chosen':chosen,'xvals':xvals,'obj':obj}
            self.lbl_obj.setText(f"Valeur objectif : {obj:.2f}")
            self.lbl_open.setText("Employés choisis: "+", ".join(chosen))
            self.display_assignments(chosen)
            self.plot_solution()         
            self.plot_bipartite_graph()  
            self.export_pdf()            
            QMessageBox.information(self,"Optimisation",f"Terminé — {len(chosen)} employés choisis. PDF généré.")
        except Exception as e:
            QMessageBox.critical(self,"Erreur optimisation",str(e))

    # -----------------------------
    # Affichage assignments
    # -----------------------------
    def display_assignments(self, chosen):
        rows=[]
        for e in self.universe:
            assigned=None
            candidates=[j for j in chosen if any(e.startswith(t) for t in self.subsets[j]['elements'])]
            if candidates:
                assigned=min(candidates,key=lambda j:self.costs[j])
            rows.append((e,assigned if assigned else "—"))
        self.txt_assign.setRowCount(len(rows))
        for i,(e,a) in enumerate(rows):
            self.txt_assign.setItem(i,0,QTableWidgetItem(str(e))); self.txt_assign.setItem(i,1,QTableWidgetItem(str(a)))
        self.txt_assign.resizeColumnsToContents()

    # -----------------------------
    # Histogramme par employé / shift
    # -----------------------------
    def plot_solution(self):
        if not self.solution: return
        self.ax_cover.clear()
        chosen = self.solution['chosen']

        # Histogramme par shift
        shift_counts = {s: [0]*len(chosen) for s in shifts}
        for i, sid in enumerate(chosen):
            for s in shifts:
                shift_counts[s][i] = sum(1 for day in days for e in self.subsets[sid]['elements'] if f"{e}_{s}_{day}" in self.universe)

        # Barres empilées
        bottom = [0]*len(chosen)
        for s in shifts:
            self.ax_cover.bar(range(len(chosen)), shift_counts[s], bottom=bottom, label=s)
            bottom = [bottom[i]+shift_counts[s][i] for i in range(len(chosen))]

        self.ax_cover.set_xticks(range(len(chosen)))
        self.ax_cover.set_xticklabels(chosen, rotation=45, ha='right')
        self.ax_cover.set_ylabel("Nombre de tâches couvertes")
        self.ax_cover.set_title("Couverture par employé et par shift (solution optimale)")
        self.ax_cover.legend()
        self.canvas_cover.draw()

    # -----------------------------
    # Graphe biparti (compact ou complet)
    # -----------------------------
    def plot_bipartite_graph(self):
        if not self.solution: return
        chosen = self.solution['chosen']

        G = nx.Graph()
        top_nodes = chosen
        if self.graph_compact:
            # Graphe compact : tâches regroupées par shift
            shift_nodes = []
            assign_dict = {}
            for e in self.universe:
                shift = "_".join(e.split("_")[1:2])  # récupère le shift
                shift_node = f"{shift}"
                if shift_node not in shift_nodes:
                    shift_nodes.append(shift_node)
                candidates = [j for j in chosen if any(e.startswith(t) for t in self.subsets[j]['elements'])]
                if candidates:
                    assign_dict[(candidates[0], shift_node)] = True
            G.add_nodes_from(top_nodes, bipartite=0)
            G.add_nodes_from(shift_nodes, bipartite=1)
            for (j, shift_node) in assign_dict.keys():
                G.add_edge(j, shift_node)
        else:
            # Graphe complet : chaque tâche individuelle
            assign_dict = {e: None for e in self.universe}
            for e in self.universe:
                candidates = [j for j in chosen if any(e.startswith(t) for t in self.subsets[j]['elements'])]
                if candidates:
                    assign_dict[e] = candidates[0]
            bottom_nodes = self.universe
            G.add_nodes_from(top_nodes, bipartite=0)
            G.add_nodes_from(bottom_nodes, bipartite=1)
            for e, j in assign_dict.items():
                if j: G.add_edge(j, e)

        self.ax_vis.clear()
        pos = nx.spring_layout(G, k=0.8, iterations=50)
        for n in G.nodes():
            if n in top_nodes: pos[n][1] += 1.0
            else: pos[n][1] -= 0.5

        nx.draw(G, pos,
                with_labels=True,
                node_color=['#f39c12' if n in top_nodes else '#3498db' for n in G.nodes],
                node_size=500,
                font_size=7,
                ax=self.ax_vis,
                alpha=0.9)

        self.ax_vis.set_title("Graphe biparti compact : employés ↔ shifts" if self.graph_compact else "Graphe biparti complet")
        self.ax_vis.axis('off')
        self.canvas_vis.draw()

    # -----------------------------
    # Export PDF
    # -----------------------------
    def export_pdf(self):
        if not self.solution: return
        pdf_path = "optimisation_station_service.pdf"
        with PdfPages(pdf_path) as pdf:
            self.fig_cover.savefig(pdf, format='pdf')
            self.fig_vis.savefig(pdf, format='pdf')

# -----------------------------
# Run
# -----------------------------
if __name__=="__main__":
    app=QApplication(sys.argv)
    apply_dark_theme(app)
    win=MainWindow()
    win.show()
    sys.exit(app.exec())
