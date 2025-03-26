from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QFileDialog, QLineEdit, QProgressBar,
                            QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from controllers.transfer import FileTransferManager

class TransferTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        # Create main layout
        main_layout = QVBoxLayout()
        
        # Source selection
        source_layout = QVBoxLayout()
        source_layout.addWidget(QLabel("Source:"))
        
        source_path_layout = QHBoxLayout()
        self.source_path = QLineEdit()
        self.source_path.setReadOnly(True)
        source_path_layout.addWidget(self.source_path)
        
        self.source_browse_btn = QPushButton("...")
        self.source_browse_btn.clicked.connect(self.browse_source)
        source_path_layout.addWidget(self.source_browse_btn)
        
        source_layout.addLayout(source_path_layout)
        main_layout.addLayout(source_layout)
        
        # Destination selection
        dest_layout = QVBoxLayout()
        dest_layout.addWidget(QLabel("Destination:"))
        
        dest_path_layout = QHBoxLayout()
        self.dest_path = QLineEdit()
        self.dest_path.setReadOnly(True)
        dest_path_layout.addWidget(self.dest_path)
        
        self.dest_browse_btn = QPushButton("...")
        self.dest_browse_btn.clicked.connect(self.browse_destination)
        dest_path_layout.addWidget(self.dest_browse_btn)
        
        dest_layout.addLayout(dest_path_layout)
        main_layout.addLayout(dest_layout)
        
        # Transfer options
        options_layout = QVBoxLayout()
        options_layout.addWidget(QLabel("Transfer includes:"))
        options_layout.addWidget(QLabel("• File integrity verification using SHA256"))
        options_layout.addWidget(QLabel("• Automatic retry (up to 3 times) for failed transfers"))
        options_layout.addWidget(QLabel("• Detailed transfer log"))
        
        main_layout.addLayout(options_layout)
        
        # Start transfer button
        self.transfer_btn = QPushButton("Start Transfer")
        self.transfer_btn.clicked.connect(self.start_transfer)
        main_layout.addWidget(self.transfer_btn)
        
        # Progress section
        main_layout.addWidget(QLabel("Overall Progress:"))
        self.overall_progress = QProgressBar()
        self.overall_progress.setMinimumHeight(25) 
        main_layout.addWidget(self.overall_progress)
        
        main_layout.addWidget(QLabel("Current File:"))
        self.file_progress = QProgressBar()
        self.file_progress.setMinimumHeight(25)
        main_layout.addWidget(self.file_progress)
        
        self.status_label = QLabel("Ready")
        main_layout.addWidget(self.status_label)
        
        # Add stretch to push widgets to the top
        main_layout.addStretch(1)
        
        self.setLayout(main_layout)
    
    def browse_source(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder:
            self.source_path.setText(folder)
    
    def browse_destination(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if folder:
            self.dest_path.setText(folder)
    
    def start_transfer(self):
        if not self.source_path.text():
            QMessageBox.warning(self, "No Source Selected", 
                               "Please select a source folder.")
            return
        
        if not self.dest_path.text():
            QMessageBox.warning(self, "No Destination Selected", 
                               "Please select a destination folder.")
            return
        
        # Create worker thread
        self.worker = TransferWorker(
            self.source_path.text(),
            self.dest_path.text()
        )
        
        # Connect signals
        self.worker.overall_progress.connect(self.update_overall_progress)
        self.worker.file_progress.connect(self.update_file_progress)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.on_finished)
        
        # Disable UI elements during processing
        self.transfer_btn.setEnabled(False)
        self.source_browse_btn.setEnabled(False)
        self.dest_browse_btn.setEnabled(False)
        
        # Start worker
        self.worker.start()
    
    def update_overall_progress(self, value):
        self.overall_progress.setValue(value)
    
    def update_file_progress(self, value):
        self.file_progress.setValue(value)
    
    def update_status(self, message):
        self.status_label.setText(message)
    
    def on_finished(self, success, stats=None):
        # Re-enable UI elements
        self.transfer_btn.setEnabled(True)
        self.source_browse_btn.setEnabled(True)
        self.dest_browse_btn.setEnabled(True)
        
        if success:
            # Show statistics
            if stats:
                message = (f"Transfer complete!\n\n"
                          f"Files transferred: {stats.get('files_transferred', 0)}\n"
                          f"Total size: {stats.get('total_size_mb', 0):.2f} MB\n"
                          f"Errors: {stats.get('errors', 0)}")
                          
                QMessageBox.information(self, "Transfer Complete", message)
            else:
                QMessageBox.information(self, "Success", 
                                      "Transfer completed successfully.")
        else:
            QMessageBox.critical(self, "Error", 
                               "An error occurred during file transfer.")


class TransferWorker(QThread):
    overall_progress = pyqtSignal(int)
    file_progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, object)
    
    def __init__(self, source_path, dest_path):
        super().__init__()
        self.source_path = source_path
        self.dest_path = dest_path
    
    def run(self):
        try:
            transfer_manager = FileTransferManager()
            
            # Connect callbacks
            def overall_progress_callback(value):
                self.overall_progress.emit(value)
            
            def file_progress_callback(value):
                self.file_progress.emit(value)
            
            def status_callback(message):
                self.status.emit(message)
            
            # Start transfer
            result = transfer_manager.transfer_files(
                self.source_path,
                self.dest_path,
                overall_progress_callback=overall_progress_callback,
                file_progress_callback=file_progress_callback,
                status_callback=status_callback
            )
            
            self.finished.emit(True, result)
            
        except Exception as e:
            self.status.emit(f"Error: {str(e)}")
            self.finished.emit(False, None)