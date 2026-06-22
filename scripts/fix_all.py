# scripts/fix_all.py
# Run this in the TouchDesigner Textport:
#   exec(open('scripts/fix_all.py').read())
#
# Fixes:
#   1. Installs mediapipe into TD's Python
#   2. Wires uTime / uIndexPos / uIntensity on the GLSL TOP

import subprocess, sys

# ── 1. Install mediapipe ──────────────────────────────────────────────────────
print("Installing mediapipe...")
try:
    subprocess.check_call([sys.executable, "-m", "pip", "install",
                           "mediapipe", "--quiet"])
    print("mediapipe installed OK.")
except Exception as e:
    print(f"pip failed: {e}  — try running TD as Administrator.")

# ── 2. Wire uniforms on the GLSL TOP ─────────────────────────────────────────
glsl = op('/project1/fire_shader1')
if glsl is None:
    print("ERROR: /project1/fire_shader1 not found. Did build_network.py finish?")
else:
    # TouchDesigner GLSL TOP stores uniforms on the 'Vectors' page.
    # Scalar float  -> par.value0name / par.value0
    # Vec2          -> par.vec0name  / par.vec0x  / par.vec0y
    # The exact prefix ('value' vs 'val' vs 'uniform') varies by TD build,
    # so we try all common ones.

    def set_uniform_float(glsl_op, slot, name, expr):
        """Try every known parameter naming convention for a float uniform."""
        for prefix in ('value', 'val', 'uniform'):
            try:
                getattr(glsl_op.par, f'{prefix}{slot}name').val = name
                getattr(glsl_op.par, f'{prefix}{slot}').expr = expr
                print(f"  {name} wired via '{prefix}{slot}'")
                return True
            except AttributeError:
                continue
        print(f"  WARNING: could not wire {name} - set it manually on GLSL TOP Vectors page.")
        return False

    def set_uniform_vec2(glsl_op, slot, name, expr_x, expr_y):
        """Try every known parameter naming convention for a vec2 uniform."""
        for prefix in ('vec', 'value', 'val', 'uniform'):
            try:
                getattr(glsl_op.par, f'{prefix}{slot}name').val = name
                getattr(glsl_op.par, f'{prefix}{slot}x').expr = expr_x
                getattr(glsl_op.par, f'{prefix}{slot}y').expr = expr_y
                print(f"  {name} wired via '{prefix}{slot}'")
                return True
            except AttributeError:
                continue
        print(f"  WARNING: could not wire {name} - set it manually on GLSL TOP Vectors page.")
        return False

    print("Wiring uniforms on fire_shader1...")
    set_uniform_float(glsl, 0, 'uTime',      "absTime.seconds")
    set_uniform_vec2 (glsl, 1, 'uIndexPos',
                      "op('/project1/hand_tracker1')['index_x']",
                      "op('/project1/hand_tracker1')['index_y']")
    set_uniform_float(glsl, 2, 'uIntensity',
                      "op('/project1/hand_tracker1')['fire_intensity']")

    print("Done. Restart TouchDesigner now so mediapipe loads cleanly.")
    print("After restart, reopen the project - the GLSL TOP and tracker should both go green.")
