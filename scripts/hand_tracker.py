# scripts/hand_tracker.py
#
# Script CHOP callback. Reads frames from a Video Device In TOP (default name
# 'videoin1'), runs MediaPipe Hands on them, tracks the index fingertip, and
# detects a thumb-to-middle-finger "snap" gesture by combining distance and
# closing velocity. Outputs four channels:
#
#   index_x, index_y   - normalized (0-1) position of the index fingertip
#   snap               - 1 for one cook right after a snap is detected, else 0
#   fire_intensity      - 0..FIRE_MAX_INTENSITY, decays over FIRE_DECAY_TIME
#
# Wire this CHOP's name into the GLSL TOP's uIndexPos / uIntensity uniforms
# (see scripts/build_network.py).
#
# Requires: mediapipe (and its numpy dependency). Run
# scripts/install_dependencies.py once from TouchDesigner's Textport if you
# haven't already.

import time

try:
    import numpy as np
    import mediapipe as mp
    DEPENDENCIES_OK = True
    _import_error = None
except ImportError as e:
    DEPENDENCIES_OK = False
    _import_error = str(e)

# ---- Tunable parameters -------------------------------------------------
SOURCE_TOP_NAME = 'videoin1'     # Video Device In TOP feeding this tracker
SNAP_DIST_THRESHOLD = 0.06       # normalized thumb-middle distance counted as "closed"
SNAP_VELOCITY_THRESHOLD = 0.35   # min closing speed (norm. units/sec) to count as a snap
SNAP_COOLDOWN = 0.25             # seconds; ignore new snaps within this window
FIRE_DECAY_TIME = 2.5            # seconds for fire to fully fade after the last snap
FIRE_MAX_INTENSITY = 2.0         # cap, so repeated snaps "intensify" instead of blowing out
FIRE_BOOST_PER_SNAP = 0.6        # intensity added by each new snap


class TrackerState:
    def __init__(self):
        self.index_x = 0.5
        self.index_y = 0.5
        self.prev_thumb_middle_dist = None
        self.prev_sample_time = time.time()
        self.fire_start_time = -999.0
        self.fire_start_intensity = 0.0
        self.snap_pulse_until = 0.0
        self.hands = None
        self.warned = False


if 'state' not in globals():
    state = TrackerState()
    if DEPENDENCIES_OK:
        state.hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6,
        )


def _get_frame_rgb():
    """Pull the latest frame from the webcam TOP as an RGB uint8 numpy array."""
    video_top = op(SOURCE_TOP_NAME)
    if video_top is None:
        return None
    frame = video_top.numpyArray(delayed=True)  # float32 RGBA, 0-1, bottom-to-top rows
    if frame is None:
        return None
    frame = np.flipud(frame)
    return (frame[:, :, :3] * 255).astype(np.uint8)


def _current_fire_intensity(now):
    elapsed = now - state.fire_start_time
    if elapsed >= FIRE_DECAY_TIME or elapsed < 0:
        return 0.0
    return state.fire_start_intensity * (1.0 - elapsed / FIRE_DECAY_TIME)


def onCook(scriptOp):
    scriptOp.clear()

    tx = scriptOp.appendChan('index_x')
    ty = scriptOp.appendChan('index_y')
    snap_chan = scriptOp.appendChan('snap')
    fire_chan = scriptOp.appendChan('fire_intensity')

    now = time.time()
    dt = max(now - state.prev_sample_time, 1e-4)
    state.prev_sample_time = now

    if not DEPENDENCIES_OK:
        if not state.warned:
            print('hand_tracker.py: missing dependency ({}). Run '
                  'scripts/install_dependencies.py from the Textport.'.format(_import_error))
            state.warned = True
        tx[0] = state.index_x
        ty[0] = state.index_y
        snap_chan[0] = 0.0
        fire_chan[0] = _current_fire_intensity(now)
        return

    snap_detected = False
    frame_rgb = _get_frame_rgb()

    if frame_rgb is not None:
        results = state.hands.process(frame_rgb)
        if results.multi_hand_landmarks:
            lm = results.multi_hand_landmarks[0].landmark

            # MediaPipe hand landmark indices: 4 = thumb tip, 8 = index tip, 12 = middle tip
            thumb_tip = lm[4]
            index_tip = lm[8]
            middle_tip = lm[12]

            state.index_x = index_tip.x
            state.index_y = index_tip.y

            dist = ((thumb_tip.x - middle_tip.x) ** 2 +
                    (thumb_tip.y - middle_tip.y) ** 2) ** 0.5

            if state.prev_thumb_middle_dist is not None:
                closing_velocity = (state.prev_thumb_middle_dist - dist) / dt
                snap_ready = (now - (state.fire_start_time if state.fire_start_time > 0 else -999)) > SNAP_COOLDOWN
                if (dist < SNAP_DIST_THRESHOLD and
                        closing_velocity > SNAP_VELOCITY_THRESHOLD and
                        snap_ready):
                    snap_detected = True

            state.prev_thumb_middle_dist = dist

    if snap_detected:
        boosted = min(_current_fire_intensity(now) + FIRE_BOOST_PER_SNAP, FIRE_MAX_INTENSITY)
        state.fire_start_intensity = boosted
        state.fire_start_time = now
        state.snap_pulse_until = now + 0.05

    tx[0] = state.index_x
    ty[0] = state.index_y
    snap_chan[0] = 1.0 if now < state.snap_pulse_until else 0.0
    fire_chan[0] = _current_fire_intensity(now) if not snap_detected else state.fire_start_intensity

    return
