from ctypes import c_void_p
from typing import Any, Mapping, Tuple, Union
from PIL import Image
from OpenGL.GL import *
import os
import renderstream as RS

from reloadableshader import ReloadableShader

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
            print(f"allocating inputtex for {self.name} at {input_size}")
            self.id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self.id)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, texInfo.width, texInfo.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
            self.size = input_size

        rs.getFrameImage(texInfo.imageId, self.frame)

class ShaderTexture(BaseTexture):
    def __init__(self, name: str, shader: ReloadableShader):
        super().__init__(name)
        self.framebuffer = -1 # self.id is the texture (to read from), framebuffer is what we render to.
        self.shader = shader
        self.textures: Mapping[str, BaseTexture] = {}

    def release(self, rs):
        super().release(rs)
        for tex in self.textures.values():
            tex.release(rs)

    def set_framebuffer(self, id, stream: RS.StreamDescription):
        "Used by the main app to set the framebuffer used by RS"
        self.framebuffer = id
        self.size = (stream.width, stream.height)

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
                shader_params.set_uniform(rs, name, info, frameData, stream, paramValues, self.textures)
            except Exception as err:
                print(f"Unable to set {name} - {err}")

        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, c_void_p(0))

        glFinish()

        glUseProgram(0)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def check_update(self):
        needs_update = self.shader.check_update()

        for tex in self.textures.values():
            if isinstance(tex, ShaderTexture):
                needs_update |= tex.check_update()

        return needs_update

    def _updateFramebuffer(self, stream: RS.StreamDescription):
        # Ensure the frame buffer we are rendering to is correctly sized, etc.
        stream_size = (stream.width, stream.height)
        if self.framebuffer < 0 or self.size != stream_size:
            if self.id >= 0:
                glDeleteTextures([self.id])

            if self.framebuffer >= 0:
                glDeleteFramebuffers([self.framebuffer])

            self.id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self.id)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, stream.width, stream.height, 0, GL_BGRA, GL_UNSIGNED_BYTE, c_void_p(0))
            self.size = stream_size

            self.framebuffer = glGenFramebuffers(1)

            glBindFramebuffer(GL_FRAMEBUFFER, self.framebuffer)
            glFramebufferTexture(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, self.id, 0)
            glDrawBuffers([GL_COLOR_ATTACHMENT0])

    def _updateTextures(self, rs: RS.RenderStream, frameData: RS.FrameData, stream: RS.StreamDescription, paramValues: Mapping[str, frameParameterTypes]):
        # Update textures before setting everything up.
        import shader_params
        for name, info in self.shader.uniforms.items():
            try:
                if info["type"] == GL_SAMPLER_2D:
                    if name not in self.textures:
                        print(f"creating texture {name}")
                        self.textures[name] = shader_params.create_texture(rs, name, info)
                    texture = self.textures[name]
                    texture.update(rs, frameData, stream, paramValues)
            except Exception as err:
                print(f"Unable to set {name} - {err}")
