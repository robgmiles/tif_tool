import os
import hashlib
import csv
import datetime

class ChecksumGenerator:
    def __init__(self):
        self.buffer_size = 65536  # 64KB buffer for reading files
    
    def generate_checksums(self, folder_path, algorithm="sha256", format_type="per_folder",
                          progress_callback=None, status_callback=None):
        """
        Generate checksums for all files in a folder
        
        Args:
            folder_path: Path to process
            algorithm: Hash algorithm to use (sha256)
            format_type: 'per_folder' or 'consolidated'
            progress_callback: Function to call with progress updates (0-100)
            status_callback: Function to call with status messages
            
        Returns:
            Dictionary with results
        """
        results = {
            'checksums': {},
            'output_files': []
        }
        
        # Count total files for progress
        total_files = 0
        for root, _, files in os.walk(folder_path):
            total_files += len(files)
        
        if total_files == 0:
            if status_callback:
                status_callback("No files found")
            return results
        
        # Track processed files for progress
        processed_files = 0
        
        # Process files based on format type
        if format_type == "consolidated":
            # Single output file
            output_file = os.path.join(folder_path, f"checksums_{algorithm}.txt")
            consolidated_checksums = []
            
            for root, _, files in os.walk(folder_path):
                for filename in files:
                    file_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(file_path, folder_path)
                    
                    # Skip the checksum file itself if it exists
                    if rel_path == f"checksums_{algorithm}.txt":
                        continue
                    
                    if status_callback:
                        status_callback(f"Processing: {rel_path}")
                    
                    # Generate checksum
                    checksum = self._calculate_checksum(file_path, algorithm)
                    
                    # Store in results dictionary
                    results['checksums'][rel_path] = checksum
                    
                    # Add to consolidated list
                    consolidated_checksums.append((checksum, rel_path))
                    
                    # Update progress
                    processed_files += 1
                    if progress_callback:
                        progress_value = int((processed_files / total_files) * 100)
                        progress_callback(progress_value)
            
            # Write consolidated checksums file
            with open(output_file, 'w') as f:
                for checksum, rel_path in consolidated_checksums:
                    f.write(f"{checksum} *{rel_path}\n")
            
            results['output_files'].append(output_file)
            
        else:  # per_folder
            # Generate checksum file per folder
            for root, _, files in os.walk(folder_path):
                if not files:
                    continue
                
                # Create relative path for the current folder
                rel_root = os.path.relpath(root, folder_path)
                
                # Skip if this is just the output file from a previous run
                if len(files) == 1 and files[0] == f"checksums_{algorithm}.txt":
                    continue
                
                # Prepare checksum file for this folder
                checksum_file = os.path.join(root, f"checksums_{algorithm}.txt")
                folder_checksums = []
                
                for filename in files:
                    # Skip the checksum file itself if it exists
                    if filename == f"checksums_{algorithm}.txt":
                        continue
                    
                    file_path = os.path.join(root, filename)
                    
                    if status_callback:
                        status_callback(f"Processing: {os.path.join(rel_root, filename)}")
                    
                    # Generate checksum
                    checksum = self._calculate_checksum(file_path, algorithm)
                    
                    # Store in results dictionary
                    rel_path = os.path.join(rel_root, filename)
                    if rel_root == '.':
                        rel_path = filename
                    results['checksums'][rel_path] = checksum
                    
                    # Add to folder checksums
                    folder_checksums.append((checksum, filename))
                    
                    # Update progress
                    processed_files += 1
                    if progress_callback:
                        progress_value = int((processed_files / total_files) * 100)
                        progress_callback(progress_value)
                
                # Write checksum file for this folder
                if folder_checksums:
                    with open(checksum_file, 'w') as f:
                        for checksum, filename in folder_checksums:
                            f.write(f"{checksum} *{filename}\n")
                    
                    results['output_files'].append(checksum_file)
        
        if status_callback:
            status_callback(f"Checksums generated for {len(results['checksums'])} files.")
        
        return results
    
    def validate_checksums(self, folder_path, progress_callback=None, status_callback=None):
        """
        Validate checksums for files in a folder
        
        Args:
            folder_path: Path to process
            progress_callback: Function to call with progress updates (0-100)
            status_callback: Function to call with status messages
            
        Returns:
            Dictionary with validation results
        """
        results = {
            'total_files': 0,
            'valid_files': 0,
            'invalid_files': [],
            'missing_checksums': [],
            'missing_files': []
        }
        
        # Find checksum files
        checksum_files = []
        for root, _, files in os.walk(folder_path):
            for filename in files:
                if filename.startswith('checksums_') and filename.endswith('.txt'):
                    checksum_files.append(os.path.join(root, filename))
        
        if not checksum_files:
            if status_callback:
                status_callback("No checksum files found")
            return results
        
        # Track total files to validate
        total_to_validate = 0
        expected_checksums = {}  # Map of file path to expected checksum
        
        # Read all checksum files first
        for checksum_file in checksum_files:
            checksum_dir = os.path.dirname(checksum_file)
            
            with open(checksum_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Parse line (format: "checksum *filename")
                    parts = line.split(' *', 1)
                    if len(parts) != 2:
                        continue
                    
                    checksum, filename = parts
                    
                    # Determine if this is a relative or absolute path
                    if os.path.isabs(filename) or '/' in filename or '\\' in filename:
                        # This is a consolidated checksum file with relative paths
                        file_path = os.path.join(folder_path, filename)
                    else:
                        # This is a per-folder checksum file
                        file_path = os.path.join(checksum_dir, filename)
                    
                    # Track this file for validation
                    expected_checksums[file_path] = checksum
                    total_to_validate += 1
        
        results['total_files'] = total_to_validate
        
        if total_to_validate == 0:
            if status_callback:
                status_callback("No files to validate in checksum files")
            return results
        
        # Validate each file
        processed_files = 0
        
        for file_path, expected_checksum in expected_checksums.items():
            if not os.path.exists(file_path):
                results['missing_files'].append(file_path)
                processed_files += 1
                continue
            
            if status_callback:
                rel_path = os.path.relpath(file_path, folder_path)
                status_callback(f"Validating: {rel_path}")
            
            # Calculate actual checksum
            # Determine algorithm from checksum length
            if len(expected_checksum) == 64:  # SHA-256
                algorithm = 'sha256'
            elif len(expected_checksum) == 40:  # SHA-1
                algorithm = 'sha1'
            elif len(expected_checksum) == 32:  # MD5
                algorithm = 'md5'
            else:
                algorithm = 'sha256'  # Default to SHA-256
            
            actual_checksum = self._calculate_checksum(file_path, algorithm)
            
            # Compare checksums
            if actual_checksum.lower() == expected_checksum.lower():
                results['valid_files'] += 1
            else:
                rel_path = os.path.relpath(file_path, folder_path)
                results['invalid_files'].append({
                    'path': rel_path,
                    'expected': expected_checksum,
                    'actual': actual_checksum
                })
            
            # Update progress
            processed_files += 1
            if progress_callback:
                progress_value = int((processed_files / total_to_validate) * 100)
                progress_callback(progress_value)
        
        # Final status update
        if status_callback:
            valid_count = results['valid_files']
            invalid_count = len(results['invalid_files'])
            missing_count = len(results['missing_files'])
            
            status_message = f"Validation complete: {valid_count} valid, {invalid_count} invalid, {missing_count} missing"
            status_callback(status_message)
        
        return results
    
    def _calculate_checksum(self, file_path, algorithm='sha256'):
        """Calculate checksum for a file"""
        if algorithm == 'sha256':
            hasher = hashlib.sha256()
        elif algorithm == 'sha1':
            hasher = hashlib.sha1()
        elif algorithm == 'md5':
            hasher = hashlib.md5()
        else:
            hasher = hashlib.sha256()  # Default to SHA-256
        
        with open(file_path, 'rb') as f:
            buffer = f.read(self.buffer_size)
            while len(buffer) > 0:
                hasher.update(buffer)
                buffer = f.read(self.buffer_size)
        
        return hasher.hexdigest()