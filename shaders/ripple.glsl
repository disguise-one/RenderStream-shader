#version 330 core

uniform float frequency = 25.0; // RS: min=0 max=50
uniform float speed = 1; // RS: max=5
uniform float amplitude = 1; // RS: min=0 max=30 display="Magnitude"
uniform vec4 peakColour = vec4(0.9, 0.9, 0.9, 0.1); // RS: isColour=True
uniform sampler2D input;

uniform float time; // RS: engine=frameData.localTime
uniform vec2 screenRes; // RS: engine="(stream.width, stream.height)"

#define PI 3.1415

float distSquared(vec2 a, vec2 b)
{
    vec2 v = a - b;
    return dot(v, v);
}


float wave(vec2 pos, vec2 center) {
	float d = distance(pos * screenRes, center * screenRes);

	return amplitude * (sin(-frequency * (d*PI) / 1000 + time * speed) + 1) / 2.0;
}

out vec4 fragColor;
in vec2 fragCoord;
void main()
{
	float height = wave(fragCoord, vec2(0.75, 0.25));
	height += wave(fragCoord, vec2(0.25, 0.75));

	vec2 uv = fragCoord + vec2(dFdx(height), dFdy(height));

	fragColor = texture(input, uv);

	fragColor.rgb = mix(fragColor.rgb, peakColour.rgb, clamp((height / amplitude) * peakColour.a, 0, 1));
	// fragColor = vec4(height, 0, 0, 1);
}
