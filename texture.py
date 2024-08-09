from __future__ import annotations
from typing import Any, Mapping, Tuple, Union
from PIL import Image
from OpenGL.GL import *
import os
import renderstream as RS

from shader import ReloadableShader, Shader

frameParameterTypes = Union[float, Tuple[(float,) * 16], str, RS.ImageFrameData]

class BaseTexture:
    def __init__(self, name: str):
        self.name = name
        self.id = -1

    def release(self, rs: RS.RenderStream):
        if self.id >= 0:
            glDeleteTextures([self.id])
            self.id = -1

    def update(self, rs: RS.RenderStream, frameData: RS.FrameData, stream: RS.StreamDescription, paramValues: Mapping[str, frameParameterTypes]):
        pass

class ImageTexture(BaseTexture):
    def __init__(self, name, imageFile):
        super().__init__(name)
        self.filename = os.path.join('images', imageFile)
        self._load()

    def _load(self):
        im = Image.open(self.filename).transpose(Image.Transpose.FLIP_TOP_BOTTOM)

        self.id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.id)

        mode = "".join(Image.Image.getbands(im))
        if mode == "RGB":
            data = im.tobytes("raw", "RGBX", 0, -1)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB8, im.width, im.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
            glGenerateMipmap(GL_TEXTURE_2D)
        else:
            data = im.tobytes("raw", "RGBA", 0, -1)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, im.width, im.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, data)
            glGenerateMipmap(GL_TEXTURE_2D)

class PreviousTexture(BaseTexture):
    TEXTURE_FRAGMENT_SHADER_TEXT = """#version 330

    uniform sampler2D input;
    in vec2 fragCoord;
    out vec4 fragColor;
    void main()
    {
        fragColor = texture(input, fragCoord);
    }
    """

    def __init__(self, name: str, parent: ShaderTexture, sampler: str):
        super().__init__(name)
        self.shader = Shader()
        self.shader.set_shader(PreviousTexture.TEXTURE_FRAGMENT_SHADER_TEXT)
        self.parent = parent
        self.sampler = sampler
        self.params = (0, 0, 0, 0, 0, 0)
        self.framebuffer = -1

    @property
    def sourceTexture(self):
        if self.sampler == 'this':
            return self.parent.id
        
        return self.parent.textures[self.sampler].id

    def update(self, rs, frameData, stream, paramValues):
        self._updateFramebuffer()

        glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)

        glDisable(GL_DEPTH_TEST)  # Disable depth test for fullscreen quad
        glClearColor(0, 0, 0, 0)
        glClear(GL_COLOR_BUFFER_BIT)

        glViewport(0, 0, self.params[1], self.params[2])

        self.shader.use_program()

        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, self.sourceTexture)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

        location = self.shader.uniforms['input']['location']
        glUniform1i(location, 0)

        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)

        glFinish()

        glUseProgram(0)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def _updateFramebuffer(self):
        glBindTexture(GL_TEXTURE_2D, self.sourceTexture)
        internal_format = glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_INTERNAL_FORMAT)
        format, type = {
            GL_RGBA32F: (GL_RGBA, GL_FLOAT),
            GL_RGBA8: (GL_RGBA, GL_UNSIGNED_BYTE),
        }[internal_format]
        input_params = (
            internal_format,
            glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_WIDTH),
            glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_HEIGHT),
            0,
            format,
            type
        )

        if self.framebuffer < 0 or self.id < 0 or self.params != input_params:
            if self.id >= 0:
                glDeleteTextures([self.id])

            if self.framebuffer >= 0:
                glDeleteFramebuffers(1, [self.framebuffer])

            self.id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self.id)
            glTexImage2D(GL_TEXTURE_2D, 0, *input_params, None)
            self.params = input_params

            self.framebuffer = glGenFramebuffers(1)

            glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)
            glFramebufferTexture(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, self.id, 0)
            glDrawBuffers([GL_COLOR_ATTACHMENT0])

            status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
            if status != GL_FRAMEBUFFER_COMPLETE:
                print(f"Unable to set up framebuffer for {self.name}: {status}")

class InputTexture(BaseTexture):
    def __init__(self, name):
        super().__init__(name)
        self.size = (0, 0)

    @property
    def frame(self):
        frame = RS.SenderFrame(RS.OpenGlData())
        frame.data.gl.texture = self.id
        return frame

    def release(self, rs):
        rs.releaseImage(self.frame)
        super().release(rs)

    def update(self, rs, frameData, stream, paramValues):
        texInfo = paramValues[self.name]
        assert(isinstance(texInfo, RS.ImageFrameData))

        input_size = (texInfo.width, texInfo.height)
        if self.id == -1 or self.size != input_size:
            self.id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self.id)
            if texInfo.format == RS.RSPixelFormat.RGBA32F:
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, texInfo.width, texInfo.height, 0, GL_RGBA, GL_FLOAT, None)
            else:
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, texInfo.width, texInfo.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
            self.size = input_size

        rs.getFrameImage(texInfo.imageId, self.frame)

class ShaderTexture(BaseTexture):
    def __init__(self, name: str, shader: ReloadableShader, key_prefix=''):
        super().__init__(name)
        self.framebuffer = -1 # self.id is the texture (to read from), framebuffer is what we render to.
        self.shader = shader
        self.key_prefix = key_prefix
        self._initTextures()

    def release(self, rs):
        if self.id >= 0:
            frame = RS.SenderFrame(RS.OpenGlData())
            frame.data.gl.texture = self.id
            rs.releaseImage(frame)

            glDeleteTextures([self.id])
            self.id = -1

        if self.framebuffer >= 0:
            glDeleteFramebuffers(1, [self.framebuffer])
            self.framebuffer = -1

        for tex in self.textures.values():
            tex.release(rs)

    def update(self, rs, frameData, stream, paramValues):
        import shader_params

        self._updateFramebuffer(stream)

        self._updateTextures(rs, frameData, stream, paramValues)

        glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)

        glDisable(GL_DEPTH_TEST)  # Disable depth test for fullscreen quad
        glClearColor(0, 0, 0, 0)
        glClear(GL_COLOR_BUFFER_BIT)

        glViewport(0, 0, stream.width, stream.height)

        self.shader.use_program()

        for name, info in self.shader.uniforms.items():
            try:
                shader_params.set_uniform(rs, name, info, frameData, stream, paramValues, self.textures, self.key_prefix)
            except Exception as err:
                print(f"Unable to set {name} - {err}")

        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)

        glFinish()

        glUseProgram(0)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def check_update(self, rs: RS.RenderStream):
        needs_update = self.shader.check_update()

        for tex in self.textures.values():
            if isinstance(tex, ShaderTexture):
                needs_update |= tex.check_update(rs)

        if needs_update:
            self.release(rs)
            self._initTextures()

        return needs_update
    
    def parameters(self):
        import shader_params
        params = shader_params.uniforms_to_parameters(self.shader.uniforms, key_prefix=self.key_prefix)
        for tex in self.textures.values():
            if isinstance(tex, ShaderTexture):
                params.extend(tex.parameters())
        return params

    def _initTextures(self):
        import shader_params
        self.textures: Mapping[str, BaseTexture] = {}
        for name, info in self.shader.uniforms.items():
            if info["type"] == GL_SAMPLER_2D:
                if 'image' in info:
                    self.textures[name] = ImageTexture(name, info['image'])
                elif 'pass' in info:
                    prefix = f"{self.key_prefix}{name}_"
                    self.textures[name] = ShaderTexture(name, shader_params.pass_shader(info['pass']), key_prefix=prefix)
                elif 'previous' in info:
                    self.textures[name] = PreviousTexture(name, self, info['previous'])
                else:
                    self.textures[name] = InputTexture(name)

    def _updateFramebuffer(self, stream: RS.StreamDescription):
        # Ensure the frame buffer we are rendering to is correctly sized, etc.
        stream_size = (stream.width, stream.height)
        if self.framebuffer < 0 or self.id < 0 or self.size != stream_size:
            if self.id >= 0:
                glDeleteTextures([self.id])

            if self.framebuffer >= 0:
                glDeleteFramebuffers(1, [self.framebuffer])

            self.id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self.id)
            if stream.format == RS.RSPixelFormat.RGBA32F or self.key_prefix != '':
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA32F, stream.width, stream.height, 0, GL_BGRA, GL_FLOAT, None)
            else:
                glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, stream.width, stream.height, 0, GL_BGRA, GL_UNSIGNED_BYTE, None)
            self.size = stream_size

            self.framebuffer = glGenFramebuffers(1)

            glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)
            glFramebufferTexture(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, self.id, 0)
            glDrawBuffers([GL_COLOR_ATTACHMENT0])

            status = glCheckFramebufferStatus(GL_FRAMEBUFFER)
            if status != GL_FRAMEBUFFER_COMPLETE:
                print(f"Unable to set up framebuffer for {self.name}: {status}")

    def _updateTextures(self, rs: RS.RenderStream, frameData: RS.FrameData, stream: RS.StreamDescription, paramValues: Mapping[str, frameParameterTypes]):
        # Update textures before setting everything up.
        import shader_params
        for name, info in self.shader.uniforms.items():
            try:
                if info["type"] == GL_SAMPLER_2D:
                    texture = self.textures[name]
                    texture.update(rs, frameData, stream, paramValues)
            except Exception as err:
                print(f"{self.name} is unable to update texture {name} - {err}")
