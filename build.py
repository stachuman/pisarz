#!/usr/bin/env python3
"""
Build script for creating standalone executables of Pisarz
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return the result"""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
        print(f"Success: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return False

def clean_build():
    """Clean previous build artifacts"""
    print("Cleaning build artifacts...")
    
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Removed {dir_name}")
    
    # Clean .pyc files
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                os.remove(os.path.join(root, file))

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    
    if not run_command([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip']):
        return False
    
    if not run_command([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt']):
        return False
    
    return True

def build_executable():
    """Build the executable using PyInstaller"""
    print("Building executable...")
    
    # Check if spec file exists
    spec_file = 'pisarz.spec'
    if not os.path.exists(spec_file):
        print(f"Error: {spec_file} not found")
        return False
    
    # Build with PyInstaller
    cmd = [sys.executable, '-m', 'PyInstaller', spec_file, '--clean', '--noconfirm']
    
    if not run_command(cmd):
        return False
    
    # Check if executable was created
    if sys.platform == 'win32':
        exe_path = 'dist/pisarz.exe'
    else:
        exe_path = 'dist/pisarz'
    
    if os.path.exists(exe_path):
        print(f"Executable created: {exe_path}")
        return True
    else:
        print("Error: Executable not found after build")
        return False

def create_installer():
    """Create installer package"""
    print("Creating installer package...")
    
    # Create a simple installer directory structure
    installer_dir = Path('installer')
    installer_dir.mkdir(exist_ok=True)
    
    # Copy executable
    if sys.platform == 'win32':
        exe_name = 'pisarz.exe'
        archive_name = 'pisarz-windows.zip'
    else:
        exe_name = 'pisarz'
        archive_name = 'pisarz-linux.tar.gz'
    
    exe_path = Path('dist') / exe_name
    if exe_path.exists():
        # Copy to installer directory
        shutil.copy2(exe_path, installer_dir / exe_name)
        
        # Create README for installer
        readme_content = f"""# Pisarz - Writing Application

## Installation

1. Extract this archive to your desired location
2. Run the executable: {exe_name}

## System Requirements

- Operating System: {'Windows 10+' if sys.platform == 'win32' else 'Linux (Ubuntu 18.04+ or equivalent)'}
- Memory: 512 MB RAM minimum
- Storage: 200 MB free space

## Features

- Rich text editing with RTF support
- Project management for writing projects
- Character and location management
- Scene organization
- Search functionality
- LLM integration for AI assistance
- Internationalization support (English, Polish)
- Focus mode for distraction-free writing

## Support

For support and bug reports, please visit:
https://github.com/yourusername/pisarz/issues

## License

This software is provided under the MIT License.
"""
        
        with open(installer_dir / 'README.txt', 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"Installer created in {installer_dir}")
        return True
    
    return False

def main():
    """Main build function"""
    print("=== Pisarz Build Script ===")
    
    # Check if we're in the right directory
    if not os.path.exists('main.py'):
        print("Error: main.py not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Clean previous builds
    clean_build()
    
    # Install dependencies
    if not install_dependencies():
        print("Failed to install dependencies")
        sys.exit(1)
    
    # Build executable
    if not build_executable():
        print("Failed to build executable")
        sys.exit(1)
    
    # Create installer
    if not create_installer():
        print("Failed to create installer")
        sys.exit(1)
    
    print("\n=== Build Complete ===")
    print("Executable built successfully!")
    
    if sys.platform == 'win32':
        print("Windows executable: dist/pisarz.exe")
    else:
        print("Linux executable: dist/pisarz")
    
    print("Installer package: installer/")

if __name__ == '__main__':
    main()