import mediapipe as mp
import numpy as np
import time

# Internal state for the tracker
class TrackerState:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.prev_dist = 0
        self.last_snap_time = 0

# Initialize global state
if 'state' not in globals():
    state = TrackerState()

def onCook(scriptOp):
    scriptOp.clear()
    
    # Create output channels
    tx = scriptOp.appendChan('index_x')
    ty = scriptOp.appendChan('index_y')
    snap = scriptOp.appendChan('snap')
    
    # Default values
    tx[0] = 0.5
    ty[0] = 0.5
    snap[0] = 0
    
    # Try to get the input video from a parameter or a connected TOP
    # We assume the user drags the TOP into a custom parameter named 'Videoinput'
    # or we can look for a TOP named 'cam_in'
    video_in = scriptOp.par.Videoinput.eval() if hasattr(scriptOp.par, 'Videoinput') else op('cam_in')
    
    if video_in:
        # Get the pixels as a numpy array
        pixels = video_in.numpyArray()
        if pixels is not None:
            # MediaPipe expects 0-255 RGB uint8
            img = (pixels[:,:,:3] * 255).astype(np.uint8)
            
            results = state.hands.process(img)
            
            if results.multi_hand_landmarks:
                hand = results.multi_hand_landmarks[0]
                thumb = hand.landmark[4]
                index = hand.landmark[8]
                middle = hand.landmark[12]
                
                # Update positions
                tx[0] = index.x
                ty[0] = index.y
                
                # Snap detection
                dist = ((thumb.x - middle.x)**2 + (thumb.y - middle.y)**2)**0.5
                velocity = abs(dist - state.prev_dist)
                
                if dist < 0.05 and velocity > 0.08:
                    if time.time() - state.last_snap_time > 0.5:
                        snap[0] = 1
                        state.last_snap_time = time.time()
                
                state.prev_dist = dist
    return
