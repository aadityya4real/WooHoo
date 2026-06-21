// Simple Pulsing Circle Shader for TouchDesigner
// To use: Link this to a GLSL TOP's Pixel Shader parameter

uniform float uTime; // TouchDesigner's default time uniform

out vec4 fragColor;

void main() {
    // Get normalized coordinates (0.0 to 1.0)
    vec2 uv = vUV.st;
    
    // Shift coordinates to center (-0.5 to 0.5)
    vec2 center = uv - 0.5;
    
    // Adjust for aspect ratio if needed (assuming square for this test)
    float dist = length(center);
    
    // Create a pulsing radius using sin and time
    float radius = 0.2 + 0.1 * sin(uTime * 3.0);
    
    // Smooth edges for the circle
    float circle = smoothstep(radius, radius - 0.01, dist);
    
    // Color: Cyan pulse
    vec3 color = vec3(0.0, 1.0, 1.0) * circle;
    
    fragColor = vec4(color, 1.0);
}
