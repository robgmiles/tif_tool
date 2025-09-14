import os
import sys
import shutil
import PyInstaller.__main__

def build_app():
    """Build the application for the current platform using --onedir mode"""
    
    # Ensure resources directory exists
    if not os.path.exists('resources'):
        os.makedirs('resources')
    
    # Create basic files if they don't exist
    if not os.path.exists('resources/styles.qss'):
        with open('resources/styles.qss', 'w') as f:
            f.write('/* Default CSS styles */\n')
            f.write('QMainWindow { background-color: #f0f0f0; }\n')
    
    # Platform-specific options
    if sys.platform.startswith('win'):
        icon_file = 'resources/icon.ico'
        output_name = 'TIFF_Preservation_Tool'
    else:
        icon_file = 'resources/icon.png'
        output_name = 'tiff_preservation_tool'
    
    # Create output on Desktop for visibility
    desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
    work_path = os.path.join(desktop_path, 'build_work')
    dist_path = os.path.join(desktop_path, 'TIFF_Tool_Build')
    
    # Make sure work and dist directories exist and are empty
    for path in [work_path, dist_path]:
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
            except Exception as e:
                print(f"Warning: Could not remove directory {path}: {e}")
        try:
            os.makedirs(path)
        except Exception as e:
            print(f"Warning: Could not create directory {path}: {e}")
    
    # Determine the correct separator for resource paths based on platform
    # On Windows, the separator is a semicolon; on others, it's a colon
    separator = ';' if sys.platform.startswith('win') else ':'
    
    # Build command - using --onedir mode (by omitting --onefile)
    pyinstaller_args = [
        'main.py',
        '--name=' + output_name,
        '--windowed',
        f'--add-data=resources{separator}resources',  # Use platform-specific separator
        '--workpath=' + work_path,
        '--distpath=' + dist_path,
        '--noconfirm',
        '--clean'
    ]
    
    # Add icon if it exists
    if os.path.exists(icon_file):
        pyinstaller_args.append('--icon=' + icon_file)
    
    # Run PyInstaller
    try:
        PyInstaller.__main__.run(pyinstaller_args)
        print(f"Build completed. Application is available at: {os.path.join(dist_path, output_name)}")
        
        # Verify that the resources were correctly packaged
        resource_dir = os.path.join(dist_path, output_name, 'resources')
        if os.path.exists(resource_dir):
            print(f"Resources directory found at: {resource_dir}")
            
            # List files in the resources directory
            resource_files = os.listdir(resource_dir)
            print(f"Resources included: {', '.join(resource_files)}")
        else:
            print("Warning: Resources directory not found in the packaged application!")
            
    except Exception as e:
        print(f"Build failed: {str(e)}")
    finally:
        # Clean up only the work directory, keep the dist for the user
        try:
            if os.path.exists(work_path):
                shutil.rmtree(work_path)
        except Exception as e:
            print(f"Warning: Could not remove work directory: {e}")

if __name__ == "__main__":
    build_app()