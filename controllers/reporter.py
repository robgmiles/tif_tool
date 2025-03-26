import os
import csv
import pandas as pd
import datetime

class Reporter:
    def __init__(self):
        pass
    
    def generate_all_reports(self, scan_results, output_folder, 
                           progress_callback=None, status_callback=None):
        """
        Generate all reports from scan results
        
        Args:
            scan_results: Dictionary of scan results from Scanner
            output_folder: Folder to save reports
            progress_callback: Function to call with progress updates (0-100)
            status_callback: Function to call with status messages
        """
        # Ensure output directory exists
        os.makedirs(output_folder, exist_ok=True)
        
        # Total number of reports to generate
        total_reports = 3  # folder count, non-TIFF, TIFF metadata
        completed_reports = 0
        
        # Generate folder count report
        if status_callback:
            status_callback("Generating folder count report...")
        
        self.generate_folder_count_report(scan_results, output_folder)
        
        completed_reports += 1
        if progress_callback:
            progress_callback(int((completed_reports / total_reports) * 100))
        
        # Generate non-TIFF file report
        if status_callback:
            status_callback("Generating non-TIFF file report...")
        
        self.generate_non_tiff_report(scan_results, output_folder)
        
        completed_reports += 1
        if progress_callback:
            progress_callback(int((completed_reports / total_reports) * 100))
        
        # Generate TIFF metadata report
        if status_callback:
            status_callback("Generating TIFF metadata report...")
        
        self.generate_tiff_metadata_report(scan_results, output_folder)
        
        completed_reports += 1
        if progress_callback:
            progress_callback(int((completed_reports / total_reports) * 100))
        
        if status_callback:
            status_callback("All reports generated successfully.")
    
    def generate_folder_count_report(self, scan_results, output_folder):
        """Generate CSV listing folders and TIFF counts"""
        output_file = os.path.join(output_folder, 'folder_count_report.csv')
        
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['folder_path', 'full_path', 'tiff_count', 'total_size_mb', 'total_size_gb', 'avg_file_size_mb']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for folder_info in scan_results['folders'].values():
                # Calculate average file size
                avg_size_mb = 0
                if folder_info['tiff_count'] > 0:
                    avg_size_mb = (folder_info['total_size'] / folder_info['tiff_count']) / (1024 * 1024)
                
                # Calculate sizes in MB and GB with 2 decimal places
                size_mb = round(folder_info['total_size'] / (1024 * 1024), 2)
                size_gb = round(folder_info['total_size'] / (1024 * 1024 * 1024), 2)
                avg_size_mb = round(avg_size_mb, 2)
                
                writer.writerow({
                    'folder_path': folder_info['rel_path'] or '(root)',
                    'full_path': folder_info['path'],
                    'tiff_count': folder_info['tiff_count'],
                    'total_size_mb': size_mb,
                    'total_size_gb': size_gb,
                    'avg_file_size_mb': avg_size_mb
                })
    
    def generate_non_tiff_report(self, scan_results, output_folder):
        """Generate CSV listing non-TIFF files"""
        output_file = os.path.join(output_folder, 'non_tiff_files.csv')
        
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['filename', 'path', 'size_bytes', 'size_mb', 'error']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for file_info in scan_results['non_tiff_files']:
                writer.writerow({
                    'filename': file_info['filename'],
                    'path': file_info['rel_path'],
                    'size_bytes': file_info['size'],
                    'size_mb': file_info['size'] / (1024 * 1024),
                    'error': file_info.get('error', '')
                })
    
    def generate_tiff_metadata_report(self, scan_results, output_folder):
        """Generate CSV with TIFF metadata"""
        output_file = os.path.join(output_folder, 'tiff_metadata_report.csv')
        
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = [
                'filename', 'path', 'size_mb', 'size_gb', 
                'width', 'height', 'dpi_x', 'dpi_y',
                'mode', 'bit_depth', 'format', 'color_profile',
                'compression'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for file_info in scan_results['tiff_files']:
                # Calculate sizes with 2 decimal places
                size_mb = round(file_info['size'] / (1024 * 1024), 2)
                size_gb = round(file_info['size'] / (1024 * 1024 * 1024), 2)
                
                writer.writerow({
                    'filename': file_info['filename'],
                    'path': file_info['rel_path'],
                    'size_mb': size_mb,
                    'size_gb': size_gb,
                    'width': file_info.get('width', ''),
                    'height': file_info.get('height', ''),
                    'dpi_x': file_info.get('dpi_x', ''),
                    'dpi_y': file_info.get('dpi_y', ''),
                    'mode': file_info.get('mode', ''),
                    'bit_depth': file_info.get('bit_depth', ''),
                    'format': file_info.get('format', ''),
                    'color_profile': file_info.get('color_profile', ''),
                    'compression': file_info.get('compression', '')
                })
