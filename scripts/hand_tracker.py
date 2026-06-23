# hand_tracker.py - compatible with mediapipe 0.10.x
# Place in scripts/ folder. In TD Textport run:
#   exec(open('scripts/apply_tracker.py').read())

import time

try:
    from mediapipe.python.solutions import hands as mp_hands_module
    from mediapipe.python.solutions.hands import Hands
    DEPS_OK = True
except ImportError as e:
    DEPS_OK = False
    _ERR = str(e)

SOURCE_TOP  = 'cam_in'
SNAP_DIST   = 0.06
SNAP_VEL    = 0.35
COOLDOWN    = 0.25
DECAY       = 2.5
MAX_INT     = 2.0
BOOST       = 0.6

class State:
    def __init__(self):
        self.ix = 0.5; self.iy = 0.5
        self.prev_dist = None
        self.prev_t = time.time()
        self.fire_t = -999.0; self.fire_i = 0.0
        self.snap_until = 0.0
        self.hands = None
        if DEPS_OK:
            self.hands = Hands(
                static_image_mode=False, max_num_hands=1,
                min_detection_confidence=0.6, min_tracking_confidence=0.6)
            print('MediaPipe Hands initialized OK')
        else:
            print('hand_tracker MISSING DEP:', _ERR)

if 'ST' not in globals():
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
        tx[0]=0.5; ty[0]=0.5; sn[0]=0; fi[0]=0; return

    snap = False
    vtop = op(SOURCE_TOP)
    if vtop is None:
        print('hand_tracker: cannot find op:', SOURCE_TOP)
        tx[0]=ST.ix; ty[0]=ST.iy; sn[0]=0; fi[0]=_intensity(now); return

    frame = vtop.numpyArray(delayed=True)
    if frame is not None:
        import numpy as np
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
                    print('SNAP! dist=%.3f vel=%.2f' % (d, vel))
            ST.prev_dist = d

    if snap:
        ST.fire_i = min(_intensity(now)+BOOST, MAX_INT)
        ST.fire_t = now; ST.snap_until = now + 0.08

    tx[0]=ST.ix; ty[0]=ST.iy
    sn[0]=1.0 if now < ST.snap_until else 0.0
    fi[0]=ST.fire_i if snap else _intensity(now)
