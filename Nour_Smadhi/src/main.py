import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__)))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader

from gui_controller import GUIController

def main():
    app = QApplication(sys.argv)
    
    # Get the correct path to UI file - FIXED PATH
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    ui_file_path = project_root / "ui" / "main.ui"
    
    print(f"Looking for UI file at: {ui_file_path}")
    
    if not ui_file_path.exists():
        print(f"Error: UI file not found at {ui_file_path}")
        print("Current working directory:", os.getcwd())
        return 1
    
    # Create and show the main window
    controller = GUIController(str(ui_file_path))
    controller.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()