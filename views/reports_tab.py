from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QFileDialog, QLineEdit, QProgressBar,
                            QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from controllers.scanner import Scanner
from controllers.reporter import Reporter

class ReportsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        # Create main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15) 
        
        # Source folder selection
        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(10)
        folder_layout.addWidget(QLabel("Select Root Folder:"))
        
        self.folder_path = QLineEdit()
        self.folder_path.setReadOnly(True)
        folder_layout.addWidget(self.folder_path)
        
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(self.browse_btn)
        
        main_layout.addLayout(folder_layout)
        
        # Generate button
        self.generate_btn = QPushButton("Generate Reports")
        self.generate_btn.clicked.connect(self.generate_reports)
        main_layout.addWidget(self.generate_btn)
        
        # Progress section
        progress_layout = QVBoxLayout()
        progress_layout.addWidget(QLabel("Progress:"))
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready")
        progress_layout.addWidget(self.status_label)
        
        main_layout.addLayout(progress_layout)
        
        # Output folder selection
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Output folder:"))
        
        self.output_path = QLineEdit()
        self.output_path.setReadOnly(True)
        output_layout.addWidget(self.output_path)
        
        self.output_browse_btn = QPushButton("Change")
        self.output_browse_btn.clicked.connect(self.browse_output_folder)
        output_layout.addWidget(self.output_browse_btn)
        
        main_layout.addLayout(output_layout)
        
        # Add stretch to push widgets to the top
        main_layout.addStretch(1)
        
        self.setLayout(main_layout)
    
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Root Folder")
        if folder:
            self.folder_path.setText(folder)
    
    def browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_path.setText(folder)
    
    def generate_reports(self):
        if not self.folder_path.text():
            QMessageBox.warning(self, "No Folder Selected", 
                               "Please select a root folder.")
            return
        
        # Create a worker thread to handle report generation
        self.worker = ReportWorker(self.folder_path.text(), 
                                  self.output_path.text() or self.folder_path.text())
        
        # Connect signals
        self.worker.progress.connect(self.update_progress)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.on_finished)
        
        # Start worker
        self.worker.start()
        
        # Disable UI elements during processing
        self.generate_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.output_browse_btn.setEnabled(False)
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def update_status(self, message):
        self.status_label.setText(message)
    
    def on_finished(self, success):
        # Re-enable UI elements
        self.generate_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.output_browse_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Success", 
                                  "Reports generated successfully.")
        else:
            QMessageBox.critical(self, "Error", 
                               "An error occurred during report generation.")


class ReportWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool)
    
    def __init__(self, source_folder, output_folder):
        super().__init__()
        self.source_folder = source_folder
        self.output_folder = output_folder
    
    def run(self):
        try:
            # Initialize Scanner
            scanner = Scanner()
            self.status.emit("Scanning directories...")
            
            # Scan for TIFF files
            scanner.scan(self.source_folder, 
                        progress_callback=self.progress.emit,
                        status_callback=self.status.emit)
            
            # Generate reports
            self.status.emit("Generating reports...")
            reporter = Reporter()
            reporter.generate_all_reports(scanner.results, self.output_folder,
                                         progress_callback=self.progress.emit,
                                         status_callback=self.status.emit)
            
            self.status.emit("Complete")
            self.finished.emit(True)
            
        except Exception as e:
            self.status.emit(f"Error: {str(e)}")
            self.finished.emit(False)