import pandas as pd
import numpy as np
import os

def load_default_data():
    """Charge les données par défaut depuis le fichier CSV"""
    try:
        data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'default_instance.csv')
        if os.path.exists(data_path):
            return pd.read_csv(data_path)
        else:
            return None
    except Exception as e:
        print(f"Erreur lors du chargement des données par défaut: {e}")
        return None

def validate_distances_matrix(distances):
    """Valide la matrice des distances"""
    if not distances:
        return False, "Matrice vide"
    
    n = len(distances)
    for i in range(n):
        if len(distances[i]) != n:
            return False, f"La ligne {i} n'a pas {n} colonnes"
        
        for j in range(n):
            if i == j and distances[i][j] != 0:
                return False, f"La diagonale doit être nulle (position {i},{j})"
            
            if distances[i][j] < 0:
                return False, f"Distance négative à la position {i},{j}"
    
    return True, "Matrice valide"

def calculate_euclidean_distance(coord1, coord2):
    """Calcule la distance Euclidienne entre deux points"""
    return np.sqrt((coord1[0] - coord2[0])**2 + (coord1[1] - coord2[1])**2)

def create_distance_matrix(coordinates):
    """Crée une matrice de distances à partir de coordonnées"""
    n = len(coordinates)
    distances = []
    
    for i in range(n):
        row = []
        for j in range(n):
            if i == j:
                row.append(0.0)
            else:
                row.append(calculate_euclidean_distance(coordinates[i], coordinates[j]))
        distances.append(row)
    
    return distances