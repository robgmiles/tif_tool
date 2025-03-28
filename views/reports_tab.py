from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                            QPushButton, QFileDialog, QLineEdit, QProgressBar,
                            QMessageBox, QFrame, QGroupBox, QTextBrowser, QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QDesktopServices
from PyQt5.QtCore import QUrl
import os

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
        
        # === Source Folder Selection Section ===
        source_group = QGroupBox("Source Selection")
        source_layout = QVBoxLayout(source_group)
        
        folder_layout = QHBoxLayout()
        folder_layout.setSpacing(10)
        folder_layout.addWidget(QLabel("Select Root Folder:"))
        
        self.folder_path = QLineEdit()
        self.folder_path.setReadOnly(True)
        folder_layout.addWidget(self.folder_path)
        
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_folder)
        self.browse_btn.setFixedWidth(100)
        folder_layout.addWidget(self.browse_btn)
        
        source_layout.addLayout(folder_layout)
        main_layout.addWidget(source_group)
        
        # === Output Folder Section ===
        output_group = QGroupBox("Output Settings")
        output_layout = QVBoxLayout(output_group)
        
        output_hbox = QHBoxLayout()
        output_hbox.addWidget(QLabel("Output folder:"))
        
        self.output_path = QLineEdit()
        self.output_path.setReadOnly(True)
        output_hbox.addWidget(self.output_path)
        
        self.output_browse_btn = QPushButton("Change")
        self.output_browse_btn.setFixedWidth(100)
        self.output_browse_btn.clicked.connect(self.browse_output_folder)
        output_hbox.addWidget(self.output_browse_btn)
        
        output_layout.addLayout(output_hbox)
        
        # Generate button - with proper styling and smaller width
        gen_btn_layout = QHBoxLayout()
        gen_btn_layout.addStretch(1)
        
        self.generate_btn = QPushButton("Generate Reports")
        self.generate_btn.setFixedWidth(200)
        self.generate_btn.setMinimumHeight(40)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a6043;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #358553;
            }
            QPushButton:pressed {
                background-color: #1d4430;
            }
            QPushButton:disabled {
                background-color: #555555;
                color: #aaaaaa;
            }
        """)
        self.generate_btn.clicked.connect(self.generate_reports)
        gen_btn_layout.addWidget(self.generate_btn)
        gen_btn_layout.addStretch(1)
        
        output_layout.addLayout(gen_btn_layout)
        main_layout.addWidget(output_group)
        
        # === Progress Section ===
        progress_group = QGroupBox("Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready")
        progress_layout.addWidget(self.status_label)
        
        main_layout.addWidget(progress_group)
        
        # === Summary Section (Initially Hidden) ===
        self.summary_group = QGroupBox("Results Summary")
        self.summary_group.setVisible(False)
        summary_layout = QVBoxLayout(self.summary_group)
        
        self.summary_browser = QTextBrowser()
        self.summary_browser.setMinimumHeight(200)
        self.summary_browser.setOpenExternalLinks(True)
        summary_layout.addWidget(self.summary_browser)
        
        # Button to open reports folder
        open_folder_layout = QHBoxLayout()
        open_folder_layout.addStretch(1)
        
        self.open_folder_btn = QPushButton("Open Reports Folder")
        self.open_folder_btn.setFixedWidth(200)
        self.open_folder_btn.setStyleSheet("""
            QPushButton {
                background-color: #0077cc;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0088ee;
            }
            QPushButton:pressed {
                background-color: #0066aa;
            }
        """)
        self.open_folder_btn.clicked.connect(self.open_output_folder)
        open_folder_layout.addWidget(self.open_folder_btn)
        open_folder_layout.addStretch(1)
        
        summary_layout.addLayout(open_folder_layout)
        main_layout.addWidget(self.summary_group)
        
        # Add stretch to push widgets to the top
        main_layout.addStretch(1)
        
        self.setLayout(main_layout)
    
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Root Folder")
        if folder:
            self.folder_path.setText(folder)
            
            # Set default output folder to be the same as input
            if not self.output_path.text():
                self.output_path.setText(os.path.join(folder, "reports"))
    
    def browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.output_path.setText(folder)
    
    def open_output_folder(self):
        """Open the output folder in the system file explorer"""
        if self.output_path.text() and os.path.exists(self.output_path.text()):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.output_path.text()))
        else:
            QMessageBox.warning(self, "Folder Not Found", 
                               "The output folder does not exist.")
    
    def generate_reports(self):
        if not self.folder_path.text():
            QMessageBox.warning(self, "No Folder Selected", 
                               "Please select a root folder.")
            return
        
        # Hide the summary section when starting a new report
        self.summary_group.setVisible(False)
        
        # Create a worker thread to handle report generation
        self.worker = ReportWorker(self.folder_path.text(), 
                                  self.output_path.text() or os.path.join(self.folder_path.text(), "reports"))
        
        # Connect signals
        self.worker.progress.connect(self.update_progress)
        self.worker.status.connect(self.update_status)
        self.worker.finished.connect(self.on_finished)
        self.worker.summary.connect(self.display_summary)
        
        # Start worker
        self.worker.start()
        
        # Disable UI elements during processing
        self.generate_btn.setEnabled(False)
        self.browse_btn.setEnabled(False)
        self.output_browse_btn.setEnabled(False)
        self.open_folder_btn.setEnabled(False)
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def update_status(self, message):
        self.status_label.setText(message)
    
    def display_summary(self, summary_html):
        """Display the summary data in the summary browser"""
        self.summary_browser.setHtml(summary_html)
        self.summary_group.setVisible(True)
    
    def on_finished(self, success):
        # Re-enable UI elements
        self.generate_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.output_browse_btn.setEnabled(True)
        self.open_folder_btn.setEnabled(True)
        
        if success:
            # Summary will be displayed through the summary signal
            pass
        else:
            QMessageBox.critical(self, "Error", 
                               "An error occurred during report generation.")
            self.summary_group.setVisible(False)


class ReportWorker(QThread):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool)
    summary = pyqtSignal(str)  # New signal for summary data
    
    def __init__(self, source_folder, output_folder):
        super().__init__()
        self.source_folder = source_folder
        self.output_folder = output_folder
    
    def run(self):
        try:
            # Ensure output directory exists
            os.makedirs(self.output_folder, exist_ok=True)
            
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
            
            # Generate summary HTML
            summary_html = self.generate_summary_html(scanner.results)
            self.summary.emit(summary_html)
            
            self.status.emit("Complete")
            self.finished.emit(True)
            
        except Exception as e:
            self.status.emit(f"Error: {str(e)}")
            self.finished.emit(False)
    
    def generate_summary_html(self, scan_results):
        """Generate HTML summary of the reports"""
        # Count asset folders (folders with TIFF files)
        asset_folders = sum(1 for folder in scan_results['folders'].values() if folder['tiff_count'] > 0)
        
        # Total TIFF files
        total_tiff_files = len(scan_results['tiff_files'])
        
        # Calculate total size
        total_size_bytes = sum(folder['total_size'] for folder in scan_results['folders'].values())
        total_size_gb = round(total_size_bytes / (1024 * 1024 * 1024), 2)
        
        # Calculate average file size
        avg_file_size_mb = 0
        if total_tiff_files > 0:
            avg_file_size_mb = round((total_size_bytes / total_tiff_files) / (1024 * 1024), 2)
        
        # DPI statistics
        dpi_stats = {'300+': 0, '200-299': 0, '100-199': 0, '<100': 0, 'Unknown': 0}
        for file_info in scan_results['tiff_files']:
            try:
                dpi_x = float(file_info.get('dpi_x', 0))
                dpi_y = float(file_info.get('dpi_y', 0))
                
                # Handle tuple DPI values
                if isinstance(dpi_x, tuple) and len(dpi_x) == 2:
                    dpi_x = float(dpi_x[0]) / float(dpi_x[1])
                if isinstance(dpi_y, tuple) and len(dpi_y) == 2:
                    dpi_y = float(dpi_y[0]) / float(dpi_y[1])
                
                dpi = max(dpi_x, dpi_y)
                
                if dpi >= 300:
                    dpi_stats['300+'] += 1
                elif dpi >= 200:
                    dpi_stats['200-299'] += 1
                elif dpi >= 100:
                    dpi_stats['100-199'] += 1
                elif dpi > 0:
                    dpi_stats['<100'] += 1
                else:
                    dpi_stats['Unknown'] += 1
            except (TypeError, ValueError):
                dpi_stats['Unknown'] += 1
        
        # Bit depth statistics
        bit_depth_stats = {}
        for file_info in scan_results['tiff_files']:
            try:
                bit_depth = int(file_info.get('bit_depth', 0))
                if bit_depth not in bit_depth_stats:
                    bit_depth_stats[bit_depth] = 0
                bit_depth_stats[bit_depth] += 1
            except (TypeError, ValueError):
                if 'Unknown' not in bit_depth_stats:
                    bit_depth_stats['Unknown'] = 0
                bit_depth_stats['Unknown'] += 1
        
        # Compression statistics
        compression_stats = {}
        for file_info in scan_results['tiff_files']:
            compression = file_info.get('compression', 'Unknown')
            if compression not in compression_stats:
                compression_stats[compression] = 0
            compression_stats[compression] += 1
        
        # Build HTML content
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 10px; }}
                h2 {{ color: #2a6043; margin-top: 20px; margin-bottom: 10px; }}
                h3 {{ color: #444444; margin-top: 15px; margin-bottom: 5px; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 15px; }}
                th, td {{ padding: 8px; text-align: left; }}
                th {{ background-color: #2a6043; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .stat-value {{ font-weight: bold; color: #2a6043; }}
                .warning {{ color: #cc0000; }}
            </style>
        </head>
        <body>
            <h2>TIFF Collection Summary</h2>
            
            <table>
                <tr>
                    <td>Asset Folders:</td>
                    <td class="stat-value">{asset_folders}</td>
                </tr>
                <tr>
                    <td>Total TIFF Files:</td>
                    <td class="stat-value">{total_tiff_files}</td>
                </tr>
                <tr>
                    <td>Total Collection Size:</td>
                    <td class="stat-value">{total_size_gb} GB</td>
                </tr>
                <tr>
                    <td>Average TIFF File Size:</td>
                    <td class="stat-value">{avg_file_size_mb} MB</td>
                </tr>
            </table>
            
            <h3>Resolution Analysis</h3>
            <table>
                <tr>
                    <th>DPI Range</th>
                    <th>Count</th>
                    <th>Percentage</th>
                </tr>
        """
        
        # Add DPI statistics rows
        for dpi_range, count in dpi_stats.items():
            percentage = round((count / total_tiff_files * 100), 1) if total_tiff_files > 0 else 0
            row_class = ""
            if dpi_range not in ["300+", "Unknown"] and count > 0:
                row_class = "warning"
            html += f"""
                <tr class="{row_class}">
                    <td>{dpi_range}</td>
                    <td>{count}</td>
                    <td>{percentage}%</td>
                </tr>
            """
        
        html += """
            </table>
            
            <h3>Bit Depth Analysis</h3>
            <table>
                <tr>
                    <th>Bit Depth</th>
                    <th>Count</th>
                    <th>Percentage</th>
                </tr>
        """
        
        # Add bit depth statistics rows
        for bit_depth, count in sorted(bit_depth_stats.items()):
            if bit_depth == 'Unknown':
                bit_depth_display = "Unknown"
            else:
                bit_depth_display = f"{bit_depth} bit"
                
            percentage = round((count / total_tiff_files * 100), 1) if total_tiff_files > 0 else 0
            html += f"""
                <tr>
                    <td>{bit_depth_display}</td>
                    <td>{count}</td>
                    <td>{percentage}%</td>
                </tr>
            """
        
        html += """
            </table>
            
            <h3>Compression Analysis</h3>
            <table>
                <tr>
                    <th>Compression</th>
                    <th>Count</th>
                    <th>Percentage</th>
                </tr>
        """
        
        # Add compression statistics rows
        for compression, count in sorted(compression_stats.items()):
            percentage = round((count / total_tiff_files * 100), 1) if total_tiff_files > 0 else 0
            html += f"""
                <tr>
                    <td>{compression}</td>
                    <td>{count}</td>
                    <td>{percentage}%</td>
                </tr>
            """
        
        html += """
            </table>
            
            <h3>Generated Reports</h3>
            <ul>
                <li>Folder Count Report - Lists all folders containing TIFF files</li>
                <li>TIFF Metadata Report - Detailed metadata for all TIFF files</li>
                <li>Non-TIFF File Report - List of all non-TIFF files found</li>
                <li>Preservation Summary - Overall collection statistics</li>
            </ul>
        </body>
        </html>
        """
        
        return html