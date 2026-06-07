# frontend/telecoms.py - VERSION OPTIMISÉE SANS FOND SATELLITE
import sys
import os
import pandas as pd
import math
import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QLabel, QSpinBox, QDoubleSpinBox, 
                               QPushButton, QTextEdit, QGroupBox, QFormLayout, 
                               QFileDialog, QMessageBox, QTabWidget,
                               QTableWidget, QTableWidgetItem, QHeaderView, 
                               QSizePolicy, QStyle, QScrollArea, QGridLayout, QFrame,
                               QGraphicsDropShadowEffect, QGraphicsView, QGraphicsScene)
from PySide6.QtGui import (QColor, QPainter, QBrush, QPalette, QLinearGradient, 
                           QPen, QFont, QPainterPath)
from PySide6.QtCore import Qt, QTimer, QSize, QPointF, QMargins, QRectF

from Nour_Besrour.backend.telecoms_backend import solve_telecom_model

# --- DESIGN SYSTEM ---
COLOR_BG = "#121218"
COLOR_PANEL = "#1e1e24"
COLOR_ACCENT = "#5c7cfa"
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

/* --- TEXT EDIT --- */
QTextEdit {{
    background-color: #0f0f13;
    border: 1px solid {COLOR_BORDER};
    border-radius: 8px;
    color: #ced4da;
    font-family: 'Consolas', monospace;
    font-size: 12px;
}}

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
        
        # En-tête avec puce couleur
        header = QHBoxLayout()
        lbl_title = QLabel(title.upper())
        lbl_title.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 11px; font-weight: 700; letter-spacing: 1px; border:none;")
        
        dot = QLabel("●")
        dot.setStyleSheet(f"color: {color_accent}; font-size: 10px; border:none;")
        
        header.addWidget(dot)
        header.addWidget(lbl_title)
        header.addStretch()
        layout.addLayout(header)
        
        # Valeur centrale
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

class TelecomsOptimizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Telecom Network Optimizer AI")
        self.resize(1400, 900)
        self.setStyleSheet(STYLESHEET)
    
        self.file_paths = {
            'antennes': "antennes.csv",
            'frequences': "frequences.csv",
            'interferences': "interferences.csv"
        }
    
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
    
        self.create_tab_donnees()
        self.create_tab_unified_dashboard()
    
        self.preview_current_file('antennes')

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
            ("antennes", "Antennes"),
            ("frequences", "Fréquences"),
            ("interferences", "Interférences")
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
            btn_change.setToolTip(f"Changer le fichier {name}...")
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
        info_lbl = QLabel("Cliquez sur le dossier pour remplacer un fichier CSV.")
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 11px; font-style: italic; margin-top: 10px;")
        vbox_left.addWidget(info_lbl)
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
        """Crée le tableau de bord unifié avec carte géographique et logs intégrés"""
        tab = QWidget()
        main_layout = QHBoxLayout(tab)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # === COLONNE DE GAUCHE : CONTRÔLES ===
        sidebar = CardFrame()
        sidebar.setFixedWidth(320)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        sidebar_layout.setSpacing(15)

        lbl_settings = QLabel("CONFIGURATION")
        lbl_settings.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-weight: bold; letter-spacing: 1px; margin-bottom: 5px;")
        sidebar_layout.addWidget(lbl_settings)

        # Groupe Paramètres
        gb_params = QGroupBox("PARAMÈTRES")
        l_params = QFormLayout()

        self.spin_budget = QDoubleSpinBox()
        self.spin_budget.setRange(0, 1e7)
        self.spin_budget.setValue(10000)
        self.spin_budget.setSuffix(" €")

        self.spin_alpha = QDoubleSpinBox()
        self.spin_alpha.setRange(0, 1000)
        self.spin_alpha.setValue(0)

        l_params.addRow("Budget Total", self.spin_budget)
        l_params.addRow("Pénalité Fréquences (α)", self.spin_alpha)
        gb_params.setLayout(l_params)
        sidebar_layout.addWidget(gb_params)

        sidebar_layout.addStretch()

        # Bouton Run
        self.btn_run = QPushButton("LANCER L'OPTIMISATION")
        self.btn_run.setObjectName("RunButton")
        self.btn_run.setCursor(Qt.PointingHandCursor)
        self.btn_run.setMinimumHeight(60)
        self.btn_run.clicked.connect(self.run_optimization)
        sidebar_layout.addWidget(self.btn_run)

        main_layout.addWidget(sidebar)

        # === COLONNE DE DROITE : RÉSULTATS, CARTE ET LOGS ===
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        content_res = QWidget()
        res_layout = QVBoxLayout(content_res)
        res_layout.setContentsMargins(0, 0, 10, 0)
        res_layout.setSpacing(25)

        # En-tête Résultats
        head_layout = QHBoxLayout()
        title = QLabel("Tableau de Bord")
        title.setStyleSheet("font-size: 24px; font-weight: 700; color: white;")

        self.lbl_status = QLabel("Prêt à optimiser")
        self.lbl_status.setStyleSheet("color: #878a99; font-style: italic; font-weight: bold;")

        head_layout.addWidget(title)
        head_layout.addStretch()
        head_layout.addWidget(self.lbl_status)
        res_layout.addLayout(head_layout)

        # 1. Cartes KPIs
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(20)
        self.kpi_cout = MetricWidget("Coût Total", "EUR", "#fcc419")
        self.kpi_antennes = MetricWidget("Antennes", "Total", "#5c7cfa")
        self.kpi_frequences = MetricWidget("Fréquences", "Utilisées", "#51cf66")
        self.kpi_budget = MetricWidget("Budget", "Restant", "#cc5de8")

        kpi_layout.addWidget(self.kpi_cout)
        kpi_layout.addWidget(self.kpi_antennes)
        kpi_layout.addWidget(self.kpi_frequences)
        kpi_layout.addWidget(self.kpi_budget)
        res_layout.addLayout(kpi_layout)

        # 2. Carte Géographique avec NOUVELLE DISPOSITION
        map_header = QHBoxLayout()
        lbl_map = QLabel("CARTE DES ANTENNES")
        lbl_map.setStyleSheet(f"color: #878a99; font-weight: bold; margin-top: 10px; letter-spacing: 1px;")

        self.lbl_map_status = QLabel("En attente d'optimisation...")
        self.lbl_map_status.setStyleSheet("color: #878a99; font-style: italic;")

        map_header.addWidget(lbl_map)
        map_header.addStretch()
        map_header.addWidget(self.lbl_map_status)
        res_layout.addLayout(map_header)

        # Conteneur principal de la carte avec NOUVELLE DISPOSITION HORIZONTALE
        map_main_container = CardFrame()
        map_main_layout = QHBoxLayout(map_main_container)
        map_main_layout.setContentsMargins(15, 15, 15, 15)
        map_main_layout.setSpacing(20)

        # === COLONNE GAUCHE : LÉGENDE + CONTRÔLES ===
        left_controls = QWidget()
        left_controls.setFixedWidth(280)
        left_layout = QVBoxLayout(left_controls)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(20)

        # 1. LÉGENDE (en haut à gauche)
        legend_card = CardFrame()
        legend_card_layout = QVBoxLayout(legend_card)
        legend_card_layout.setContentsMargins(12, 12, 12, 12)
        
        lbl_legend = QLabel("LÉGENDE DES FRÉQUENCES")
        lbl_legend.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        legend_card_layout.addWidget(lbl_legend)

        self.legend_container = QWidget()
        self.legend_layout = QVBoxLayout(self.legend_container)
        self.legend_layout.setSpacing(5)
        self.legend_layout.setContentsMargins(0, 8, 0, 0)

        # Placeholder pour la légende
        placeholder = QLabel("Aucune fréquence assignée")
        placeholder.setStyleSheet(f"color: {COLOR_BORDER}; font-size: 10px; font-style: italic;")
        self.legend_layout.addWidget(placeholder)

        legend_card_layout.addWidget(self.legend_container)
        left_layout.addWidget(legend_card)

        # 2. CONTRÔLES CARTE (en bas à gauche)
        controls_card = CardFrame()
        controls_card_layout = QVBoxLayout(controls_card)
        controls_card_layout.setContentsMargins(12, 12, 12, 12)
        controls_card_layout.setSpacing(10)
        
        lbl_controls = QLabel("CONTRÔLES DE VUE")
        lbl_controls.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 11px; font-weight: bold; letter-spacing: 1px;")
        controls_card_layout.addWidget(lbl_controls)

        # Boutons de contrôle de la carte
        btn_style = f"""
            QPushButton {{
                background-color: #23232a;
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
            }}
            QPushButton:hover {{
                background-color: #2a2a35;
                border-color: {COLOR_ACCENT};
            }}
        """

        self.btn_zoom_in = QPushButton("🔍 Zoom +")
        self.btn_zoom_in.setCursor(Qt.PointingHandCursor)
        self.btn_zoom_in.clicked.connect(self.zoom_in_map)
        self.btn_zoom_in.setStyleSheet(btn_style)

        self.btn_zoom_out = QPushButton("🔍 Zoom -")
        self.btn_zoom_out.setCursor(Qt.PointingHandCursor)
        self.btn_zoom_out.clicked.connect(self.zoom_out_map)
        self.btn_zoom_out.setStyleSheet(btn_style)

        self.btn_reset_view = QPushButton("↺ Réinitialiser")
        self.btn_reset_view.setCursor(Qt.PointingHandCursor)
        self.btn_reset_view.clicked.connect(self.reset_map_view)
        self.btn_reset_view.setStyleSheet(btn_style)

        controls_card_layout.addWidget(self.btn_zoom_in)
        controls_card_layout.addWidget(self.btn_zoom_out)
        controls_card_layout.addWidget(self.btn_reset_view)
        
        left_layout.addWidget(controls_card)
        left_layout.addStretch()

        map_main_layout.addWidget(left_controls)

        # === COLONNE DROITE : CARTE GRAPHIQUE (GRANDE) ===
        map_card = CardFrame()
        map_card_layout = QVBoxLayout(map_card)
        map_card_layout.setContentsMargins(0, 0, 0, 0)

        # Scene graphique pour la carte
        self.map_scene = QGraphicsScene()
        self.map_scene.setBackgroundBrush(QColor(COLOR_PANEL))
        
        # View pour afficher la scène
        self.map_view = QGraphicsView(self.map_scene)
        self.map_view.setRenderHint(QPainter.Antialiasing)
        self.map_view.setRenderHint(QPainter.SmoothPixmapTransform)
        self.map_view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.map_view.setStyleSheet("border: 1px solid " + COLOR_BORDER + "; border-radius: 8px;")
        self.map_view.setMinimumHeight(500)

        # Variables pour le zoom
        self.map_zoom = 1.0

        map_card_layout.addWidget(self.map_view)
        map_main_layout.addWidget(map_card, 1)

        res_layout.addWidget(map_main_container, 1)

                # 3. SECTION DÉTAILS DE L'OPTIMISATION (TABLEAUX) ⭐ AGGRANDIE ⭐
        details_header = QHBoxLayout()
        lbl_details = QLabel("RÉSULTATS DÉTAILLÉS")
        lbl_details.setStyleSheet(f"""
            color: {COLOR_TEXT_DIM}; 
            font-weight: bold; 
            font-size: 16px;
            margin-top: 20px; 
            letter-spacing: 1px;
        """)
        details_header.addWidget(lbl_details)
        details_header.addStretch()
        res_layout.addLayout(details_header)

        # Conteneur principal pour les tableaux - HAUTEUR AUGMENTÉE
        details_container = CardFrame()
        details_container.setMinimumHeight(500)  # Augmenté de 300 à 500 pixels
        details_layout = QVBoxLayout(details_container)
        details_layout.setContentsMargins(15, 15, 15, 15)
        details_layout.setSpacing(15)

        # Tabs pour organiser les différents tableaux - STYLE AMÉLIORÉ
        self.details_tabs = QTabWidget()
        self.details_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 2px solid {COLOR_BORDER};
                border-radius: 8px;
                background: {COLOR_PANEL};
                margin-top: 0px;
            }}
            QTabBar::tab {{
                background: #23232a;
                color: {COLOR_TEXT_DIM};
                padding: 12px 25px;
                font-weight: 600;
                font-size: 13px;
                border: 1px solid {COLOR_BORDER};
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 3px;
            }}
            QTabBar::tab:selected {{ 
                background: {COLOR_PANEL}; 
                color: {COLOR_ACCENT}; 
                border-bottom: 3px solid {COLOR_ACCENT};
                font-weight: 700;
            }}
            QTabBar::tab:hover:!selected {{ 
                color: white; 
                background: #2a2a35; 
            }}
            QTabBar::tab:first {{ margin-left: 5px; }}
        """)

        # TAB 1: Allocation des Antennes - TABLEAU PLUS GRAND
        allocation_widget = QWidget()
        allocation_layout = QVBoxLayout(allocation_widget)
        allocation_layout.setContentsMargins(0, 0, 0, 0)
        self.table_allocation = self.create_styled_table()
        self.table_allocation.setMinimumHeight(350)  # Hauteur augmentée
        allocation_layout.addWidget(self.table_allocation)
        self.details_tabs.addTab(allocation_widget, "Allocation par Antenne")

        # TAB 2: Statistiques par Fréquence
        frequencies_widget = QWidget()
        frequencies_layout = QVBoxLayout(frequencies_widget)
        frequencies_layout.setContentsMargins(0, 0, 0, 0)
        self.table_frequencies = self.create_styled_table()
        self.table_frequencies.setMinimumHeight(350)
        frequencies_layout.addWidget(self.table_frequencies)
        self.details_tabs.addTab(frequencies_widget, "Analyse par Fréquence")

        # TAB 3: Analyse Budgétaire
        budget_widget = QWidget()
        budget_layout = QVBoxLayout(budget_widget)
        budget_layout.setContentsMargins(0, 0, 0, 0)
        self.table_budget = self.create_styled_table()
        self.table_budget.setMinimumHeight(350)
        budget_layout.addWidget(self.table_budget)
        self.details_tabs.addTab(budget_widget, "Analyse Budgétaire")

        # TAB 4: Interférences
        interferences_widget = QWidget()
        interferences_layout = QVBoxLayout(interferences_widget)
        interferences_layout.setContentsMargins(0, 0, 0, 0)
        self.table_interferences = self.create_styled_table()
        self.table_interferences.setMinimumHeight(350)
        interferences_layout.addWidget(self.table_interferences)
        self.details_tabs.addTab(interferences_widget, "Matrice d'Interférences")

        details_layout.addWidget(self.details_tabs)
        res_layout.addWidget(details_container, 2)  # Facteur d'expansion augmenté à 2


        # 4. LOGS GUROBI
        logs_header = QHBoxLayout()
        lbl_logs = QLabel("LOGS DU MODÈLE GUROBI")
        lbl_logs.setStyleSheet(f"color: #878a99; font-weight: bold; margin-top: 20px; letter-spacing: 1px;")

        log_buttons = QHBoxLayout()
        log_buttons.setSpacing(10)
        
        self.btn_clear_logs = QPushButton("Effacer les logs")
        self.btn_clear_logs.setCursor(Qt.PointingHandCursor)
        self.btn_clear_logs.setStyleSheet(f"""
            QPushButton {{
                background-color: #23232a;
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                padding: 6px 12px;
                color: white;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: #2a2a35;
                border-color: {COLOR_ACCENT};
            }}
        """)
        self.btn_clear_logs.clicked.connect(self.clear_logs)
        
        self.btn_save_logs = QPushButton("Sauvegarder")
        self.btn_save_logs.setCursor(Qt.PointingHandCursor)
        self.btn_save_logs.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLOR_ACCENT};
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                color: white;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #6c8cff;
            }}
        """)
        self.btn_save_logs.clicked.connect(self.save_logs)
        
        log_buttons.addStretch()
        log_buttons.addWidget(self.btn_clear_logs)
        log_buttons.addWidget(self.btn_save_logs)
        
        logs_header.addWidget(lbl_logs)
        logs_header.addStretch()
        logs_header.addLayout(log_buttons)
        res_layout.addLayout(logs_header)

        logs_container = CardFrame()
        logs_container.setMinimumHeight(400)
        logs_layout = QVBoxLayout(logs_container)
        logs_layout.setContentsMargins(10, 10, 10, 10)
        
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setStyleSheet(f"""
            QTextEdit {{
                background-color: #0a0a0d;
                border: 1px solid {COLOR_BORDER};
                border-radius: 6px;
                color: #e9ecef;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 11px;
                padding: 10px;
            }}
        """)
        
        import datetime
        init_log = f"""
{'='*70}
TELECOM NETWORK OPTIMIZER AI - LOGS GUROBI
Initialisé le: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*70}

En attente de l'exécution du modèle...
        """
        self.logs_text.setText(init_log)
        
        logs_layout.addWidget(self.logs_text)
        res_layout.addWidget(logs_container, 2)

        scroll.setWidget(content_res)
        main_layout.addWidget(scroll, 1)

        self.tabs.addTab(tab, "OPTIMISATION & ANALYSE")
    
    def create_styled_table(self):
        """Crée un tableau stylisé avec les bonnes configurations"""
        table = QTableWidget()
        table.verticalHeader().setVisible(False)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.horizontalHeader().setStretchLastSection(True)
        table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLOR_PANEL};
                gridline-color: {COLOR_BORDER};
                border: none;
                border-radius: 6px;
            }}
            QTableWidget::item {{
                padding: 8px;
                color: {COLOR_TEXT_MAIN};
            }}
            QTableWidget::item:selected {{
                background-color: rgba(92, 124, 250, 0.3);
            }}
            QTableWidget::item:alternate {{
                background-color: #1a1a20;
            }}
            QHeaderView::section {{
                background-color: #23232a;
                color: {COLOR_TEXT_DIM};
                padding: 10px;
                border: none;
                font-weight: bold;
                text-transform: uppercase;
                font-size: 11px;
            }}
        """)
        return table
    
    def clear_logs(self):
        """Efface les logs"""
        self.logs_text.clear()
        init_log = f"""
{'='*70}
TELECOM NETWORK OPTIMIZER AI - LOGS GUROBI
Initialisé le: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*70}

Logs effacés.
        """
        self.logs_text.setText(init_log)
    
    def save_logs(self):
        """Sauvegarde les logs dans un fichier"""
        fname, _ = QFileDialog.getSaveFileName(
            self, "Sauvegarder les logs", "", 
            "Fichiers texte (*.txt);;Tous les fichiers (*)"
        )
        if fname:
            try:
                with open(fname, 'w', encoding='utf-8') as f:
                    f.write(self.logs_text.toPlainText())
                QMessageBox.information(self, "Succès", f"Logs sauvegardés dans {fname}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible de sauvegarder : {str(e)}")
   
    def generate_color_from_string(self, text):
        """Génère une couleur cohérente à partir d'une chaîne de texte"""
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_int = int(hash_obj.hexdigest()[:8], 16)

        # Générer des couleurs vives pour une bonne visibilité
        r = (hash_int & 0xFF) % 200 + 55
        g = ((hash_int >> 8) & 0xFF) % 200 + 55
        b = ((hash_int >> 16) & 0xFF) % 200 + 55

        return f"#{r:02x}{g:02x}{b:02x}"

    def draw_map(self, antennes_details):
        """Dessine la carte avec les antennes - VERSION ULTRA MODERNE"""
        if not hasattr(self, 'map_scene') or self.map_scene is None:
            print("ERREUR: map_scene n'a pas été initialisé")
            self.lbl_map_status.setText("Erreur: carte non initialisée")
            return
        
        self.map_scene.clear()

        if not antennes_details:
            self.lbl_map_status.setText("Aucune donnée de position disponible")
            return
        
        # 🌐 FOND DE CARTE AVEC GRILLE TECHNOLOGIQUE
        self.draw_tech_grid_background()

        # Vérifier si nous avons des coordonnées valides
        has_coords = any(ant['x'] != 0 or ant['y'] != 0 for ant in antennes_details)

        # Générer des positions en cercle si pas de coordonnées
        if not has_coords:
            for i, ant in enumerate(antennes_details):
                angle = 2 * math.pi * i / len(antennes_details)
                radius = 250  # Augmenté pour plus d'espace
                ant['x'] = radius * math.cos(angle)
                ant['y'] = radius * math.sin(angle)

        # Normaliser les coordonnées pour l'affichage
        xs = [ant['x'] for ant in antennes_details]
        ys = [ant['y'] for ant in antennes_details]

        min_x, max_x = min(xs), max(xs) if xs else (0, 1)
        min_y, max_y = min(ys), max(ys) if ys else (0, 1)

        # Échelle pour l'affichage - augmentée pour meilleure visibilité
        range_x = max_x - min_x if max_x != min_x else 1
        range_y = max_y - min_y if max_y != min_y else 1
        scale = min(300 / range_x, 300 / range_y) if range_x > 0 and range_y > 0 else 60

        # 🎨 PALETTE DE COULEURS INSPIRÉE DU PIE CHART (Bleus et Violets dégradés)
        colors_pie_inspired = {
            'FR1': '#748ffc',  # Bleu moyen-clair (du pie)
            'FR2': '#5c7cfa',  # Bleu principal (du pie)
            'FR3': '#4c6ef5',  # Bleu foncé (du pie)
            'CH1': '#4dabf7',  # Cyan clair
            'CH2': '#339af0',  # Cyan moyen
            'CH3': '#228be6',  # Cyan foncé
            'GSM': '#91a7ff',  # Bleu très clair
            'UMTS': '#6c8cff', # Bleu-violet clair
            'LTE': '#5c7cfa',  # Bleu principal
            '5G': '#4c6ef5'    # Bleu intense
        }

        # Créer la légende avec les nouvelles couleurs
        self.update_legend(antennes_details, colors_pie_inspired)

        # 📍 DESSINER LES ZONES D'INFLUENCE AVEC ANIMATION VISUELLE
        for ant in antennes_details:
            x = (ant['x'] - min_x) * scale
            y = (ant['y'] - min_y) * scale
            freq = ant['frequence']
            base_color = colors_pie_inspired.get(freq, self.generate_color_from_string(freq))
            
            # ZONE D'INFLUENCE EXTERNE (très subtile)
            outer_halo_color = QColor(base_color)
            outer_halo_color.setAlpha(15)
            outer_halo = self.map_scene.addEllipse(x - 60, y - 60, 120, 120)
            outer_halo.setBrush(outer_halo_color)
            outer_halo.setPen(QPen(QColor(base_color), 1, Qt.DotLine))
            outer_halo.setZValue(-3)
            outer_halo.setOpacity(0.4)
            
            # ZONE DE COUVERTURE MOYENNE
            mid_halo_color = QColor(base_color)
            mid_halo_color.setAlpha(40)
            mid_halo = self.map_scene.addEllipse(x - 35, y - 35, 70, 70)
            mid_halo.setBrush(mid_halo_color)
            mid_halo.setPen(QPen(QColor(base_color), 1.5, Qt.DashLine))
            mid_halo.setZValue(-2)
            mid_halo.setOpacity(0.6)
            
            # ZONE DE COUVERTURE INTERNE (la plus forte)
            inner_halo_color = QColor(base_color)
            inner_halo_color.setAlpha(60)
            inner_halo = self.map_scene.addEllipse(x - 22, y - 22, 44, 44)
            inner_halo.setBrush(inner_halo_color)
            inner_halo.setPen(QPen(Qt.NoPen))
            inner_halo.setZValue(-1)

        # 🔴 DESSINER LES INTERFÉRENCES EN PREMIER (sous les antennes)
        interference_count = 0
        try:
            if os.path.exists(self.file_paths['interferences']):
                edges_df = pd.read_csv(self.file_paths['interferences'])
                
                edge_cols = []
                for col in edges_df.columns:
                    if col.lower() in ['ant1', 'ant2', 'node1', 'node2', 'source', 'target']:
                        edge_cols.append(col)
                
                if len(edge_cols) >= 2:
                    col1, col2 = edge_cols[0], edge_cols[1]
                else:
                    col1 = edges_df.columns[0] if len(edges_df.columns) > 0 else None
                    col2 = edges_df.columns[1] if len(edges_df.columns) > 1 else None
                
                if col1 and col2:
                    for _, row in edges_df.iterrows():
                        ant1 = str(row[col1])
                        ant2 = str(row[col2])
                        
                        pos1 = next((ant for ant in antennes_details if str(ant['id']) == ant1), None)
                        pos2 = next((ant for ant in antennes_details if str(ant['id']) == ant2), None)
                        
                        if pos1 and pos2:
                            interference_count += 1
                            x1 = (pos1['x'] - min_x) * scale
                            y1 = (pos1['y'] - min_y) * scale
                            x2 = (pos2['x'] - min_x) * scale
                            y2 = (pos2['y'] - min_y) * scale
                            
                            # LIGNE D'INTERFÉRENCE AVEC EFFET GLOW DOUBLE
                            # Couche de glow externe (plus épaisse et transparente)
                            glow_outer = QPen(QColor("#ff6b6b"), 6, Qt.SolidLine)
                            glow_outer.setCapStyle(Qt.RoundCap)
                            line_outer = self.map_scene.addLine(x1, y1, x2, y2, glow_outer)
                            line_outer.setZValue(0)
                            line_outer.setOpacity(0.2)
                            
                            # Couche principale
                            glow_pen = QPen(QColor("#ff4757"), 2.5, Qt.DashLine)
                            glow_pen.setCapStyle(Qt.RoundCap)
                            glow_pen.setDashPattern([8, 4])  # Pattern personnalisé
                            line = self.map_scene.addLine(x1, y1, x2, y2, glow_pen)
                            line.setZValue(1)
                            line.setOpacity(0.85)
                            
                            # Points aux extrémités pour marquer l'interférence
                            for px, py in [(x1, y1), (x2, y2)]:
                                marker = self.map_scene.addEllipse(px - 4, py - 4, 8, 8)
                                marker.setBrush(QColor("#ff4757"))
                                marker.setPen(QPen(QColor("white"), 1.5))
                                marker.setZValue(2)
                            
                            line.setToolTip(f"""
                            <div style="background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2d1f1f, stop:1 #1e1414); 
                                        color: white; padding: 15px; border-radius: 10px; border: 2px solid #ff6b6b;">
                            <div style="text-align: center; margin-bottom: 8px;">
                                <b style="color: #ff6b6b; font-size: 16px;">⚠ CONFLIT DE FRÉQUENCE</b>
                            </div>
                            <hr style="border: none; border-top: 1px solid #ff6b6b44; margin: 8px 0;"/>
                            <table style="width: 100%; color: #adb5bd; font-size: 12px;">
                                <tr>
                                    <td><b>Antenne 1:</b></td>
                                    <td style="color: white; font-weight: bold;">{ant1}</td>
                                </tr>
                                <tr>
                                    <td><b>Antenne 2:</b></td>
                                    <td style="color: white; font-weight: bold;">{ant2}</td>
                                </tr>
                                <tr>
                                    <td colspan="2" style="padding-top: 8px;">
                                        <span style="color: #fcc419; font-weight: bold;">⚡ Même fréquence interdite</span>
                                    </td>
                                </tr>
                            </table>
                            </div>
                            """)
        except Exception as e:
            print(f"Erreur lors du chargement des interférences: {e}")

        # 📡 DESSINER LES ANTENNES AVEC DESIGN PREMIUM
        for ant in antennes_details:
            x = (ant['x'] - min_x) * scale
            y = (ant['y'] - min_y) * scale
            freq = ant['frequence']
            base_color = colors_pie_inspired.get(freq, self.generate_color_from_string(freq))

            # EFFET DE PULSATION (cercle externe animé)
            pulse_circle = self.map_scene.addEllipse(x - 24, y - 24, 48, 48)
            pulse_color = QColor(base_color)
            pulse_color.setAlpha(80)
            pulse_circle.setBrush(pulse_color)
            pulse_circle.setPen(QPen(QColor(base_color), 2, Qt.DotLine))
            pulse_circle.setZValue(2)
            pulse_circle.setOpacity(0.4)

            # ANNEAU EXTÉRIEUR (bordure épaisse blanche)
            outer_ring = self.map_scene.addEllipse(x - 20, y - 20, 40, 40)
            outer_ring.setBrush(QColor("#23232a"))  # Fond panel
            outer_ring.setPen(QPen(QColor("white"), 3))
            outer_ring.setZValue(3)
            
            # CERCLE PRINCIPAL (antenne colorée avec gradient)
            main_circle = self.map_scene.addEllipse(x - 16, y - 16, 32, 32)
            color = QColor(base_color)
            
            # Gradient radial pour effet 3D brillant
            gradient = QLinearGradient(x - 16, y - 16, x + 16, y + 16)
            gradient.setColorAt(0, color.lighter(140))
            gradient.setColorAt(0.5, color)
            gradient.setColorAt(1, color.darker(120))
            
            main_circle.setBrush(QBrush(gradient))
            main_circle.setPen(QPen(color.darker(140), 2))
            main_circle.setZValue(4)

            # ANNEAU INTÉRIEUR (surbrillance)
            inner_highlight = self.map_scene.addEllipse(x - 10, y - 10, 20, 20)
            highlight_color = QColor(base_color)
            highlight_color.setAlpha(100)
            inner_highlight.setBrush(highlight_color.lighter(180))
            inner_highlight.setPen(QPen(Qt.NoPen))
            inner_highlight.setZValue(5)
            inner_highlight.setOpacity(0.6)

            # POINT CENTRAL (core)
            center_core = self.map_scene.addEllipse(x - 4, y - 4, 8, 8)
            center_core.setBrush(QColor("white"))
            center_core.setPen(QPen(color.darker(150), 1))
            center_core.setZValue(6)

            # ICÔNE DE SIGNAL (3 barres au-dessus de l'antenne)
            signal_base_y = y - 32
            for i, height in enumerate([6, 10, 14]):
                bar_x = x - 8 + (i * 6)
                bar = self.map_scene.addRect(bar_x, signal_base_y - height, 4, height)
                bar.setBrush(QColor(base_color))
                bar.setPen(QPen(Qt.NoPen))
                bar.setZValue(7)
                bar.setOpacity(0.7)

            # TEXTE ID (style moderne sous l'antenne)
            ant_id = str(ant['id'])
            display_id = ant_id if len(ant_id) <= 5 else ant_id[:4] + ".."
            
            # Fond pour le texte (badge arrondi avec QPainterPath)
            from PySide6.QtGui import QPainterPath
            badge_path = QPainterPath()
            badge_rect = QRectF(x - 22, y + 26, 44, 18)
            badge_path.addRoundedRect(badge_rect, 4, 4)
            
            text_bg = self.map_scene.addPath(badge_path)
            text_bg.setBrush(QColor(base_color))
            text_bg.setPen(QPen(Qt.NoPen))
            text_bg.setZValue(8)
            text_bg.setOpacity(0.9)
            
            # Texte blanc sur fond coloré
            text = self.map_scene.addText(display_id)
            text.setDefaultTextColor(QColor("white"))
            font = QFont("Segoe UI", 8, QFont.Bold)
            text.setFont(font)
            text.setPos(x - text.boundingRect().width()/2, y + 28)
            text.setZValue(9)

            # Tooltip PREMIUM avec design ultra-moderne
            demande_value = ant.get('demande', 'N/A')
            demande_bar = ""
            if isinstance(demande_value, (int, float)) and demande_value != 'N/A':
                demande_pct = min(int((demande_value / 10) * 100), 100)  # Normaliser sur 10
                demande_bar = f"""
                <div style="margin-top: 8px;">
                    <div style="background: #2a2a35; border-radius: 4px; height: 6px; overflow: hidden;">
                        <div style="background: {base_color}; height: 100%; width: {demande_pct}%;"></div>
                    </div>
                </div>
                """
            
            tooltip = f"""
            <div style="background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1e1e24, stop:1 #121218); 
                        color: white; padding: 18px; border-radius: 12px; 
                        border: 3px solid {base_color}; min-width: 220px;
                        box-shadow: 0 8px 32px rgba(0,0,0,0.4);">
                <div style="text-align: center; margin-bottom: 12px;">
                    <div style="display: inline-block; background: {base_color}33; 
                                padding: 8px 16px; border-radius: 20px; border: 2px solid {base_color};">
                        <b style="color: {base_color}; font-size: 18px;">📡 {ant['id']}</b>
                    </div>
                </div>
                <hr style="border: none; border-top: 2px solid {base_color}44; margin: 12px 0;"/>
                <table style="width: 100%; color: #adb5bd; font-size: 13px; line-height: 1.8;">
                    <tr>
                        <td style="padding: 4px 0;"><b style="color: #878a99;">Fréquence:</b></td>
                        <td style="text-align: right;">
                            <span style="color: {base_color}; font-weight: bold; 
                                        background: {base_color}22; padding: 3px 10px; 
                                        border-radius: 8px; border: 1px solid {base_color};">
                                {freq}
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 4px 0;"><b style="color: #878a99;">Coût:</b></td>
                        <td style="color: #fcc419; font-weight: bold; text-align: right;">
                            {ant['cout']:.0f} €
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 4px 0;"><b style="color: #878a99;">Demande:</b></td>
                        <td style="color: #51cf66; font-weight: bold; text-align: right;">
                            {demande_value}
                        </td>
                    </tr>
                    {demande_bar}
                    <tr>
                        <td style="padding: 4px 0;"><b style="color: #878a99;">Position:</b></td>
                        <td style="color: #5c7cfa; text-align: right; font-family: monospace;">
                            ({ant['x']:.1f}, {ant['y']:.1f})
                        </td>
                    </tr>
                </table>
                <div style="margin-top: 12px; text-align: center; color: {base_color}; 
                            font-size: 11px; opacity: 0.7;">
                    ● ZONE DE COUVERTURE ACTIVE ●
                </div>
            </div>
            """
            main_circle.setToolTip(tooltip)
            outer_ring.setToolTip(tooltip)
            text_bg.setToolTip(tooltip)
            text.setToolTip(tooltip)

        # Mettre à jour le statut en haut (remplace update_map_stats)
        if interference_count > 0:
            self.lbl_map_status.setText(f"✅ {len(antennes_details)} antennes | ⚠ {interference_count} interférences")
            self.lbl_map_status.setStyleSheet("color: #fcc419; font-weight: bold;")
        else:
            self.lbl_map_status.setText(f"✅ {len(antennes_details)} antennes | Aucune interférence")
            self.lbl_map_status.setStyleSheet("color: #51cf66; font-weight: bold;")

        # Ajuster la vue avec marges
        if antennes_details:
            rect = self.map_scene.sceneRect()
            # Ajouter des marges pour ne pas couper les éléments
            margin = 80
            self.map_scene.setSceneRect(
                rect.x() - margin, 
                rect.y() - margin, 
                rect.width() + 2*margin, 
                rect.height() + 2*margin
            )
            self.map_view.fitInView(self.map_scene.sceneRect(), Qt.KeepAspectRatio)
            self.map_zoom = 1.0

    def draw_tech_grid_background(self):
        """Dessine un fond de carte avec grille technologique subtile"""
        # Définir une zone de grille large
        grid_size = 1000
        grid_spacing = 50
        
        # Grille principale (lignes fines)
        pen_main = QPen(QColor(COLOR_BORDER), 0.5, Qt.SolidLine)
        for i in range(-grid_size, grid_size, grid_spacing):
            # Lignes verticales
            line = self.map_scene.addLine(i, -grid_size, i, grid_size, pen_main)
            line.setZValue(-10)
            line.setOpacity(0.3)
            # Lignes horizontales
            line = self.map_scene.addLine(-grid_size, i, grid_size, i, pen_main)
            line.setZValue(-10)
            line.setOpacity(0.3)
        
        # Grille secondaire (lignes plus épaisses tous les 200px)
        pen_secondary = QPen(QColor(COLOR_ACCENT), 1, Qt.SolidLine)
        for i in range(-grid_size, grid_size, grid_spacing * 4):
            line = self.map_scene.addLine(i, -grid_size, i, grid_size, pen_secondary)
            line.setZValue(-9)
            line.setOpacity(0.15)
            line = self.map_scene.addLine(-grid_size, i, grid_size, i, pen_secondary)
            line.setZValue(-9)
            line.setOpacity(0.15)
        
        # Cercles concentriques au centre (effet radar)
        center_x, center_y = 0, 0
        for radius in [100, 200, 300, 400]:
            circle = self.map_scene.addEllipse(
                center_x - radius, center_y - radius, 
                radius * 2, radius * 2
            )
            circle.setPen(QPen(QColor(COLOR_ACCENT), 1, Qt.DashLine))
            circle.setBrush(Qt.NoBrush)
            circle.setZValue(-8)
            circle.setOpacity(0.1)

    def update_legend(self, antennes_details, colors):
        """Met à jour la légende des fréquences - VERSION AMÉLIORÉE"""
        # Nettoyer la légende existante
        while self.legend_layout.count():
            item = self.legend_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Compter les fréquences utilisées
        freq_count = {}
        for ant in antennes_details:
            freq = ant['frequence']
            freq_count[freq] = freq_count.get(freq, 0) + 1

        # Trier par utilisation décroissante
        for freq, count in sorted(freq_count.items(), key=lambda x: x[1], reverse=True):
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(5, 3, 5, 3)
            row_layout.setSpacing(10)

            # Container pour le carré de couleur avec bordure
            color_container = QFrame()
            color_container.setFixedSize(20, 20)
            color = colors.get(freq, self.generate_color_from_string(freq))
            color_container.setStyleSheet(f"""
                QFrame {{
                    background-color: {color};
                    border: 2px solid white;
                    border-radius: 4px;
                }}
            """)

            # Texte avec meilleure typographie
            label = QLabel(f"<b>{freq}</b> · {count} antenne{'s' if count > 1 else ''}")
            label.setStyleSheet(f"""
                color: white; 
                font-size: 11px; 
                font-weight: normal; 
                border: none;
                padding-left: 5px;
            """)

            # Badge avec le pourcentage
            total = len(antennes_details)
            pct = (count / total * 100) if total > 0 else 0
            badge = QLabel(f"{pct:.0f}%")
            badge.setStyleSheet(f"""
                background-color: {color}33;
                color: {color};
                border: 1px solid {color};
                border-radius: 8px;
                padding: 2px 8px;
                font-size: 10px;
                font-weight: bold;
            """)
            badge.setFixedHeight(20)

            row_layout.addWidget(color_container)
            row_layout.addWidget(label, 1)
            row_layout.addWidget(badge)

            # Effet hover
            row.setStyleSheet("""
                QWidget:hover {
                    background-color: rgba(255, 255, 255, 0.05);
                    border-radius: 4px;
                }
            """)

            self.legend_layout.addWidget(row)

        # Ajouter un espace en bas
        self.legend_layout.addStretch()
      
    def zoom_in_map(self):
        """Zoom in sur la carte"""
        if hasattr(self, 'map_view') and self.map_view:
            self.map_zoom *= 1.2
            self.map_view.scale(1.2, 1.2)

    def zoom_out_map(self):
        """Zoom out sur la carte"""
        if hasattr(self, 'map_view') and self.map_view:
            self.map_zoom /= 1.2
            self.map_view.scale(1/1.2, 1/1.2)

    def reset_map_view(self):
        """Réinitialise la vue de la carte"""
        if hasattr(self, 'map_view') and self.map_view:
            self.map_view.resetTransform()
            self.map_zoom = 1.0
            if hasattr(self, 'map_scene'):
                self.map_view.fitInView(self.map_scene.sceneRect(), Qt.KeepAspectRatio)

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

    def run_optimization(self):
        # Vérification des fichiers
        if None in self.file_paths.values() or not all(os.path.exists(p) for p in self.file_paths.values()):
            QMessageBox.warning(self, "Erreur", "Veuillez charger tous les fichiers CSV nécessaires.")
            return
            
        # Feedback visuel
        self.btn_run.setText("CALCUL EN COURS...")
        self.btn_run.setEnabled(False)
        self.lbl_status.setText("Optimisation en cours...")
        self.lbl_status.setStyleSheet("color: #fcc419;")
        QApplication.processEvents()
        
        try:
            params = {
                'budget': self.spin_budget.value(),
                'alpha': self.spin_alpha.value()
            }
            
            # Ajouter un log de début dans l'interface
            self.logs_text.append(f"\n{'='*70}")
            self.logs_text.append(f"DÉBUT DE L'OPTIMISATION - {datetime.datetime.now().strftime('%H:%M:%S')}")
            self.logs_text.append(f"Paramètres: Budget={params['budget']}€, α={params['alpha']}")
            self.logs_text.append(f"{'='*70}\n")
            
            result = solve_telecom_model(params, self.file_paths)
            self.update_dashboard(result)
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur Critique", f"Une erreur est survenue pendant l'optimisation :\n{str(e)}")
            self.lbl_status.setText("Erreur Système")
            self.lbl_status.setStyleSheet("color: #ff6b6b;")
            
            # Ajouter l'erreur aux logs
            self.logs_text.append(f"<span style='color: #ff6b6b; font-weight: bold;'>❌ ERREUR: {str(e)}</span>")
            self.logs_text.append(f"\n{'='*70}\n")
        
        finally:
            self.btn_run.setText("LANCER L'OPTIMISATION")
            self.btn_run.setEnabled(True)
    
    def update_dashboard(self, result):
        if result["status"] != "optimal":
            QMessageBox.warning(self, "Attention", f"Résultat non optimal :\n{result.get('message', 'Inconnu')}")
            self.lbl_status.setText("Non Optimal / Erreur")
            self.lbl_status.setStyleSheet("color: #ff6b6b;")
            
            # Afficher les logs même en cas d'erreur
            if "gurobi_logs" in result:
                self.update_gurobi_logs(result["gurobi_logs"], is_error=True)
            return

        self.lbl_status.setText("Optimisation Terminée")
        self.lbl_status.setStyleSheet("color: #51cf66;")

        m = result["metriques"]
        self.kpi_cout.update_value(int(result['cout_total']))
        self.kpi_antennes.update_value(m['nb_antennes'])
        self.kpi_frequences.update_value(m['nb_frequences_utilisees'])

        budget_restant = self.spin_budget.value() - result['cout_total']
        self.kpi_budget.update_value(int(max(0, budget_restant)))

        # DESSINER LA CARTE
        if 'antennes_details' in result and result['antennes_details']:
            self.draw_map(result['antennes_details'])
        else:
            antennes_details = []
            for ant_id, freq in result["solution"].items():
                antennes_details.append({
                    'id': ant_id,
                    'frequence': freq,
                    'cout': 0,
                    'x': 0,
                    'y': 0,
                    'demande': 1
                })
            self.draw_map(antennes_details)
        
        # METTRE À JOUR LES TABLEAUX DÉTAILLÉS
        self.update_detailed_tables(result)

        # Afficher les logs Gurobi
        if "gurobi_logs" in result:
            self.update_gurobi_logs(result["gurobi_logs"], is_error=False)
    
    def update_gurobi_logs(self, logs, is_error=False):
        """Met à jour l'affichage des logs Gurobi"""
        self.logs_text.append("\n" + "="*70)
        self.logs_text.append(f"📊 RÉSULTATS DE L'OPTIMISATION - {datetime.datetime.now().strftime('%H:%M:%S')}")
        self.logs_text.append("="*70 + "\n")
        
        for log_entry in logs:
            # Appliquer un style différent selon le type de message
            if log_entry.startswith("ERREUR:") or is_error:
                self.logs_text.append(f"<span style='color: #ff6b6b; font-weight: bold;'>❌ {log_entry}</span>")
            elif "INITIALISATION" in log_entry or "FIN" in log_entry or "STATUT:" in log_entry:
                self.logs_text.append(f"<span style='color: #5c7cfa; font-weight: bold;'>📋 {log_entry}</span>")
            elif "DÉBUT" in log_entry or "OPTIMISATION" in log_entry:
                self.logs_text.append(f"<span style='color: #fcc419; font-weight: bold;'>⚡ {log_entry}</span>")
            elif "STATISTIQUES" in log_entry:
                self.logs_text.append(f"<span style='color: #51cf66; font-weight: bold;'>📊 {log_entry}</span>")
            elif "Optimal solution found" in log_entry:
                self.logs_text.append(f"<span style='color: #51cf66; font-weight: bold; font-size: 12px;'>✅ {log_entry}</span>")
            elif "Solution count" in log_entry:
                self.logs_text.append(f"<span style='color: #fcc419; font-weight: bold;'>📈 {log_entry}</span>")
            else:
                self.logs_text.append(f"<span style='color: #e9ecef;'>• {log_entry}</span>")
        
        # Ajouter un séparateur
        self.logs_text.append("\n" + "="*70)
        
        # Faire défiler jusqu'au bas
        self.logs_text.verticalScrollBar().setValue(
            self.logs_text.verticalScrollBar().maximum()
        )
    
    def update_detailed_tables(self, result):
        """Met à jour tous les tableaux détaillés avec les résultats de l'optimisation"""
        if result["status"] != "optimal":
            return
        
        self.populate_allocation_table(result)
        self.populate_frequency_analysis_table(result)
        self.populate_budget_analysis_table(result)
        self.populate_interference_matrix_table(result)

    def populate_allocation_table(self, result):
        """Remplit le tableau d'allocation des antennes"""
        antennes = result['antennes_details']
        
        self.table_allocation.clear()
        self.table_allocation.setRowCount(len(antennes))
        self.table_allocation.setColumnCount(6)
        
        headers = ["ID Antenne", "Fréquence", "Demande", "Coût (€)", "Position X", "Position Y"]
        self.table_allocation.setHorizontalHeaderLabels(headers)
        
        antennes_sorted = sorted(antennes, key=lambda x: str(x['id']))
        
        for row, ant in enumerate(antennes_sorted):
            item_id = QTableWidgetItem(str(ant['id']))
            item_id.setTextAlignment(Qt.AlignCenter)
            self.table_allocation.setItem(row, 0, item_id)
            
            freq = ant['frequence']
            item_freq = QTableWidgetItem(f"  {freq}")
            item_freq.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            color = self.generate_color_from_string(freq)
            item_freq.setForeground(QBrush(QColor(color)))
            item_freq.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table_allocation.setItem(row, 1, item_freq)
            
            item_demand = QTableWidgetItem(str(ant['demande']))
            item_demand.setTextAlignment(Qt.AlignCenter)
            self.table_allocation.setItem(row, 2, item_demand)
            
            item_cost = QTableWidgetItem(f"{ant['cout']:.2f}")
            item_cost.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_cost.setForeground(QBrush(QColor("#fcc419")))
            self.table_allocation.setItem(row, 3, item_cost)
            
            item_x = QTableWidgetItem(f"{ant['x']:.2f}")
            item_x.setTextAlignment(Qt.AlignCenter)
            self.table_allocation.setItem(row, 4, item_x)
            
            item_y = QTableWidgetItem(f"{ant['y']:.2f}")
            item_y.setTextAlignment(Qt.AlignCenter)
            self.table_allocation.setItem(row, 5, item_y)
        
        self.table_allocation.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_allocation.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

    def populate_frequency_analysis_table(self, result):
        """Remplit le tableau d'analyse par fréquence"""
        antennes = result['antennes_details']
        
        freq_stats = {}
        for ant in antennes:
            freq = ant['frequence']
            if freq not in freq_stats:
                freq_stats[freq] = {
                    'count': 0,
                    'total_demand': 0,
                    'total_cost': 0,
                    'cost_per_unit': ant['cout']
                }
            freq_stats[freq]['count'] += 1
            freq_stats[freq]['total_demand'] += ant['demande']
            freq_stats[freq]['total_cost'] = ant['cout']
        
        self.table_frequencies.clear()
        self.table_frequencies.setRowCount(len(freq_stats))
        self.table_frequencies.setColumnCount(6)
        
        headers = ["Fréquence", "Nb Antennes", "Demande Totale", "Coût Unitaire", "% Antennes", "% Demande"]
        self.table_frequencies.setHorizontalHeaderLabels(headers)
        
        total_antennes = len(antennes)
        total_demand = sum(ant['demande'] for ant in antennes)
        
        sorted_freqs = sorted(freq_stats.items(), key=lambda x: x[1]['count'], reverse=True)
        
        for row, (freq, stats) in enumerate(sorted_freqs):
            item_freq = QTableWidgetItem(freq)
            item_freq.setTextAlignment(Qt.AlignCenter)
            color = self.generate_color_from_string(freq)
            item_freq.setForeground(QBrush(QColor(color)))
            item_freq.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table_frequencies.setItem(row, 0, item_freq)
            
            item_count = QTableWidgetItem(str(stats['count']))
            item_count.setTextAlignment(Qt.AlignCenter)
            item_count.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table_frequencies.setItem(row, 1, item_count)
            
            item_demand = QTableWidgetItem(str(stats['total_demand']))
            item_demand.setTextAlignment(Qt.AlignCenter)
            self.table_frequencies.setItem(row, 2, item_demand)
            
            item_cost = QTableWidgetItem(f"{stats['cost_per_unit']:.2f} €")
            item_cost.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_cost.setForeground(QBrush(QColor("#fcc419")))
            self.table_frequencies.setItem(row, 3, item_cost)
            
            pct_antennes = (stats['count'] / total_antennes * 100) if total_antennes > 0 else 0
            item_pct_ant = QTableWidgetItem(f"{pct_antennes:.1f}%")
            item_pct_ant.setTextAlignment(Qt.AlignCenter)
            item_pct_ant.setForeground(QBrush(QColor("#5c7cfa")))
            self.table_frequencies.setItem(row, 4, item_pct_ant)
            
            pct_demand = (stats['total_demand'] / total_demand * 100) if total_demand > 0 else 0
            item_pct_dem = QTableWidgetItem(f"{pct_demand:.1f}%")
            item_pct_dem.setTextAlignment(Qt.AlignCenter)
            item_pct_dem.setForeground(QBrush(QColor("#51cf66")))
            self.table_frequencies.setItem(row, 5, item_pct_dem)
        
        self.table_frequencies.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

    def populate_budget_analysis_table(self, result):
        """Remplit le tableau d'analyse budgétaire"""
        budget_total = self.spin_budget.value()
        cout_total = result['cout_total']
        budget_restant = budget_total - cout_total
        
        antennes = result['antennes_details']
        
        freq_costs = {}
        for ant in antennes:
            freq = ant['frequence']
            if freq not in freq_costs:
                freq_costs[freq] = ant['cout']
        
        self.table_budget.clear()
        self.table_budget.setRowCount(len(freq_costs) + 4)
        self.table_budget.setColumnCount(4)
        
        headers = ["Catégorie", "Montant (€)", "% Budget", "Statut"]
        self.table_budget.setHorizontalHeaderLabels(headers)
        
        row = 0
        
        for freq, cost in sorted(freq_costs.items(), key=lambda x: x[1], reverse=True):
            pct = (cost / budget_total * 100) if budget_total > 0 else 0
            
            item_freq = QTableWidgetItem(f"Fréquence {freq}")
            color = self.generate_color_from_string(freq)
            item_freq.setForeground(QBrush(QColor(color)))
            item_freq.setFont(QFont("Segoe UI", 10, QFont.Bold))
            self.table_budget.setItem(row, 0, item_freq)
            
            item_cost = QTableWidgetItem(f"{cost:.2f}")
            item_cost.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table_budget.setItem(row, 1, item_cost)
            
            item_pct = QTableWidgetItem(f"{pct:.2f}%")
            item_pct.setTextAlignment(Qt.AlignCenter)
            self.table_budget.setItem(row, 2, item_pct)
            
            item_status = QTableWidgetItem("✓ Alloué")
            item_status.setTextAlignment(Qt.AlignCenter)
            item_status.setForeground(QBrush(QColor("#51cf66")))
            self.table_budget.setItem(row, 3, item_status)
            
            row += 1
        
        for col in range(4):
            item = QTableWidgetItem("")
            item.setBackground(QBrush(QColor(COLOR_BORDER)))
            self.table_budget.setItem(row, col, item)
        row += 1
        
        item_total = QTableWidgetItem("COÛT TOTAL")
        item_total.setFont(QFont("Segoe UI", 11, QFont.Bold))
        item_total.setForeground(QBrush(QColor("#fcc419")))
        self.table_budget.setItem(row, 0, item_total)
        
        item_total_val = QTableWidgetItem(f"{cout_total:.2f}")
        item_total_val.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        item_total_val.setFont(QFont("Segoe UI", 11, QFont.Bold))
        item_total_val.setForeground(QBrush(QColor("#fcc419")))
        self.table_budget.setItem(row, 1, item_total_val)
        
        pct_used = (cout_total / budget_total * 100) if budget_total > 0 else 0
        item_pct_used = QTableWidgetItem(f"{pct_used:.2f}%")
        item_pct_used.setTextAlignment(Qt.AlignCenter)
        item_pct_used.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.table_budget.setItem(row, 2, item_pct_used)
        row += 1
        
        item_rest = QTableWidgetItem("BUDGET RESTANT")
        item_rest.setFont(QFont("Segoe UI", 11, QFont.Bold))
        item_rest.setForeground(QBrush(QColor("#5c7cfa")))
        self.table_budget.setItem(row, 0, item_rest)
        
        item_rest_val = QTableWidgetItem(f"{budget_restant:.2f}")
        item_rest_val.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        item_rest_val.setFont(QFont("Segoe UI", 11, QFont.Bold))
        item_rest_val.setForeground(QBrush(QColor("#5c7cfa")))
        self.table_budget.setItem(row, 1, item_rest_val)
        
        pct_rest = (budget_restant / budget_total * 100) if budget_total > 0 else 0
        item_pct_rest = QTableWidgetItem(f"{pct_rest:.2f}%")
        item_pct_rest.setTextAlignment(Qt.AlignCenter)
        item_pct_rest.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.table_budget.setItem(row, 2, item_pct_rest)
        row += 1
        
        item_budget = QTableWidgetItem("BUDGET TOTAL")
        item_budget.setFont(QFont("Segoe UI", 11, QFont.Bold))
        item_budget.setForeground(QBrush(QColor("#cc5de8")))
        self.table_budget.setItem(row, 0, item_budget)
        
        item_budget_val = QTableWidgetItem(f"{budget_total:.2f}")
        item_budget_val.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        item_budget_val.setFont(QFont("Segoe UI", 11, QFont.Bold))
        item_budget_val.setForeground(QBrush(QColor("#cc5de8")))
        self.table_budget.setItem(row, 1, item_budget_val)
        
        item_100 = QTableWidgetItem("100.00%")
        item_100.setTextAlignment(Qt.AlignCenter)
        item_100.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.table_budget.setItem(row, 2, item_100)
        
        self.table_budget.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table_budget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table_budget.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table_budget.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

    def populate_interference_matrix_table(self, result):
        """Remplit le tableau de la matrice d'interférences"""
        try:
            if not os.path.exists(self.file_paths['interferences']):
                self.table_interferences.clear()
                self.table_interferences.setRowCount(1)
                self.table_interferences.setColumnCount(1)
                self.table_interferences.setItem(0, 0, QTableWidgetItem("Aucun fichier d'interférences"))
                return
            
            edges_df = pd.read_csv(self.file_paths['interferences'])
            solution = result['solution']
            
            edge_cols = []
            for col in edges_df.columns:
                if col.lower() in ['ant1', 'ant2', 'node1', 'node2', 'source', 'target']:
                    edge_cols.append(col)
            
            if len(edge_cols) < 2:
                edge_cols = [edges_df.columns[0], edges_df.columns[1]]
            
            col1, col2 = edge_cols[0], edge_cols[1]
            
            interference_data = []
            conflicts_avoided = 0
            
            for _, row in edges_df.iterrows():
                ant1 = str(row[col1])
                ant2 = str(row[col2])
                
                if ant1 in solution and ant2 in solution:
                    freq1 = solution[ant1]
                    freq2 = solution[ant2]
                    
                    is_conflict = (freq1 == freq2)
                    if not is_conflict:
                        conflicts_avoided += 1
                    
                    interference_data.append({
                        'ant1': ant1,
                        'ant2': ant2,
                        'freq1': freq1,
                        'freq2': freq2,
                        'conflict': is_conflict
                    })
            
            self.table_interferences.clear()
            self.table_interferences.setRowCount(len(interference_data) + 2)
            self.table_interferences.setColumnCount(5)
            
            headers = ["Antenne 1", "Antenne 2", "Fréquence 1", "Fréquence 2", "Statut"]
            self.table_interferences.setHorizontalHeaderLabels(headers)
            
            summary_text = f"RÉSUMÉ: {conflicts_avoided}/{len(interference_data)} conflits évités"
            item_summary = QTableWidgetItem(summary_text)
            item_summary.setFont(QFont("Segoe UI", 11, QFont.Bold))
            item_summary.setForeground(QBrush(QColor("#51cf66")))
            item_summary.setTextAlignment(Qt.AlignCenter)
            self.table_interferences.setItem(0, 0, item_summary)
            self.table_interferences.setSpan(0, 0, 1, 5)
            
            for col in range(5):
                item = QTableWidgetItem("")
                item.setBackground(QBrush(QColor(COLOR_BORDER)))
                self.table_interferences.setItem(1, col, item)
            
            for row, data in enumerate(interference_data, start=2):
                item_ant1 = QTableWidgetItem(data['ant1'])
                item_ant1.setTextAlignment(Qt.AlignCenter)
                self.table_interferences.setItem(row, 0, item_ant1)
                
                item_ant2 = QTableWidgetItem(data['ant2'])
                item_ant2.setTextAlignment(Qt.AlignCenter)
                self.table_interferences.setItem(row, 1, item_ant2)
                
                item_freq1 = QTableWidgetItem(data['freq1'])
                item_freq1.setTextAlignment(Qt.AlignCenter)
                color1 = self.generate_color_from_string(data['freq1'])
                item_freq1.setForeground(QBrush(QColor(color1)))
                item_freq1.setFont(QFont("Segoe UI", 9, QFont.Bold))
                self.table_interferences.setItem(row, 2, item_freq1)
                
                item_freq2 = QTableWidgetItem(data['freq2'])
                item_freq2.setTextAlignment(Qt.AlignCenter)
                color2 = self.generate_color_from_string(data['freq2'])
                item_freq2.setForeground(QBrush(QColor(color2)))
                item_freq2.setFont(QFont("Segoe UI", 9, QFont.Bold))
                self.table_interferences.setItem(row, 3, item_freq2)
                
                if data['conflict']:
                    item_status = QTableWidgetItem("⚠ CONFLIT")
                    item_status.setForeground(QBrush(QColor("#ff6b6b")))
                else:
                    item_status = QTableWidgetItem("✓ OK")
                    item_status.setForeground(QBrush(QColor("#51cf66")))
                item_status.setTextAlignment(Qt.AlignCenter)
                item_status.setFont(QFont("Segoe UI", 9, QFont.Bold))
                self.table_interferences.setItem(row, 4, item_status)
            
            self.table_interferences.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            
        except Exception as e:
            print(f"Erreur matrice interférences: {e}")
            self.table_interferences.clear()
            self.table_interferences.setRowCount(1)
            self.table_interferences.setColumnCount(1)
            self.table_interferences.setItem(0, 0, QTableWidgetItem(f"Erreur: {str(e)}"))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TelecomsOptimizer()
    window.show()
    sys.exit(app.exec())