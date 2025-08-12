"""
Build script for creating executable from Stock Management System
"""
import os
import subprocess
import sys

def create_exe():
    """Create executable using PyInstaller"""
    
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define the main script
    main_script = os.path.join(current_dir, "main.py")
    
    # Define PyInstaller command
    pyinstaller_cmd = [
        "pyinstaller",
        "--onefile",                    # Create a single executable file
        "--windowed",                   # Don't show console window
        "--name=StockManagement",       # Name of the executable
        "--icon=logo.png",              # Use logo as icon (if available)
        "--add-data=logo.png;.",        # Include logo.png
        "--add-data=loginbackground.jpg;.",  # Include background image
        "--add-data=models;models",     # Include models directory
        "--add-data=ui;ui",             # Include ui directory
        "--add-data=utils;utils",       # Include utils directory
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=pyodbc",
        "--hidden-import=reportlab",
        "--hidden-import=arabic_reshaper",
        "--hidden-import=bidi",
        "--hidden-import=sqlalchemy",
        "--distpath=dist",              # Output directory
        "--workpath=build",             # Build directory
        "--specpath=.",                 # Spec file location
        main_script
    ]
    
    print("Creating executable with PyInstaller...")
    print("Command:", " ".join(pyinstaller_cmd))
    
    try:
        # Run PyInstaller
        result = subprocess.run(pyinstaller_cmd, check=True, capture_output=True, text=True)
        print("PyInstaller output:")
        print(result.stdout)
        
        if result.stderr:
            print("PyInstaller warnings/errors:")
            print(result.stderr)
        
        print("\n✅ Executable created successfully!")
        print(f"📁 Location: {os.path.join(current_dir, 'dist', 'StockManagement.exe')}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating executable: {e}")
        print(f"Return code: {e.returncode}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        
    except FileNotFoundError:
        print("❌ PyInstaller not found. Please install it first:")
        print("pip install pyinstaller")

if __name__ == "__main__":
    create_exe()
