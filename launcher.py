import sys
import os
import subprocess
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel,
    QHBoxLayout, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, QTimer

# Import des applications existantes
from Abdelkader_Mohamed_Louay.frontend import AirlineApp
from Amal_Torejmane.frontend import ModernLogisticsApp
from Baya_Bouzouita.MonApp_RH_optimisation_station_service import MainWindow as RHOptimizationApp
from Nour_Besrour.frontend.telecoms_frontend import TelecomsOptimizer


class MainLauncher(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Operations Decision Suite")
        self.setFixedSize(450, 650)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # CRITIQUE: Le launcher ne doit PAS fermer l'application quand il se ferme
        self.setAttribute(Qt.WA_QuitOnClose, False)

        self.current_app = None
        self.external_process = None  # AJOUTÉ: Pour suivre le processus externe
        self.process_timer = None     # AJOUTÉ: Timer pour vérifier le processus
        self.app_monitor_timer = None # AJOUTÉ: Timer pour surveiller les apps Qt
        self.init_ui()

    # ---------- UI STYLES ----------
    def setup_style(self):
        self.setStyleSheet("""
            QFrame#MainContainer {
                background-color: #121218;
                border: 1px solid #2a2a35;
                border-radius: 12px;
            }
            QLabel#HeaderTitle {
                color: #ffffff;
                font-size: 18px;
                font-weight: 700;
                letter-spacing: 1px;
                margin-top: 15px;
            }
            QLabel#HeaderSub {
                color: #878a99;
                font-size: 11px;
                text-transform: uppercase;
                margin-bottom: 20px;
            }
            QPushButton {
                background-color: #1e1e24;
                color: #ffffff;
                border: 1px solid #2a2a35;
                border-radius: 8px;
                padding: 15px;
                text-align: left;
                margin-bottom: 8px;
            }
            QPushButton:hover {
                background-color: #26262e;
                border-color: #5c7cfa;
            }
        """)

    # ---------- BOUTON MODULE ----------
    def create_module_button(self, title, description, callback, is_active=False):
        btn = QPushButton()
        layout = QVBoxLayout(btn)
        layout.setSpacing(2)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(
            "font-weight:bold; font-size:13px; color:#5c7cfa;"
        )

        lbl_desc = QLabel(description)
        lbl_desc.setStyleSheet(
            "font-size:11px; color:#878a99;"
        )
        lbl_desc.setWordWrap(True)

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_desc)

        btn.clicked.connect(callback)

        if is_active:
            btn.setStyleSheet("""
                QPushButton {
                    border: 1px solid #5c7cfa;
                }
            """)

        return btn

    # ---------- INTERFACE ----------
    def init_ui(self):
        self.setup_style()

        main_layout = QVBoxLayout(self)

        container = QFrame()
        container.setObjectName("MainContainer")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(25, 20, 25, 25)

        # Bouton fermeture
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet(
            "background:transparent; border:none; color:#555; font-size:16px;"
        )
        close_btn.clicked.connect(self.quit_application)  # MODIFIÉ: Méthode spécifique pour quitter
        layout.addWidget(close_btn, 0, Qt.AlignRight)

        # Titres
        title = QLabel("OPTIMIZATION SUITE")
        title.setObjectName("HeaderTitle")
        layout.addWidget(title, 0, Qt.AlignCenter)

        subtitle = QLabel("Sélectionnez un moteur de résolution")
        subtitle.setObjectName("HeaderSub")
        layout.addWidget(subtitle, 0, Qt.AlignCenter)

        # Boutons modules
        layout.addWidget(self.create_module_button(
            "HUMANITAIRE",
            "Acheminement de l'aide alimentaire aux zones sinistrées",
            self.launch_humanitarian_app,
            is_active=True
        ))

        layout.addWidget(self.create_module_button(
            "TRANSPORT",
            "Affectation des avions aux vols et du surclassement passagers",
            self.launch_transport_app,
            is_active=True
        ))

        layout.addWidget(self.create_module_button(
            "TÉLÉCOMS",
            "Allocation de fréquences radio sans interférence par cellule",
            self.launch_telecoms_app,
            is_active=True
        ))

        layout.addWidget(self.create_module_button(
            "SERVICES PUBLICS",
            "Optimisation de l'implantation des stations de recharge électrique",
            self.launch_public_services_app,
            is_active=True
        ))

        layout.addWidget(self.create_module_button(
            "RH / PLANNING",
            "Planification optimale du personnel de station-service 24h",
            self.launch_rh_app,
            is_active=True
        ))

        layout.addStretch()
        main_layout.addWidget(container)

    # ---------- LANCEMENT APPS ----------
    def launch_transport_app(self):
        self._launch_app(AirlineApp)

    def launch_humanitarian_app(self):
        self._launch_app(ModernLogisticsApp)

    def launch_rh_app(self):
        self._launch_app(RHOptimizationApp)

    def launch_telecoms_app(self):
        self._launch_app(TelecomsOptimizer)
    
    # MODIFIÉ: Surveillance du processus externe
    def launch_public_services_app(self):
        try:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
            possible_paths = [
                os.path.join(base_path, "Nour_Smadhi", "launcher.py"),
                os.path.join(base_path, "Nour_Smadhi", "main.py"),
                os.path.join(base_path, "Nour_Smadhi", "src", "main.py")
            ]
            
            script_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    script_path = path
                    break
            
            if script_path:
                self.hide()
                
                # Lance le processus sans attendre (non-bloquant)
                self.external_process = subprocess.Popen([sys.executable, script_path])
                
                # Crée un timer pour vérifier si le processus est terminé
                self.process_timer = QTimer()
                self.process_timer.timeout.connect(self.check_external_process)
                self.process_timer.start(500)  # Vérifie toutes les 500ms
                
            else:
                QMessageBox.warning(
                    self,
                    "Fichier introuvable",
                    "Impossible de trouver le fichier d'application Services Publics.\n"
                    "Vérifiez que Nour_Smadhi/launcher.py ou Nour_Smadhi/src/main.py existe."
                )
                
        except Exception as e:
            QMessageBox.warning(
                self,
                "Erreur",
                f"Erreur lors du lancement de l'application Services Publics:\n{str(e)}"
            )
            self.show()

    # AJOUTÉ: Vérifie si le processus externe est toujours actif
    def check_external_process(self):
        if self.external_process is not None:
            # poll() retourne None si le processus est actif, sinon le code de sortie
            if self.external_process.poll() is not None:
                # Le processus est terminé
                self.process_timer.stop()
                self.external_process = None
                self.show()  # Revenir à la page d'accueil

    # AJOUTÉ: Surveille l'état des applications Qt internes
    def start_app_monitor(self):
        """Démarre un timer pour surveiller si l'application est toujours ouverte"""
        if self.app_monitor_timer:
            self.app_monitor_timer.stop()
        
        self.app_monitor_timer = QTimer()
        self.app_monitor_timer.timeout.connect(self.check_app_status)
        self.app_monitor_timer.start(500)  # Vérifie toutes les 500ms

    def check_app_status(self):
        """Vérifie si l'application courante est toujours active"""
        if self.current_app is not None:
            try:
                # Vérifie si la fenêtre existe toujours
                # Si l'objet a été détruit, cela lèvera une exception
                if not self.current_app.isVisible():
                    # L'application a été fermée
                    if self.app_monitor_timer:
                        self.app_monitor_timer.stop()
                        self.app_monitor_timer = None
                    self.current_app = None
                    self.show()  # Revenir à la page d'accueil
            except RuntimeError:
                # L'objet C++ sous-jacent a été détruit (fenêtre fermée avec X)
                if self.app_monitor_timer:
                    self.app_monitor_timer.stop()
                    self.app_monitor_timer = None
                self.current_app = None
                self.show()  # Revenir à la page d'accueil

    def _launch_app(self, app_class):
        if self.current_app:
            try:
                self.current_app.close()
            except RuntimeError:
                pass  # L'objet a déjà été détruit

        try:
            self.current_app = app_class()
            
            # CRITIQUE: Intercepter les événements de fermeture
            # Empêcher l'app de fermer toute l'application
            self.current_app.setAttribute(Qt.WA_QuitOnClose, False)
            
            self.current_app.show()
            self.hide()

            # MODIFIÉ: Toujours utiliser le timer pour plus de fiabilité
            self.start_app_monitor()
        except Exception as e:
            # Si l'application ne peut pas se lancer, revenir au launcher
            QMessageBox.warning(
                self,
                "Erreur",
                f"Erreur lors du lancement de l'application:\n{str(e)}"
            )
            self.show()

    # ---------- UTILITAIRES ----------
    def quit_application(self):
        """Quitte complètement l'application"""
        # Nettoyer tous les timers
        if self.app_monitor_timer:
            self.app_monitor_timer.stop()
            self.app_monitor_timer = None
        
        if self.process_timer:
            self.process_timer.stop()
            self.process_timer = None
        
        # Fermer les applications
        if self.external_process and self.external_process.poll() is None:
            self.external_process.terminate()
            
        if self.current_app:
            try:
                self.current_app.close()
            except RuntimeError:
                pass
        
        # Quitter l'application complète
        QApplication.quit()
    
    def show_launcher(self):
        """Retourne à la page d'accueil"""
        # Arrêter tous les timers
        if self.app_monitor_timer:
            self.app_monitor_timer.stop()
            self.app_monitor_timer = None
        
        if self.process_timer:
            self.process_timer.stop()
            self.process_timer = None
        
        self.current_app = None
        self.external_process = None
        self.show()

    def closeEvent(self, event):
        # MODIFIÉ: Ne pas arrêter l'app complète, juste nettoyer
        # Ceci gère le cas où on ferme le launcher avec le X de Windows
        if self.app_monitor_timer:
            self.app_monitor_timer.stop()
            self.app_monitor_timer = None
        
        if self.process_timer:
            self.process_timer.stop()
            self.process_timer = None
        
        if self.external_process and self.external_process.poll() is None:
            self.external_process.terminate()
            
        if self.current_app:
            try:
                self.current_app.close()
            except RuntimeError:
                pass
        
        # Quitter l'application complète
        QApplication.quit()
        event.accept()