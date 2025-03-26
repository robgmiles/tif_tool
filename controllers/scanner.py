import os
from PIL import Image

class Scanner:
    def __init__(self):
        self.results = {
            'tiff_files': [],
            'non_tiff_files': [],
            'folders': {}
        }
    
    def scan(self, root_folder, progress_callback=None, status_callback=None):
        """
        Recursively scan a directory for TIFF files
        
        Args:
            root_folder: Path to scan
            progress_callback: Function to call with progress updates (0-100)
            status_callback: Function to call with status messages
        """
        # Get total file count for progress tracking
        total_files = 0
        for _, _, files in os.walk(root_folder):
            total_files += len(files)
        
        if total_files == 0:
            if status_callback:
                status_callback("No files found")
            return
        
        # Track processed files for progress
        processed_files = 0
        
        # Walk through directory tree
        for dirpath, dirnames, filenames in os.walk(root_folder):
            # Create relative path for reporting
            rel_path = os.path.relpath(dirpath, root_folder)
            if rel_path == '.':
                rel_path = ''
            
            # Initialize folder record
            self.results['folders'][dirpath] = {
                'path': dirpath,
                'rel_path': rel_path,
                'tiff_count': 0,
                'total_size': 0
            }
            
            # Process each file
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                
                try:
                    # Check if file is a TIFF
                    if filename.lower().endswith(('.tif', '.tiff')):
                        # Get file size
                        file_size = os.path.getsize(file_path)
                        
                        # Extract basic metadata
                        try:
                            with Image.open(file_path) as img:
                                metadata = {
                                    'filename': filename,
                                    'path': file_path,
                                    'rel_path': os.path.join(rel_path, filename),
                                    'size': file_size,
                                    'width': img.width,
                                    'height': img.height,
                                    'format': img.format,
                                    'mode': img.mode
                                }

                                # Extract DPI information
                                try:
                                    dpi = img.info.get('dpi', (0, 0))
                                    metadata['dpi_x'] = dpi[0]
                                    metadata['dpi_y'] = dpi[1]
                                except Exception:
                                    metadata['dpi_x'] = 0
                                    metadata['dpi_y'] = 0
                                
                                # Extract bit depth
                                if img.mode == '1':
                                    metadata['bit_depth'] = 1  # Binary
                                elif img.mode == 'L':
                                    metadata['bit_depth'] = 8  # Grayscale
                                elif img.mode == 'P':
                                    metadata['bit_depth'] = 8  # Palette
                                elif img.mode == 'RGB':
                                    metadata['bit_depth'] = 24  # RGB
                                elif img.mode == 'RGBA':
                                    metadata['bit_depth'] = 32  # RGBA
                                elif img.mode == 'CMYK':
                                    metadata['bit_depth'] = 32  # CMYK
                                elif img.mode == 'I':
                                    metadata['bit_depth'] = 32  # 32-bit integer
                                elif img.mode == 'F':
                                    metadata['bit_depth'] = 32  # 32-bit float
                                else:
                                    metadata['bit_depth'] = 0  # Unknown
                                
                                # Extract color profile
                                try:
                                    if 'icc_profile' in img.info:
                                        metadata['color_profile'] = 'ICC Profile Present'
                                    else:
                                        metadata['color_profile'] = 'No ICC Profile'
                                except Exception:
                                    metadata['color_profile'] = 'Unknown'
                                
                                # Extract compression
                                try:
                                    if hasattr(img, 'tag'):
                                        # For PIL's TiffImagePlugin
                                        compression = img.tag.get(259, None)
                                        if compression:
                                            compression_value = compression[0]
                                            compression_types = {
                                                1: 'Uncompressed',
                                                2: 'CCITT 1D',
                                                3: 'CCITT Group 3',
                                                4: 'CCITT Group 4',
                                                5: 'LZW',
                                                6: 'JPEG (old)',
                                                7: 'JPEG',
                                                8: 'Adobe Deflate',
                                                9: 'JBIG B&W',
                                                10: 'JBIG Color',
                                                32773: 'PackBits',
                                                32946: 'Deflate',
                                                34712: 'JPEG 2000'
                                            }
                                            metadata['compression'] = compression_types.get(compression_value, f'Unknown ({compression_value})')
                                        else:
                                            metadata['compression'] = 'Unknown'
                                    else:
                                        metadata['compression'] = 'Unknown'
                                except Exception:
                                    metadata['compression'] = 'Unknown'
                                
                                # Add to TIFF files list
                                self.results['tiff_files'].append(metadata)
                                
                                # Update folder statistics
                                self.results['folders'][dirpath]['tiff_count'] += 1
                                self.results['folders'][dirpath]['total_size'] += file_size
                                
                        except Exception as e:
                            # File is not a valid TIFF or other error
                            self.results['non_tiff_files'].append({
                                'filename': filename,
                                'path': file_path,
                                'rel_path': os.path.join(rel_path, filename),
                                'size': file_size,
                                'error': str(e)
                            })
                    else:
                        # Non-TIFF file
                        file_size = os.path.getsize(file_path)
                        self.results['non_tiff_files'].append({
                            'filename': filename,
                            'path': file_path,
                            'rel_path': os.path.join(rel_path, filename),
                            'size': file_size
                        })
                
                except Exception as e:
                    # Handle file access errors
                    if status_callback:
                        status_callback(f"Error processing {filename}: {str(e)}")
                
                # Update progress
                processed_files += 1
                if progress_callback:
                    progress_value = int((processed_files / total_files) * 100)
                    progress_callback(progress_value)
                
                if status_callback:
                    status_callback(f"Processing: {file_path}")
        
        # Final status update
        if status_callback:
            status_callback(f"Scan complete. Found {len(self.results['tiff_files'])} TIFF files in {len(self.results['folders'])} folders.")