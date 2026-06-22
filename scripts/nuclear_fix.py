# scripts/nuclear_fix.py
# Run in Textport: exec(open('scripts/nuclear_fix.py').read())
# Fixes: mediapipe install, bad callback DAT content, uniform wiring

import sys, subprocess

# ── 1. Diagnose & install mediapipe ──────────────────────────────────────────
print("=== Python executable:", sys.executable)
try:
    import mediapipe
    print("mediapipe already importable:", mediapipe.__version__)
except ImportError:
    print("mediapipe not found. Installing with --force-reinstall...")
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install',
            'mediapipe', '--force-reinstall', '--no-cache-dir'
        ])
        print("Install done. Verifying...")
        import importlib
        import importlib.util
        spec = importlib.util.find_spec('mediapipe')
        if spec:
            print("mediapipe found at:", spec.origin)
        else:
            print("STILL not found after install.")
            print("Manual fix: open CMD as Admin and run:")
            print(" ", sys.executable, "-m pip install mediapipe")
    except Exception as e:
        print("Install failed:", e)

# ── 2. Overwrite ALL script callback DATs with safe try/except code ───────────
SAFE_CALLBACKS = '''import time

try:
    import numpy as np
    import mediapipe as mp
    DEPS_OK = True
except ImportError as e:
    DEPS_OK = False
    _ERR = str(e)

SOURCE_TOP = 'videoin1'
SNAP_DIST  = 0.06
SNAP_VEL   = 0.35
COOLDOWN   = 0.25
DECAY      = 2.5
MAX_INT    = 2.0
BOOST      = 0.6

class State:
    def __init__(self):
        self.ix = 0.5; self.iy = 0.5
        self.prev_dist = None
        self.prev_t = time.time()
        self.fire_t = -999.0; self.fire_i = 0.0
        self.snap_until = 0.0
        self.hands = None
        if DEPS_OK:
            self.hands = mp.solutions.hands.Hands(
                static_image_mode=False, max_num_hands=1,
                min_detection_confidence=0.6, min_tracking_confidence=0.6)

if 'ST' not in globals():
    ST = State()

def _intensity(now):
    e = now - ST.fire_t
    if e < 0 or e >= DECAY: return 0.0
    return ST.fire_i * (1.0 - e / DECAY)

def onCook(scriptOp):
    scriptOp.clear()
    tx  = scriptOp.appendChan('index_x')
    ty  = scriptOp.appendChan('index_y')
    sn  = scriptOp.appendChan('snap')
    fi  = scriptOp.appendChan('fire_intensity')
    now = time.time()
    dt  = max(now - ST.prev_t, 1e-4); ST.prev_t = now

    if not DEPS_OK:
        print('hand_tracker: missing dep:', _ERR)
        tx[0]=ST.ix; ty[0]=ST.iy; sn[0]=0; fi[0]=_intensity(now)
        return

    snap = False
    vtop = op(SOURCE_TOP)
    if vtop:
        frame = vtop.numpyArray(delayed=True)
        if frame is not None:
            import numpy as np
            frame = (np.flipud(frame)[:,:,:3]*255).astype(np.uint8)
            res = ST.hands.process(frame)
            if res.multi_hand_landmarks:
                lm = res.multi_hand_landmarks[0].landmark
                th = lm[4]; ix = lm[8]; mi = lm[12]
                ST.ix = ix.x; ST.iy = ix.y
                d = ((th.x-mi.x)**2+(th.y-mi.y)**2)**0.5
                if ST.prev_dist is not None:
                    vel = (ST.prev_dist - d) / dt
                    gap = now - ST.fire_t
                    if d < SNAP_DIST and vel > SNAP_VEL and gap > COOLDOWN:
                        snap = True
                ST.prev_dist = d

    if snap:
        ST.fire_i = min(_intensity(now)+BOOST, MAX_INT)
        ST.fire_t = now; ST.snap_until = now + 0.05

    tx[0]=ST.ix; ty[0]=ST.iy
    sn[0]=1.0 if now < ST.snap_until else 0.0
    fi[0]=ST.fire_i if snap else _intensity(now)
'''

# Find every Text DAT with 'callback' or 'script' in its name and rewrite it
fixed = 0
for dat in root.findChildren(type=textDAT):
    if 'callback' in dat.name.lower() or ('script' in dat.name.lower() and 'callbacks' in dat.name.lower()):
        dat.text = SAFE_CALLBACKS
        dat.par.syncfile = False   # don't overwrite our edit from file
        print("Rewrote:", dat.path)
        fixed += 1
if fixed == 0:
    print("No callback DATs found - are operators in /project1?")

# ── 3. Wire uniforms using the correct vec0/vec1/vec2 parameter names ─────────
glsl_ops = root.findChildren(type=glslTOP)
if not glsl_ops:
    print("No GLSL TOP found - run build_network.py first then re-run this.")
else:
    g = glsl_ops[0]
    print("Wiring uniforms on:", g.path)
    try:
        g.par.vec0name.val   = 'uTime'
        g.par.vec0valuex.expr = 'absTime.seconds'
        g.par.vec1name.val   = 'uIndexPos'
        # find the Script CHOP
        schop = root.findChildren(type=scriptCHOP)
        cpath = schop[0].path if schop else '/project1/hand_tracker1'
        g.par.vec1valuex.expr = f"op('{cpath}')['index_x']"
        g.par.vec1valuey.expr = f"op('{cpath}')['index_y']"
        g.par.vec2name.val   = 'uIntensity'
        g.par.vec2valuex.expr = f"op('{cpath}')['fire_intensity']"
        print("Uniforms wired to:", cpath)
    except AttributeError as e:
        print("Uniform wire error:", e)

print("\n=== Done. Press Ctrl+S to save, then RESTART TouchDesigner. ===")
