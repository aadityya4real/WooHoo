# scripts/build_network.py
#
# TouchDesigner project files (.toe) are a proprietary binary format, so they
# can't be authored as a text file in this repo. Instead, this script uses
# TouchDesigner's own Python API to BUILD the operator network for you, the
# same way you'd build it by hand by dragging operators into the network
# editor. Run it once per new/empty project.
#
# HOW TO RUN
#   1. Open (or create) your TouchDesigner project and save it inside this
#      repo folder so relative paths line up.
#   2. Open the Textport: Dialogs > Textport (or Alt+T / Cmd+T).
#   3. exec(open('scripts/build_network.py').read())
#
# WHAT IT BUILDS (all inside /project1)
#   videoin1        Video Device In TOP   - webcam source
#   hand_tracker1   Script CHOP           - runs scripts/hand_tracker.py
#   fire_pixel_shader  Text DAT           - holds shaders/fire_effect.glsl, Sync to File ON
#   fire_shader1    GLSL TOP              - renders the fire using the tracker's channels
#   composite1      Over TOP              - layers fire_shader1 on top of videoin1
#   output1         Null TOP              - final output, hook your Window COMP to this
#
# NOTE ON GLSL TOP UNIFORM PARAMETER NAMES
#   The exact parameter names for "Vectors" / "Values" pages on the GLSL TOP
#   differ slightly between TouchDesigner builds. If the uniform-wiring lines
#   below raise an AttributeError, open fire_shader1's parameters dialog,
#   go to the Vectors/Values page by hand, and point:
#     uTime      -> absTime.seconds
#     uIndexPos  -> op('hand_tracker1')['index_x'] / ['index_y']
#     uIntensity -> op('hand_tracker1')['fire_intensity']
#   Everything else in this script is unaffected by that.

import os

REPO_ROOT = project.folder  # assumes the .toe lives at the repo root; edit if not


def build():
    root = op('/project1')
    if root is None:
        root = root_op  # fallback to root network if /project1 doesn't exist in your TD version

    # 1. Webcam input -------------------------------------------------------
    videoin = root.create(videodeviceinTOP, 'videoin1')
    videoin.par.device = 0  # change index if you have more than one camera
    videoin.nodeX, videoin.nodeY = 0, 0

    # 2. Hand tracking Script CHOP ------------------------------------------
    tracker = root.create(scriptCHOP, 'hand_tracker1')
    tracker.par.callbacks = os.path.join(REPO_ROOT, 'scripts', 'hand_tracker.py')
    tracker.nodeX, tracker.nodeY = 0, -150
    # hand_tracker.py reads op('videoin1') directly, so keep both operators
    # in this same network.

    # 3. Fire pixel shader, loaded from the repo with Sync to File ----------
    fire_dat = root.create(textDAT, 'fire_pixel_shader')
    fire_dat.par.file = os.path.join(REPO_ROOT, 'shaders', 'fire_effect.glsl')
    fire_dat.par.syncfile = True
    fire_dat.nodeX, fire_dat.nodeY = 200, -300

    # 4. GLSL TOP -------------------------------------------------------------
    fire = root.create(glslTOP, 'fire_shader1')
    fire.par.pixeldat = fire_dat
    fire.par.resolutionw = 1280
    fire.par.resolutionh = 720
    try:
        fire.par.value0name = 'uTime'
        fire.par.value0 = 'absTime.seconds'
        fire.par.value1name = 'uIndexPos'
        fire.par.value1x = "op('hand_tracker1')['index_x']"
        fire.par.value1y = "op('hand_tracker1')['index_y']"
        fire.par.value2name = 'uIntensity'
        fire.par.value2 = "op('hand_tracker1')['fire_intensity']"
    except AttributeError:
        print('Uniform parameter names differ on this TD build - see the NOTE at the '
              'top of build_network.py and wire uTime/uIndexPos/uIntensity by hand.')
    fire.nodeX, fire.nodeY = 200, -150

    # 5. Composite webcam + fire ---------------------------------------------
    comp = root.create(overTOP, 'composite1')
    comp.inputConnectors[0].connect(videoin)
    comp.inputConnectors[1].connect(fire)
    comp.nodeX, comp.nodeY = 400, 0

    # 6. Final output -----------------------------------------------------------
    out = root.create(nullTOP, 'output1')
    out.inputConnectors[0].connect(comp)
    out.nodeX, out.nodeY = 600, 0

    print('Hand-tracking fire effect network built. Hook a Window COMP to output1 to display it.')


build()
