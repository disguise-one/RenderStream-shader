## RenderStream-ShaderToy

Loads GLSL fragment shaders and presents them as selectable RenderStream scenes.

Shader uniforms are exposed as controllable RenderStream parameters.

## Installing

1. Ensure [RenderStream-Python](https://github.com/disguise-one/renderStream-py) is installed
2. Copy the repository into a folder in your RenderStream Projects folder.
3. In Designer, configure a RenderStream layer to use the shadertoy asset.

## Shader uniform syntax

Uniforms can be extended with attributes which control how the property is exposed to RenderStream.

They take the form:

`uniform <type> <name> = <default value>; // RS: <attr>=<value> <attr2>="<value with spaces>"`

Other than the `<type>` and `<name>`, which are required by GLSL syntax, all other values are optional.

### Attribute list

#### `isColour`
If set to `True`, specifies that the vec4 is treated as a colour.

#### `engine`
Executes the contents of the attribute as python code which sets the uniform. The uniform is not exposed. There are a number of variables available:

* `frameData` - the RS.FrameData object for the current frame
* `stream` - the RS.StreamDefinition object for the current stream
* `paramValues` - the values for the exposed parameters

#### `min`, `max`,  `step`
For floating point and vector values, provides the range used for editing within Designer.

#### `display`
Change the text the exposed parameter is displayed as in the Designer UI.

#### `group`
Puts the exposed parameter into a different group in the Designer UI.
