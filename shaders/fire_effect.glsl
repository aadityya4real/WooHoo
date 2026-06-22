// shaders/fire_effect.glsl
// Procedural fire pixel shader for TouchDesigner's GLSL TOP.
// Driven by scripts/hand_tracker.py via three uniforms:
//   uTime       - seconds, e.g. wired to absTime.seconds
//   uIndexPos   - normalized (0-1) index fingertip position, from hand_tracker1
//   uIntensity  - 0..2.0, from hand_tracker1 (fades out, boosts on repeat snaps)
//
// NOTE: TouchDesigner's GLSL TOP automatically supplies `vec3 vUV` as the
// fragment's normalized texture coordinate - no need to declare it yourself.

uniform float uTime;
uniform vec2 uIndexPos;
uniform float uIntensity;

out vec4 fragColor;

// Simple hash function for noise
float hash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

// 2D Noise function
float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(a, b, u.x) + (c - a) * u.y * (1.0 - u.x) + (d - b) * u.x * u.y;
}

// Fractal Brownian Motion for realistic flames
float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    vec2 shift = vec2(100.0);
    for (int i = 0; i < 5; ++i) {
        v += a * noise(p);
        p = p * 2.0 + shift;
        a *= 0.5;
    }
    return v;
}

void main() {
    vec2 uv = vUV.st;

    // Flip Y because webcam/tracking coordinates are often inverted relative to UV space
    vec2 target = vec2(uIndexPos.x, 1.0 - uIndexPos.y);

    // Distance from the index fingertip
    vec2 diff = uv - target;
    diff.y *= 1.2; // stretch flames vertically

    float dist = length(diff);

    // Animate the noise upward
    vec2 noise_uv = uv * 10.0;
    noise_uv.y -= uTime * 5.0;

    float n = fbm(noise_uv);

    // Shape the flame: tapered at top, wider at bottom
    float flame_shape = 1.0 - (dist * 15.0);
    flame_shape += n * 0.4;

    // Apply intensity - 0 means no flame, >1.0 (repeat snaps) makes it bigger/brighter
    flame_shape *= clamp(uIntensity, 0.0, 2.0);

    // Color mapping (Yellow -> Orange -> Red)
    vec3 color = vec3(1.5, 0.5, 0.1) * flame_shape;
    color += vec3(1.0, 1.0, 0.0) * pow(max(0.0, flame_shape - 0.4), 2.0);

    float alpha = smoothstep(0.0, 0.1, flame_shape);

    fragColor = vec4(color, alpha);
}
