import os
import shutil
import hashlib
import time
import logging
from datetime import datetime

class FileTransferManager:
    def __init__(self):
        self.buffer_size = 16 * 1024 * 1024  # 16MB buffer
        self.max_retries = 3
        
        # Set up logging
        self.log_file = None
        self.logger = logging.getLogger('file_transfer')
        self.logger.setLevel(logging.INFO)
    
    def transfer_files(self, source_path, dest_path, 
                      overall_progress_callback=None,
                      file_progress_callback=None,
                      status_callback=None):
        """
        Transfer files from source to destination with integrity verification
        
        Args:
            source_path: Source directory
            dest_path: Destination directory
            overall_progress_callback: Function for overall progress updates
            file_progress_callback: Function for current file progress updates
            status_callback: Function for status message updates
            
        Returns:
            Dictionary with transfer statistics
        """
        # Set up logging for this transfer
        self._setup_logging(dest_path)
        
        # Results tracking
        results = {
            'start_time': datetime.now(),
            'end_time': None,
            'files_transferred': 0,
            'total_size': 0,  # in bytes
            'total_size_mb': 0,  # in MB
            'errors': 0,
            'retries': 0
        }
        
        # Get file list with sizes
        files_to_transfer = []
        total_size = 0
        
        if status_callback:
            status_callback("Scanning source directory...")
        
        for root, _, files in os.walk(source_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, source_path)
                
                try:
                    file_size = os.path.getsize(file_path)
                    files_to_transfer.append({
                        'source': file_path,
                        'destination': os.path.join(dest_path, rel_path),
                        'rel_path': rel_path,
                        'size': file_size
                    })
                    total_size += file_size
                except Exception as e:
                    self.logger.error(f"Error getting size for {file_path}: {str(e)}")
                    results['errors'] += 1
        
        if len(files_to_transfer) == 0:
            message = "No files found to transfer"
            if status_callback:
                status_callback(message)
            self.logger.info(message)
            return results
        
        # Create destination directories as needed
        self._create_destination_dirs(source_path, dest_path, files_to_transfer)
        
        # Update status
        if status_callback:
            status_callback(f"Transferring {len(files_to_transfer)} files ({total_size / (1024*1024):.2f} MB)")
        
        # Track progress
        transferred_size = 0
        
        # Transfer each file
        for i, file_info in enumerate(files_to_transfer):
            source_file = file_info['source']
            dest_file = file_info['destination']
            rel_path = file_info['rel_path']
            file_size = file_info['size']
            
            # Update status
            if status_callback:
                status_callback(f"Copying: {rel_path} ({file_size / (1024*1024):.2f} MB)")
            
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(dest_file), exist_ok=True)
            
            # Transfer the file with verification
            success, retries = self._transfer_file_with_verification(
                source_file, 
                dest_file, 
                file_size,
                file_progress_callback
            )
            
            # Update statistics
            if success:
                results['files_transferred'] += 1
                results['total_size'] += file_size
                results['retries'] += retries
            else:
                results['errors'] += 1
            
            # Update overall progress
            transferred_size += file_size
            if overall_progress_callback:
                progress = int((transferred_size / total_size) * 100)
                overall_progress_callback(progress)
        
        # Finalize results
        results['end_time'] = datetime.now()
        results['duration'] = (results['end_time'] - results['start_time']).total_seconds()
        results['total_size_mb'] = results['total_size'] / (1024 * 1024)
        
        # Final log
        self.logger.info(f"Transfer complete: {results['files_transferred']} files, "
                         f"{results['total_size_mb']:.2f} MB, {results['errors']} errors")
        
        # Final status update
        if status_callback:
            status_callback(f"Transfer complete: {results['files_transferred']} files transferred")
        
        return results
    
    def _transfer_file_with_verification(self, source_file, dest_file, file_size,
                                        file_progress_callback=None):
        """
        Transfer a single file with checksum verification and retry logic
        
        Returns:
            (success, retries) tuple
        """
        retries = 0
        max_retries = self.max_retries
        
        while retries <= max_retries:
            try:
                # Copy the file with progress updates
                self._copy_with_progress(source_file, dest_file, file_size, file_progress_callback)
                
                # Verify the file integrity
                source_checksum = self._calculate_checksum(source_file)
                dest_checksum = self._calculate_checksum(dest_file)
                
                if source_checksum == dest_checksum:
                    # Transfer succeeded
                    if retries > 0:
                        self.logger.info(f"Transfer of {dest_file} succeeded after {retries} retries")
                    return True, retries
                
                # Checksum mismatch
                retries += 1
                self.logger.warning(f"Checksum verification failed for {dest_file}, "
                                   f"retry {retries}/{max_retries}")
                
                # Delete the failed copy
                if os.path.exists(dest_file):
                    os.remove(dest_file)
                
                # If we've reached max retries, give up
                if retries > max_retries:
                    self.logger.error(f"Max retries reached for {dest_file}")
                    return False, retries
                
                # Wait briefly before retry
                time.sleep(1)
                
            except Exception as e:
                retries += 1
                self.logger.error(f"Error transferring {source_file} to {dest_file}: {str(e)}")
                
                # If we've reached max retries, give up
                if retries > max_retries:
                    return False, retries
                
                # Wait briefly before retry
                time.sleep(1)
        
        return False, retries
    
    def _copy_with_progress(self, source_file, dest_file, file_size, progress_callback=None):
        """Copy a file with progress updates"""
        copied_size = 0
        
        with open(source_file, 'rb') as src, open(dest_file, 'wb') as dst:
            while True:
                buffer = src.read(self.buffer_size)
                if not buffer:
                    break
                
                dst.write(buffer)
                copied_size += len(buffer)
                
                if progress_callback:
                    progress = int((copied_size / file_size) * 100) if file_size > 0 else 100
                    progress_callback(progress)
    
    def _calculate_checksum(self, file_path):
        """Calculate SHA256 checksum for a file"""
        hasher = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            buffer = f.read(self.buffer_size)
            while len(buffer) > 0:
                hasher.update(buffer)
                buffer = f.read(self.buffer_size)
        
        return hasher.hexdigest()
    
    def _create_destination_dirs(self, source_path, dest_path, files_to_transfer):
        """Create all necessary destination directories"""
        directories = set()
        
        for file_info in files_to_transfer:
            dir_path = os.path.dirname(file_info['destination'])
            directories.add(dir_path)
        
        for dir_path in directories:
            os.makedirs(dir_path, exist_ok=True)
    
    def _setup_logging(self, base_path):
        """Set up logging for this transfer"""
        log_dir = os.path.join(base_path, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file = os.path.join(log_dir, f'transfer_{timestamp}.log')
        
        # Create file handler
        file_handler = logging.FileHandler(self.log_file)
        file_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        self.logger.addHandler(file_handler)
        
        # Log transfer start
        self.logger.info(f"Transfer started at {datetime.now()}")