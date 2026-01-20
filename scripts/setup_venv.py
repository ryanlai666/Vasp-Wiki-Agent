#!/usr/bin/env python3
"""
Script to set up Python virtual environment for VASP Wiki RAG Agent.
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    project_root = Path(__file__).parent.parent
    venv_path = project_root / "venv"
    
    print("Setting up Python virtual environment...")
    
    # Check if venv already exists
    if venv_path.exists():
        print(f"Virtual environment already exists at {venv_path}")
        response = input("Do you want to recreate it? (y/N): ")
        if response.lower() != 'y':
            print("Keeping existing virtual environment.")
            return
        import shutil
        shutil.rmtree(venv_path)
        print("Removed existing virtual environment.")
    
    # Create virtual environment
    print(f"Creating virtual environment at {venv_path}...")
    subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
    
    # Determine activation script path
    # On Windows (including Git Bash), venv uses Scripts/python.exe
    # On Unix (Linux/Mac/WSL), venv uses bin/python
    if sys.platform == "win32":
        python_path = venv_path / "Scripts" / "python.exe"
    else:
        python_path = venv_path / "bin" / "python"
    
    # Resolve to absolute path to avoid issues
    python_path = python_path.resolve()
    
    # Verify the Python executable exists
    if not python_path.exists():
        print(f"Error: Python executable not found at {python_path}")
        print("Please check that the virtual environment was created correctly.")
        sys.exit(1)
    
    print("Installing dependencies...")
    requirements_file = project_root / "requirements.txt"
    
    if not requirements_file.exists():
        print(f"Error: {requirements_file} not found!")
        sys.exit(1)
    
    # Use python -m pip instead of calling pip directly (more reliable)
    # Try to upgrade pip, but don't fail if it can't
    print("Upgrading pip...")
    upgrade_result = subprocess.run(
        [str(python_path), "-m", "pip", "install", "--upgrade", "pip"],
        capture_output=True
    )
    if upgrade_result.returncode != 0:
        print("Warning: Could not upgrade pip (this is usually okay)")
        print(upgrade_result.stderr.decode() if upgrade_result.stderr else "")
    
    # Install requirements
    print("Installing requirements...")
    subprocess.run(
        [str(python_path), "-m", "pip", "install", "-r", str(requirements_file)],
        check=True
    )
    
    print("\n" + "="*50)
    print("Virtual environment setup complete!")
    print("="*50)
    print("\nTo activate the virtual environment:")
    if sys.platform == "win32":
        # Windows (PowerShell, CMD, or Git Bash)
        print(f"  # In Git Bash:")
        print(f"  source {venv_path}/Scripts/activate")
        print(f"  # In PowerShell:")
        print(f"  .\\venv\\Scripts\\Activate.ps1")
        print(f"  # In CMD:")
        print(f"  {venv_path}\\Scripts\\activate.bat")
    else:
        # Linux/Mac/WSL
        print(f"  source {venv_path}/bin/activate")
    print("\nTo verify installation:")
    print(f"  {python_path} --version")
    print(f"  {python_path} -m pip list")

if __name__ == "__main__":
    main()
