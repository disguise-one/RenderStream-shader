# Shader uniform syntax

Uniforms take the form:

`uniform <type> <name> = <default value>; // RS: <attr>=<value> <attr2>="<value with spaces>"`

Other than the `<type>` and `<name>`, which are required by GLSL syntax, all other values are optional.

## Common attributes
All uniforms are able to use the following attributes

### `group`
Puts the exposed parameter into a different group in the Designer UI.

### `display`
Change the text the exposed parameter is displayed as in the Designer UI.

## Numeric attributes
Numeric attributes, including vectors, are controllable using the following attributes

### `isColour`
If set to `True`, specifies that the vec4 is treated as a colour.

### `min`, `max`,  `step`
For floating point and vector values, provides the range used for editing within Designer.

### `engine`
Executes the contents of the attribute as python code which sets the uniform. The uniform is not exposed. There are a number of variables available:

* `frameData` - the RS.FrameData object for the current frame. 
* `stream` - the RS.StreamDescription object for the current stream
* `paramValues` - the values for the exposed parameters, allowing computed properties based on other uniforms.

The example shaders use the engine attribute. For example, a uniform which contains the resolution of the current stream served by this instance could be

`uniform vec2 iResolution; // RS: engine=(stream.width,stream.height)`

#### `FrameData` properties

    tTracked: ctypes.c_double   # disguise tracked time - not related to animation
    localTime: ctypes.c_double  # Engine-local animation time
    localTimeDelta: ctypes.c_double  # delta time since the last frame affecting the engine-local animation time
    frameRateNumerator: ctypes.c_uint
    frameRateDenominator: ctypes.c_uint
    flags: FrameDataFlags  # Flags to control frame processing
    scene: ctypes.c_uint32  # Hash of the selected scene for this frame.

#### `StreamDescription` properties

    handle: StreamHandle
    channel: ctypes.c_char_p
    mappingId: ctypes.c_uint64
    iViewpoint: ctypes.c_int32
    name: ctypes.c_char_p
    width: ctypes.c_uint32
    height: ctypes.c_uint32
    format: RSPixelFormat
    clipping: ProjectionClipping

## Sampler attributes
Samplers have different attributes to control the source of the texture data and how the sampler interprets texture data.

### `image`
The texture data is loaded as an image from the `images` folder. It is not exposed as a parameter to RenderStream.

The value must be the filename of the file in the images folder, including the extension, but excluding the folder.

### `pass`
The texture data is generated every frame by a secondary shader. Helpful for optimisation and separating parts of the workload.

The value must be the filename of the shader file in the `shaders/passes` folder, including the extension but excluding the folder.

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