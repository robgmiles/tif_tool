from PyQt5.QtWidgets import QMainWindow, QTabWidget
from PyQt5.QtCore import Qt

from views.reports_tab import ReportsTab
from views.checksum_tab import ChecksumTab
from views.transfer_tab import TransferTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.init_ui()
        
    def init_ui(self):
        # Set window properties
        self.setWindowTitle('TIFF Preservation Tool')
        self.setMinimumSize(1000, 700)  # Larger window size
        
        # Create tab widget and ensure it doesn't apply custom styling to the tab bar
        self.tabs = QTabWidget()
        
        # Create tab pages
        self.reports_tab = ReportsTab()
        self.checksum_tab = ChecksumTab()
        self.transfer_tab = TransferTab()
        
        # Add tabs with fixed width
        self.tabs.addTab(self.reports_tab, "Reports")
        self.tabs.addTab(self.checksum_tab, "Checksums")
        self.tabs.addTab(self.transfer_tab, "File Transfer")
        
        # Make sure tab bar spans full width and tabs have equal width
        self.tabs.setUsesScrollButtons(False)  # Important: disable scroll buttons
        self.tabs.tabBar().setExpanding(True)  # Make tabs expand to fill width
        
        # Set the tab widget as the central widget
        self.setCentralWidget(self.tabs)