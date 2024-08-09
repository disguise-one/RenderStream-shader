from ctypes import c_void_p
import os
from OpenGL.GL import *
from OpenGL.GL import shaders

# Vertex shader for fullscreen quad
VERTEX_SHADER_TEXT = """#version 330

in vec4 attrib_Position;
in vec2 attrib_TexCoord;

out vec2 fragCoord;

void main()
{
    gl_Position = attrib_Position;
    fragCoord = attrib_TexCoord;
}
"""

ERROR_FRAGMENT_SHADER_TEXT = """#version 330

out vec4 fragColor;
void main()
{
    fragColor = vec4(1, 0, 0, 1);
}
"""


_vertex_shader = None
_error_fragment_shader = None
def vertex_shader():
    global _vertex_shader
    if _vertex_shader is None:
        _vertex_shader = shaders.compileShader(VERTEX_SHADER_TEXT, GL_VERTEX_SHADER)
    return _vertex_shader

def error_fragment_shader():
    global _error_fragment_shader
    if _error_fragment_shader is None:
        _error_fragment_shader = shaders.compileShader(ERROR_FRAGMENT_SHADER_TEXT, GL_FRAGMENT_SHADER)
    return _error_fragment_shader

class Shader:
    def set_shader(self, shader_text):
        if hasattr(self, 'fragment_shader'):
            glDeleteShader(self.fragment_shader)

        self.fragment_shader = self._compile_fragment_shader(shader_text)
        self.shader_program = self._compile_shader_program()
        self.uniforms = self._get_shader_uniforms(shader_text)

    def use_program(self):
        glUseProgram(self.shader_program)

        attrib_Position = glGetAttribLocation(self.shader_program, 'attrib_Position')
        glVertexAttribPointer(attrib_Position, 3, GL_FLOAT, GL_FALSE, 5 * 4, c_void_p(0))
        glEnableVertexAttribArray(attrib_Position)

        attrib_TexCoord = glGetAttribLocation(self.shader_program, 'attrib_TexCoord')
        if attrib_TexCoord >= 0:
            glVertexAttribPointer(attrib_TexCoord, 2, GL_FLOAT, GL_FALSE, 5 * 4, c_void_p(3*4))
            glEnableVertexAttribArray(attrib_TexCoord)

    def _compile_fragment_shader(self, shader_text):
        shader = glCreateShader(GL_FRAGMENT_SHADER)
        glShaderSource( shader, [ shader_text.encode() ] )
        glCompileShader( shader )
        result = glGetShaderiv( shader, GL_COMPILE_STATUS )
        if not result:
            print(f"Failed to compile {self.filename}: {glGetShaderInfoLog( shader ).decode()}")
            glDeleteShader(shader)
            shader = error_fragment_shader()
        return shader

    def _compile_shader_program(self):
        if hasattr(self, 'shader_program'):
            glDeleteProgram(self.shader_program)

        return shaders.compileProgram(vertex_shader(), self.fragment_shader)

    def _get_shader_uniforms(self, shader_text):
        # Query the number of active uniforms
        num_uniforms = glGetProgramiv(self.shader_program, GL_ACTIVE_UNIFORMS)

        uniforms = {}
        for i in range(num_uniforms):
            # Get uniform details
            name, size, uniform_type = glGetActiveUniform(self.shader_program, i)

            name = name.decode()
            location = glGetUniformLocation(self.shader_program, name)

            attrs = self._get_uniform_attrs(name, uniform_type, shader_text)
            attrs.update({
                'location': location,
                'type': uniform_type,
                'size': size,
            })

            # Store uniform details in a dictionary
            uniforms[name] = attrs

        return uniforms

    def _get_uniform_attrs(self, name, type, shader_text):
        import re, shlex
        match = re.search(rf'^\s*uniform.*\b{re.escape(name)}\b(?:\s*=\s*(.*?))?;(?:.*// RS:(.*))?', shader_text, re.MULTILINE)
        attrs = {}
        if match:
            # Set default by parsing an initial value assignment from the code
            if match.group(1):
                default_text = match.group(1).strip()
                default_match = re.search(r'[a-zA-Z_][a-zA-Z0-9_]*(\(.*\))', default_text)
                if default_match:
                    attrs["default"] = eval(default_match.group(1))
                else:
                    attrs["default"] = eval(default_text)

            # Allow any attribute (including default) to be set manually
            if match.group(2):
                from ast import literal_eval
                attr_text = match.group(2).strip()
                for keyval in shlex.split(attr_text):
                    name, value_text = keyval.split('=', 1)
                    try:
                        attrs[name] = literal_eval(value_text)
                    except (ValueError, SyntaxError):
                        attrs[name] = value_text

        return attrs

class ReloadableShader(Shader):
    def __init__(self, filename):
        self.filename = filename
        self.load_shader()

    def load_shader(self):
        self.last_mod_time = os.path.getmtime(self.filename)
        with open(self.filename, 'r') as file:
            shader_text = file.read()
            self.set_shader(shader_text)

    def check_update(self):
        current_mod_time = os.path.getmtime(self.filename)
        if current_mod_time != self.last_mod_time:
            print(f"'{self.filename}' modified. Reloading shader...")
            self.load_shader()
            return True
        return False
