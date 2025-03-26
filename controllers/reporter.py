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
        
        # Generate a summary report
        if status_callback:
            status_callback("Generating summary report...")
        
        self.generate_summary_report(scan_results, output_folder)
        
        if status_callback:
            status_callback("All reports generated successfully.")
    
    def generate_folder_count_report(self, scan_results, output_folder):
        """Generate CSV listing folders and TIFF counts (only for folders containing TIFFs)"""
        output_file = os.path.join(output_folder, 'folder_count_report.csv')
        
        with open(output_file, 'w', newline='') as csvfile:
            fieldnames = ['folder_path', 'full_path', 'tiff_count', 'total_size_mb', 'total_size_gb', 'avg_file_size_mb']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for folder_info in scan_results['folders'].values():
                # Skip folders that don't contain any TIFF files
                if folder_info['tiff_count'] <= 0:
                    continue
                    
                # Calculate average file size
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
                # Calculate size in MB with 2 decimal places
                size_mb = round(file_info['size'] / (1024 * 1024), 2)
                
                writer.writerow({
                    'filename': file_info['filename'],
                    'path': file_info['rel_path'],
                    'size_bytes': file_info['size'],
                    'size_mb': size_mb,
                    'error': file_info.get('error', '')
                })
    
    def generate_tiff_metadata_report(self, scan_results, output_folder):
        """Generate CSV with comprehensive TIFF metadata"""
        output_file = os.path.join(output_folder, 'tiff_metadata_report.csv')
        
        with open(output_file, 'w', newline='') as csvfile:
            # Expanded fieldnames to include all the new metadata
            fieldnames = [
                'filename', 'path', 'size_mb', 'size_gb', 
                'width', 'height', 'dpi_x', 'dpi_y',
                'mode', 'photometric', 'bit_depth', 'bits_per_sample', 'samples_per_pixel',
                'color_profile', 'compression', 'planar_config',
                'tiff_version', 'is_bigtiff', 'is_tiled', 'tile_width', 'tile_height',
                'software', 'datetime', 'xmp', 'exif', 'iptc'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            for file_info in scan_results['tiff_files']:
                # Calculate sizes with 2 decimal places
                size_mb = round(file_info['size'] / (1024 * 1024), 2)
                size_gb = round(file_info['size'] / (1024 * 1024 * 1024), 2)
                
                # Prepare row with all metadata fields
                row = {
                    'filename': file_info['filename'],
                    'path': file_info['rel_path'],
                    'size_mb': size_mb,
                    'size_gb': size_gb,
                    'width': file_info.get('width', ''),
                    'height': file_info.get('height', ''),
                    'dpi_x': file_info.get('dpi_x', ''),
                    'dpi_y': file_info.get('dpi_y', ''),
                    'mode': file_info.get('mode', ''),
                    'photometric': file_info.get('photometric', ''),
                    'bit_depth': file_info.get('bit_depth', ''),
                    'bits_per_sample': file_info.get('bits_per_sample', ''),
                    'samples_per_pixel': file_info.get('samples_per_pixel', ''),
                    'color_profile': file_info.get('color_profile', ''),
                    'compression': file_info.get('compression', ''),
                    'planar_config': file_info.get('planar_config', ''),
                    'tiff_version': file_info.get('tiff_version', ''),
                    'is_bigtiff': file_info.get('is_bigtiff', ''),
                    'is_tiled': file_info.get('is_tiled', ''),
                    'tile_width': file_info.get('tile_width', ''),
                    'tile_height': file_info.get('tile_height', ''),
                    'software': file_info.get('software', ''),
                    'datetime': file_info.get('datetime', ''),
                    'xmp': file_info.get('xmp', ''),
                    'exif': file_info.get('exif', ''),
                    'iptc': file_info.get('iptc', '')
                }
                
                writer.writerow(row)
                
    def generate_summary_report(self, scan_results, output_folder):
        """Generate a summary report with preservation statistics"""
        output_file = os.path.join(output_folder, 'preservation_summary.csv')
        
        # Calculate summary statistics
        total_tiff_files = len(scan_results['tiff_files'])
        total_non_tiff_files = len(scan_results['non_tiff_files'])
        total_folders = len(scan_results['folders'])
        
        # DPI statistics
        dpi_counts = {'300+': 0, '200-299': 0, '100-199': 0, '<100': 0, 'Unknown': 0}
        for file_info in scan_results['tiff_files']:
            try:
                dpi_x = float(file_info.get('dpi_x', 0))
                dpi_y = float(file_info.get('dpi_y', 0))
                
                # Handle tuple DPI values if they still exist
                if isinstance(dpi_x, tuple) and len(dpi_x) == 2:
                    dpi_x = float(dpi_x[0]) / float(dpi_x[1])
                if isinstance(dpi_y, tuple) and len(dpi_y) == 2:
                    dpi_y = float(dpi_y[0]) / float(dpi_y[1])
                
                dpi = max(dpi_x, dpi_y)
                
                if dpi >= 300:
                    dpi_counts['300+'] += 1
                elif dpi >= 200:
                    dpi_counts['200-299'] += 1
                elif dpi >= 100:
                    dpi_counts['100-199'] += 1
                elif dpi > 0:
                    dpi_counts['<100'] += 1
                else:
                    dpi_counts['Unknown'] += 1
            except (TypeError, ValueError):
                # Handle any conversion errors
                dpi_counts['Unknown'] += 1
        
        # Compression statistics
        compression_counts = {}
        for file_info in scan_results['tiff_files']:
            compression = file_info.get('compression', 'Unknown')
            if compression not in compression_counts:
                compression_counts[compression] = 0
            compression_counts[compression] += 1
        
        # Color profile statistics
        profile_counts = {}
        for file_info in scan_results['tiff_files']:
            profile = file_info.get('color_profile', 'Unknown')
            if profile not in profile_counts:
                profile_counts[profile] = 0
            profile_counts[profile] += 1
        
        # Bit depth statistics
        bit_depth_counts = {}
        for file_info in scan_results['tiff_files']:
            try:
                bit_depth = int(file_info.get('bit_depth', 0))
                if bit_depth not in bit_depth_counts:
                    bit_depth_counts[bit_depth] = 0
                bit_depth_counts[bit_depth] += 1
            except (TypeError, ValueError):
                # Handle any conversion errors
                if 'Unknown' not in bit_depth_counts:
                    bit_depth_counts['Unknown'] = 0
                bit_depth_counts['Unknown'] += 1
        
        # Calculate total size
        total_size_bytes = sum(folder['total_size'] for folder in scan_results['folders'].values())
        total_size_gb = round(total_size_bytes / (1024 * 1024 * 1024), 2)
        
        # Write the summary
        with open(output_file, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Basic statistics
            writer.writerow(['Digital Preservation Summary'])
            writer.writerow([])
            writer.writerow(['File Statistics', ''])
            writer.writerow(['Total TIFF Files', total_tiff_files])
            writer.writerow(['Total Non-TIFF Files', total_non_tiff_files])
            writer.writerow(['Total Folders', total_folders])
            writer.writerow(['Total Size (GB)', total_size_gb])
            writer.writerow([])
            
            # DPI Distribution
            writer.writerow(['DPI Distribution', ''])
            for dpi_range, count in dpi_counts.items():
                percentage = round((count / total_tiff_files * 100), 2) if total_tiff_files > 0 else 0
                writer.writerow([f"{dpi_range} DPI", f"{count} ({percentage}%)"])
            writer.writerow([])
            
            # Compression Distribution
            writer.writerow(['Compression Distribution', ''])
            for compression, count in compression_counts.items():
                percentage = round((count / total_tiff_files * 100), 2) if total_tiff_files > 0 else 0
                writer.writerow([compression, f"{count} ({percentage}%)"])
            writer.writerow([])
            
            # Color Profile Distribution
            writer.writerow(['Color Profile Distribution', ''])
            for profile, count in profile_counts.items():
                percentage = round((count / total_tiff_files * 100), 2) if total_tiff_files > 0 else 0
                writer.writerow([profile, f"{count} ({percentage}%)"])
            writer.writerow([])
            
            # Bit Depth Distribution
            writer.writerow(['Bit Depth Distribution', ''])
            for bit_depth, count in bit_depth_counts.items():
                percentage = round((count / total_tiff_files * 100), 2) if total_tiff_files > 0 else 0
                writer.writerow([str(bit_depth) + " bit", f"{count} ({percentage}%)"])
            
            # Add timestamp
            writer.writerow([])
            writer.writerow(['Report generated', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")])