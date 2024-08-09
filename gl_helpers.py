from ctypes import c_void_p
from OpenGL.GL import *
import renderstream as RS
import glfw
import glm
from win32gui import GetDC

def initWithOffscreenGLWindow(rs: RS.RenderStream):
    # Initialize the library
    glfw.init()
    # Set window hint NOT visible
    glfw.window_hint(glfw.VISIBLE, False)
    # Create a windowed mode window and its OpenGL context
    window = glfw.create_window(10, 10, "renderstream shadertoy", None, None)

    # Make the window's context current
    glfw.make_context_current(window)
    
    hrc = glfw.get_wgl_context(window)
    hdc = GetDC(glfw.get_win32_window(window))

    rs.initialiseGpGpuWithOpenGlContexts(hrc, hdc)

    version = glGetString(GL_VERSION)
    print(f"OpenGL Version: {version.decode('utf-8')}")

def getCameraViewProjMatrices(cam: RS.CameraData, clipping: RS.ProjectionClipping):
    nearZ = cam.nearZ
    farZ = cam.farZ

    if cam.orthoWidth > 0.0:
        cameraAspect = cam.sensorX / cam.sensorY
        imageWidth = cam.orthoWidth
        imageHeight = imageWidth / cameraAspect
    else:
        imageWidth = (cam.sensorX / cam.focalLength) * nearZ
        imageHeight = (cam.sensorY / cam.focalLength) * nearZ

    l = (-0.5 + clipping.left) * imageWidth
    r = (-0.5 + clipping.right) * imageWidth
    t = (-0.5 + 1.0 - clipping.top) * imageHeight
    b = (-0.5 + 1.0 - clipping.bottom) * imageHeight

    if cam.orthoWidth > 0.0:
        proj = glm.ortho(l, r, t, b, nearZ, farZ)
    else:
        proj = glm.frustum(l, r, t, b, nearZ, farZ)

    rad = glm.radians
    rz = glm.rotate(rad(cam.rz), glm.vec3(0, 0, -1))
    rx = glm.rotate(rad(cam.rx), glm.vec3(1, 0, 0))
    ry = glm.rotate(rad(cam.ry), glm.vec3(0, -1, 0))
    camRotation = ry * rx * rz
    camTranslation = glm.translate(glm.vec3(cam.x, cam.y, -cam.z))
    view = glm.transpose(camRotation) * glm.inverse(camTranslation)

    return view, proj

def appLoop(rs: RS.RenderStream, initGL, render):
    initWithOffscreenGLWindow(rs)

    initGL(rs)
    
    streams: RS.StreamDescriptions = None

    while True:
        try:
            frameData = rs.awaitFrameData(5000)

            for iStream in range(streams.nStreams):
                stream: RS.StreamDescription = streams.streams[iStream]

                senderFrame, response = render(rs, frameData, stream)

                if senderFrame is not None and response is not None:
                    rs.sendFrame(stream.handle, senderFrame, response)
        except RS.RenderStreamError as e:
            if e.error == RS.RS_ERROR.STREAMS_CHANGED:
                streams = rs.getStreams()
                continue
            elif e.error == RS.RS_ERROR.TIMEOUT:
                continue
            elif e.error == RS.RS_ERROR.INCORRECT_SCHEMA:
                print("INCORRECT_SCHEMA")
                continue
            elif e.error != RS.RS_ERROR.QUIT:
                import traceback as tb
                tb.print_exc()
                break
            else:
                print("Exiting normally")
                break
        except:
            import traceback as tb
            tb.print_exc()
            break
