from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QFileDialog, QLineEdit, QProgressBar,
                            QMessageBox, QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from controllers.checksum import ChecksumGenerator

class ChecksumTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        # Create main layout
        main_layout = QVBoxLayout()
        
        # Folder selection section
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Select Folder:"))
        
        self.folder_path = QLineEdit()
        self.folder_path.setReadOnly(True)
        folder_layout.addWidget(self.folder_path)
        
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(self.browse_btn)
        
        main_layout.addLayout(folder_layout)
        
        # Mode selection
        mode_layout = QHBoxLayout()
        
        self.generate_radio = QRadioButton("Generate Checksums")
        self.generate_radio.setChecked(True)
        self.validate_radio = QRadioButton("Validate Checksums")
        
        # Add to button group for exclusive selection
        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.generate_radio)
        self.mode_group.addButton(self.validate_radio)
        
        mode_layout.addWidget(self.generate_radio)
        mode_layout.addWidget(self.validate_radio)
        
        main_layout.addLayout(mode_layout)
        
        # Output format options
        format_layout = QVBoxLayout()
        format_layout.addWidget(QLabel("Output Format:"))
        
        self.per_folder_radio = QRadioButton("Separate file per folder")
        self.per_folder_radio.setChecked(True)
        format_layout.addWidget(self.per_folder_radio)
        
        self.consolidated_radio = QRadioButton("Single consolidated file")
        format_layout.addWidget(self.consolidated_radio)
        
        # Add to button group for exclusive selection
        self.format_group = QButtonGroup()
        self.format_group.addButton(self.per_folder_radio)
        self.format_group.addButton(self.consolidated_radio)
        
        main_layout.addLayout(format_layout)
        
        # Action button
        self.action_btn = QPushButton("Generate SHA256 Checksums")
        self.action_btn.clicked.connect(self.process_checksums)
        main_layout.addWidget(self.action_btn)
        
        # Progress section
        progress_layout = QVBoxLayout()
        progress_layout.addWidget(QLabel("Progress:"))
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready")
        progress_layout.addWidget(self.status_label)
        
        main_layout.addLayout(progress_layout)
        
        # Add stretch to push widgets to the top
        main_layout.addStretch(1)
        
        self.setLayout(main_layout)
    
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_path.setText(folder)
    
    def process_checksums(self):
        if not self.folder_path.text():
            QMessageBox.warning(self, "No Folder Selected", 
                               "Please select a folder.")
            return
        
        # Determine mode
        mode = "generate" if self.generate_radio.isChecked() else "validate"
        
        # Determine format
        format_type = "per_folder" if self.per_folder_radio.isChecked() else "consolidated"
        
        # Create worker thread
        self.worker = ChecksumWorker(
            self.folder_path.text(),
            mode=mode,
            format_type=format_type
        )
        
        # Connect signals
        self.worker.progress.connect(self.update_progress)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.on_finished)
        
        # Update button text based on mode
        if mode == "generate":
            self.action_btn.setText("Generating...")
        else:
            self.action_btn.setText("Validating...")
        
        # Disable UI elements during processing
        self.action_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.generate_radio.setEnabled(False)
        self.validate_radio.setEnabled(False)
        self.per_folder_radio.setEnabled(False)
        self.consolidated_radio.setEnabled(False)
        
        # Start worker
        self.worker.start()
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def update_status(self, message):
        self.status_label.setText(message)
    
    def on_finished(self, success, results=None):
        # Re-enable UI elements
        self.action_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.generate_radio.setEnabled(True)
        self.validate_radio.setEnabled(True)
        self.per_folder_radio.setEnabled(True)
        self.consolidated_radio.setEnabled(True)
        
        # Reset button text
        mode = "generate" if self.generate_radio.isChecked() else "validate"
        if mode == "generate":
            self.action_btn.setText("Generate SHA256 Checksums")
        else:
            self.action_btn.setText("Validate SHA256 Checksums")
        
        if success:
            if mode == "generate":
                QMessageBox.information(self, "Success", 
                                      "Checksums generated successfully.")
            else:
                if results and 'invalid_files' in results and results['invalid_files']:
                    msg = f"Validation complete. {len(results['invalid_files'])} files failed checksum validation."
                    QMessageBox.warning(self, "Validation Results", msg)
                else:
                    QMessageBox.information(self, "Success", 
                                          "All files passed checksum validation.")
        else:
            QMessageBox.critical(self, "Error", 
                               "An error occurred during checksum processing.")


class ChecksumWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, object)
    
    def __init__(self, folder_path, mode="generate", format_type="per_folder"):
        super().__init__()
        self.folder_path = folder_path
        self.mode = mode
        self.format_type = format_type
    
    def run(self):
        try:
            generator = ChecksumGenerator()
            
            if self.mode == "generate":
                self.status.emit("Generating SHA256 checksums...")
                result = generator.generate_checksums(
                    self.folder_path,
                    algorithm="sha256",
                    format_type=self.format_type,
                    progress_callback=self.progress.emit,
                    status_callback=self.status.emit
                )
                self.finished.emit(True, result)
            else:
                self.status.emit("Validating checksums...")
                result = generator.validate_checksums(
                    self.folder_path,
                    progress_callback=self.progress.emit,
                    status_callback=self.status.emit
                )
                self.finished.emit(True, result)
            
        except Exception as e:
            self.status.emit(f"Error: {str(e)}")
            self.finished.emit(False, None)