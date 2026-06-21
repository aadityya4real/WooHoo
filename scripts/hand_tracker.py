import time

# Safe TouchDesigner tracker state
class TrackerState:
    def __init__(self):
        self.index_x = 0.5
        self.index_y = 0.5
        self.prev_dist = 0
        self.last_snap_time = 0
        self.fire_intensity = 0

# Initialize global state
if 'state' not in globals():
    state = TrackerState()


def onCook(scriptOp):
    scriptOp.clear()

    tx = scriptOp.appendChan('index_x')
    ty = scriptOp.appendChan('index_y')
    snap = scriptOp.appendChan('snap')
    fire = scriptOp.appendChan('fire_intensity')

    tx[0] = state.index_x
    ty[0] = state.index_y
    snap[0] = 0
    fire[0] = state.fire_intensity

    return