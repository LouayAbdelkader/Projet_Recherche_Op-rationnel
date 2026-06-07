import sys
from PySide6.QtWidgets import QApplication
from launcher import MainLauncher 

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    launcher = MainLauncher()
    launcher.show()
    
    sys.exit(app.exec())