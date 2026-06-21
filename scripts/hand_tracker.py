import cv2
import mediapipe as mp
import time

# This script is designed to be used inside a Script CHOP or a Python DAT in TouchDesigner
# It outputs hand landmark positions and detects a 'snap' gesture.

class HandTracker:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.prev_dist = 0
        self.snap_threshold = 0.05
        self.velocity_threshold = 0.1
        self.last_snap_time = 0

    def process_frame(self, frame):
        # Convert the BGR image to RGB
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(image)
        
        index_pos = [0.5, 0.5] # Default center
        snap_detected = 0
        
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Landmark 4: Thumb Tip
                # Landmark 8: Index Tip
                # Landmark 12: Middle Tip
                
                thumb = hand_landmarks.landmark[4]
                index = hand_landmarks.landmark[8]
                middle = hand_landmarks.landmark[12]
                
                # Update index finger position
                index_pos = [index.x, index.y]
                
                # Calculate distance between thumb and middle finger for snap detection
                dist = ((thumb.x - middle.x)**2 + (thumb.y - middle.y)**2)**0.5
                velocity = abs(dist - self.prev_dist)
                
                # Detect snap: sudden decrease in distance or high velocity movement between thumb and middle
                if dist < self.snap_threshold and velocity > self.velocity_threshold:
                    if time.time() - self.last_snap_time > 0.5: # Debounce
                        snap_detected = 1
                        self.last_snap_time = time.time()
                
                self.prev_dist = dist
                
        return index_pos, snap_detected

# For TouchDesigner Script CHOP usage:
# tracker = HandTracker()
# def onCook(scriptOp):
#     frame = op('video_input').numpyArray() # Simplified logic
#     pos, snap = tracker.process_frame(frame)
#     scriptOp.appendChan('index_x')[0] = pos[0]
#     scriptOp.appendChan('index_y')[1] = pos[1]
#     scriptOp.appendChan('snap')[0] = snap
