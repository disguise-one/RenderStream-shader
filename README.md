## RenderStream-ShaderToy

Loads GLSL fragment shaders and presents them as selectable RenderStream scenes.

Shader uniforms are exposed as controllable RenderStream parameters.

![ripple demo image](./doc/ripple.png)<br/>
*The ripple demo shader running on the `ada.jpg` sample image*

## Installing

1. Ensure [RenderStream-Python](https://github.com/disguise-one/renderStream-py) is installed
2. Copy the repository into a folder in your RenderStream Projects folder.
3. In Designer, configure a RenderStream layer to use the shadertoy asset.

![the RenderStream layer](./doc/layer.png)<br/>
*The ripple demo running in a RenderStream Layer inside Designer*

## Creating new shaders

The demos included in the repository are for reference, in order to make the most of RenderStream-ShaderToy, custom shaders need to be written.

Shaders are placed in the `shaders` folder in the RenderStream-shader asset folder. All files with a `.glsl` extension are parsed and added as scenes in the RenderStream asset, selectable in the Designer Layer.

When a RenderStream layer is running, you are able to freely edit the shader files - when they are updated on-disk the shader is automatically reloaded and parsed, dynamically updating available parameters and the visual effect. This is natually less effective in a clustered environment for at-scale shader rendering, but is very useful for shader development.

### Uniforms

Shaders have properties called uniforms, which are values which remain the same (i.e. are uniform) over a single generated frame. These uniforms are exposed as controllable parameters within the RenderStream Layer. They can be [extended with attributes](./doc/uniforms.md) which control how the property is exposed to RenderStream.

### Passes

More complex shaders may require multiple generative inputs - e.g. a scene with a terrain might generate a height map in a separate and sample that instead of computing it for every ray cast.

Passes are added to the `shaders/passes` folder. All glsl files are available to all scene shaders in the shaders folder using the [pass attribute](./doc/uniforms.md#pass).

Passes are also possible to manipulate using the [previous attribute](./doc/uniforms.md#previous) which allows access to a previous frame's image data, which is useful for many types of shader effects.

### Images

Some shaders use a pre-defined image as reference, for example as a source of noise. The repository includes some noise images which are useful for texturing effects. Other images can be added to the `images/` folder as required.