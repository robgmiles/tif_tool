import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from views.main_window import MainWindow

def main():
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    
    # Set application style to Fusion (works well with custom dark themes)
    app.setStyle('Fusion')
    
    # Load and apply stylesheet
    with open('resources/styles.qss', 'r') as f:
        app.setStyleSheet(f.read())
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()