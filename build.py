# build.py
import os
import sys
import shutil
import PyInstaller.__main__

def build_app():
    """Build the application for the current platform"""
    
    # Ensure resources directory exists
    if not os.path.exists('resources'):
        os.makedirs('resources')
    
    # Create basic files if they don't exist
    if not os.path.exists('resources/styles.qss'):
        with open('resources/styles.qss', 'w') as f:
            f.write('/* CSS styles will be here */')
    
    # Platform-specific options
    if sys.platform.startswith('win'):
        icon_file = 'resources/icon.ico'
        output_name = 'TIFF_Preservation_Tool'
    elif sys.platform.startswith('darwin'):
        icon_file = 'resources/icon.icns'
        output_name = 'TIFF_Preservation_Tool'
    else:
        icon_file = 'resources/icon.png'
        output_name = 'tiff_preservation_tool'
    
    # Create default icon if it doesn't exist
    if not os.path.exists(icon_file):
        # This would normally create a default icon file
        print(f"Warning: Icon file {icon_file} not found. Using default PyInstaller icon.")
    
    # Build command
    pyinstaller_args = [
        'main.py',
        '--name=' + output_name,
        '--onefile',
        '--windowed',
        '--add-data=resources:resources',
        '--clean'
    ]
    
    # Add icon if it exists
    if os.path.exists(icon_file):
        pyinstaller_args.append('--icon=' + icon_file)
    
    # Run PyInstaller
    PyInstaller.__main__.run(pyinstaller_args)
    
    print(f"Build completed. Executable is in the dist/ directory.")

if __name__ == "__main__":
    build_app()