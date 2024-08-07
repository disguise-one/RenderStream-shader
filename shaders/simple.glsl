#version 330

out vec4 fragColor;
in vec2 fragCoord;

uniform float blue;

void main()
{
    fragColor = vec4(fragCoord.x, fragCoord.y, blue, 1.0);
}