# frontend.py
import sys
import os
import pandas as pd
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QSpinBox, QDoubleSpinBox, 
                               QPushButton, QTextEdit, QGroupBox, QFormLayout, 
                               QFileDialog, QMessageBox, QTabWidget,
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QSizePolicy, QStyle, QScrollArea, QGridLayout, QFrame,
                               QGraphicsDropShadowEffect, QGraphicsView, QGraphicsScene, 
                               QGraphicsRectItem, QGraphicsEllipseItem, QGraphicsPathItem, 
                               QGraphicsTextItem)
from PySide6.QtGui import (QColor, QPainter, QBrush, QPalette, QLinearGradient, 
                           QPen, QFont, QPainterPath)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtCharts import (QChart, QChartView, QPieSeries, QBarSeries, QBarSet, 
                              QBarCategoryAxis, QValueAxis)

from .backend import solve_model

# --- DESIGN SYSTEM ---
COLOR_BG = "#121218"           # Fond très sombre
COLOR_PANEL = "#1e1e24"        # Fond des cartes
COLOR_ACCENT = "#5c7cfa"       # Bleu principal
COLOR_TEXT_MAIN = "#ffffff"
COLOR_TEXT_DIM = "#878a99"
COLOR_BORDER = "#2a2a35"

STYLESHEET = f"""
QMainWindow {{ background-color: {COLOR_BG}; }}
QWidget {{ font-family: 'Segoe UI', 'Roboto', sans-serif; font-size: 13px; color: {COLOR_TEXT_MAIN}; }}

/* --- TABS --- */
QTabWidget::pane {{ border: none; background: transparent; }}
QTabBar::tab {{
    background: transparent;
    color: {COLOR_TEXT_DIM};
    padding: 12px 24px;
    font-weight: 600;
    font-size: 14px;
    border-bottom: 3px solid transparent;
}}
QTabBar::tab:selected {{ color: {COLOR_ACCENT}; border-bottom: 3px solid {COLOR_ACCENT}; }}
QTabBar::tab:hover:!selected {{ color: #ffffff; }}

/* --- INPUTS --- */
QLineEdit, QSpinBox, QDoubleSpinBox {{
    background-color: #23232a;
    border: 1px solid {COLOR_BORDER};
    border-radius: 6px;
    color: white;
    padding: 8px;
    font-weight: bold;
}}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 1px solid {COLOR_ACCENT};
    background-color: #2a2a32;
}}

/* --- BUTTONS --- */
QPushButton {{
    background-color: #2a2a35;
    color: white;
    border: 1px solid {COLOR_BORDER};
    padding: 10px 15px;
    border-radius: 6px;
    font-weight: 600;
}}
QPushButton:hover {{ background-color: #32323e; border-color: {COLOR_TEXT_DIM}; }}

QPushButton#RunButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4c6ef5, stop:1 #748ffc);
    color: white;
    border: none;
    font-size: 15px;
    padding: 15px;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    border-radius: 8px;
}}
QPushButton#RunButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5c7cfa, stop:1 #91a7ff);
}}

/* --- TABLES --- */
QTableWidget {{
    background-color: {COLOR_PANEL};
    gridline-color: {COLOR_BORDER};
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    outline: none;
}}
QHeaderView::section {{
    background-color: #23232a;
    color: {COLOR_TEXT_DIM};
    padding: 8px;
    border: none;
    font-weight: bold;
    text-transform: uppercase;
    font-size: 11px;
}}
QTableWidget::item {{ padding: 5px; }}
QTableWidget::item:selected {{ background-color: rgba(92, 124, 250, 0.2); }}

/* --- SCROLLBAR --- */
QScrollBar:vertical {{ background: transparent; width: 8px; margin: 0; }}
QScrollBar::handle:vertical {{ background: #3f3f4b; min-height: 20px; border-radius: 4px; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}

/* --- GROUP BOX --- */
QGroupBox {{
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    margin-top: 1.5em;
    padding-top: 10px;
    font-weight: bold;
    color: {COLOR_ACCENT};
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; }}
"""

def apply_shadow(widget, blur=15, alpha=50):
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(blur)
    shadow.setColor(QColor(0, 0, 0, alpha))
    shadow.setOffset(0, 4)
    widget.setGraphicsEffect(shadow)

class CardFrame(QFrame):
    """Conteneur stylisé pour les widgets du dashboard"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            CardFrame {{
                background-color: {COLOR_PANEL};
                border-radius: 12px;
                border: 1px solid {COLOR_BORDER};
            }}
        """)
        apply_shadow(self)

class MetricWidget(CardFrame):
    """Carte KPI animée"""
    def __init__(self, title, unit="", color_accent=COLOR_ACCENT):
        super().__init__()
        self.setMinimumHeight(110)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        header = QHBoxLayout()
        lbl_title = QLabel(title.upper())
        lbl_title.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 11px; font-weight: 700; letter-spacing: 1px; border:none;")
        
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {color_accent}; font-size: 10px; border:none;")
        
        header.addWidget(dot)
        header.addWidget(lbl_title)
        header.addStretch()
        layout.addLayout(header)
        
        row_val = QHBoxLayout()
        self.lbl_val = QLabel("0")
        self.lbl_val.setStyleSheet("color: white; font-size: 32px; font-weight: 600; border:none;")
        
        lbl_unit = QLabel(unit)
        lbl_unit.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 14px; margin-bottom: 6px; border:none;")
        
        row_val.addWidget(self.lbl_val)
        row_val.addWidget(lbl_unit, 0, Qt.AlignBottom)
        row_val.addStretch()
        layout.addLayout(row_val)

    def update_value(self, target):
        self.target = target
        self.current = 0
        self.step = target / 25 if target != 0 else 0
        self.timer = QTimer()
        self.timer.timeout.connect(self._tick)
        self.timer.start(15)

    def _tick(self):
        self.current += self.step
        if (self.step > 0 and self.current >= self.target) or (self.step < 0 and self.current <= self.target) or self.step == 0:
            self.current = self.target
            self.timer.stop()
        
        if isinstance(self.target, int):
            self.lbl_val.setText(f"{int(self.current):,}".replace(",", " "))
        else:
            self.lbl_val.setText(f"{self.current:.1f}")

class RouteItem(CardFrame):
    """Représentation d'une route avec nom complet du mode"""
    def __init__(self, route_data):
        super().__init__()
        self.setFixedHeight(95) # Légèrement plus haut pour le texte complet
        self.setStyleSheet(f"""
            CardFrame {{
                background-color: {COLOR_PANEL};
                border-radius: 8px;
                border: 1px solid {COLOR_BORDER};
            }}
            QLabel {{ border: none; }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # --- Badge Mode (Modifié pour le nom complet) ---
        mode_container = QWidget()
        mode_container.setFixedWidth(110) # Largeur augmentée pour le texte complet
        mode_layout = QVBoxLayout(mode_container)
        mode_layout.setContentsMargins(0,0,0,0)
        mode_layout.setAlignment(Qt.AlignCenter)
        
        mode_full_name = route_data['mode']
        
        # Logique de couleur basée sur le nom
        badge_color = "#9775fa" if "Avion" in mode_full_name else "#4dabf7"
        if "Frigo" in mode_full_name or "Refrig" in mode_full_name:
            badge_color = "#3bc9db" # Cyan pour le froid
            
        lbl_icon = QLabel(mode_full_name.upper()) 
        lbl_icon.setAlignment(Qt.AlignCenter)
        lbl_icon.setWordWrap(True) # Permet le retour à la ligne si le nom est très long
        lbl_icon.setStyleSheet(f"""
            background-color: {badge_color}33; 
            color: {badge_color}; 
            border-radius: 6px; 
            font-weight: 800; 
            font-size: 10px;
            padding: 4px;
        """)
        
        lbl_count = QLabel(f"Unités: {route_data['nb_vehicules']}")
        lbl_count.setAlignment(Qt.AlignCenter)
        lbl_count.setStyleSheet("color: #878a99; font-size: 10px; margin-top:2px;")
        
        mode_layout.addWidget(lbl_icon)
        mode_layout.addWidget(lbl_count)
        layout.addWidget(mode_container)
        
        # --- Reste du trajet (inchangé ou optimisé) ---
        path_layout = QVBoxLayout()
        path_layout.setSpacing(2)
        l_orig = QLabel(f"De : {route_data['origine']}")
        l_orig.setStyleSheet("font-size: 13px; font-weight: bold; color: #adb5bd;")
        l_dest = QLabel(f"À : {route_data['destination']}")
        l_dest.setStyleSheet("font-size: 15px; font-weight: bold; color: white;")
        
        path_layout.addWidget(l_orig)
        path_layout.addWidget(l_dest)
        layout.addLayout(path_layout)
        
        arrow = QLabel("→")
        arrow.setStyleSheet("color: #4dabf7; font-size: 20px; font-weight: bold;")
        layout.addWidget(arrow)
        layout.addSpacing(10)
        
        # Détails produits
        load_layout = QVBoxLayout()
        lbl_load = QLabel("CONTENU")
        lbl_load.setStyleSheet("font-size: 9px; color: #878a99; font-weight: bold; letter-spacing: 1px;")
        
        payload_txt = ", ".join([f"{p['nom']} ({int(p['quantite'])})" for p in route_data['produits']])
        val_load = QLabel(payload_txt)
        val_load.setStyleSheet("color: #dee2e6; font-size: 11px;")
        val_load.setWordWrap(True)
        
        load_layout.addWidget(lbl_load)
        load_layout.addWidget(val_load)
        layout.addLayout(load_layout, 2)

# === NOUVELLE CLASSE POUR LE GRAPHE VISUEL ===
class LogisticsGraphWidget(QGraphicsView):
    """Widget pour dessiner le graphe logistique (Entrepôts -> Zones)"""
    def __init__(self):
        super().__init__()
        self.setScene(QGraphicsScene())
        self.setRenderHint(QPainter.Antialiasing)
        self.setStyleSheet(f"background: {COLOR_PANEL}; border: 1px solid {COLOR_BORDER}; border-radius: 8px;")
        self.setMinimumHeight(300) 
        
    def draw_network(self, routes_data):
        self.scene().clear()
        
        depots = sorted(list(set(r['origine'] for r in routes_data)))
        zones = sorted(list(set(r['destination'] for r in routes_data)))
        
        if not depots or not zones: return

        width = self.width() if self.width() > 0 else 600
        height = self.height() if self.height() > 0 else 280
        margin_x = 100
        margin_y = 50
        
        pos_depots = {}
        pos_zones = {}

        # Dessin Entrepôts
        step_d = (height - 2 * margin_y) / (len(depots) - 1) if len(depots) > 1 else 0
        for i, depot in enumerate(depots):
            y = margin_y + i * step_d if len(depots) > 1 else height / 2
            x = margin_x
            pos_depots[depot] = (x, y)
            
            rect_size = 40
            rect = QGraphicsRectItem(x - rect_size/2, y - rect_size/2, rect_size, rect_size)
            rect.setBrush(QBrush(QColor("#2a2a35")))
            rect.setPen(QPen(QColor(COLOR_ACCENT), 2))
            self.scene().addItem(rect)
            
            text = QGraphicsTextItem(depot)
            text.setDefaultTextColor(QColor("white"))
            text.setFont(QFont("Segoe UI", 8, QFont.Bold))
            text.setPos(x - text.boundingRect().width()/2, y - rect_size/2 - 20)
            self.scene().addItem(text)

        # Dessin Zones
        step_z = (height - 2 * margin_y) / (len(zones) - 1) if len(zones) > 1 else 0
        for i, zone in enumerate(zones):
            y = margin_y + i * step_z if len(zones) > 1 else height / 2
            x = width - margin_x
            pos_zones[zone] = (x, y)
            
            radius = 20
            ellipse = QGraphicsEllipseItem(x - radius, y - radius, radius * 2, radius * 2)
            ellipse.setBrush(QBrush(QColor("#2a1515")))
            ellipse.setPen(QPen(QColor("#ff6b6b"), 2))
            self.scene().addItem(ellipse)
            
            text = QGraphicsTextItem(zone)
            text.setDefaultTextColor(QColor("white"))
            text.setFont(QFont("Segoe UI", 8, QFont.Bold))
            text.setPos(x - text.boundingRect().width()/2, y - radius - 20)
            self.scene().addItem(text)

        # Dessin Lignes
        grouped_routes = {}
        for route in routes_data:
            key = (route['origine'], route['destination'])
            if key not in grouped_routes: grouped_routes[key] = []
            grouped_routes[key].append(route)

        for (u, v), routes in grouped_routes.items():
            start = pos_depots[u]
            end = pos_zones[v]
            
            offset_step = 15
            total_lines = len(routes)
            start_y_base = start[1] - ((total_lines - 1) * offset_step) / 2
            end_y_base = end[1] - ((total_lines - 1) * offset_step) / 2

            for idx, r in enumerate(routes):
                sy = start_y_base + idx * offset_step
                ey = end_y_base + idx * offset_step
                
                path = QPainterPath()
                path.moveTo(start[0] + 20, sy)
                path.lineTo(end[0] - 20, ey)
                
                pen = QPen()
                pen.setWidth(2)
                
                is_frigo = "Frigo" in r['mode'] or "Refrig" in r['mode']
                is_avion = "Avion" in r['mode']
                
                if is_frigo:
                    pen.setColor(QColor("#4dabf7"))
                    pen.setStyle(Qt.SolidLine)
                    label_txt = "Frigo"
                elif is_avion:
                    pen.setColor(QColor("#9775fa"))
                    pen.setStyle(Qt.DotLine)
                    label_txt = "Avion"
                else:
                    pen.setColor(QColor("#878a99"))
                    pen.setStyle(Qt.DashLine)
                    label_txt = "Std"

                line_item = QGraphicsPathItem(path)
                line_item.setPen(pen)
                self.scene().addItem(line_item)
                
                mid_x = (start[0] + end[0]) / 2
                mid_y = (sy + ey) / 2
                
                total_qty = sum(p['quantite'] for p in r['produits'])
                lbl = QGraphicsTextItem(f"{label_txt}\n({int(total_qty)}u)")
                lbl.setFont(QFont("Segoe UI", 7))
                lbl.setDefaultTextColor(pen.color())
                lbl.setPos(mid_x - 10, mid_y - 15)
                self.scene().addItem(lbl)



class LogWidget(CardFrame):
    """Widget pour afficher les logs de l'optimisation"""
    def __init__(self):
        super().__init__()
        self.setMaximumHeight(300)  # Hauteur maximale pour les logs
        self.setMinimumHeight(200)  # Hauteur minimale
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # En-tête
        header = QHBoxLayout()
        lbl_title = QLabel("JOURNAL D'OPTIMISATION")
        lbl_title.setStyleSheet(f"""
            color: {COLOR_TEXT_DIM}; 
            font-weight: bold; 
            font-size: 12px; 
            letter-spacing: 1px;
        """)
        
        self.btn_clear = QPushButton("Effacer")
        self.btn_clear.setFixedSize(70, 25)
        self.btn_clear.setStyleSheet(f"""
            QPushButton {{
                background-color: #2a2a35;
                color: {COLOR_TEXT_DIM};
                border: 1px solid {COLOR_BORDER};
                border-radius: 4px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: #32323e;
                color: white;
            }}
        """)
        
        header.addWidget(lbl_title)
        header.addStretch()
        header.addWidget(self.btn_clear)
        layout.addLayout(header)
        
        # Zone de texte pour les logs
        self.text_log = QTextEdit()
        self.text_log.setReadOnly(True)
        self.text_log.setStyleSheet(f"""
            QTextEdit {{
                background-color: #1a1a20;
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                color: {COLOR_TEXT_MAIN};
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 16px;
                padding: 8px;
            }}
        """)
        self.text_log.setLineWrapMode(QTextEdit.NoWrap)
        
        layout.addWidget(self.text_log)
        
        # Connecter le bouton effacer
        self.btn_clear.clicked.connect(self.clear_logs)
        
        # Initialiser avec un message
        self.add_log("Système initialisé. Prêt pour l'optimisation.")
    
    def add_log(self, message):
        """Ajoute un message aux logs avec horodatage"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        # Garder seulement les 50 derniers logs pour éviter l'accumulation
        current_text = self.text_log.toPlainText()
        lines = current_text.split('\n')
        if len(lines) > 50:
            lines = lines[-50:]
        
        lines.append(log_entry)
        self.text_log.setPlainText('\n'.join(lines))
        
        # Scroll vers le bas
        scrollbar = self.text_log.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def clear_logs(self):
        """Efface tous les logs"""
        self.text_log.clear()
        self.add_log("Journal effacé.")

class ModernLogisticsApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Logistics Optimizer AI")
        self.resize(1400, 900)
        self.setStyleSheet(STYLESHEET)
        
        # --- MODIFICATION ICI : CHEMINS ABSOLUS ---
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))

        self.file_paths = {
            'produits': os.path.join(BASE_DIR, "produits.csv"),
            'vehicules': os.path.join(BASE_DIR, "vehicules_types.csv"),
            'entrepots': os.path.join(BASE_DIR, "entrepots.csv"),
            'demandes': os.path.join(BASE_DIR, "demandes.csv"),
            'transport': os.path.join(BASE_DIR, "transport_couts.csv")
        }
        
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self.create_tab_donnees()
        self.create_tab_unified_dashboard()
        
        self.preview_current_file('demandes')

    def create_tab_donnees(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        left_panel = CardFrame()
        left_panel.setFixedWidth(300)
        vbox_left = QVBoxLayout(left_panel)
        vbox_left.setSpacing(10)
        
        lbl_title = QLabel("SOURCES DE DONNÉES")
        lbl_title.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-weight: bold; margin-bottom: 10px; letter-spacing: 1px;")
        vbox_left.addWidget(lbl_title)
        
        files_map = [
            ("demandes", "Demandes Clients"),
            ("entrepots", "Stocks Entrepôts"),
            ("vehicules", "Types Véhicules"),
            ("produits", "Catalogue Produits"),
            ("transport", "Coûts Transport")
        ]
        
        icon_import = self.style().standardIcon(QStyle.SP_DirOpenIcon)
        icon_view = self.style().standardIcon(QStyle.SP_FileIcon)
        
        for key, name in files_map:
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(5)
            
            btn_view = QPushButton(f"  {name}")
            btn_view.setIcon(icon_view)
            btn_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            btn_view.setCursor(Qt.PointingHandCursor)
            btn_view.setStyleSheet(f"""
                QPushButton {{ 
                    text-align: left; 
                    padding-left: 10px; 
                    background: transparent; 
                    border: 1px solid transparent;
                    color: {COLOR_TEXT_MAIN};
                    border-radius: 4px;
                }}
                QPushButton:hover {{ background: rgba(255,255,255,0.05); color: {COLOR_ACCENT}; }}
            """)
            btn_view.clicked.connect(lambda checked=False, k=key: self.preview_current_file(k))
            
            btn_change = QPushButton()
            btn_change.setIcon(icon_import)
            btn_change.setFixedSize(36, 36)
            btn_change.setCursor(Qt.PointingHandCursor)
            btn_change.setStyleSheet(f"""
                QPushButton {{ 
                    background: #23232a; 
                    border: 1px solid {COLOR_BORDER}; 
                    border-radius: 4px; 
                }}
                QPushButton:hover {{ border-color: {COLOR_ACCENT}; background: #2a2a35; }}
            """)
            btn_change.clicked.connect(lambda checked=False, k=key: self.load_new_file(k))
            
            row_layout.addWidget(btn_view)
            row_layout.addWidget(btn_change)
            vbox_left.addWidget(row_widget)
            
        vbox_left.addStretch()
        layout.addWidget(left_panel)

        right_panel = QVBoxLayout()
        self.lbl_file_name = QLabel("APERÇU")
        self.lbl_file_name.setStyleSheet("font-size: 18px; font-weight: 600; margin-bottom: 10px; color: white;")
        right_panel.addWidget(self.lbl_file_name)
        
        self.table_view = QTableWidget()
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.setFrameShape(QFrame.NoFrame)
        self.table_view.setAlternatingRowColors(False)
        
        table_container = CardFrame()
        l_table = QVBoxLayout(table_container)
        l_table.setContentsMargins(1,1,1,1)
        l_table.addWidget(self.table_view)
        
        right_panel.addWidget(table_container)
        layout.addLayout(right_panel)
        self.tabs.addTab(tab, "DONNÉES")

    def create_tab_unified_dashboard(self):
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # === SIDEBAR ===
        sidebar = CardFrame()
        sidebar.setFixedWidth(320)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        sidebar_layout.setSpacing(15)

        lbl_settings = QLabel("CONFIGURATION")
        lbl_settings.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-weight: bold; letter-spacing: 1px; margin-bottom: 5px;")
        sidebar_layout.addWidget(lbl_settings)

        gb_flotte = QGroupBox("DISPONIBILITÉ Véhicule")
        self.layout_flotte = QFormLayout()
        self.layout_flotte.setLabelAlignment(Qt.AlignLeft)
        gb_flotte.setLayout(self.layout_flotte)
        sidebar_layout.addWidget(gb_flotte)

        gb_params = QGroupBox("PARAMÈTRES")
        l_params = QFormLayout()
        
        self.spin_retard = QDoubleSpinBox()
        self.spin_retard.setRange(0, 99999); self.spin_retard.setValue(500)
        
        self.spin_mesusage = QDoubleSpinBox()
        self.spin_mesusage.setRange(0, 99999); self.spin_mesusage.setValue(50)
        
        l_params.addRow("Pénalité Retard (€)", self.spin_retard)
        l_params.addRow("Pénalité Mésusage", self.spin_mesusage)
        gb_params.setLayout(l_params)
        sidebar_layout.addWidget(gb_params)

        sidebar_layout.addStretch()

        self.btn_run = QPushButton("LANCER L'OPTIMISATION")
        self.btn_run.setObjectName("RunButton")
        self.btn_run.setCursor(Qt.PointingHandCursor)
        self.btn_run.setMinimumHeight(60)
        self.btn_run.clicked.connect(self.run_optimization)
        sidebar_layout.addWidget(self.btn_run)

        main_layout.addWidget(sidebar)

        # === RÉSULTATS ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        
        content_res = QWidget()
        res_layout = QVBoxLayout(content_res)
        res_layout.setContentsMargins(0, 0, 10, 0)
        res_layout.setSpacing(25)

        head_layout = QHBoxLayout()
        title = QLabel("Tableau de Bord")
        title.setStyleSheet("font-size: 24px; font-weight: 700; color: white;")
        
        self.lbl_status = QLabel("Prêt à optimiser")
        self.lbl_status.setStyleSheet("color: #878a99; font-style: italic; font-weight: bold;")
        
        head_layout.addWidget(title)
        head_layout.addStretch()
        head_layout.addWidget(self.lbl_status)
        res_layout.addLayout(head_layout)

        # KPIs
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(20)
        self.kpi_cout = MetricWidget("Coût Total", "EUR", "#fcc419")
        self.kpi_service = MetricWidget("Taux Service", "%", "#51cf66")
        self.kpi_routes = MetricWidget("Routes", "Total", "#5c7cfa")
        self.kpi_flotte = MetricWidget("Véhicules", "Actifs", "#cc5de8")
        
        kpi_layout.addWidget(self.kpi_cout)
        kpi_layout.addWidget(self.kpi_service)
        kpi_layout.addWidget(self.kpi_routes)
        kpi_layout.addWidget(self.kpi_flotte)
        res_layout.addLayout(kpi_layout)

        # Charts
        charts_row = QHBoxLayout()
        charts_row.setSpacing(20)
        
        self.chart_pie_view = self.create_chart_view("Répartition Véhicule")
        real_chart_view = self.chart_pie_view.findChild(QChartView)
        self.pie_series = QPieSeries()
        real_chart_view.chart().addSeries(self.pie_series)
        
        self.chart_bar_view = self.create_chart_view("Volumes par Produit")
        
        charts_row.addWidget(self.chart_pie_view)
        charts_row.addWidget(self.chart_bar_view)
        res_layout.addLayout(charts_row)

        # --- GRAPH VIEW INTEGRATION ---
        lbl_graph = QLabel("VISUALISATION DU RÉSEAU")
        lbl_graph.setStyleSheet(f"color: #878a99; font-weight: bold; margin-top: 15px; letter-spacing: 1px;")
        res_layout.addWidget(lbl_graph)

        self.network_view = LogisticsGraphWidget()
        res_layout.addWidget(self.network_view)
        # -----------------------------

        # Liste Routes
        lbl_plan = QLabel("PLAN DE TRANSPORT DÉTAILLÉ")
        lbl_plan.setStyleSheet(f"color: #878a99; font-weight: bold; margin-top: 10px; letter-spacing: 1px;")
        res_layout.addWidget(lbl_plan)
        
        self.routes_container = QWidget()
        self.routes_layout = QVBoxLayout(self.routes_container)
        self.routes_layout.setSpacing(10)
        self.routes_layout.setContentsMargins(0,0,0,0)
        
        self.lbl_placeholder = QLabel("Aucune donnée. Configurez les paramètres à gauche et cliquez sur 'Lancer'.")
        self.lbl_placeholder.setAlignment(Qt.AlignCenter)
        self.lbl_placeholder.setStyleSheet(f"color: {COLOR_BORDER}; font-size: 16px; margin: 40px;")
        self.routes_layout.addWidget(self.lbl_placeholder)

        res_layout.addWidget(self.routes_container)
                # --- SECTION LOGS ---
        lbl_logs = QLabel("JOURNAL DU SYSTÈME")
        lbl_logs.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-weight: bold; margin-top: 20px; letter-spacing: 1px;")
        res_layout.addWidget(lbl_logs)
        
        self.log_widget = LogWidget()
        res_layout.addWidget(self.log_widget)
        # --------------------
        
        res_layout.addStretch()

        scroll.setWidget(content_res)
        main_layout.addWidget(scroll, 1)

        self.refresh_flotte_inputs()
        self.tabs.addTab(tab, "OPTIMISATION & ANALYSE")
        self.log_display = QTextEdit()

        

    def create_chart_view(self, title):
        container = CardFrame()
        layout = QVBoxLayout(container)
        lbl = QLabel(title)
        lbl.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-weight: bold; font-size: 12px; margin-bottom: 5px;")
        layout.addWidget(lbl)
        chart = QChart()
        chart.setBackgroundBrush(Qt.NoBrush)
        chart.layout().setContentsMargins(0, 0, 0, 0)
        chart.legend().setVisible(False)
        view = QChartView(chart)
        view.setRenderHint(QPainter.Antialiasing)
        view.setStyleSheet("background: transparent;")
        view.setMinimumHeight(250)
        layout.addWidget(view)
        return container

    def preview_current_file(self, key):
        self.lbl_file_name.setText(f"FICHIER : {key.upper()}.CSV")
        path = self.file_paths.get(key)
        if path and os.path.exists(path):
            try:
                df = pd.read_csv(path)
                self.table_view.clear()
                self.table_view.setRowCount(df.shape[0])
                self.table_view.setColumnCount(df.shape[1])
                self.table_view.setHorizontalHeaderLabels(df.columns)
                for i in range(df.shape[0]):
                    for j in range(df.shape[1]):
                        item = QTableWidgetItem(str(df.iloc[i, j]))
                        item.setForeground(QBrush(QColor(COLOR_TEXT_MAIN)))
                        self.table_view.setItem(i, j, item)
            except Exception as e:
                pass
                
    def load_new_file(self, key):
        fname, _ = QFileDialog.getOpenFileName(self, "Ouvrir CSV", "", "CSV (*.csv)")
        if fname:
            self.file_paths[key] = fname
            self.preview_current_file(key)
            if key == 'vehicules': self.refresh_flotte_inputs()

    def refresh_flotte_inputs(self):
        while self.layout_flotte.count():
            item = self.layout_flotte.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        self.spin_flotte = {}
        path = self.file_paths['vehicules']
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
                for mode in df["ID_Mode"].unique():
                    sp = QSpinBox()
                    sp.setRange(0, 9999); sp.setValue(10)
                    self.spin_flotte[mode] = sp
                    self.layout_flotte.addRow(mode, sp)
            except: pass

    def run_optimization(self):
        self.btn_run.setText("CALCUL EN COURS...")
        self.btn_run.setEnabled(False)
        self.lbl_status.setText("Optimisation en cours...")
        self.lbl_status.setStyleSheet("color: #fcc419;")
        QApplication.processEvents()
        
        # Ajouter log de début
        if self.log_widget:
            self.log_widget.add_log("Démarrage de l'optimisation...")
            self.log_widget.add_log(f"Paramètres: Retard={self.spin_retard.value()}€, Mésusage={self.spin_mesusage.value()}€")
        
        try:
            flotte = {m: s.value() for m, s in self.spin_flotte.items()}
            penalites = {'Retard': self.spin_retard.value(), 'Mesusage': self.spin_mesusage.value()}
            
            # Log de la flotte
            if self.log_widget:
                fleet_str = ", ".join([f"{k}: {v}" for k, v in flotte.items()])
                self.log_widget.add_log(f"Flotte configurée: {fleet_str}")
            
            result = solve_model({'flotte': flotte, 'penalites': penalites}, self.file_paths)
            
            # Log du résultat
            if self.log_widget:
                if result["status"] == "optimal":
                    self.log_widget.add_log(f"Optimisation terminée avec succès (coût: {result['cout_total']:.2f}€)")
                    self.log_widget.add_log(f"Statistiques: {result['metriques']['taux_satisfaction']:.1f}% satisfaction, {result['metriques']['nb_routes']} routes")
                else:
                    self.log_widget.add_log(f"Échec de l'optimisation: {result.get('message', 'Raison inconnue')}")
            
            self.update_dashboard(result)
            
        except Exception as e:
            # Log de l'erreur
            if self.log_widget:
                self.log_widget.add_log(f"ERREUR: {str(e)}")
            
            QMessageBox.critical(self, "Erreur Critique", f"Une erreur est survenue pendant l'optimisation :\n{str(e)}")
            self.lbl_status.setText("Erreur Système")
            self.lbl_status.setStyleSheet("color: #ff6b6b;")
        
        finally:
            self.btn_run.setText("LANCER L'OPTIMISATION")
            self.btn_run.setEnabled(True)

    def update_dashboard(self, result):
        if hasattr(self, 'lbl_placeholder') and self.lbl_placeholder:
            self.lbl_placeholder.deleteLater()
            self.lbl_placeholder = None

        if result["status"] != "optimal":
            QMessageBox.warning(self, "Attention", f"Résultat non optimal :\n{result.get('message', 'Inconnu')}")
            self.lbl_status.setText("Non Optimal / Erreur")
            self.lbl_status.setStyleSheet("color: #ff6b6b;")
            return
            
        self.lbl_status.setText("✅ Optimisation Terminée")
        # Ajouter un log de fin
        if self.log_widget:
            m = result["metriques"]
            self.log_widget.add_log(f"Résultats finaux: {m['livraisons_totales']:.0f} unités livrées, {m['manques_totaux']:.0f} manques")
            self.log_widget.add_log(f"Utilisation véhicules: {sum(v['utilise'] for v in result['utilisation_vehicules'].values())} / {sum(v['disponible'] for v in result['utilisation_vehicules'].values())}")
        self.lbl_status.setStyleSheet("color: #51cf66;")
        
        m = result["metriques"]
        self.kpi_cout.update_value(int(result['cout_total']))
        self.kpi_service.update_value(m['taux_satisfaction'])
        self.kpi_routes.update_value(m['nb_routes'])
        self.kpi_flotte.update_value(m['nb_vehicules_total'])
        
        # Pie Chart
        self.pie_series.clear()
        colors = ["#4dabf7", "#748ffc", "#9775fa", "#faa2c1"]
        idx = 0
        for mode, data in result["utilisation_vehicules"].items():
            if data["utilise"] > 0:
                label = f"{mode} ({int(data['utilise'])})"
                sl = self.pie_series.append(label, data["utilise"])
                sl.setLabelVisible(True)
                sl.setLabelColor(QColor("white"))
                sl.setColor(QColor(colors[idx % len(colors)]))
                idx += 1
        
        # Bar Chart
        chart = self.chart_bar_view.findChild(QChartView).chart()
        chart.removeAllSeries()
        for ax in chart.axes(): chart.removeAxis(ax)
        
        prod_qty = {}
        for r in result["routes"]:
            for p in r["produits"]:
                prod_qty[p["nom"]] = prod_qty.get(p["nom"], 0) + p["quantite"]
        
        if prod_qty:
            set0 = QBarSet("Quantité")
            set0.setColor(QColor(COLOR_ACCENT))
            set0.setBorderColor(Qt.transparent)
            
            cats = []
            for k, v in sorted(prod_qty.items(), key=lambda x:x[1], reverse=True)[:5]:
                set0.append(v)
                cats.append(k)
                
            series = QBarSeries()
            series.append(set0)
            chart.addSeries(series)
            
            axisX = QBarCategoryAxis()
            axisX.append(cats)
            axisX.setLabelsColor(QColor(COLOR_TEXT_DIM))
            chart.addAxis(axisX, Qt.AlignBottom)
            series.attachAxis(axisX)
            
            axisY = QValueAxis()
            axisY.setLabelsColor(QColor(COLOR_TEXT_DIM))
            chart.addAxis(axisY, Qt.AlignLeft)
            series.attachAxis(axisY)

        # --- UPDATE DU GRAPHE VISUEL ---
        if "routes" in result:
            self.network_view.draw_network(result["routes"])

        # Update Routes List
        while self.routes_layout.count():
            w = self.routes_layout.takeAt(0).widget()
            if w: w.deleteLater()
            
        if result["manques"]:
            w = QFrame()
            w.setStyleSheet("background: #2a1515; border: 1px solid #e03131; border-radius: 6px; padding: 10px;")
            l = QVBoxLayout(w)
            l.addWidget(QLabel("⚠️ DEMANDE NON SATISFAISANTE", styleSheet="color: #ff6b6b; font-weight: bold;"))
            for mk in result["manques"]:
                 l.addWidget(QLabel(f"• {mk['produit']} @ {mk['zone']} : -{mk['quantite']}", styleSheet="color: #ffa8a8;"))
            self.routes_layout.addWidget(w)

        for r in result["routes"]:
            self.routes_layout.addWidget(RouteItem(r))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModernLogisticsApp()
    window.show()
    sys.exit(app.exec())
    HumanitarianApp = ModernLogisticsApp
