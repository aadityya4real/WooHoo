# scripts/install_dependencies.py
#
# Run this once from inside TouchDesigner's Textport so the packages install
# into TD's own Python environment:
#
#   exec(open('scripts/install_dependencies.py').read())
#
# (Path is relative to TD's working directory - use an absolute path if that
# doesn't resolve, e.g. exec(open(project.folder + '/scripts/install_dependencies.py').read()) )

import subprocess
import sys

REQUIRED_PACKAGES = ['mediapipe']          # needed by scripts/hand_tracker.py
OPTIONAL_PACKAGES = ['opencv-python']      # only needed if you want a separate cv2 debug window


def _pip_install(package):
    print(f'Installing {package}...')
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])


def install_dependencies(include_optional=False):
    print('Starting dependency installation for TouchDesigner...')
    try:
        for package in REQUIRED_PACKAGES:
            _pip_install(package)
        if include_optional:
            for package in OPTIONAL_PACKAGES:
                _pip_install(package)
        print('Installation successful! Restart TouchDesigner if hand_tracker.py '
              'still reports a missing dependency.')
    except Exception as e:
        print(f'Error during installation: {e}')
        print('Try running TouchDesigner as Administrator, or install manually via CMD using '
              'the same python.exe that ships inside the TouchDesigner install folder.')


if __name__ == '__main__':
    install_dependencies()
