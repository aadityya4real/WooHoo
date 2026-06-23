# scripts/force_mediapipe.py
# exec(open('scripts/force_mediapipe.py').read())
import sys, os, importlib.util

TD_SITE = r'C:\Program Files\Derivative\TouchDesigner\bin\Lib\site-packages'
MP_INIT  = os.path.join(TD_SITE, 'mediapipe', '__init__.py')

print('Checking:', MP_INIT)
print('Exists:', os.path.exists(MP_INIT))

# Wipe TD's fake stub + all submodules
for k in list(sys.modules.keys()):
    if 'mediapipe' in k:
        del sys.modules[k]

if not os.path.exists(MP_INIT):
    print('ERROR: mediapipe not at expected path. Run in Admin CMD:')
    print(r'"C:\Program Files\Derivative\TouchDesigner\bin\python.exe" -m pip install mediapipe==0.10.14 --target "C:\Program Files\Derivative\TouchDesigner\bin\Lib\site-packages"')
else:
    # Put real path FIRST so all submodule imports resolve correctly
    if TD_SITE not in sys.path:
        sys.path.insert(0, TD_SITE)
    else:
        sys.path.remove(TD_SITE)
        sys.path.insert(0, TD_SITE)

    # Load real mediapipe directly from file
    spec = importlib.util.spec_from_file_location(
        'mediapipe', MP_INIT,
        submodule_search_locations=[os.path.join(TD_SITE, 'mediapipe')]
    )
    mp = importlib.util.module_from_spec(spec)
    sys.modules['mediapipe'] = mp
    spec.loader.exec_module(mp)

    print('Loaded from:', mp.__file__)
    print('Version:', mp.__version__)

    # Now test the hand tracker import
    try:
        from mediapipe.python.solutions.hands import Hands
        print('Hands import OK')
    except Exception as e:
        print('Hands import FAILED:', e)

    # Inject into hand_tracker callback
    NEW_CODE = open(project.folder + '/scripts/hand_tracker.py').read()
    for dat in root.findChildren(type=textDAT):
        if 'hand_tracker' in dat.name.lower() and 'callback' in dat.name.lower():
            dat.text = NEW_CODE
            dat.par.syncfile = False
            print('Injected tracker into:', dat.path)

    # Fix GLSL TOP uniform error
    for g in root.findChildren(type=glslTOP):
        try:
            g.par.vec0valuex.expr = 'absTime.seconds'
            g.par.vec1valuex.expr = "float(op('/project1/hand_tracker1')['index_x'] or 0.5)"
            g.par.vec1valuey.expr = "float(op('/project1/hand_tracker1')['index_y'] or 0.5)"
            g.par.vec2valuex.expr = "float(op('/project1/hand_tracker1')['fire_intensity'] or 0.0)"
            print('Uniforms fixed on:', g.path)
        except: pass

    print('\nDone! Ctrl+S to save.')
