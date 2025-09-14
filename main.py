import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from views.main_window import MainWindow

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def main():
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    
    # Set application style to Fusion (works well with custom dark themes)
    app.setStyle('Fusion')
    
    # Load and apply stylesheet with proper resource path handling
    stylesheet_path = resource_path('resources/styles.qss')
    
    try:
        with open(stylesheet_path, 'r') as f:
            app.setStyleSheet(f.read())
    except Exception as e:
        print(f"Warning: Could not load stylesheet: {e}")
        # Continue without stylesheet rather than crashing
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()