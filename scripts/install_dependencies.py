import subprocess
import sys
import os

def install_dependencies():
    print("Starting dependency installation for TouchDesigner...")
    # Get the path to TouchDesigner's internal python executable
    # In TD, you can run this in a Text DAT
    try:
        packages = ['mediapipe', 'opencv-python']
        for package in packages:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print("Installation successful!")
    except Exception as e:
        print(f"Error during installation: {e}")
        print("Try running TouchDesigner as Administrator or manually installing via CMD.")

if __name__ == "__main__":
    install_dependencies()
