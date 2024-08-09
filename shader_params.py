from typing import Any, Mapping
import os
import renderstream as RS
from OpenGL.GL import *
import texture
from shader import ReloadableShader

iTexture = 0 # per-frame texture counter

def reset_frame():
    "Called to ensure all textures are bound to unique values every frame"
    global iTexture
    iTexture = 0

def set_uniform(rs: RS.RenderStream, name: str, info: Mapping, frameData: RS.FrameData, stream: RS.StreamDescription, paramValues: Mapping, textures: Mapping[str, texture.BaseTexture], key_prefix=''):
    location = info['location']
    type = info['type']
    param_key = key_prefix + name

    def engine_eval():
        return eval(info['engine'], {
            'frameData': frameData,
            'stream': stream,
            'paramValues': paramValues,
        })
    
    def field_values(*field_suffixes):
        return tuple(paramValues[f"{param_key}{suffix}"] for suffix in field_suffixes)

    if type == GL_SAMPLER_2D:
        global iTexture
        texture = textures[name]

        glActiveTexture(GL_TEXTURE0 + iTexture)
        glBindTexture(GL_TEXTURE_2D, texture.id)

        # Set texture parameters
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, filter_to_gl(info.get('min_filter', 'linear')))
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, filter_to_gl(info.get('mag_filter', 'linear')))

        default_wrap = info.get('wrap', 'repeat')
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, wrap_to_gl(info.get('wrap_s', default_wrap)))
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, wrap_to_gl(info.get('wrap_t', default_wrap)))

        glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, info.get('border_colour', (0., 0., 0., 0.)))

        glUniform1i(location, iTexture)

        iTexture += 1
    elif type == GL_INT:
        if 'engine' in info:
            glUniform1i(location, engine_eval())
        else:
            glUniform1i(location, int(paramValues[param_key]))
    elif type == GL_FLOAT:
        if 'engine' in info:
            glUniform1f(location, engine_eval())
        else:
            glUniform1f(location, paramValues[param_key])
    elif type == GL_FLOAT_VEC2:
        if 'engine' in info:
            glUniform2f(location, *engine_eval())
        else:
            glUniform2f(location, *field_values("_x", "_y"))
    elif type == GL_FLOAT_VEC3:
        if 'engine' in info:
            glUniform3f(location, *engine_eval())
        elif is_colour_vec(info):
            glUniform3f(location, *field_values("_r", "_g", "_b"))
        else:
            glUniform3f(location, *field_values("_x", "_y", "_z"))
    elif type == GL_FLOAT_VEC4:
        if 'engine' in info:
            glUniform4f(location, *engine_eval())
        elif is_colour_vec(info):
            glUniform4f(location, *field_values("_r", "_g", "_b", "_a"))
        else:
            glUniform4f(location, *field_values("_x", "_y", "_z", "_w"))

def uniforms_to_parameters(uniforms: dict, key_prefix=''):
    params = []
    for name, info in sorted(uniforms.items()):
        name: str

        if 'engine' in info:
            continue # controlled programmatically.

        displayName = info.get('display', name_to_display(name))
        group = info.get('group', '')

        def append_fields(key_suffixes, display_suffixes):
            for i, (key_suffix, display_suffix) in enumerate(zip(key_suffixes, display_suffixes)):
                params.append(RS.RemoteParameter(key_prefix + name + key_suffix, displayName + display_suffix, group, get_numeric_default(info, i)))

        type = info['type']
        if type == GL_SAMPLER_2D:
            if 'image' in info or 'pass' in info or 'previous' in info:
                continue # local sources are not exposed.
            params.append(RS.RemoteParameter(key_prefix + name, displayName, group, RS.RemoteParameterType.IMAGE))
        elif type == GL_INT:
            params.append(RS.RemoteParameter(key_prefix + name, displayName, group, get_int_default(info)))
        elif type == GL_FLOAT:
            params.append(RS.RemoteParameter(key_prefix + name, displayName, group, get_numeric_default(info)))
        elif type == GL_FLOAT_VEC2:
            append_fields(('_x', '_y'), (" X", " Y"))
        elif type == GL_FLOAT_VEC3:
            if is_colour_vec(info):
                append_fields(('_r', '_g', '_b'), (" R", " G", " B"))
            else:
                append_fields(('_x', '_y', '_z'), (" X", " Y", " Z"))
        elif type == GL_FLOAT_VEC4:
            if is_colour_vec(info):
                append_fields(('_r', '_g', '_b', '_a'), (" R", " G", " B", " A"))
            else:
                append_fields(('_x', '_y', '_z', '_w'), (" X", " Y", " Z", " W"))
    return params

def filter_to_gl(filter_name: str):
    return {
        'nearest': GL_NEAREST,
        'linear': GL_LINEAR,
        'nearest_mipmap_nearest': GL_NEAREST_MIPMAP_NEAREST,
        'nearest_mipmap_linear': GL_NEAREST_MIPMAP_LINEAR,
        'linear_mipmap_nearest': GL_LINEAR_MIPMAP_NEAREST,
        'linear_mipmap_linear': GL_LINEAR_MIPMAP_LINEAR,
    }[filter_name]

def wrap_to_gl(wrap_name: str):
    return {
        'clamp_to_edge': GL_CLAMP_TO_EDGE,
        'clamp_to_border': GL_CLAMP_TO_BORDER,
        'mirrored_repeat': GL_MIRRORED_REPEAT,
        'repeat': GL_REPEAT,
        'mirror_clamp_to_edge': GL_MIRROR_CLAMP_TO_EDGE,
    }[wrap_name]

def pass_shader(pass_name):
    return ReloadableShader(os.path.join("shaders/passes", pass_name))

def is_colour_vec(info):
    return 'isColour' in info and info['isColour']

def get_numeric_default(info, default_index=None):
    default = 0.0
    if 'default' in info:
        if default_index is not None:
            default = info['default'][default_index]
        else:
            default = info['default']
    return RS.NumericalDefaults(
        default,
        info.get('min', 0.0),
        info.get('max', 1.0),
        info.get('step', 0.1),
    )

def get_int_default(info, default_index=None):
    default = 0.0
    if 'default' in info:
        if default_index is not None:
            default = info['default'][default_index]
        else:
            default = info['default']
    return RS.NumericalDefaults(
        default,
        info.get('min', 0.0),
        info.get('max', 100.0),
        info.get('step', 1.0),
    )

def name_to_display(name):
    import re
    name = re.sub(r'(?<!^)(?=[A-Z])', ' ', name)
    name = name.replace('_', ' ').replace('-', ' ').strip().lower()
    return name[0].upper() + name[1:]
