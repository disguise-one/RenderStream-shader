from typing import Any, Mapping, Tuple, Union
from PIL import Image
from OpenGL.GL import *
import os
import renderstream as RS

frameParameterTypes = Union[float, Tuple[(float,) * 16], str, RS.ImageFrameData]

class BaseTexture:
    def __init__(self, name: str):
        self.name = name
        self.id = -1

    def __del__(self):
        if self.id >= 0:
            glDeleteTextures([self.id])

    def update(self, rs: RS.RenderStream, paramValues: Mapping[str, frameParameterTypes]):
        pass

class ImageTexture(BaseTexture):
    def __init__(self, name, imageFile):
        super().__init__(name)
        im = Image.open(os.path.join('images', imageFile)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)

        self.id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.id)

        mode = "".join(Image.Image.getbands(im))
        print('image is', mode)
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

    def update(self, rs, paramValues):
        texInfo = paramValues[self.name]
        assert(isinstance(texInfo, RS.ImageFrameData))

        input_size = (texInfo.width, texInfo.height)
        if self.id == -1 or self.size != input_size:
            self.id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, self.id)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, texInfo.width, texInfo.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, None)
            self.size = input_size

        frame = RS.SenderFrame(RS.OpenGlData())
        frame.data.gl.texture = self.id
        rs.getFrameImage(texInfo.imageId, frame)
