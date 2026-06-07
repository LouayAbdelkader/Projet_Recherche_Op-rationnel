import os
import sys
import time 
from PySide6.QtWidgets import (QMainWindow, QFileDialog, QMessageBox,
                               QTableWidgetItem, QHeaderView, QWidget,
                               QVBoxLayout, QLabel, QInputDialog, QPushButton,
                               QSpinBox, QCheckBox, QTextEdit, QDoubleSpinBox)
from PySide6.QtCore import QFile
from custom_widgets import CardFrame, MetricWidget, apply_shadow
from constants import STYLESHEET
from worker_thread import OptimizationThread
from PySide6.QtUiTools import QUiLoader
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
from matplotlib.figure import Figure


class GUIController(QMainWindow):
    def __init__(self, ui_file_path):
        super().__init__()
        self.ui_file_path = ui_file_path
        
        # Initialiser toutes les variables AVANT setup_connections
        self.zone_types = []
        self.station_costs = []
        self.budget = 20000.0
        self.budget_widget = None
        self.distances = []
        self.demands = []
        self.coordinates = []
        self.current_canvas = None
        self.btn_optimize = None
        self.optimization_thread = None
        
        # Charger l'interface
        self.load_ui(ui_file_path)
        
        # Configurer les connexions (maintenant toutes les variables sont initialisées)
        self.setup_connections()
        
        # Initialiser les données
        self.setup_initial_data()

    def load_ui(self, ui_file_path):  
        """Charge le fichier UI et initialise l'interface"""
        print(f"[UI] Chargement du fichier UI: {ui_file_path}")
        print(f"[UI] Le fichier existe: {os.path.exists(ui_file_path)}")
        
        file = QFile(ui_file_path)
        if not file.open(QFile.ReadOnly):
            error_msg = f"Impossible d'ouvrir le fichier UI: {ui_file_path}"
            print(f"[UI ERREUR] {error_msg}")
            fallback_widget = QWidget()
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Erreur: Fichier UI introuvable"))
            layout.addWidget(QLabel(f"Chemin: {ui_file_path}"))
            fallback_widget.setLayout(layout)
            self.setCentralWidget(fallback_widget)
            return
        
        loader = QUiLoader()
        
        # Enregistrer les widgets personnalisés
        loader.registerCustomWidget(CardFrame)
        loader.registerCustomWidget(MetricWidget)
        
        self.ui = loader.load(file)
        file.close()
        
        if self.ui:
            self.setCentralWidget(self.ui)
            self.setWindowTitle("Optimisation de Stations de Recharge Électrique")
            
            # Appliquer le stylesheet global
            self.setStyleSheet(STYLESHEET)
            
            # Initialiser les widgets personnalisés
            self.init_custom_widgets()
            
            print("[UI] UI chargé avec succès!")
        else:
            print("[UI ERREUR] Échec du chargement de l'UI")
    
    def init_custom_widgets(self):
        """Initialise les widgets personnalisés après chargement de l'UI"""
        # Initialiser les MetricWidget
        kpi_obj = self.ui.findChild(MetricWidget, "kpi_objective")
        if kpi_obj:
            kpi_obj.set_data("Distance Totale", "-", "km")
            print("[UI] kpi_objective initialisé")
        
        kpi_stat = self.ui.findChild(MetricWidget, "kpi_stations")
        if kpi_stat:
            kpi_stat.set_data("Stations Ouvertes", "-", "zones", "#51cf66")
            print("[UI] kpi_stations initialisé")
        
        # Appliquer les ombres aux CardFrame
        cards = self.ui.findChildren(CardFrame)
        for card in cards:
            apply_shadow(card)
        print(f"[UI] {len(cards)} CardFrame avec ombres appliquées")
        
        # Initialiser la référence au bouton d'optimisation
        self.btn_optimize = self.ui.findChild(QPushButton, "btn_run")
        if self.btn_optimize:
            print(f"[UI] Bouton d'optimisation trouvé: {self.btn_optimize.objectName()}")
        else:
            print("[UI] Bouton 'btn_run' non trouvé, recherche alternative...")
            self.btn_optimize = self.find_widget_by_name_or_text("btn_run", "LANCER L'OPTIMISATION")
            if self.btn_optimize:
                print(f"[UI] Bouton d'optimisation trouvé par texte: {self.btn_optimize.objectName()}")
    
    def setup_connections(self):  
        """Connecte les signaux des widgets aux slots"""
        print("\n[CONNECTIONS] Configuration des connexions...")
        
        # Recherche et connexion des boutons
        btn_import = self.find_widget_by_name_or_text("btn_import_csv", "Importer")
        if btn_import:
            btn_import.clicked.connect(self.import_csv)
            print("[CONNECTIONS] btn_import_csv connecté")
        
        btn_generate = self.find_widget_by_name_or_text("btn_generate_data", "Générer")
        if btn_generate:
            btn_generate.clicked.connect(self.generate_sample_data)
            print("[CONNECTIONS] btn_generate_data connecté")
        
        # Bouton d'optimisation - recherche par nom ou texte
        if self.btn_optimize:
            self.btn_optimize.clicked.connect(self.run_optimization)
            print("[CONNECTIONS] Bouton d'optimisation connecté")
        else:
            # Recherche de secours
            self.btn_optimize = self.find_widget_by_name_or_text("btn_run", "LANCER L'OPTIMISATION")
            if self.btn_optimize:
                self.btn_optimize.clicked.connect(self.run_optimization)
                print("[CONNECTIONS] Bouton d'optimisation trouvé et connecté (secours)")
            else:
                print("[CONNECTIONS ERREUR] Bouton d'optimisation non trouvé!")
                self.list_all_widgets()
        
        # Paramètres
        spin_zones = self.ui.findChild(QSpinBox, "spin_num_zones")
        if spin_zones:
            spin_zones.valueChanged.connect(self.on_parameters_changed)
            print("[CONNECTIONS] spin_num_zones connecté")
            budget_spin = self.ui.findChild(QDoubleSpinBox, "spin_budget")
        if budget_spin:
            self.budget_widget = budget_spin
            budget_spin.setValue(self.budget)  # Initialiser avec la valeur par défaut
            print(f"[CONNECTIONS] Champ budget trouvé et initialisé à {self.budget}€")
        
        print("[CONNECTIONS] Configuration terminée")
    
    def find_widget_by_name_or_text(self, name, text):
        """Trouve un widget par son nom ou son texte"""
        # Recherche par nom
        if name:
            widget = self.ui.findChild(QPushButton, name)
            if widget:
                return widget
        
        # Recherche par texte parmi tous les QPushButton
        if text:
            buttons = self.ui.findChildren(QPushButton)
            for btn in buttons:
                if text.lower() in btn.text().lower():
                    return btn
        
        return None
    
    def list_all_widgets(self):
        """Liste tous les widgets pour débogage"""
        print("\n[DEBUG] Liste de tous les widgets:")
        
        buttons = self.ui.findChildren(QPushButton)
        print(f"QPushButton ({len(buttons)}):")
        for btn in buttons:
            print(f"  - Nom: {btn.objectName()}, Texte: '{btn.text()}'")
        
        spinboxes = self.ui.findChildren(QSpinBox)
        print(f"\nQSpinBox ({len(spinboxes)}):")
        for spin in spinboxes:
            print(f"  - Nom: {spin.objectName()}, Valeur: {spin.value()}")
        
        checkboxes = self.ui.findChildren(QCheckBox)
        print(f"\nQCheckBox ({len(checkboxes)}):")
        for check in checkboxes:
            print(f"  - Nom: {check.objectName()}, Texte: '{check.text()}'")
        
        tables = self.ui.findChildren(type(self.ui.table_distances))
        print(f"\nQTableWidget ({len(tables)}):")
        for table in tables:
            print(f"  - Nom: {table.objectName()}")
    
    def setup_initial_data(self):
        """Initialise les tables avec des données par défaut"""
        if hasattr(self.ui, 'table_distances'):
            self.setup_distances_table()
            self.generate_sample_data()
        else:
            print("[INIT ERREUR] table_distances non trouvée")
            QMessageBox.warning(self, "Erreur", "Table des distances non trouvée")
    
    def setup_distances_table(self):
        """Configure l'apparence de la table des distances"""
        if hasattr(self.ui, 'table_distances'):
            self.ui.table_distances.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.ui.table_distances.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
    
    def reset_optimize_button(self):
        """Réinitialise le bouton d'optimisation à son état normal"""
        print("[BUTTON] Réinitialisation du bouton d'optimisation...")
        
        # Méthode 1: Utiliser la référence stockée
        if self.btn_optimize:
            self.btn_optimize.setEnabled(True)
            self.btn_optimize.setText("LANCER L'OPTIMISATION")
            print("[BUTTON] Bouton réinitialisé via référence")
            return True
        
        # Méthode 2: Rechercher par nom
        btn = self.ui.findChild(QPushButton, "btn_run")
        if btn:
            btn.setEnabled(True)
            btn.setText("LANCER L'OPTIMISATION")
            self.btn_optimize = btn  # Mettre à jour la référence
            print("[BUTTON] Bouton trouvé par nom et réinitialisé")
            return True
        
        # Méthode 3: Rechercher parmi tous les boutons
        buttons = self.ui.findChildren(QPushButton)
        for button in buttons:
            if "calcul" in button.text().lower() or not button.isEnabled():
                button.setEnabled(True)
                button.setText("LANCER L'OPTIMISATION")
                self.btn_optimize = button  # Mettre à jour la référence
                print(f"[BUTTON] Bouton trouvé par état et réinitialisé: {button.objectName()}")
                return True
        
        print("[BUTTON ERREUR] Impossible de trouver le bouton d'optimisation!")
        return False
    
    def import_csv(self):
        """Importe les données depuis un fichier CSV avec support pour les en-têtes"""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Importer un fichier CSV", "", "CSV Files (*.csv)"
            )
            
            if file_path:
                print(f"[IMPORT] Importation depuis: {file_path}")
                data = []
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                    if not lines:
                        QMessageBox.warning(self, "Attention", "Fichier CSV vide.")
                        return
                    
                    # Détecter le séparateur (virgule ou point-virgule)
                    first_line = lines[0].strip()
                    if ',' in first_line and ';' in first_line:
                        # Les deux séparateurs présents, utiliser le plus fréquent
                        comma_count = first_line.count(',')
                        semicolon_count = first_line.count(';')
                        separator = ',' if comma_count > semicolon_count else ';'
                    elif ',' in first_line:
                        separator = ','
                    elif ';' in first_line:
                        separator = ';'
                    else:
                        separator = ','  # Par défaut
                    
                    print(f"[IMPORT] Séparateur détecté: '{separator}'")
                    
                    # Déterminer si le fichier a des en-têtes
                    has_headers = False
                    try:
                        # Vérifier si la première ligne contient des valeurs numériques
                        test_values = [x.strip() for x in first_line.split(separator)]
                        float(test_values[1])  # Essayer de convertir la première valeur
                    except (ValueError, IndexError):
                        has_headers = True
                    
                    # Lire les données
                    start_line = 1 if has_headers else 0
                    for line in lines[start_line:]:
                        line = line.strip()
                        if not line:
                            continue
                        
                        # Nettoyer les guillemets éventuels
                        line = line.replace('"', '').replace("'", "")
                        
                        # Diviser la ligne
                        if separator == ',':
                            row = [x.strip() for x in line.split(',')]
                        else:
                            row = [x.strip() for x in line.split(';')]
                        
                        # Sauter les lignes qui ne sont pas des données de distances
                        # (par exemple, les en-têtes secondaires ou les lignes vides)
                        if not row:
                            continue
                        
                        # Vérifier si c'est une ligne de données valide
                        # Doit contenir uniquement des nombres (ou vides pour la diagonale)
                        try:
                            # Pour les fichiers avec zone names dans la première colonne
                            if not row[0].replace('.', '').replace('-', '').isdigit() and len(row) > 1:
                                # La première colonne pourrait être un label de zone, on la saute
                                row = row[1:]
                            
                            # Convertir en float
                            float_row = []
                            for val in row:
                                if val == '' or val.lower() == 'nan' or val == '0.0' or val == '0':
                                    float_row.append(0.0)
                                else:
                                    float_row.append(float(val))
                            
                            # S'assurer que toutes les lignes ont la même longueur
                            if len(data) > 0 and len(float_row) != len(data[0]):
                                # Remplir avec des zéros si nécessaire
                                if len(float_row) < len(data[0]):
                                    float_row.extend([0.0] * (len(data[0]) - len(float_row)))
                                else:
                                    float_row = float_row[:len(data[0])]
                            
                            data.append(float_row)
                            
                        except ValueError:
                            # Cette ligne n'est pas des données numériques, la sauter
                            continue
                
                if data:
                    # Vérifier la taille de la matrice
                    n = len(data)
                    print(f"[IMPORT] {n} zones importées")
                    
                    # Vérifier que c'est une matrice carrée
                    if all(len(row) == n for row in data):
                        self.load_data_from_list(data)
                        QMessageBox.information(self, "Succès", 
                            f"Matrice des distances importée depuis {file_path}\n"
                            f"Taille: {n}×{n}\n"
                            f"Types de zones et coûts générés aléatoirement.")
                    else:
                        # Matrice non carrée - essayer de la rendre carrée
                        print(f"[IMPORT] Matrice non carrée: {n}×{len(data[0])}")
                        QMessageBox.warning(self, "Attention", 
                            f"La matrice n'est pas carrée ({n}×{len(data[0])}). "
                            f"Tentative d'ajustement...")
                        
                        # Prendre la dimension minimale
                        min_dim = min(n, len(data[0]))
                        data_square = [row[:min_dim] for row in data[:min_dim]]
                        self.load_data_from_list(data_square)
                        
                        QMessageBox.information(self, "Succès", 
                            f"Matrice ajustée à {min_dim}×{min_dim} et importée.")
                else:
                    QMessageBox.warning(self, "Attention", 
                        "Aucune donnée numérique trouvée dans le fichier CSV.")
                    
        except UnicodeDecodeError:
            # Essayer avec un encodage différent
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    # Réessayer avec le même code mais latin-1
                    # ... (même logique d'importation)
                    pass
            except Exception as e2:
                QMessageBox.critical(self, "Erreur", 
                    f"Erreur d'encodage: {str(e2)}")
                    
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'import: {str(e)}")
    
    def load_data_from_list(self, data):
        """Charge les données depuis une liste"""
        n = len(data)
        print(f"[DATA] Chargement de {n} zones")
        
        if hasattr(self.ui, 'spin_num_zones'):
            self.ui.spin_num_zones.setValue(n)
        
        self.ui.table_distances.clear()
        self.ui.table_distances.setRowCount(n)
        self.ui.table_distances.setColumnCount(n)
        
        # Générer des coordonnées aléatoires
        self.coordinates = (np.random.rand(n, 2) * 100).tolist()
        
        # Générer les types/coûts
        self._generate_costs_and_types(n)

        # Remplir la table des distances
        for i in range(n):
            for j in range(n):
                value = 0.0
                if i < len(data) and j < len(data[i]):
                    value = float(data[i][j])
                
                item = QTableWidgetItem(str(value))
                self.ui.table_distances.setItem(i, j, item)
        
        headers = [f"Zone {i+1} ({self.zone_types[i]})" for i in range(n)]
        self.ui.table_distances.setHorizontalHeaderLabels(headers)
        self.ui.table_distances.setVerticalHeaderLabels(headers)
        
        self.extract_data_from_tables()
        
    def _generate_costs_and_types(self, n):
        """Génère les types de demande et les coûts associés"""
        types = np.random.choice(['Fort', 'Moyen', 'Faible'], n, p=[0.2, 0.5, 0.3])
        self.zone_types = types.tolist()
        
        cost_map = {'Fort': 5000.0, 'Moyen': 3000.0, 'Faible': 1500.0}
        self.station_costs = [cost_map[t] for t in self.zone_types]
            
        print(f"[DATA] Types: {self.zone_types}")
        print(f"[DATA] Coûts: {self.station_costs}")

    def generate_sample_data(self):
        """Génère des données d'exemple"""
        try:
            if not hasattr(self.ui, 'spin_num_zones'):
                print("[GENERATE ERREUR] spin_num_zones non trouvé")
                return
                
            n = self.ui.spin_num_zones.value()
            print(f"[GENERATE] Génération de {n} zones...")
            
            self.ui.table_distances.clear()
            self.ui.table_distances.setRowCount(n)
            self.ui.table_distances.setColumnCount(n)
            
            self.coordinates = (np.random.rand(n, 2) * 100).tolist()
            
            # Générer les nouveaux types et coûts
            self._generate_costs_and_types(n)
            
            # Remplir la table des distances (calcul Euclidien)
            for i in range(n):
                for j in range(n):
                    if i == j:
                        value = 0.0
                    else:
                        dx = self.coordinates[i][0] - self.coordinates[j][0]
                        dy = self.coordinates[i][1] - self.coordinates[j][1]
                        value = round(np.sqrt(dx**2 + dy**2), 2)
                    
                    item = QTableWidgetItem(str(value))
                    self.ui.table_distances.setItem(i, j, item)
            
            headers = [f"Zone {i+1} ({self.zone_types[i]})" for i in range(n)]
            self.ui.table_distances.setHorizontalHeaderLabels(headers)
            self.ui.table_distances.setVerticalHeaderLabels(headers)
            
            self.extract_data_from_tables()
            self.ui.table_distances.viewport().update()
            
            QMessageBox.information(self, "Données générées",
                f"Données d'exemple générées pour {n} zones.")
            
        except Exception as e:
            print(f"[GENERATE ERREUR] {str(e)}")
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la génération: {str(e)}")
    
    def extract_data_from_tables(self):
        """Extrait les distances et génère/vérifie les demandes/coûts"""
        try:
            if not hasattr(self.ui, 'table_distances'):
                return
                
            n = self.ui.table_distances.rowCount()
            self.distances = []
            
            # Demandes (générées/fixées lors de la génération des types)
            self.demands = [1] * n
            
            # Générer les coûts si n a changé
            if len(self.station_costs) != n:
                self._generate_costs_and_types(n)
                 
            # Extraction des distances
            for i in range(n):
                row = []
                for j in range(n):
                    item = self.ui.table_distances.item(i, j)
                    if item and item.text():
                        val = float(item.text())
                        row.append(val)
                    else:
                        row.append(0.0)
                self.distances.append(row)
                
            print(f"[EXTRACT] Données extraites: {n} zones")
                
        except Exception as e:
            print(f"[EXTRACT ERREUR] {str(e)}")
            QMessageBox.warning(self, "Attention", f"Erreur lors de l'extraction: {str(e)}")
    
    def on_parameters_changed(self):
        """Appelé quand le nombre de zones change"""
        self.extract_data_from_tables()
    
    def run_optimization(self):
        """Lance le processus d'optimisation avec contrainte budgétaire"""
        print("\n" + "="*60)
        print("DÉBUT DE L'OPTIMISATION")
        print("="*60)
        
        try:
            # Désactiver le bouton IMMÉDIATEMENT pour éviter les clics multiples
            if self.btn_optimize:
                self.btn_optimize.setEnabled(False)
                self.btn_optimize.setText("Calcul en cours...")
                print("[OPTIM] Bouton désactivé")
            else:
                # Recherche de secours
                self.btn_optimize = self.ui.findChild(QPushButton, "btn_run")
                if self.btn_optimize:
                    self.btn_optimize.setEnabled(False)
                    self.btn_optimize.setText("Calcul en cours...")
                    print("[OPTIM] Bouton trouvé et désactivé (secours)")
                else:
                    print("[OPTIM ERREUR] Impossible de trouver le bouton!")
                lbl_status = self.ui.findChild(QLabel, "lbl_status")
                if lbl_status:
                    lbl_status.setText("🟡 Optimisation en cours...")
                    lbl_status.setStyleSheet("color: #fcc419; font-weight: bold; font-style: italic;")
            self.extract_data_from_tables()
            
            if not self.distances or not self.station_costs:
                # Réactiver le bouton si erreur
                self.reset_optimize_button()
                QMessageBox.warning(self, "Attention", "Données d'entrée manquantes.")
                return
            
            n = len(self.distances)
            print(f"[OPTIM] Nombre de zones: {n}")
            print(f"[OPTIM] Coûts des stations: {self.station_costs}")
            
            # Récupérer le budget
            if self.budget_widget:
                budget = self.budget_widget.value()
                print(f"[OPTIM] Budget récupéré depuis l'interface: {budget}€")
            else:
                # Fallback: chercher le widget par nom
                budget_spin = self.ui.findChild(QDoubleSpinBox, "spin_budget")
                if budget_spin:
                    budget = budget_spin.value()
                    self.budget_widget = budget_spin
                    print(f"[OPTIM] Budget trouvé et récupéré: {budget}€")
                else:
                    # Si aucun widget budget n'existe, utiliser la valeur par défaut
                    budget = self.budget
                    print(f"[OPTIM] Aucun widget budget trouvé, utilisation de la valeur par défaut: {budget}€")
            
            self.budget = budget  # Mettre à jour le budget interne
            # Récupérer les autres paramètres
            max_stations = None
            capacity = None
            max_distance = None
            capacities = None  # Initialize here to avoid UnboundLocalError
            
            # Paramètre p (nombre de stations)
            spin_stations = self.ui.findChild(QSpinBox, "spin_num_stations")
            if spin_stations:
                max_stations = spin_stations.value()
                if max_stations == 0:
                    max_stations = None
                print(f"[OPTIM] Nombre max de stations: {max_stations}")
            
            # Distance maximale
            spin_distance = self.ui.findChild(QDoubleSpinBox, "spin_max_distance")
            if spin_distance:
                max_distance = spin_distance.value()
                print(f"[OPTIM] Distance maximale initiale: {max_distance}")
            
            # Capacité
            spin_capacity = self.ui.findChild(QSpinBox, "spin_capacity")
            if spin_capacity:
                capacity = spin_capacity.value()
                print(f"[OPTIM] Capacité par station: {capacity}")
            
            # Contrôles d'activation
            check_distance = self.ui.findChild(QCheckBox, "check_max_distance")
            check_capacity = self.ui.findChild(QCheckBox, "check_capacity")
            
            # Appliquer les contraintes si activées
            if check_distance:
                if not check_distance.isChecked():
                    max_distance = None
                    print("[OPTIM] Contrainte de distance désactivée (checkbox non coché)")
                elif max_distance and max_distance > 0:
                    print(f"[OPTIM] Contrainte de distance activée: {max_distance}")
                else:
                    print("[OPTIM] Contrainte de distance activée mais valeur invalide")
                    max_distance = None
            
            if check_capacity:
                if not check_capacity.isChecked():
                    capacity = None
                    capacities = None
                    print("[OPTIM] Contrainte de capacité désactivée (checkbox non coché)")
                elif capacity and capacity > 0:
                    print(f"[OPTIM] Contrainte de capacité activée: {capacity}")
                    capacities = [capacity] * n
                else:
                    print("[OPTIM] Contrainte de capacité activée mais valeur invalide")
                    capacity = None
                    capacities = None
            else:
                capacities = None
            
            # Double-check max_distance
            max_distance = max_distance if max_distance and max_distance > 0 else None
            
            print(f"\n[OPTIM] Paramètres finaux transmis au solveur:")
            print(f"  - Budget: {budget}€")
            print(f"  - Stations max: {max_stations}")
            print(f"  - Distance max: {max_distance}")
            print(f"  - Capacités: {capacities}")
            
            # DEBUG: Check distances matrix
            print(f"[DEBUG] Distances matrix shape: {len(self.distances)}x{len(self.distances[0]) if self.distances else 0}")
            if self.distances:
                # Flatten distances to check range
                flat_distances = [dist for row in self.distances for dist in row if dist > 0]
                if flat_distances:
                    print(f"[DEBUG] Distances range: min={min(flat_distances):.2f}, max={max(flat_distances):.2f}")
                    if max_distance:
                        print(f"[DEBUG] Max distance constraint: {max_distance}")
                        print(f"[DEBUG] Number of distances > constraint: {sum(1 for d in flat_distances if d > max_distance)}")
            
            print("[OPTIM] Lancement du thread d'optimisation...")
            
            # Lancer l'optimisation dans un thread
            self.optimization_thread = OptimizationThread(
                self.distances, 
                self.demands, 
                self.station_costs,
                self.budget,
                max_stations,
                capacities, 
                max_distance
            )
            self.optimization_thread.finished_signal.connect(self.on_optimization_finished)
            self.optimization_thread.error_signal.connect(self.on_optimization_error)
            self.optimization_thread.start()
            
            print("[OPTIM] Thread démarré avec succès!")
            
        except Exception as e:
            print(f"[OPTIM ERREUR] {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Réactiver le bouton en cas d'erreur
            self.reset_optimize_button()
            
            QMessageBox.critical(self, "Erreur", f"Erreur lors du lancement: {str(e)}")
    
    def on_optimization_finished(self, result):
        """Appelé quand l'optimisation est terminée avec succès"""
        print("\n" + "="*60)
        print("OPTIMISATION TERMINÉE")
        print("="*60)
        
        # RÉACTIVER LE BOUTON EN PREMIER
        self.reset_optimize_button()

        lbl_status = self.ui.findChild(QLabel, "lbl_status")
        if lbl_status:
            lbl_status.setText("🟢 Optimisation terminée")
            lbl_status.setStyleSheet("color: #51cf66; font-weight: bold; font-style: normal;")

        if result:
            print(f"[RESULT] Type: {type(result)}")
            print(f"[RESULT] Clés: {list(result.keys())}")
        else:
            print("[RESULT] Aucun résultat (None)")
        
        if result:
            # ADD THESE TWO METHOD CALLS
            self.display_results(result)
            self.plot_solution(result)
            
            # Afficher un message de succès
            stations_count = len(result.get('stations_ouvertes', []))
            objective_value = result.get('objective_value', 0)
            cout_total = result.get('cout_total', 0)
            budget_initial = result.get('budget_initial', self.budget)
            
            print(f"\n[RÉSUMÉ] Solution trouvée:")
            print(f"  - Stations: {stations_count}")
            print(f"  - Coût: {cout_total:.2f}€ / {budget_initial:.2f}€")
            print(f"  - Distance: {objective_value:.2f}")
            
            QMessageBox.information(self, "Optimisation terminée",
                f"Solution optimale trouvée!\n\n"
                f"• Stations ouvertes: {stations_count}\n"
                f"• Coût d'installation: {cout_total:.2f}€ (Budget max: {budget_initial:.2f}€)\n"
                f"• Distance totale minimisée: {objective_value:.2f}")
        else:
            QMessageBox.warning(self, "Attention", "Aucune solution trouvée.")
    
    def on_optimization_error(self, error_message):
        """Appelé quand il y a une erreur lors de l'optimisation"""
        print(f"\n[OPTIM ERREUR] {error_message}")
        
        # RÉACTIVER LE BOUTON
        self.reset_optimize_button()
        lbl_status = self.ui.findChild(QLabel, "lbl_status")
        if lbl_status:
            lbl_status.setText("🔴 Erreur d'optimisation")
            lbl_status.setStyleSheet("color: #ff6b6b; font-weight: bold; font-style: normal;")
            print("[STATUS] Statut mis à jour: Erreur d'optimisation (rouge)")   
        QMessageBox.critical(self, "Erreur d'optimisation", error_message)

    # ============================================================================
    # ADD THESE MISSING METHODS STARTING HERE
    # ============================================================================
    
    def display_results(self, result):
        """Affiche les résultats de l'optimisation sous forme de rapport HTML simplifié"""
        try:
            print("\n[DISPLAY] Génération du rapport simplifié...")
            
            # 1. Update individual KPIs (keep these since they're the main dashboard metrics)
            kpi_distance = self.ui.findChild(MetricWidget, "kpi_total_distance")
            kpi_stations = self.ui.findChild(MetricWidget, "kpi_stations_opened")
            kpi_budget = self.ui.findChild(MetricWidget, "kpi_budget_used")
            
            obj_value = result.get('objective_value', 0)
            stations_count = len(result.get('stations_ouvertes', []))
            cout_total = result.get('cout_total', 0)
            budget_initial = result.get('budget_initial', self.budget)
            budget_percent = (cout_total / budget_initial * 100) if budget_initial > 0 else 0
            
            if kpi_distance:
                kpi_distance.set_data("Distance Totale", f"{obj_value:.2f}", "km", "#4d9fff")
            if kpi_stations:
                kpi_stations.set_data("Stations Ouvertes", stations_count, "sites", "#51cf66")
            if kpi_budget:
                kpi_budget.set_data("Budget Utilisé", f"{cout_total:,.0f}€", f"({budget_percent:.1f}%)", "#f1c40f")

            # 2. Update stations list with enhanced design
            text_stations = self.ui.findChild(QTextEdit, "text_stations_list")
            if text_stations:
                stations = result.get('stations_ouvertes', [])
                html_stations = """
                <!DOCTYPE html>
                <html>
                <head>
                <style>
                    body { 
                        font-family: 'Segoe UI', 'Roboto', sans-serif; 
                        color: #e0e6ed; 
                        margin: 0; 
                        padding: 0; 
                        background: transparent; 
                        font-size: 13px;
                        line-height: 1.5;
                    }
                    .header {
                        color: #5c7cfa;
                        font-size: 14px;
                        font-weight: 600;
                        margin-bottom: 15px;
                        padding-bottom: 8px;
                        border-bottom: 2px solid rgba(92, 124, 250, 0.3);
                        letter-spacing: 0.5px;
                    }
                    .stations-table {
                        width: 100%;
                        border-collapse: collapse;
                    }
                    .station-row {
                        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                        transition: background-color 0.2s ease;
                    }
                    .station-row:hover {
                        background-color: rgba(92, 124, 250, 0.05);
                    }
                    .station-cell {
                        padding: 10px 8px;
                        vertical-align: middle;
                    }
                    .station-number {
                        color: #ffffff;
                        font-weight: 600;
                        font-size: 13px;
                    }
                    .station-zone {
                        color: #a0aec0;
                        font-size: 12.5px;
                    }
                    .station-type {
                        font-size: 12px;
                        font-weight: 700;
                        padding: 6px 12px;
                        border-radius: 12px;
                        display: inline-block;
                        min-width: 65px;
                        text-align: center;
                        letter-spacing: 0.5px;
                        text-transform: uppercase;
                        border: 2px solid;
                        background-color: #1e1e24; /* CHANGED: Solid dark background */
                    }
                    /* RED for Fort */
                    .type-fort {
                        color: #ff6b6b;
                        border-color: #ff6b6b;
                        box-shadow: 0 2px 4px rgba(255, 107, 107, 0.3);
                        text-shadow: 0 1px 2px rgba(255, 107, 107, 0.3);
                    }
                    /* BLUE for Moyen */
                    .type-moyen {
                        color: #4d9fff;
                        border-color: #4d9fff;
                        box-shadow: 0 2px 4px rgba(77, 159, 255, 0.3);
                        text-shadow: 0 1px 2px rgba(77, 159, 255, 0.3);
                    }
                    /* GREEN for Faible */
                    .type-faible {
                        color: #51cf66;
                        border-color: #51cf66;
                        box-shadow: 0 2px 4px rgba(81, 207, 102, 0.3);
                        text-shadow: 0 1px 2px rgba(81, 207, 102, 0.3);
                    }
                    .station-cost {
                        color: #f1c40f;
                        font-weight: 700;
                        font-size: 13px;
                        text-align: right;
                        text-shadow: 0 1px 2px rgba(241, 196, 15, 0.3);
                    }
                    .summary-footer {
                        margin-top: 20px;
                        padding-top: 15px;
                        border-top: 1px solid rgba(255, 255, 255, 0.1);
                        color: #7c8594;
                        font-size: 11.5px;
                        font-style: italic;
                        text-align: center;
                    }
                </style>
                </head>
                <body>
                """
                
                html_stations += """
                <div class="header">Emplacements sélectionnés</div>
                <table class="stations-table">
                """
                
                for i, station in enumerate(stations, 1):
                    zone_type = self.zone_types[station] if station < len(self.zone_types) else "N/A"
                    cost = self.station_costs[station] if station < len(self.station_costs) else 0
                    
                    # Determine CSS class based on zone type
                    type_class = {
                        'Fort': 'type-fort',
                        'Moyen': 'type-moyen',
                        'Faible': 'type-faible'
                    }.get(zone_type, 'type-moyen')
                    
                    html_stations += f"""
                    <tr class="station-row">
                        <td class="station-cell">
                            <div class="station-number">Station {i}</div>
                        </td>
                        <td class="station-cell">
                            <div class="station-zone">Zone {station+1}</div>
                        </td>
                        <td class="station-cell">
                            <div class="station-type {type_class}">{zone_type}</div>
                        </td>
                        <td class="station-cell">
                            <div class="station-cost">{cost:,.0f}€</div>
                        </td>
                    </tr>
                    """
                
                html_stations += "</table>"
                
                # Add a summary footer
                total_cost = sum(self.station_costs[station] for station in stations if station < len(self.station_costs))
                html_stations += f"""
                <div class="summary-footer">
                    Total: {total_cost:,.0f}€ • {len(stations)} station{'' if len(stations) == 1 else 's'}
                </div>
                """
                
                html_stations += """
                </body>
                </html>
                """
                text_stations.setHtml(html_stations)

            # 3. SIMPLIFIED REPORT - Enhanced design
            text_output = self.ui.findChild(QTextEdit, "text_assignations")
            if text_output:
                assignations = result.get('assignations', {})
                
                # Group zones by station
                station_map = {}
                for zone, stat in assignations.items():
                    if stat not in station_map: 
                        station_map[stat] = []
                    station_map[stat].append(zone)
                
                # Calculate some useful metrics for the report
                total_zones = len(assignations)
                avg_zones_per_station = total_zones / len(station_map) if station_map else 0
                
                # Get distances for each assignment
                assignment_distances = []
                for zone, station in assignations.items():
                    if (zone < len(self.distances) and station < len(self.distances) and 
                        zone != station):
                        distance = self.distances[zone][station]
                        assignment_distances.append(distance)
                
                avg_distance = sum(assignment_distances) / len(assignment_distances) if assignment_distances else 0
                max_distance = max(assignment_distances) if assignment_distances else 0
                
                # Start enhanced HTML String
                html = """
                <!DOCTYPE html>
                <html>
                <head>
                <style>
                    body { 
                        font-family: 'Segoe UI', 'Roboto', sans-serif; 
                        color: #e0e6ed; 
                        margin: 0; 
                        padding: 15px; 
                        background: #0a0e1a; 
                        font-size: 13px;
                        line-height: 1.6;
                    }
                    .header { 
                        background: #1e1e24; /* CHANGED: Solid color instead of gradient */
                        border: 1px solid rgba(92, 124, 250, 0.3);
                        color: #e0e6ed; 
                        padding: 20px; 
                        border-radius: 10px; 
                        margin-bottom: 20px; 
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
                    }
                    .header h2 { 
                        margin: 0; 
                        font-size: 18px; 
                        color: #5c7cfa; 
                        font-weight: 600;
                        letter-spacing: 0.5px;
                    }
                    .assignment-stats {
                        background: #1e1e24; /* CHANGED: Solid color */
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        border-radius: 10px;
                        padding: 20px;
                        margin-bottom: 25px;
                        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.15);
                    }
                    .stat-row {
                        display: flex;
                        justify-content: space-between;
                        padding: 10px 0;
                        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
                        align-items: center;
                    }
                    .stat-row:last-child {
                        border-bottom: none;
                    }
                    .stat-label {
                        color: #a0aec0;
                        font-size: 13px;
                        font-weight: 500;
                    }
                    .stat-value {
                        color: #ffffff;
                        font-weight: 600;
                        font-size: 13.5px;
                    }
                    .zone-assignments {
                        margin-top: 25px;
                    }
                    .station-assignment {
                        background: #1e1e24; /* CHANGED: Solid color */
                        border: 1px solid rgba(255, 255, 255, 0.1);
                        border-radius: 10px;
                        padding: 20px;
                        margin-bottom: 18px;
                        transition: transform 0.2s ease, box-shadow 0.2s ease;
                        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.15);
                    }
                    .station-assignment:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.25);
                    }
                    .station-header {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 15px;
                        padding-bottom: 12px;
                        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                    }
                    .station-title {
                        color: #5c7cfa;
                        font-weight: 600;
                        font-size: 15px;
                    }
                    .station-meta {
                        font-size: 12.5px;
                        color: #4d9fff;
                        background: #1e1e24; /* CHANGED: Solid color */
                        padding: 4px 10px;
                        border-radius: 12px;
                        font-weight: 500;
                        border: 1px solid rgba(77, 159, 255, 0.3);
                    }
                    .zones-list {
                        display: flex;
                        flex-wrap: wrap;
                        gap: 8px;
                        margin-top: 12px;
                    }
                    .zone-item {
                        background: #1e1e24; /* CHANGED: Solid color */
                        color: #4d9fff;
                        padding: 6px 14px;
                        border-radius: 8px;
                        font-size: 12.5px;
                        border: 1px solid rgba(77, 159, 255, 0.25);
                        font-weight: 500;
                        transition: all 0.2s ease;
                        display: flex;
                        align-items: center;
                        gap: 6px;
                    }
                    .zone-item:hover {
                        background: #23232a; /* Slightly lighter on hover */
                        transform: translateY(-1px);
                        box-shadow: 0 3px 8px rgba(77, 159, 255, 0.2);
                    }
                    .zone-distance {
                        color: #a0aec0;
                        font-size: 11px;
                        font-weight: normal;
                    }
                    .empty-state {
                        text-align: center;
                        padding: 40px 20px;
                        color: #7c8594;
                        font-size: 14px;
                        font-style: italic;
                        background: rgba(255, 255, 255, 0.03);
                        border-radius: 8px;
                        border: 1px dashed rgba(255, 255, 255, 0.1);
                    }
                    .summary-note {
                        color: #7c8594;
                        font-size: 12px;
                        font-style: italic;
                        margin-top: 25px;
                        padding-top: 18px;
                        border-top: 1px solid rgba(255, 255, 255, 0.1);
                        text-align: center;
                        line-height: 1.6;
                    }
                </style>
                </head>
                <body>
                """
                
                # Header
                html += f"""
                <div class="header">
                    <h2>Affectation des Zones aux Stations</h2>
                </div>
                """
                
                # Quick assignment statistics
                html += """
                <div class="assignment-stats">
                    <div class="stat-row">
                        <span class="stat-label">Nombre total de zones</span>
                        <span class="stat-value">""" + f"{total_zones}" + """</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Stations actives</span>
                        <span class="stat-value">""" + f"{len(station_map)}" + """</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Zones par station (moyenne)</span>
                        <span class="stat-value">""" + f"{avg_zones_per_station:.1f}" + """</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Distance moyenne</span>
                        <span class="stat-value">""" + f"{avg_distance:.2f} km" + """</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Distance maximale</span>
                        <span class="stat-value">""" + f"{max_distance:.2f} km" + """</span>
                    </div>
                </div>
                """
                
                # Zone assignments by station
                html += "<div class='zone-assignments'>"
                
                if station_map:
                    for stat, zones in sorted(station_map.items()):
                        zone_count = len(zones)
                        
                        # Calculate average distance for this station
                        station_distances = []
                        for zone in zones:
                            if zone < len(self.distances) and stat < len(self.distances):
                                distance = self.distances[zone][stat]
                                station_distances.append(distance)
                        
                        avg_station_distance = sum(station_distances) / len(station_distances) if station_distances else 0
                        
                        html += f"""
                        <div class="station-assignment">
                            <div class="station-header">
                                <div class="station-title">Station {stat+1} (Zone {stat+1})</div>
                                <div class="station-meta">
                                    {zone_count} zone{'' if zone_count == 1 else 's'} • {avg_station_distance:.1f} km moyenne
                                </div>
                            </div>
                            <div class="zones-list">
                        """
                        
                        for zone in sorted(zones):
                            if zone < len(self.distances) and stat < len(self.distances):
                                distance = self.distances[zone][stat]
                                html += f"""
                                <div class="zone-item" title="Distance: {distance:.2f} km">
                                    Zone {zone+1}
                                    <span class="zone-distance">({distance:.1f} km)</span>
                                </div>
                                """
                        
                        html += """
                            </div>
                        </div>
                        """
                else:
                    html += """
                    <div class="empty-state">
                        ⚠️ Aucune affectation de zones disponible
                    </div>
                    """
                
                html += "</div>"
                
                # Summary note
                html += f"""
                <div class="summary-note">
                    Affectations générées le {time.strftime('%d/%m/%Y à %H:%M')}. 
                    Chaque zone est assignée à la station la plus proche dans la limite des contraintes budgétaires.
                </div>
                """
                
                html += """
                </body>
                </html>
                """
                
                # Set the HTML to the widget
                text_output.setHtml(html)
                print("[DISPLAY] Rapport d'affectation généré avec succès")
            
            # 4. Display important optimization logs - CLEAN WHITE VERSION
            text_logs = self.ui.findChild(QTextEdit, "text_logs") 
            if text_logs:
                # Filter and format the most important logs
                important_logs = []
                
                # Add optimization summary
                important_logs.append("========================================================")
                important_logs.append("DÉBUT DE L'OPTIMISATION")
                important_logs.append("========================================================")
                
                # Add key parameters
                important_logs.append(f"[OPTIM] Nombre de zones: {len(self.coordinates)}")
                important_logs.append(f"[OPTIM] Budget récupéré depuis l'interface: {self.budget}€")
                
                # Get max_stations from UI
                spin_stations = self.ui.findChild(QSpinBox, "spin_num_stations")
                max_stations = spin_stations.value() if spin_stations else 0
                important_logs.append(f"[OPTIM] Nombre max de stations: {max_stations}")
                
                # Add constraint status
                check_distance = self.ui.findChild(QCheckBox, "check_max_distance")
                check_capacity = self.ui.findChild(QCheckBox, "check_capacity")
                
                distance_enabled = check_distance.isChecked() if check_distance else False
                capacity_enabled = check_capacity.isChecked() if check_capacity else False
                
                important_logs.append(f"[OPTIM] Contrainte de distance: {'activée' if distance_enabled else 'désactivée'}")
                important_logs.append(f"[OPTIM] Contrainte de capacité: {'activée' if capacity_enabled else 'désactivée'}")
                
                # Add optimization result
                important_logs.append("")
                important_logs.append("[OPTIM] Lancement du thread d'optimisation...")
                important_logs.append("[Thread] Début de l'optimisation...")
                
                # Check if optimization was successful
                model_status = result.get('model_status', 'UNKNOWN')
                if model_status in ['OPTIMAL', 'FEASIBLE']:
                    important_logs.append("[Thread] Optimisation terminée. Résultat: OUI")
                else:
                    important_logs.append(f"[Thread] Optimisation terminée. Résultat: {model_status}")
                
                important_logs.append("========================================================")
                important_logs.append("OPTIMISATION TERMINÉE")
                important_logs.append("========================================================")
                
                # Add solution summary
                important_logs.append(f"[RÉSUMÉ] Solution trouvée:")
                important_logs.append(f"  - Stations: {stations_count}")
                important_logs.append(f"  - Coût: {cout_total:.2f}€ / {budget_initial:.2f}€")
                important_logs.append(f"  - Distance: {obj_value:.2f}")
                
                # Format the logs with HTML - CLEAN WHITE VERSION
                html_logs = """
                <!DOCTYPE html>
                <html>
                <head>
                <style>
                    body { 
                        font-family: 'Consolas', 'Monaco', monospace; 
                        color: #ffffff; /* CHANGED: White text */
                        margin: 0; 
                        padding: 15px; 
                        background: #0f0f13; 
                        font-size: 13px;
                        line-height: 1.6;
                    }
                    .log-header {
                        color: #5c7cfa;
                        font-weight: 600;
                        margin: 15px 0 10px 0;
                        text-align: center;
                        font-size: 14px;
                        border-bottom: 2px solid rgba(92, 124, 250, 0.3);
                        padding-bottom: 8px;
                        letter-spacing: 0.5px;
                    }
                    .log-divider {
                        color: #5c7cfa;
                        font-weight: 600;
                        text-align: center;
                        margin: 20px 0;
                        border-top: 2px solid rgba(92, 124, 250, 0.3);
                        padding-top: 15px;
                    }
                    .log-line {
                        margin: 8px 0;
                        padding-left: 10px;
                        border-left: 2px solid transparent;
                        color: #ffffff; /* White text */
                    }
                    .log-optim {
                        border-left-color: #5c7cfa;
                        color: #ffffff; /* White text */
                    }
                    .log-thread {
                        border-left-color: #51cf66;
                        color: #ffffff; /* White text */
                    }
                    .log-constraint {
                        border-left-color: #f1c40f;
                        color: #ffffff; /* White text */
                    }
                    .log-summary {
                        background: #1e1e24; /* Solid dark background */
                        border-left: 4px solid #5c7cfa;
                        padding: 12px 15px;
                        margin: 15px 0;
                        border-radius: 0 8px 8px 0;
                        color: #ffffff; /* White text */
                        font-weight: 500;
                        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.2);
                    }
                    .timestamp {
                        color: #7c8594;
                        font-size: 12px;
                        font-style: italic;
                        margin-top: 20px;
                        padding-top: 15px;
                        border-top: 1px solid rgba(255, 255, 255, 0.1);
                        text-align: center;
                    }
                    .empty-line {
                        height: 10px;
                    }
                </style>
                </head>
                <body>
                """
                
                # Add logs content with clean formatting (no emojis)
                html_logs += '<div class="log-header">DÉBUT DE L\'OPTIMISATION</div>'
                
                for log in important_logs:
                    # Skip divider lines and header text lines
                    if "========================================================" in log:
                        continue
                    if log in ["DÉBUT DE L'OPTIMISATION", "OPTIMISATION TERMINÉE"]:
                        continue
                    
                    if log == "":
                        html_logs += '<div class="empty-line"></div>'
                    elif log.startswith("[RÉSUMÉ]"):
                        html_logs += f'<div class="log-summary">{log}</div>'
                    elif log.startswith("[Thread]"):
                        if "OUI" in log or "OPTIMAL" in log or "FEASIBLE" in log:
                            # NO EMOJI - just white text
                            html_logs += f'<div class="log-line log-thread">{log}</div>'
                        else:
                            # NO EMOJI - just white text
                            html_logs += f'<div class="log-line log-thread">{log}</div>'
                    elif log.startswith("[OPTIM]"):
                        # NO EMOJI - just white text
                        html_logs += f'<div class="log-line log-optim">{log}</div>'
                    elif "désactivée" in log or "activée" in log:
                        # NO EMOJI - just white text
                        html_logs += f'<div class="log-line log-constraint">{log}</div>'
                    elif log == "OPTIMISATION TERMINÉE":
                        html_logs += '<div class="log-header">OPTIMISATION TERMINÉE</div>'
                    else:
                        html_logs += f'<div class="log-line">{log}</div>'
                
                # Add the OPTIMISATION TERMINÉE header before the summary
                html_logs += '<div class="log-header">OPTIMISATION TERMINÉE</div>'
                
                # Add timestamp
                html_logs += f'<div class="timestamp">Logs générés le {time.strftime("%d/%m/%Y à %H:%M:%S")}</div>'
                
                html_logs += """
                </body>
                </html>
                """
                
                text_logs.setHtml(html_logs)
                print("[DISPLAY] Logs d'optimisation affichés avec succès")
                
        except Exception as e:
            print(f"[DISPLAY ERREUR] {str(e)}")
            import traceback
            traceback.print_exc()
    
    def plot_solution(self, result):
        """Crée un graphique visualisant la solution avec couleurs par type de zone (thème clair)"""
        try:
            print("[PLOT] Création du graphique avec thème clair...")
            print(f"[PLOT] self.coordinates type: {type(self.coordinates)}")
            print(f"[PLOT] self.coordinates length: {len(self.coordinates) if self.coordinates else 0}")
            print(f"[PLOT] Zone types: {self.zone_types}")
            
            # Nettoyer le canvas précédent
            if hasattr(self, 'current_canvas') and self.current_canvas:
                try:
                    self.current_canvas.deleteLater()
                except RuntimeError as e:
                    print(f"[PLOT] Canvas déjà détruit: {e}")
            
            # Vérifier que nous avons des coordonnées
            if not self.coordinates or len(self.coordinates) == 0:
                print("[PLOT] Aucune coordonnée disponible, tentative de recréation...")
                n = len(self.distances) if self.distances else 0
                if n > 0:
                    self.coordinates = (np.random.rand(n, 2) * 100).tolist()
                    print(f"[PLOT] Coordonnées recréées: {len(self.coordinates)} points")
                else:
                    print("[PLOT] Impossible de créer des coordonnées")
                    return
            
            # Convertir les coordonnées en numpy array
            coords = np.array(self.coordinates)
            print(f"[PLOT] Coordonnées shape: {coords.shape}")
            
            # Extraire les données de la solution
            stations = result.get('stations_ouvertes', [])
            assignations = result.get('assignations', {})
            
            # SIMPLIFIED: Bigger figure for clearer plot
            fig = Figure(figsize=(12, 9), dpi=100, facecolor='white')
            
            # SIMPLIFIED: Use all space for the plot, no special legend space
            fig.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.1)
            
            ax = fig.add_subplot(111, facecolor='white')
            
            # Définir les couleurs pour chaque type de zone
            type_colors = {
                'Fort': '#e74c3c',     # Rouge vif pour Fort
                'Moyen': '#2ecc71',    # Vert vif pour Moyen
                'Faible': '#3498db'    # Bleu vif pour Faible
            }
            
            # Séparer les coordonnées par type pour un meilleur contrôle
            fort_coords = []
            moyen_coords = []
            faible_coords = []
            
            for i, zone_type in enumerate(self.zone_types):
                if i < len(coords):
                    if zone_type == 'Fort':
                        fort_coords.append(coords[i])
                    elif zone_type == 'Moyen':
                        moyen_coords.append(coords[i])
                    elif zone_type == 'Faible':
                        faible_coords.append(coords[i])
            
            # Convertir en arrays numpy
            if fort_coords: fort_coords = np.array(fort_coords)
            if moyen_coords: moyen_coords = np.array(moyen_coords)
            if faible_coords: faible_coords = np.array(faible_coords)
            
            # SIMPLIFIED: Smaller shapes with thinner borders
            if len(fort_coords) > 0:
                ax.scatter(fort_coords[:, 0], fort_coords[:, 1], 
                        c='#e74c3c', s=100,  # Smaller: 100 instead of 140
                        label='Zone Forte', alpha=0.9, edgecolors='#c0392b', 
                        linewidth=0.3, zorder=3)  # Thinner: 0.3 instead of 0.5
            
            if len(moyen_coords) > 0:
                ax.scatter(moyen_coords[:, 0], moyen_coords[:, 1], 
                        c='#2ecc71', s=100,  # Smaller: 100 instead of 140
                        label='Zone Moyenne', alpha=0.9, edgecolors='#27ae60', 
                        linewidth=0.3, zorder=3)  # Thinner: 0.3 instead of 0.5
            
            if len(faible_coords) > 0:
                ax.scatter(faible_coords[:, 0], faible_coords[:, 1], 
                        c='#3498db', s=100,  # Smaller: 100 instead of 140
                        label='Zone Faible', alpha=0.9, edgecolors='#2980b9', 
                        linewidth=0.3, zorder=3)  # Thinner: 0.3 instead of 0.5
            
            # SIMPLIFIED: Smaller stations
            if stations:
                station_indices = [s for s in stations if s < len(coords)]
                if station_indices:
                    station_coords = coords[station_indices]
                    
                    station_types = []
                    for idx in station_indices:
                        if idx < len(self.zone_types):
                            station_types.append(self.zone_types[idx])
                        else:
                            station_types.append('N/A')
                    
                    for i, (x, y) in enumerate(station_coords):
                        # SIMPLIFIED: Smaller station with thinner border
                        ax.scatter(x, y, 
                                c='#f1c40f', s=200,  # Smaller: 200 instead of 280
                                label='Station' if i == 0 else "", 
                                marker='p', edgecolors='black', 
                                linewidth=1.0, zorder=10)  # Thinner: 1.0 instead of 1.5
            
            # SIMPLIFIED: Thinner assignment lines
            for zone, station in assignations.items():
                if (zone < len(coords) and station < len(coords) and 
                    zone >= 0 and station >= 0):
                    x_values = [coords[zone, 0], coords[station, 0]]
                    y_values = [coords[zone, 1], coords[station, 1]]
                    
                    zone_type = self.zone_types[zone] if zone < len(self.zone_types) else 'Moyen'
                    line_color = type_colors.get(zone_type, '#7f8c8d')
                    
                    ax.plot(x_values, y_values, '--', color=line_color, 
                        alpha=0.6, linewidth=1.2, zorder=2)  # Thinner: 1.2 instead of 1.8
            
            # SIMPLIFIED: Smaller zone labels
            for i, (x, y) in enumerate(coords):
                if i < len(self.zone_types):
                    text_color = 'black'
                    ax.annotate(f'{i+1}', (x, y), xytext=(3, 3),  # Smaller offset: 3 instead of 5
                            textcoords='offset points', fontsize=9,  # Smaller: 9 instead of 10
                            fontweight='bold', color=text_color, zorder=4,
                            bbox=dict(boxstyle="round,pad=0.2",  # Smaller padding: 0.2 instead of 0.3
                                    facecolor='white', 
                                    edgecolor='lightgray', 
                                    alpha=0.7))  # Slightly more transparent
            
            # SIMPLIFIED: Clearer axis labels
            ax.set_xlabel('Coordonnée X (km)', fontsize=12, color='black', fontweight='bold')
            ax.set_ylabel('Coordonnée Y (km)', fontsize=12, color='black', fontweight='bold')
            ax.set_title('Visualisation de la Solution d\'Optimisation', 
                        fontsize=14, fontweight='bold', color='black', pad=15)  # Smaller: 14 instead of 16
            
            # SIMPLIFIED: Minimal legend at bottom right (doesn't cover plot)
            from matplotlib.lines import Line2D
            
            # Very simple legend elements
            legend_elements = [
                Line2D([0], [0], marker='o', color='w', markerfacecolor='#e74c3c',
                    markersize=8, markeredgecolor='#c0392b', markeredgewidth=0.3,
                    label='Forte'),
                Line2D([0], [0], marker='o', color='w', markerfacecolor='#2ecc71',
                    markersize=8, markeredgecolor='#27ae60', markeredgewidth=0.3,
                    label='Moyenne'),
                Line2D([0], [0], marker='o', color='w', markerfacecolor='#3498db',
                    markersize=8, markeredgecolor='#2980b9', markeredgewidth=0.3,
                    label='Faible'),
                Line2D([0], [0], marker='p', color='w', markerfacecolor='#f1c40f',
                    markersize=10, markeredgecolor='black', markeredgewidth=1.0,
                    label='Station'),
            ]
            
            # SIMPLIFIED: Small legend at bottom right corner
            legend = ax.legend(
                handles=legend_elements,
                loc='lower right',  # Bottom right corner
                fontsize=9,  # Very small font
                framealpha=0.9,
                frameon=True,
                fancybox=True,
                borderpad=0.5,
                labelspacing=0.5,
                handletextpad=1.0
            )
            
            legend.get_frame().set_facecolor('white')
            legend.get_frame().set_edgecolor('#95a5a6')
            legend.get_frame().set_linewidth(0.8)
            for text in legend.get_texts():
                text.set_color('black')
            
            # SIMPLIFIED: Subtle grid
            ax.grid(True, alpha=0.2, linestyle=':', color='#bdc3c7')  # Dotted grid
            
            # Couleur des ticks
            ax.tick_params(colors='black')
            
            # SIMPLIFIED: Thinner border
            for spine in ax.spines.values():
                spine.set_color('#7f8c8d')
                spine.set_linewidth(1.5)  # Thinner: 1.5 instead of 2
            
            # SIMPLIFIED: More margin for clearer view
            x_min, x_max = coords[:, 0].min(), coords[:, 0].max()
            y_min, y_max = coords[:, 1].min(), coords[:, 1].max()
            x_margin = (x_max - x_min) * 0.15  # More margin: 15% instead of 10%
            y_margin = (y_max - y_min) * 0.15  # More margin: 15% instead of 10%
            
            ax.set_xlim(x_min - x_margin, x_max + x_margin)
            ax.set_ylim(y_min - y_margin, y_max + y_margin)
            
            # Add revenue info as text annotation (small, out of the way)
            revenue_text = "Revenus: Forte=5k€, Moyenne=3k€, Faible=1.5k€"
            ax.text(0.02, 0.02, revenue_text, transform=ax.transAxes, 
                    fontsize=8, color='#7f8c8d', alpha=0.8,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor='white', 
                            edgecolor='lightgray', alpha=0.7))
            
            # Créer le canvas
            canvas = FigureCanvas(fig)
            self.current_canvas = canvas
            
            # Trouver le conteneur pour le graphique
            plot_container = self.ui.findChild(QWidget, "chart_placeholder")
            if plot_container:
                print(f"[PLOT] Conteneur chart_placeholder trouvé!")
                
                # Nettoyer le conteneur
                for child in plot_container.children():
                    if isinstance(child, (FigureCanvas, QLabel)):
                        child.setParent(None)
                        child.deleteLater()
                
                # Ajouter le canvas
                if not plot_container.layout():
                    plot_container.setLayout(QVBoxLayout())
                plot_container.layout().addWidget(canvas)
                
                # Forcer le rafraîchissement
                canvas.draw()
                plot_container.update()
                canvas.update()
                canvas.flush_events()
                
                print("[PLOT] Graphique avec thème clair ajouté à chart_placeholder")
                
            else:
                # SIMPLIFIED: Standard window size
                print("[PLOT] Création d'une fenêtre séparée...")
                plot_window = QWidget()
                plot_window.setWindowTitle("Visualisation de la solution")
                plot_window.setGeometry(100, 100, 900, 700)  # Standard size
                plot_window.setStyleSheet("background-color: white;")
                layout = QVBoxLayout()
                layout.addWidget(canvas)
                
                plot_window.setLayout(layout)
                plot_window.show()
                canvas.draw()
            
            print("[PLOT] Graphique avec thème clair créé avec succès!")
            
        except Exception as e:
            print(f"[PLOT ERREUR] {str(e)}")
            import traceback
            traceback.print_exc()