# exec(open('scripts/final_fix.py').read())
import sys

# 1. Add mediapipe path
mp_path = r'C:\users\aadit\appdata\roaming\python\python311\site-packages'
if mp_path not in sys.path:
    sys.path.insert(0, mp_path)

CORRECT_CODE = r'''import sys
_mp_path = r'C:\users\aadit\appdata\roaming\python\python311\site-packages'
if _mp_path not in sys.path:
    sys.path.insert(0, _mp_path)

import time
try:
    import numpy as np
    import mediapipe as mp
    DEPS_OK = True
except ImportError as e:
    DEPS_OK = False
    _ERR = str(e)
    print('hand_tracker: MISSING DEP:', e)

SOURCE_TOP = 'cam_in'
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
            print('MediaPipe Hands initialized OK')

ST = State()

def _intensity(now):
    e = now - ST.fire_t
    if e < 0 or e >= DECAY: return 0.0
    return ST.fire_i * (1.0 - e / DECAY)

def onCook(scriptOp):
    scriptOp.clear()
    tx = scriptOp.appendChan('index_x')
    ty = scriptOp.appendChan('index_y')
    sn = scriptOp.appendChan('snap')
    fi = scriptOp.appendChan('fire_intensity')
    now = time.time()
    dt  = max(now - ST.prev_t, 1e-4); ST.prev_t = now

    if not DEPS_OK:
        tx[0]=0.5; ty[0]=0.5; sn[0]=0; fi[0]=0
        return

    snap = False
    vtop = op(SOURCE_TOP)
    if vtop is None:
        print('hand_tracker: cannot find op:', SOURCE_TOP)
        tx[0]=ST.ix; ty[0]=ST.iy; sn[0]=0; fi[0]=_intensity(now)
        return

    frame = vtop.numpyArray(delayed=True)
    if frame is not None:
        frame = (np.flipud(frame)[:,:,:3]*255).astype(np.uint8)
        res = ST.hands.process(frame)
        if res.multi_hand_landmarks:
            lm = res.multi_hand_landmarks[0].landmark
            th = lm[4]; ix_lm = lm[8]; mi = lm[12]
            ST.ix = ix_lm.x; ST.iy = ix_lm.y
            d = ((th.x-mi.x)**2+(th.y-mi.y)**2)**0.5
            if ST.prev_dist is not None:
                vel = (ST.prev_dist - d) / dt
                if d < SNAP_DIST and vel > SNAP_VEL and (now - ST.fire_t) > COOLDOWN:
                    snap = True
                    print('SNAP detected! dist=', round(d,3), 'vel=', round(vel,3))
            ST.prev_dist = d

    if snap:
        ST.fire_i = min(_intensity(now)+BOOST, MAX_INT)
        ST.fire_t = now; ST.snap_until = now + 0.08

    tx[0]=ST.ix; ty[0]=ST.iy
    sn[0]=1.0 if now < ST.snap_until else 0.0
    fi[0]=ST.fire_i if snap else _intensity(now)
'''

# 2. Overwrite ALL callback DATs with correct code (SOURCE_TOP = 'cam_in')
fixed = 0
for dat in root.findChildren(type=textDAT):
    if 'callback' in dat.name.lower():
        dat.text = CORRECT_CODE
        dat.par.syncfile = False
        print('Fixed:', dat.path)
        fixed += 1

if fixed == 0:
    print('No callback DATs found!')

# 3. Create permanent startup DAT
existing = op('/project1/mediapipe_path_fix')
startup = existing if existing else op('/project1').create(textDAT, 'mediapipe_path_fix')
startup.text = ("import sys\n"
    r"_p=r'C:\users\aadit\appdata\roaming\python\python311\site-packages'" + "\n"
    "if _p not in sys.path: sys.path.insert(0,_p)\n"
    "print('mediapipe path loaded')")
startup.par.executeonstart = True
print('Startup DAT ready:', startup.path)

# 4. Re-wire uniforms properly
glsls = root.findChildren(type=glslTOP)
schops = root.findChildren(type=scriptCHOP)
if glsls and schops:
    g = glsls[0]
    cpath = schops[0].path
    try:
        g.par.vec0name.val    = 'uTime'
        g.par.vec0valuex.expr = 'absTime.seconds'
        g.par.vec1name.val    = 'uIndexPos'
        g.par.vec1valuex.expr = f"op('{cpath}')['index_x']"
        g.par.vec1valuey.expr = f"op('{cpath}')['index_y']"
        g.par.vec2name.val    = 'uIntensity'
        g.par.vec2valuex.expr = f"op('{cpath}')['fire_intensity']"
        print('Uniforms wired:', g.path, '->', cpath)
    except Exception as e:
        print('Uniform error:', e)

print('\nDone! Ctrl+S then RESTART TD. Fire will work after restart.')
