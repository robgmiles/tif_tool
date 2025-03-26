import os
import datetime
from PIL import Image
import tifffile
import numpy as np

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
                        
                        # Initialize metadata dictionary with basic file info
                        metadata = {
                            'filename': filename,
                            'path': file_path,
                            'rel_path': os.path.join(rel_path, filename),
                            'size': file_size,
                            'width': 0,
                            'height': 0,
                            'format': 'TIFF',
                            'mode': '',
                            'dpi_x': 0,
                            'dpi_y': 0,
                            'bit_depth': 0,
                            'color_profile': 'Unknown',
                            'compression': 'Unknown',
                            'software': 'Unknown',
                            'datetime': 'Unknown',
                            'tiff_version': 'Unknown',
                            'subfile_type': 'Unknown',
                            'planar_config': 'Unknown',
                            'samples_per_pixel': 0,
                            'photometric': 'Unknown',
                            'xmp': 'No',
                            'exif': 'No',
                            'iptc': 'No',
                            'is_bigtiff': 'No',
                            'is_tiled': 'No',
                            'tile_width': 0,
                            'tile_height': 0
                        }
                        
                        # Try to extract metadata using tifffile first
                        tifffile_success = False
                        try:
                            with tifffile.TiffFile(file_path) as tif:
                                tifffile_success = True
                                
                                # Get basic image dimensions from first page
                                if len(tif.pages) > 0:
                                    page = tif.pages[0]
                                    metadata['width'] = page.imagewidth
                                    metadata['height'] = page.imagelength
                                    
                                    # Get samples per pixel and bit depth
                                    metadata['samples_per_pixel'] = page.samplesperpixel
                                    metadata['bits_per_sample'] = page.bitspersample
                                    
                                    # Calculate total bit depth
                                    try:
                                        if isinstance(page.bitspersample, (list, tuple, np.ndarray)):
                                            metadata['bit_depth'] = sum(page.bitspersample)
                                        else:
                                            metadata['bit_depth'] = page.bitspersample * page.samplesperpixel
                                            
                                        # Store bits_per_sample for reporting
                                        if isinstance(page.bitspersample, (list, tuple, np.ndarray)):
                                            metadata['bits_per_sample'] = ','.join(str(b) for b in page.bitspersample)
                                        else:
                                            metadata['bits_per_sample'] = str(page.bitspersample)
                                    except (TypeError, ValueError):
                                        metadata['bit_depth'] = 0
                                        metadata['bits_per_sample'] = 'Unknown'
                                    
                                    # Get photometric interpretation
                                    if hasattr(page, 'photometric'):
                                        photometric_types = {
                                            0: 'WhiteIsZero',
                                            1: 'BlackIsZero',
                                            2: 'RGB',
                                            3: 'Palette',
                                            4: 'Mask',
                                            5: 'CMYK',
                                            6: 'YCbCr',
                                            8: 'CIELab',
                                            9: 'ICCLab'
                                        }
                                        metadata['photometric'] = photometric_types.get(
                                            page.photometric, f'Unknown ({page.photometric})')
                                    
                                    # Get planar configuration
                                    if hasattr(page, 'planarconfig'):
                                        planar_types = {
                                            1: 'Chunky',
                                            2: 'Planar'
                                        }
                                        metadata['planar_config'] = planar_types.get(
                                            page.planarconfig, f'Unknown ({page.planarconfig})')
                                    
                                    # Get resolution (DPI)
                                    if hasattr(page, 'tags') and 282 in page.tags and 283 in page.tags:
                                        x_resolution = page.tags[282].value
                                        y_resolution = page.tags[283].value
                                        
                                        # Handle tuple resolution values (convert to float)
                                        if isinstance(x_resolution, tuple) and len(x_resolution) == 2:
                                            x_resolution = float(x_resolution[0]) / float(x_resolution[1])
                                        if isinstance(y_resolution, tuple) and len(y_resolution) == 2:
                                            y_resolution = float(y_resolution[0]) / float(y_resolution[1])
                                        
                                        # Check resolution unit
                                        resolution_unit = 2  # Default is inches
                                        if 296 in page.tags:
                                            resolution_unit = page.tags[296].value
                                        
                                        # Convert resolution to DPI if needed
                                        if resolution_unit == 1:  # No unit, use as is
                                            metadata['dpi_x'] = float(x_resolution)
                                            metadata['dpi_y'] = float(y_resolution)
                                        elif resolution_unit == 2:  # Inches
                                            metadata['dpi_x'] = float(x_resolution)
                                            metadata['dpi_y'] = float(y_resolution)
                                        elif resolution_unit == 3:  # Centimeters
                                            # Convert from pixels/cm to pixels/inch
                                            metadata['dpi_x'] = float(x_resolution) * 2.54
                                            metadata['dpi_y'] = float(y_resolution) * 2.54
                                    
                                    # Get compression
                                    if hasattr(page, 'compression'):
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
                                        metadata['compression'] = compression_types.get(
                                            page.compression, f'Unknown ({page.compression})')
                                    
                                    # Check if image is tiled
                                    if hasattr(page, 'is_tiled') and page.is_tiled:
                                        metadata['is_tiled'] = 'Yes'
                                        metadata['tile_width'] = page.tilewidth
                                        metadata['tile_height'] = page.tilelength
                                
                                # Get software information
                                if hasattr(tif, 'software') and tif.software:
                                    metadata['software'] = tif.software
                                
                                # Get datetime information
                                if hasattr(tif, 'datetime') and tif.datetime:
                                    metadata['datetime'] = tif.datetime
                                
                                # Check for metadata types
                                metadata['xmp'] = 'Yes' if hasattr(tif, 'xmp') and tif.xmp else 'No'
                                metadata['exif'] = 'Yes' if hasattr(tif, 'exif') and tif.exif else 'No'
                                metadata['iptc'] = 'Yes' if hasattr(tif, 'iptc') and tif.iptc else 'No'
                                
                                # Check if it's a BigTIFF
                                metadata['is_bigtiff'] = 'Yes' if tif.is_bigtiff else 'No'
                                
                                # Check TIFF version
                                metadata['tiff_version'] = f"{tif.byteorder} {tif.version}"
                                
                                # Color profile information
                                if hasattr(tif, 'is_colored') and tif.is_colored:
                                    if 34675 in page.tags:  # ICC profile tag
                                        metadata['color_profile'] = 'ICC Profile Present'
                                    else:
                                        metadata['color_profile'] = 'No ICC Profile'
                                
                                # Set mode based on photometric interpretation
                                if 'photometric' in metadata:
                                    if metadata['photometric'] == 'BlackIsZero':
                                        metadata['mode'] = 'Grayscale'
                                    elif metadata['photometric'] == 'WhiteIsZero':
                                        metadata['mode'] = 'Grayscale (Inverted)'
                                    elif metadata['photometric'] == 'RGB':
                                        metadata['mode'] = 'RGB'
                                    elif metadata['photometric'] == 'Palette':
                                        metadata['mode'] = 'Palette'
                                    elif metadata['photometric'] == 'CMYK':
                                        metadata['mode'] = 'CMYK'
                                    elif metadata['photometric'] == 'YCbCr':
                                        metadata['mode'] = 'YCbCr'
                                    elif metadata['photometric'] in ['CIELab', 'ICCLab']:
                                        metadata['mode'] = 'Lab'
                                
                        except Exception as tiff_error:
                            # If tifffile fails, fall back to Pillow
                            if status_callback:
                                status_callback(f"tifffile extraction failed for {filename}, falling back to Pillow")
                        
                        # If tifffile failed, try with Pillow
                        if not tifffile_success:
                            try:
                                with Image.open(file_path) as img:
                                    metadata['width'] = img.width
                                    metadata['height'] = img.height
                                    metadata['format'] = img.format
                                    metadata['mode'] = img.mode

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
                            except Exception as pil_error:
                                # If both tifffile and Pillow fail, add to non-TIFF files with error
                                self.results['non_tiff_files'].append({
                                    'filename': filename,
                                    'path': file_path,
                                    'rel_path': os.path.join(rel_path, filename),
                                    'size': file_size,
                                    'error': f"tifffile error: {str(tiff_error)}, PIL error: {str(pil_error)}"
                                })
                                # Skip to next file
                                continue
                        
                        # Add to TIFF files list
                        self.results['tiff_files'].append(metadata)
                        
                        # Update folder statistics
                        self.results['folders'][dirpath]['tiff_count'] += 1
                        self.results['folders'][dirpath]['total_size'] += file_size
                                
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