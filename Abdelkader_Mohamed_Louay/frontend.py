# frontend.py - Application complète avec affichage de la satisfaction
import sys
import os
import pandas as pd
import gurobipy as gp
from gurobipy import GRB
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QSpinBox, QDoubleSpinBox, 
                               QPushButton, QTextEdit, QGroupBox, QFormLayout, 
                               QFileDialog, QMessageBox, QTabWidget,
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QSizePolicy, QStyle, QScrollArea, QFrame,
                               QGraphicsDropShadowEffect, QSlider)
from PySide6.QtGui import QColor, QPainter, QBrush, QIcon, QTextCursor, QPen, QFont, QPainterPath, QLinearGradient, QRadialGradient
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtCharts import (QChart, QChartView, QPieSeries, QBarSeries, QBarSet, 
                               QBarCategoryAxis, QValueAxis)


# ==========================================
# 0. LOGIQUE BACKEND (OPTIMISATION) AVEC LOGS GUROBI
# ==========================================
def solve_airline_model(params, file_paths):
    """
    Fonction wrapper qui exécute le modèle Gurobi et retourne 
    un dictionnaire structuré pour l'UI.
    """
    try:
        # 1. Chargement
        if not os.path.exists(file_paths['avions']) or not os.path.exists(file_paths['vols']):
            return {"status": "error", "message": "Fichiers CSV manquants"}

        df_avions = pd.read_csv(file_paths['avions'])
        df_vols = pd.read_csv(file_paths['vols'])

        # Données
        A = df_avions['AvionID'].tolist()
        V = df_vols['VolID'].tolist()
        
        K_eco = df_avions.set_index('AvionID')['K_eco'].to_dict()
        K_bus = df_avions.set_index('AvionID')['K_bus'].to_dict()
        C_op  = df_avions.set_index('AvionID')['C_op'].to_dict()
        # E_CO2 : Si la colonne n'existe pas, on met une valeur par défaut
        if 'E_CO2' in df_avions.columns:
            E_CO2 = df_avions.set_index('AvionID')['E_CO2'].to_dict()
        else:
            E_CO2 = {a: 50 for a in A} 
        
        P_eco = df_vols.set_index('VolID')['P_eco'].to_dict()
        P_bus = df_vols.set_index('VolID')['P_bus'].to_dict()
        Duree_Vol = df_vols.set_index('VolID')['Duree'].to_dict()

        # Matrices
        t, c, s = {}, {}, {}
        for i in A:
            for j in V:
                t[i,j] = Duree_Vol[j]
                c[i,j] = 200 # Coût fixe standard
                s[i,j] = 80  # Satisfaction standard

        C_conflit = [] # Liste de conflits (ex: [(1, 2)])
        
        # Paramètres depuis l'UI
        C_up = params.get('cost_upgrade', 50)
        Q_CO2_max = params.get('max_co2', 5000)
        w1, w2, w3 = params.get('w1', 0.5), params.get('w2', 0.3), params.get('w3', 0.2)

        # Modèle avec capture des logs
        import io
        import contextlib
        
        log_capture = io.StringIO()
        model = gp.Model("Airline_Opt")
        model.setParam('OutputFlag', 1)  # Activer les logs Gurobi
        
        # Capturer les logs
        with contextlib.redirect_stdout(log_capture), contextlib.redirect_stderr(log_capture):
            x = model.addVars(A, V, vtype=GRB.BINARY, name="x")
            u = model.addVars(V, vtype=GRB.INTEGER, lb=0, name="u")

            # Objectif
            cost_part = gp.quicksum((c[i,j] + C_op[i] * t[i,j]) * x[i,j] for i in A for j in V) + \
                        gp.quicksum(C_up * u[j] for j in V)
            satisfaction_part = gp.quicksum(s[i,j] * x[i,j] for i in A for j in V)
            time_part = gp.quicksum(t[i,j] * x[i,j] for i in A for j in V)
            
            model.setObjective(w1 * cost_part - w2 * satisfaction_part + w3 * time_part, GRB.MINIMIZE)

            # Contraintes
            for j in V: model.addConstr(gp.quicksum(x[i,j] for i in A) == 1)
            for j in V: model.addConstr(P_bus[j] + u[j] <= gp.quicksum(K_bus[i] * x[i,j] for i in A))
            for j in V: model.addConstr(P_eco[j] - u[j] <= gp.quicksum(K_eco[i] * x[i,j] for i in A))
            for j in V: model.addConstr(u[j] <= P_eco[j])
            
            # Contrainte CO2
            model.addConstr(gp.quicksum(E_CO2[i] * t[i,j] * x[i,j] for i in A for j in V) <= Q_CO2_max)

            model.optimize()
        
        # Récupérer les logs
        logs = log_capture.getvalue()

        # Résultat
        if model.status == GRB.OPTIMAL:
            res_routes = []
            total_upgrades = 0
            plane_usage = {}
            total_co2 = 0
            total_satisfaction = 0  # Ajout pour calculer la satisfaction totale

            for j in V:
                assigned_plane = -1
                satisfaction_vol = 0  # Ajout
                for i in A:
                    if x[i,j].X > 0.5:
                        assigned_plane = i
                        plane_type = df_avions.loc[df_avions['AvionID']==i, 'Type'].values[0]
                        plane_usage[plane_type] = plane_usage.get(plane_type, 0) + 1
                        total_co2 += E_CO2[i] * t[i,j]
                        satisfaction_vol = s[i,j]  # Récupération de la satisfaction
                        total_satisfaction += satisfaction_vol  # Cumul
                        break
                
                nb_up = int(u[j].X)
                total_upgrades += nb_up
                
                res_routes.append({
                    "vol_id": j,
                    "route": df_vols.loc[df_vols['VolID']==j, 'Route'].values[0],
                    "avion": df_avions.loc[df_avions['AvionID']==assigned_plane, 'Type'].values[0],
                    "avion_id": assigned_plane,
                    "duree": Duree_Vol[j],
                    "demande_eco": P_eco[j],
                    "demande_bus": P_bus[j],
                    "surclassement": nb_up,
                    "satisfaction": satisfaction_vol,  # Ajout de la satisfaction
                    "cout_vol": c[assigned_plane, j] + C_op[assigned_plane] * t[assigned_plane, j] if assigned_plane != -1 else 0  # Ajout du coût
                })

            # Calcul de la satisfaction moyenne
            satisfaction_moyenne = total_satisfaction / len(V) if len(V) > 0 else 0

            return {
                "status": "optimal",
                "kpis": {
                    "cout": model.objVal, 
                    "upgrades": total_upgrades,
                    "co2": total_co2, 
                    "vols_ok": len(V),
                    "satisfaction": total_satisfaction,  # Ajout
                    "satisfaction_moyenne": satisfaction_moyenne  # Ajout
                },
                "routes": res_routes,
                "usage": plane_usage,
                "logs": logs  # AJOUT: Logs Gurobi
            }
        else:
            return {
                "status": "infeasible", 
                "message": "Aucune solution trouvée (Contraintes trop strictes ?)",
                "logs": logs  # AJOUT: Logs même en cas d'erreur
            }

    except Exception as e:
        return {
            "status": "error", 
            "message": str(e),
            "logs": f"ERREUR: {str(e)}"  # AJOUT: Logs d'erreur
        }

# ==========================================
# 1. DESIGN SYSTEM & CONSTANTES
# ==========================================
COLOR_BG = "#121218"
COLOR_PANEL = "#1e1e24"
COLOR_ACCENT = "#5c7cfa"
COLOR_TEXT_MAIN = "#ffffff"
COLOR_TEXT_DIM = "#878a99"
COLOR_BORDER = "#2a2a35"

STYLESHEET = f"""
QMainWindow {{ background-color: {COLOR_BG}; }}
QWidget {{ font-family: 'Segoe UI', sans-serif; font-size: 13px; color: {COLOR_TEXT_MAIN}; }}

/* Onglets */
QTabWidget::pane {{ border: none; background: transparent; }}
QTabBar::tab {{ background: transparent; color: {COLOR_TEXT_DIM}; padding: 12px 24px; font-weight: 600; border-bottom: 3px solid transparent; }}
QTabBar::tab:selected {{ color: {COLOR_ACCENT}; border-bottom: 3px solid {COLOR_ACCENT}; }}

/* === CHAMPS DE SAISIE (Inputs) AVEC FLÈCHES === */
QLineEdit, QSpinBox, QDoubleSpinBox {{ 
    background-color: #23232a; 
    border: 1px solid {COLOR_BORDER}; 
    border-radius: 6px; 
    color: white; 
    padding: 8px 10px; 
    selection-background-color: {COLOR_ACCENT};
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{ 
    border: 1px solid {COLOR_ACCENT}; 
    background-color: #2b2b36; 
}}

/* Configuration des boutons Haut/Bas */
QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 25px;
    border-left: 1px solid {COLOR_BORDER};
    background-color: transparent;
    margin-right: 2px;
    margin-top: 2px;
}}
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 25px;
    border-left: 1px solid {COLOR_BORDER};
    background-color: transparent;
    margin-right: 2px;
    margin-bottom: 2px;
}}

/* Changement de couleur au survol des boutons */
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: #2a2a35; 
    border: 1px solid {COLOR_ACCENT};
    border-radius: 2px;
}}

/* === ICONES DES FLÈCHES BLEUES === */
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjNWM3Y2ZhIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlsaW5lIHBvaW50cz0iMTggMTUgMTIgOSA2IDE1Ij48L3BvbHlsaW5lPjwvc3ZnPg==);
    width: 10px; height: 10px;
}}

QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    image: url(data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjNWM3Y2ZhIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBvbHlsaW5lIHBvaW50cz0iNiA5IDEyIDE1IDE4IDkiPjwvcG9seWxpbmU+PC9zdmc+);
    width: 10px; height: 10px;
}}

/* Boutons */
QPushButton {{ background-color: #2a2a35; color: white; border: 1px solid {COLOR_BORDER}; padding: 10px; border-radius: 6px; font-weight: 600; }}
QPushButton:hover {{ background-color: #32323e; border-color: {COLOR_TEXT_DIM}; }}
QPushButton#RunButton {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4c6ef5, stop:1 #748ffc); border: none; font-size: 15px; padding: 15px; border-radius: 8px; }}
QPushButton#RunButton:hover {{ background: #5c7cfa; }}
QPushButton#RunButton:disabled {{ background: #3f3f4b; color: #878a99; }}

/* Tableaux */
QTableWidget {{ background-color: {COLOR_PANEL}; border: 1px solid {COLOR_BORDER}; border-radius: 8px; gridline-color: {COLOR_BORDER}; }}
QHeaderView::section {{ background-color: #23232a; color: {COLOR_TEXT_DIM}; padding: 8px; border: none; font-weight: bold; }}
QTableWidget::item {{ padding: 5px; }}

/* GroupBox & Sliders */
QGroupBox {{ border: 1px solid {COLOR_BORDER}; border-radius: 8px; margin-top: 1.5em; padding-top: 15px; font-weight: bold; color: {COLOR_ACCENT}; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; }}
QSlider::groove:horizontal {{ border: 1px solid #3f3f4b; height: 6px; background: #2a2a35; margin: 2px 0; border-radius: 3px; }}
QSlider::handle:horizontal {{ background: {COLOR_ACCENT}; border: 1px solid {COLOR_ACCENT}; width: 14px; height: 14px; margin: -5px 0; border-radius: 7px; }}
"""

def apply_shadow(widget):
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(15)
    shadow.setColor(QColor(0, 0, 0, 50))
    shadow.setOffset(0, 4)
    widget.setGraphicsEffect(shadow)

# ==========================================
# 2. WIDGETS PERSONNALISÉS
# ==========================================
class CardFrame(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"CardFrame {{ background-color: {COLOR_PANEL}; border-radius: 12px; border: 1px solid {COLOR_BORDER}; }}")
        apply_shadow(self)

class MetricWidget(CardFrame):
    def __init__(self, title, unit="", color_accent=COLOR_ACCENT):
        super().__init__()
        self.setMinimumHeight(110)
        layout = QVBoxLayout(self)
        
        header = QHBoxLayout()
        lbl_title = QLabel(title.upper())
        lbl_title.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 11px; font-weight: 700; border:none;")
        dot = QLabel("●"); dot.setStyleSheet(f"color: {color_accent}; font-size: 10px; border:none;")
        header.addWidget(dot); header.addWidget(lbl_title); header.addStretch()
        layout.addLayout(header)
        
        row_val = QHBoxLayout()
        self.lbl_val = QLabel("0")
        self.lbl_val.setStyleSheet("color: white; font-size: 32px; font-weight: 600; border:none;")
        lbl_unit = QLabel(unit)
        lbl_unit.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 14px; margin-bottom: 6px; border:none;")
        row_val.addWidget(self.lbl_val); row_val.addWidget(lbl_unit, 0, Qt.AlignBottom); row_val.addStretch()
        layout.addLayout(row_val)

    def update_value(self, target):
        if isinstance(target, (int, float)):
            val_str = f"{target:,.1f}".replace(",", " ")
        else:
            val_str = str(target)
        self.lbl_val.setText(val_str)

class FlightItem(CardFrame):
    def __init__(self, route_data):
        super().__init__()
        self.setFixedHeight(95)  # Augmenter la hauteur pour la satisfaction
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Icone
        icon_box = QWidget()
        icon_box.setFixedWidth(60)
        vb = QVBoxLayout(icon_box); vb.setContentsMargins(0,0,0,0)
        lbl_icon = QLabel("✈")
        lbl_icon.setAlignment(Qt.AlignCenter)
        lbl_icon.setStyleSheet(f"background-color: {COLOR_ACCENT}33; color: {COLOR_ACCENT}; border-radius: 6px; font-size: 18px; padding: 5px;")
        vb.addWidget(lbl_icon)
        layout.addWidget(icon_box)
        
        # Infos
        info_layout = QVBoxLayout()
        l_route = QLabel(route_data['route'])
        l_route.setStyleSheet("font-size: 15px; font-weight: bold; color: white; border:none;")
        l_plane = QLabel(f"Avion : {route_data['avion']}")
        l_plane.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_DIM}; border:none;")
        info_layout.addWidget(l_route)
        info_layout.addWidget(l_plane)
        layout.addLayout(info_layout, 1)
        
        # Stats avec satisfaction
        stats_layout = QVBoxLayout()
        l_dur = QLabel(f"⏱ {route_data['duree']}h")
        l_dur.setStyleSheet("color: white; font-weight:bold; border:none;")
        
        # Affichage de la satisfaction
        if 'satisfaction' in route_data:
            satisfaction = route_data['satisfaction']
            # Choisir la couleur en fonction du niveau de satisfaction
            satisfaction_color = "#ffd43b"  # Jaune par défaut
            if satisfaction >= 80:
                satisfaction_color = "#51cf66"  # Vert pour satisfaction élevée
            elif satisfaction <= 60:
                satisfaction_color = "#ff6b6b"  # Rouge pour satisfaction basse
            
            l_sat = QLabel(f"😊 {satisfaction:.0f}/100")
            l_sat.setStyleSheet(f"color: {satisfaction_color}; font-weight:bold; font-size: 11px; border:none;")
            stats_layout.addWidget(l_sat)
        
        l_pax = QLabel(f"Pax: {route_data['demande_eco'] + route_data['demande_bus']}")
        l_pax.setStyleSheet(f"color: {COLOR_TEXT_DIM}; border:none;")
        stats_layout.addWidget(l_dur)
        stats_layout.addWidget(l_pax)
        layout.addLayout(stats_layout)
        
        layout.addSpacing(15)

        # Badge avec plus d'informations
        badge_layout = QVBoxLayout()
        
        if route_data['surclassement'] > 0:
            badge = QLabel(f"UPGRADE\n+{route_data['surclassement']}")
            badge.setAlignment(Qt.AlignCenter)
            badge.setStyleSheet("background-color: #e03131; color: white; border-radius: 4px; font-weight: bold; font-size: 10px; padding: 5px; border:none;")
        else:
            badge = QLabel("✓ OK")
            badge.setAlignment(Qt.AlignCenter)
            badge.setStyleSheet("background-color: #2f9e44; color: white; border-radius: 4px; font-weight: bold; font-size: 10px; padding: 5px; border:none;")
        
        badge_layout.addWidget(badge)
        
        # Affichage du coût si disponible
        if 'cout_vol' in route_data:
            l_cout = QLabel(f"${route_data['cout_vol']:.0f}")
            l_cout.setAlignment(Qt.AlignCenter)
            l_cout.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 9px; margin-top: 3px; border:none;")
            badge_layout.addWidget(l_cout)
        
        layout.addLayout(badge_layout)

# ==========================================
# 2.5 WIDGET DE VISUALISATION RÉSEAU
# ==========================================
class NetworkVisualizationWidget(QWidget):
    """Widget personnalisé pour visualiser les affectations avions → vols"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(800)
        self.setStyleSheet(f"background-color: #1a1a20; border-radius: 12px; border: 1px solid {COLOR_BORDER};")

        self.avions = []
        self.vols = []
        self.affectations = []
        self.animation_progress = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)

    def set_data(self, avions_data, vols_data, affectations_data):
        colors = ["#4dabf7", "#748ffc", "#9775fa", "#faa2c1", "#ff8787", "#51cf66", "#ffd43b"]

        self.avions = []
        for i, avion in enumerate(avions_data):
            self.avions.append({
                'id': avion['id'],
                'type': avion['type'],
                'hours': avion.get('hours', 0),
                'color': colors[i % len(colors)]
            })

        self.vols = []
        for vol in vols_data:
            self.vols.append({
                'id': vol['id'],
                'route': vol['route'],
                'duree': vol['duree'],
                'satisfaction': vol.get('satisfaction', 80)  # Ajout de la satisfaction
            })

        self.affectations = []
        for aff in affectations_data:
            avion_color = next((a['color'] for a in self.avions if a['id'] == aff['avion_id']), COLOR_ACCENT)
            self.affectations.append({
                'avion_id': aff['avion_id'],
                'vol_id': aff['vol_id'],
                'duree': aff['duree'],
                'upgrades': aff.get('upgrades', 0),
                'color': avion_color
            })

        self.animation_progress = 0
        self.timer.start(20)
        self.update()

    def animate(self):
        if self.animation_progress < 100:
            self.animation_progress += 2
            self.update()
        else:
            self.timer.stop()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        margin_left = 120
        margin_right = 160 
        margin_top = 80
        margin_bottom = 60

        avions_x = margin_left
        vols_x = w - margin_right

        num_avions = len(self.avions)
        num_vols = len(self.vols)
        available_height = h - margin_top - margin_bottom

        NODE_HEIGHT_AVION = 70  
        NODE_HEIGHT_VOL = 60  # Augmenté pour la satisfaction
        PADDING = 25

        if num_avions > 0:
            total_h_avions = num_avions * NODE_HEIGHT_AVION + (num_avions - 1) * PADDING
            avion_start_y = margin_top + (available_height - total_h_avions) / 2
            avion_spacing = NODE_HEIGHT_AVION + PADDING
        else:
            avion_start_y = margin_top
            avion_spacing = NODE_HEIGHT_AVION + PADDING

        if num_vols > 0:
            total_h_vols = num_vols * NODE_HEIGHT_VOL + (num_vols - 1) * PADDING
            vol_start_y = margin_top + (available_height - total_h_vols) / 2
            vol_spacing = NODE_HEIGHT_VOL + PADDING
        else:
            vol_start_y = margin_top
            vol_spacing = NODE_HEIGHT_VOL + PADDING

        progress = self.animation_progress / 100.0

        # Titres
        painter.setPen(QPen(QColor(COLOR_ACCENT), 2))
        painter.setFont(QFont("Segoe UI", 13, QFont.Bold))

        # Titre Avions
        painter.drawText(QRectF(margin_left - 80, -10, 160, 35), Qt.AlignCenter, "✈  AVIONS")
        
        # Titre Vols
        painter.drawText(QRectF(vols_x - 80 + 50, -10, 160, 35), Qt.AlignCenter, "VOLS  ✈")

        # Lignes séparatrices
        painter.setPen(QPen(QColor(COLOR_BORDER), 2))

        # LIENS
        for aff in self.affectations:
            avion_idx = next((i for i, a in enumerate(self.avions) if a['id'] == aff['avion_id']), -1)
            vol_idx = next((i for i, v in enumerate(self.vols) if v['id'] == aff['vol_id']), -1)
            
            if avion_idx == -1 or vol_idx == -1: continue

            start_y = avion_start_y + avion_idx * avion_spacing + (NODE_HEIGHT_AVION / 2)
            end_y = vol_start_y + vol_idx * vol_spacing + (NODE_HEIGHT_VOL / 2)

            start_point = QPointF(avions_x + 75, start_y)
            end_point = QPointF(vols_x - 40, end_y)       

            dist_x = end_point.x() - start_point.x()
            ctrl1_x = start_point.x() + dist_x * 0.4
            ctrl2_x = start_point.x() + dist_x * 0.6

            if progress > 0:
                base_color = QColor(aff['color'])
                pen_style = Qt.DashLine if aff['upgrades'] > 0 else Qt.SolidLine
                pen_width = 2.5 if aff['upgrades'] > 0 else 2.0
                
                pen_color = QColor(base_color)
                pen_color.setAlpha(int(180 * progress))
                
                painter.setPen(QPen(pen_color, pen_width, pen_style))
                painter.setBrush(Qt.NoBrush)

                path = self.create_bezier_curve(start_point, end_point, ctrl1_x, ctrl2_x, progress)
                painter.drawPath(path)

                if progress > 0.85:
                    mid_x = (start_point.x() + end_point.x()) / 2
                    mid_y = (start_y + end_y) / 2
                    
                    label_text = f"{aff['duree']:.1f}h"
                    if aff['upgrades'] > 0:
                        label_text += " ⚠"

                    painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
                    text_w = 55
                    text_rect = QRectF(mid_x - text_w/2, mid_y - 10, text_w, 20)
                    
                    painter.setBrush(QColor("#1a1a20"))
                    painter.setPen(QPen(base_color, 1))
                    painter.drawRoundedRect(text_rect, 5, 5)
                    
                    painter.setPen(QColor(COLOR_TEXT_MAIN))
                    painter.drawText(text_rect, Qt.AlignCenter, label_text)

        # NOEUDS AVIONS
        for i, avion in enumerate(self.avions):
            y = avion_start_y + i * avion_spacing
            rect = QRectF(avions_x - 70, y, 140, NODE_HEIGHT_AVION)
            color = QColor(avion['color'])

            if progress > 0:
                shadow_rect = rect.translated(3, 3)
                painter.setBrush(QBrush(QColor(0, 0, 0, int(40 * progress))))
                painter.setPen(Qt.NoPen)
                painter.drawRoundedRect(shadow_rect, 10, 10)

                grad = QLinearGradient(rect.topLeft(), rect.bottomLeft())
                grad.setColorAt(0, QColor(color.red(), color.green(), color.blue(), int(60 * progress)))
                grad.setColorAt(1, QColor(color.red(), color.green(), color.blue(), int(20 * progress)))
                painter.setBrush(QBrush(grad))
                
                painter.setPen(QPen(QColor(color.red(), color.green(), color.blue(), int(255 * progress)), 2))
                painter.drawRoundedRect(rect, 10, 10)

                painter.setPen(QColor(COLOR_TEXT_MAIN))
                painter.setFont(QFont("Segoe UI", 11, QFont.Bold))
                painter.drawText(QRectF(rect.x(), rect.y() + 6, rect.width(), 20), Qt.AlignCenter, avion['type'])

                painter.setPen(QColor("#a0a0b0"))
                painter.setFont(QFont("Segoe UI", 8))
                painter.drawText(QRectF(rect.x(), rect.y() + 28, rect.width(), 15), Qt.AlignCenter, f"ID: {avion['id']}")

                painter.setPen(color)
                painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
                painter.drawText(QRectF(rect.x(), rect.y() + 46, rect.width(), 15), Qt.AlignCenter, f"⏱ {avion['hours']:.1f}h")

        # NOEUDS VOLS (avec satisfaction)
        for i, vol in enumerate(self.vols):
            y = vol_start_y + i * vol_spacing
            center = QPointF(vols_x, y + NODE_HEIGHT_VOL / 2)
            radius = 22 

            if progress > 0:
                painter.setBrush(Qt.NoBrush)
                painter.setPen(QPen(QColor(COLOR_ACCENT), 2))
                painter.drawEllipse(center, radius + 2, radius + 2)

                grad = QRadialGradient(center, radius)
                grad.setColorAt(0, QColor(COLOR_BORDER))
                grad.setColorAt(1, QColor("#1a1a20"))
                painter.setBrush(QBrush(grad))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(center, radius, radius)

                painter.setPen(QColor(COLOR_TEXT_MAIN))
                painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
                painter.drawText(QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2), 
                               Qt.AlignCenter, str(vol['id']))

                # Label Route
                route_rect_x = vols_x + radius + 15
                route_rect_y = center.y() - 13
                route_rect = QRectF(route_rect_x, route_rect_y, 110, 26)
                
                painter.setPen(QPen(QColor(COLOR_BORDER), 1))
                painter.drawLine(int(vols_x + radius + 2), int(center.y()), int(route_rect_x), int(center.y()))

                painter.setBrush(QColor("#252530"))
                painter.setPen(QPen(QColor(COLOR_ACCENT), 1))
                painter.drawRoundedRect(route_rect, 4, 4)

                painter.setFont(QFont("Segoe UI", 8))
                painter.setPen(QColor("#a0a0b0"))
                painter.drawText(route_rect, Qt.AlignCenter, vol['route'][:15] + ("..." if len(vol['route']) > 15 else ""))

                # Affichage de la satisfaction
                if 'satisfaction' in vol:
                    satisfaction = vol['satisfaction']
                    sat_color = QColor("#ffd43b")  # Jaune par défaut
                    if satisfaction >= 80:
                        sat_color = QColor("#51cf66")  # Vert
                    elif satisfaction <= 60:
                        sat_color = QColor("#ff6b6b")  # Rouge
                    
                    # Cercle de satisfaction
                    sat_radius = 8
                    sat_x = vols_x - radius - 25
                    sat_y = center.y()
                    
                    painter.setBrush(QBrush(sat_color))
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(QPointF(sat_x, sat_y), sat_radius, sat_radius)
                    
                    # Texte de satisfaction
                    painter.setPen(QPen(QColor("#ffffff"), 1))
                    painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
                    painter.drawText(QRectF(sat_x - 25, sat_y - 20, 50, 40), 
                                   Qt.AlignCenter, f"{satisfaction:.0f}")

    def create_bezier_curve(self, start, end, ctrl1_x, ctrl2_x, progress):
        path = QPainterPath()
        path.moveTo(start)
        ctrl1 = QPointF(ctrl1_x, start.y())
        ctrl2 = QPointF(ctrl2_x, end.y())

        if progress < 1.0:
            t = progress
            x = (1-t)**3 * start.x() + 3*(1-t)**2*t * ctrl1.x() + 3*(1-t)*t**2 * ctrl2.x() + t**3 * end.x()
            y = (1-t)**3 * start.y() + 3*(1-t)**2*t * ctrl1.y() + 3*(1-t)*t**2 * ctrl2.y() + t**3 * end.y()
            current_end = QPointF(x, y)
            path.cubicTo(ctrl1, ctrl2, current_end)
        else:
            path.cubicTo(ctrl1, ctrl2, end)

        return path

# ==========================================
# 3. APPLICATION PRINCIPALE
# ==========================================
class AirlineApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Airline Fleet Optimizer")
        self.resize(1400, 900)  # Légèrement plus large
        self.setStyleSheet(STYLESHEET)
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        self.file_paths = {
        'avions': os.path.join(BASE_DIR, "avions.csv"),
        'vols': os.path.join(BASE_DIR, "vols.csv")
        }
        
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self.create_tab_donnees()
        self.create_tab_dashboard()
        self.create_tab_network()
        
        self.update_file_labels()

    def create_tab_donnees(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20); layout.setSpacing(20)

        left_panel = CardFrame()
        left_panel.setFixedWidth(300)
        vbox = QVBoxLayout(left_panel)
        vbox.addWidget(QLabel("SOURCES DE DONNÉES", styleSheet=f"color:{COLOR_TEXT_DIM}; font-weight:bold; margin-bottom:10px;"))
        
        self.file_status_labels = {}

        for key, name, icon in [('avions', 'Ressources (Avions)', '✈️'), ('vols', 'Programme (Vols)', '📅')]:
            row_widget = QWidget()
            row_layout = QVBoxLayout(row_widget)
            row_layout.setContentsMargins(0,0,0,15)
            
            lbl_title = QLabel(f"{icon} {name}")
            lbl_title.setStyleSheet("font-weight:bold; font-size:14px;")
            row_layout.addWidget(lbl_title)
            
            btn = QPushButton(f"Choisir un fichier...")
            btn.setStyleSheet(f"text-align: left; padding-left: 10px; color: {COLOR_TEXT_DIM}; border: 1px dashed {COLOR_BORDER};")
            btn.setCursor(Qt.PointingHandCursor)
            
            lbl_current = QLabel("Aucun fichier")
            lbl_current.setStyleSheet("color: #ff6b6b; font-size: 11px; margin-top: 2px;")
            self.file_status_labels[key] = (btn, lbl_current)

            btn.clicked.connect(lambda c, k=key: self.load_new_file(k))
            
            row_layout.addWidget(btn)
            row_layout.addWidget(lbl_current)
            
            btn_view = QPushButton("Voir les données")
            btn_view.setCursor(Qt.PointingHandCursor)
            btn_view.setStyleSheet("background-color: #003366; color: white; border: none; padding: 6px 12px; margin-top: 5px; border-radius: 4px;")
            btn_view.clicked.connect(lambda c, k=key: self.preview_current_file(k))
            row_layout.addWidget(btn_view)

            vbox.addWidget(row_widget)
            
        vbox.addStretch()
        layout.addWidget(left_panel)

        right_panel = QVBoxLayout()
        self.lbl_preview = QLabel("APERÇU DES DONNÉES")
        self.lbl_preview.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        right_panel.addWidget(self.lbl_preview)
        
        self.table_view = QTableWidget()
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setStyleSheet(f"alternate-background-color: #23232a;")
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        right_panel.addWidget(self.table_view)
        
        layout.addLayout(right_panel)
        self.tabs.addTab(tab, "DONNÉES")

    def create_tab_dashboard(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20); layout.setSpacing(20)

        sidebar = CardFrame()
        sidebar.setFixedWidth(340) 
        sb_layout = QVBoxLayout(sidebar)
        
        sb_layout.addWidget(QLabel("CONFIGURATION", styleSheet=f"color:{COLOR_TEXT_DIM}; font-weight:bold; font-size:12px; letter-spacing:1px;"))
        sb_layout.addSpacing(10)

        gb_weights = QGroupBox("PRIORITÉS (Poids)")
        l_w = QVBoxLayout()
        l_w.setSpacing(15)
        
        self.sliders = {}
        weights_config = [
            ('w1', ' Coûts Oper.', 50, "Importance de réduire les coûts"), 
            ('w2', ' Satisfaction', 30, "Importance du confort client"), 
            ('w3', ' Temps Vol', 20, "Importance de la rapidité")
        ]

        for key, name, def_val, tip in weights_config:
            row_cont = QWidget()
            row = QHBoxLayout(row_cont); row.setContentsMargins(0,0,0,0)
            
            lbl = QLabel(name); lbl.setToolTip(tip)
            lbl.setStyleSheet("border:none; width: 90px;")
            
            sl = QSlider(Qt.Horizontal)
            sl.setRange(0, 100)
            sl.setValue(def_val)
            
            val_lbl = QLabel(f"{def_val}%")
            val_lbl.setStyleSheet(f"color: {COLOR_ACCENT}; font-weight:bold; border:none; width: 35px; text-align:right;")
            sl.valueChanged.connect(lambda v, l=val_lbl: l.setText(f"{v}%"))
            
            self.sliders[key] = sl
            row.addWidget(lbl); row.addWidget(sl); row.addWidget(val_lbl)
            l_w.addWidget(row_cont)
            
        gb_weights.setLayout(l_w)
        sb_layout.addWidget(gb_weights)

        gb_params = QGroupBox("PARAMÈTRES GLOBAUX")
        l_p = QFormLayout()
        l_p.setSpacing(10)
        
        self.spin_cup = QDoubleSpinBox()
        self.spin_cup.setRange(0, 5000)
        self.spin_cup.setValue(50)
        self.spin_cup.setSuffix(" $")
        self.spin_cup.setDecimals(0)
        
        self.spin_co2 = QDoubleSpinBox()
        self.spin_co2.setRange(0, 1000000)
        self.spin_co2.setValue(5000)
        self.spin_co2.setSuffix(" kg")
        self.spin_co2.setSingleStep(100)
        self.spin_co2.setDecimals(0)

        l_p.addRow("Coût par Upgrade :", self.spin_cup)
        l_p.addRow("Quota CO2 Max :", self.spin_co2)
        
        gb_params.setLayout(l_p)
        sb_layout.addWidget(gb_params)
        
        sb_layout.addStretch()
        
        self.btn_run = QPushButton("LANCER L'AFFECTATION")
        self.btn_run.setObjectName("RunButton")
        self.btn_run.setCursor(Qt.PointingHandCursor)
        self.btn_run.clicked.connect(self.run_optimization)
        sb_layout.addWidget(self.btn_run)
        
        layout.addWidget(sidebar)

        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setStyleSheet("background: transparent; border: none;")
        content = QWidget()
        res_layout = QVBoxLayout(content)
        res_layout.setSpacing(20)

        h_res = QHBoxLayout()
        h_res.addWidget(QLabel("Tableau de Bord", styleSheet="font-size: 24px; font-weight: 700; color: white;"))
        self.lbl_status = QLabel("Prêt")
        h_res.addWidget(self.lbl_status)
        res_layout.addLayout(h_res)

        # KPIs (avec satisfaction)
        kpi_layout = QHBoxLayout()
        self.kpi_cout = MetricWidget("Coût Est.", "$", "#ff6b6b")
        self.kpi_up = MetricWidget("Surclassés", "Pax", "#51cf66")
        self.kpi_co2 = MetricWidget("Total CO2", "kg", "#5c7cfa")
        self.kpi_vols = MetricWidget("Vols Couverts", "", "#9775fa")
        self.kpi_satisfaction = MetricWidget("Satisfaction", "/100", "#ffd43b")
        
        for k in [self.kpi_cout, self.kpi_up, self.kpi_co2, self.kpi_vols, self.kpi_satisfaction]: 
            kpi_layout.addWidget(k)
        res_layout.addLayout(kpi_layout)

        chart_row = QHBoxLayout()
        self.chart_pie_view = self.create_chart_container("Utilisation Ressource Avions")
        chart_row.addWidget(self.chart_pie_view)
        self.chart_bar_view = self.create_chart_container("Surclassements par Vol")
        chart_row.addWidget(self.chart_bar_view)
        res_layout.addLayout(chart_row)

        res_layout.addWidget(QLabel("AFFECTATIONS DÉTAILLÉES", styleSheet=f"color:{COLOR_TEXT_DIM}; font-weight:bold; margin-top:10px;"))
        self.res_container = QVBoxLayout()
        res_layout.addLayout(self.res_container)
        
        res_layout.addWidget(QLabel("LOGS DU SOLVEUR GUROBI", styleSheet=f"color:{COLOR_ACCENT}; font-weight:bold; font-size:14px; margin-top:20px;"))
        
        self.logs_widget = CardFrame()
        logs_layout = QVBoxLayout(self.logs_widget)
        logs_layout.setSpacing(10)
        
        logs_buttons_layout = QHBoxLayout()
        self.btn_clear_logs = QPushButton("Effacer les logs")
        self.btn_clear_logs.clicked.connect(self.clear_logs)
        self.btn_save_logs = QPushButton("Sauvegarder les logs")
        self.btn_save_logs.clicked.connect(self.save_logs)
        
        logs_buttons_layout.addWidget(self.btn_clear_logs)
        logs_buttons_layout.addWidget(self.btn_save_logs)
        logs_buttons_layout.addStretch()
        
        logs_layout.addLayout(logs_buttons_layout)
        
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setMinimumHeight(200)
        self.logs_text.setStyleSheet(f"""
            background-color: #1a1a20; 
            color: #a0a0b0; 
            border: 1px solid {COLOR_BORDER}; 
            border-radius: 6px; 
            font-family: 'Consolas', 'Courier New', monospace; 
            font-size: 11px; 
            padding: 10px;
        """)
        
        scroll_bar = self.logs_text.verticalScrollBar()
        scroll_bar.setStyleSheet(f"""
            QScrollBar:vertical {{
                background: transparent;
                width: 10px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLOR_ACCENT};
                border-radius: 5px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
        """)
        
        logs_layout.addWidget(self.logs_text)
        res_layout.addWidget(self.logs_widget)
        
        res_layout.addStretch()
        main_scroll.setWidget(content)
        layout.addWidget(main_scroll, 1)

        self.tabs.addTab(tab, "OPTIMISATION")

    def create_tab_network(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header = QHBoxLayout()
        title = QLabel("Visualisation du Réseau d'Affectation")
        title.setStyleSheet("font-size: 24px; font-weight: 700; color: white;")
        header.addWidget(title)
        header.addStretch()
        
        legend = QLabel("━ Ligne pleine : Vol normal  • - - Ligne pointillée : Avec surclassement")
        legend.setStyleSheet("color: #878a99; font-size: 12px;")
        header.addWidget(legend)
        
        layout.addLayout(header)
        
        self.network_widget = NetworkVisualizationWidget()
        layout.addWidget(self.network_widget)
        
        stats_layout = QHBoxLayout()
        self.lbl_network_stats = QLabel("Exécutez l'optimisation pour voir le réseau")
        self.lbl_network_stats.setStyleSheet("color: #878a99; font-size: 13px; padding: 10px;")
        self.lbl_network_stats.setAlignment(Qt.AlignCenter)
        stats_layout.addWidget(self.lbl_network_stats)
        layout.addLayout(stats_layout)
        
        self.tabs.addTab(tab, "RÉSEAU")

    def create_chart_container(self, title):
        frame = CardFrame()
        l = QVBoxLayout(frame)
        l.addWidget(QLabel(title, styleSheet=f"color:{COLOR_TEXT_DIM}; font-weight:bold;"))
        chart = QChart(); chart.setBackgroundBrush(Qt.NoBrush); chart.legend().setVisible(False)
        view = QChartView(chart); view.setRenderHint(QPainter.Antialiasing); view.setStyleSheet("background: transparent;")
        view.setMinimumHeight(250)
        l.addWidget(view)
        return frame

    def update_file_labels(self):
        for key, path in self.file_paths.items():
            if key in self.file_status_labels:
                btn, lbl = self.file_status_labels[key]
                if os.path.exists(path):
                    filename = os.path.basename(path)
                    btn.setText(filename)
                    btn.setStyleSheet(f"text-align: left; padding-left: 10px; color: white; border: 1px solid {COLOR_BORDER}; background: #23232a;")
                    lbl.setText("✅ Chargé")
                    lbl.setStyleSheet("color: #51cf66; font-size: 11px;")
                else:
                    btn.setText("Choisir un fichier...")
                    lbl.setText("❌ Fichier introuvable")
                    lbl.setStyleSheet("color: #ff6b6b; font-size: 11px;")

    def load_new_file(self, key):
        fname, _ = QFileDialog.getOpenFileName(self, "Ouvrir CSV", "", "CSV (*.csv)")
        if fname:
            self.file_paths[key] = fname
            self.update_file_labels()
            self.preview_current_file(key)

    def preview_current_file(self, key):
        self.lbl_preview.setText(f"CONTENU : {key.upper()}")
        path = self.file_paths.get(key)
        if path and os.path.exists(path):
            try:
                df = pd.read_csv(path)
                self.table_view.setRowCount(df.shape[0])
                self.table_view.setColumnCount(df.shape[1])
                self.table_view.setHorizontalHeaderLabels(df.columns)
                for i in range(df.shape[0]):
                    for j in range(df.shape[1]):
                        self.table_view.setItem(i, j, QTableWidgetItem(str(df.iloc[i, j])))
            except Exception as e:
                QMessageBox.warning(self, "Erreur", f"Erreur de lecture: {e}")

    def run_optimization(self):
        self.btn_run.setText("CALCUL EN COURS...")
        self.btn_run.setEnabled(False)
        self.lbl_status.setText("Optimisation...")
        QApplication.processEvents()

        params = {
            'w1': self.sliders['w1'].value() / 100,
            'w2': self.sliders['w2'].value() / 100,
            'w3': self.sliders['w3'].value() / 100,
            'cost_upgrade': self.spin_cup.value(),
            'max_co2': self.spin_co2.value()
        }

        res = solve_airline_model(params, self.file_paths)

        if res['status'] == 'optimal':
            self.update_dashboard(res)
            self.update_network_visualization(res)
            self.lbl_status.setText("✅ Solution Optimale")
            self.lbl_status.setStyleSheet("color: #51cf66; font-weight: bold;")
        else:
            QMessageBox.warning(self, "Attention", f"{res.get('message')}")
            self.lbl_status.setText("❌ Problème")
            self.lbl_status.setStyleSheet("color: #ff6b6b; font-weight: bold;")
            
            if 'logs' in res:
                self.logs_text.setPlainText(res['logs'])

        self.btn_run.setText("LANCER L'AFFECTATION")
        self.btn_run.setEnabled(True)

    def update_dashboard(self, data):
        # KPIs
        self.kpi_cout.update_value(data['kpis']['cout'])
        self.kpi_up.update_value(data['kpis']['upgrades'])
        self.kpi_co2.update_value(data['kpis']['co2'])
        self.kpi_vols.update_value(data['kpis']['vols_ok'])
        
        # Mise à jour de la satisfaction
        if 'satisfaction_moyenne' in data['kpis']:
            self.kpi_satisfaction.update_value(data['kpis']['satisfaction_moyenne'])
        elif 'satisfaction' in data['kpis']:
            total_satisfaction = data['kpis']['satisfaction']
            nb_vols = data['kpis']['vols_ok']
            if nb_vols > 0:
                avg_satisfaction = total_satisfaction / nb_vols
                self.kpi_satisfaction.update_value(round(avg_satisfaction, 1))

        # Pie Chart
        chart_pie = self.chart_pie_view.findChild(QChartView).chart()
        chart_pie.removeAllSeries()
        series = QPieSeries()
        colors = ["#4dabf7", "#748ffc", "#9775fa", "#faa2c1", "#ff8787"]
        for i, (plane, count) in enumerate(data['usage'].items()):
            sl = series.append(plane, count)
            sl.setLabel(f"{plane} ({count})")
            sl.setLabelVisible(True)
            sl.setLabelColor(QColor("white"))
            sl.setColor(QColor(colors[i % len(colors)]))
        chart_pie.addSeries(series)

        # Bar Chart
        chart_bar = self.chart_bar_view.findChild(QChartView).chart()
        chart_bar.removeAllSeries()
        for ax in chart_bar.axes(): chart_bar.removeAxis(ax)
        
        set0 = QBarSet("Surclassements")
        set0.setColor(QColor("#ff6b6b"))
        set0.setBorderColor(Qt.transparent)
        cats = []
        
        sorted_routes = sorted(data['routes'], key=lambda x: x['surclassement'], reverse=True)
        for r in sorted_routes[:10]:
            set0.append(r['surclassement'])
            cats.append(str(r['vol_id']))
            
        series_bar = QBarSeries()
        series_bar.append(set0)
        chart_bar.addSeries(series_bar)
        
        axisX = QBarCategoryAxis(); axisX.append(cats); axisX.setLabelsColor(QColor(COLOR_TEXT_DIM))
        chart_bar.addAxis(axisX, Qt.AlignBottom); series_bar.attachAxis(axisX)
        axisY = QValueAxis(); axisY.setLabelsColor(QColor(COLOR_TEXT_DIM)); 
        chart_bar.addAxis(axisY, Qt.AlignLeft); series_bar.attachAxis(axisY)

        # Liste des vols
        while self.res_container.count():
            w = self.res_container.takeAt(0).widget()
            if w: w.deleteLater()
            
        for r in data['routes']:
            # S'assurer que tous les champs nécessaires sont présents
            if 'satisfaction' not in r:
                r['satisfaction'] = 80  # Valeur par défaut
            self.res_container.addWidget(FlightItem(r))
        
        # Logs
        if 'logs' in data:
            self.logs_text.setPlainText(data['logs'])
            cursor = self.logs_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.logs_text.setTextCursor(cursor)

    def update_network_visualization(self, data):
        avions_data = []
        avions_hours = {}
        
        for route in data['routes']:
            avion_id = route['avion_id']
            if avion_id not in avions_hours:
                avions_hours[avion_id] = 0
            avions_hours[avion_id] += route['duree']
        
        avions_seen = set()
        for route in data['routes']:
            if route['avion_id'] not in avions_seen:
                avions_data.append({
                    'id': route['avion_id'],
                    'type': route['avion'],
                    'hours': avions_hours.get(route['avion_id'], 0)
                })
                avions_seen.add(route['avion_id'])
        
        # Inclure la satisfaction dans les données des vols
        vols_data = []
        for r in data['routes']:
            vol_info = {
                'id': r['vol_id'],
                'route': r['route'],
                'duree': r['duree'],
                'demande_eco': r['demande_eco'],
                'demande_bus': r['demande_bus']
            }
            # Ajouter la satisfaction si disponible
            if 'satisfaction' in r:
                vol_info['satisfaction'] = r['satisfaction']
            vols_data.append(vol_info)
        
        affectations_data = [{
            'avion_id': r['avion_id'],
            'vol_id': r['vol_id'],
            'duree': r['duree'],
            'upgrades': r['surclassement']
        } for r in data['routes']]
        
        self.network_widget.set_data(avions_data, vols_data, affectations_data)
        
        # Statistiques améliorées avec satisfaction
        total_links = len(affectations_data)
        upgrades_count = sum(1 for a in affectations_data if a['upgrades'] > 0)
        
        # Calcul de la satisfaction moyenne
        satisfactions = [r.get('satisfaction', 80) for r in data['routes']]
        avg_satisfaction = sum(satisfactions) / len(satisfactions) if satisfactions else 80
        
        stats_text = f"📊 {len(avions_data)} avions • {len(vols_data)} vols • {total_links} connexions • "
        stats_text += f"😊 Satisfaction: {avg_satisfaction:.1f}/100"
        
        if upgrades_count > 0:
            stats_text += f" • ⚠️ {upgrades_count} vols avec surclassement"
        
        self.lbl_network_stats.setText(stats_text)

    def clear_logs(self):
        self.logs_text.clear()

    def save_logs(self):
        fname, _ = QFileDialog.getSaveFileName(self, "Sauvegarder les logs", "", "Fichiers texte (*.txt);;Tous les fichiers (*)")
        if fname:
            try:
                with open(fname, 'w', encoding='utf-8') as f:
                    f.write(self.logs_text.toPlainText())
                QMessageBox.information(self, "Succès", f"Logs sauvegardés dans:\n{fname}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Erreur de sauvegarde:\n{str(e)}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AirlineApp()
    window.show()
    sys.exit(app.exec())