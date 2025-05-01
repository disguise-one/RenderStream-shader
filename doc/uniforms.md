# Shader Uniform Syntax

Uniforms in GLSL shaders define properties that remain constant over a single frame. They are declared as:

`uniform <type> <name> = <default value>; // RS: <attr>=<value> <attr2>="<value with spaces>"`

Only `<type>` and `<name>` are required by GLSL syntax. All other values are optional.

## Common Attributes

### `group`
Organizes the exposed parameter into a specific group in the Designer UI.

### `display`
Specifies a custom label for the parameter in the Designer UI.

## Numeric Attributes

For numeric uniforms, including vectors, the following attributes are available:

### `isColour`
If set to `True`, treats the `vec4` as a colour.

### `min`, `max`, `step`
Defines the range and step size for editing floating-point and vector values in Designer.

### `engine`
Executes Python code to set the uniform value dynamically. The uniform is not exposed as a parameter. Available variables include:

- `frameData`: The `RS.FrameData` object for the current frame.
- `stream`: The `RS.StreamDescription` object for the current stream.
- `paramValues`: Values of other exposed parameters, enabling computed properties.

Example:

`uniform vec2 iResolution; // RS: engine=(stream.width,stream.height)`

#### `FrameData` Properties

- `tTracked`: Tracked time (not related to animation).
- `localTime`: Engine-local animation time.
- `localTimeDelta`: Time delta since the last frame.
- `frameRateNumerator`, `frameRateDenominator`: Frame rate details.
- `flags`: Frame processing flags.
- `scene`: Hash of the selected scene for this frame.

#### `StreamDescription` Properties

- `handle`, `channel`, `mappingId`, `iViewpoint`, `name`: Stream metadata.
- `width`, `height`: Stream resolution.
- `format`: Pixel format.
- `clipping`: Projection clipping.

## Sampler Attributes

Samplers control texture data sources and interpretation. Attributes include:

### `image`
The texture data is loaded as an image from the `images` folder. It is not exposed as a parameter to RenderStream.

The value must be the filename of the file in the images folder, including the extension, but excluding the folder.

### `pass`
Generates texture data every frame using a secondary shader. Specify the filename (with extension) from the `shaders/passes` folder.

### `previous`
The texture data is reused from a previous frame.

The value must be either `this`, to access the previously generated frame, or the name of a sampler.

Note that using this is likely to cause discrepancies in a cluster environment if frames are ever skipped, as the previous data will diverge.

### `min_filter`, `mag_filter`
How to minify or magnify texture data when sampled at a different scale than the original texture data.

Mipmap levels are only available for image texture data, not for live streamed texture inputs.

* `nearest` - No interpolation (see: `GL_NEAREST`)
* `linear` - (*Default*) Linear interpolation (see: `GL_LINEAR`)
* `nearest_mipmap_nearest` - No interpolation, select nearest mip level (see: `GL_NEAREST_MIPMAP_NEAREST`)
* `nearest_mipmap_linear` -  No interpolation, blend between mip levels (see: `GL_NEAREST_MIPMAP_LINEAR`)
* `linear_mipmap_nearest` - Linear interpolation, select nearest mip level (see: `GL_LINEAR_MIPMAP_NEAREST`)
* `linear_mipmap_linear` - Linear interpolation, blend between mip levels (see: `GL_LINEAR_MIPMAP_LINEAR`)

### `wrap`, `wrap_s`, `wrap_t`
These options determine how the sampler behaves when the input UV coordinate is outside the 0-1 range.

`wrap` is a convenience method for specifying both `wrap_s` and `wrap_t` together.

* `clamp_to_edge` - Stretches the final pixel at the edge (see: `GL_CLAMP_TO_EDGE`)
* `clamp_to_border` - Switches to a predefined `border_colour` (see: `GL_CLAMP_TO_BORDER`)
* `mirrored_repeat` - Mirrors the texture on every repeat (see: `GL_MIRRORED_REPEAT`)
* `repeat` - (*Default*) Wraps around between 0 and 1 (see: `GL_REPEAT`)
* `mirror_clamp_to_edge` - allows a single mirrored repeat before clamping to the final pixel value (see: `GL_MIRROR_CLAMP_TO_EDGE`)

### `border_colour`
This is a tuple of 4 values which hold the colour the sampler should use at the edge of the texture when `clamp_to_border` is specified.

The default is `(0, 0, 0, 0)`