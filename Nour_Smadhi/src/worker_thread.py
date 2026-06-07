# worker_thread.py

from PySide6.QtCore import QThread, Signal

# Importation de la fonction d'optimisation
from optimization import solve_budget_constrained_median

class OptimizationThread(QThread):
    """Thread pour exécuter l'optimisation sans bloquer l'interface"""
    finished_signal = Signal(object)
    error_signal = Signal(str)
    
    def __init__(self, distances, demands, station_costs, budget, max_stations=None, capacities=None, max_distance=None):
        super().__init__()
        self.distances = distances
        self.demands = demands
        self.station_costs = station_costs
        self.budget = budget
        self.max_stations = max_stations
        self.capacities = capacities
        self.max_distance = max_distance
    
    def run(self):
        try:
            print("[Thread] Début de l'optimisation...")
            result = solve_budget_constrained_median(
                self.distances,
                self.demands,
                self.station_costs,
                self.budget,
                self.max_stations,
                self.capacities,
                self.max_distance
            )
            print(f"[Thread] Optimisation terminée. Résultat: {'OUI' if result else 'NON'}")
            self.finished_signal.emit(result)
        except Exception as e:
            print(f"[Thread] Erreur: {str(e)}")
            import traceback
            traceback.print_exc()
            self.error_signal.emit(str(e))