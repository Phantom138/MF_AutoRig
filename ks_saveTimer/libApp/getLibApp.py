# from __future__ import absolute_import
import importlib


_HOST_APP_MODULES_ = [
    ['maya', {'cmds':'maya.cmds'}],
    ['nuke', {'nuke':'nuke'}],
    # ['fusion', {'fs':'fusionscript'}],
    # ['houdini', {'hou':'hou'}],
    # ['blender', {'bpy':'bpy'}],
]

_LIB_APP_LIST_ = {
    'desktop': 'libDesktop',
    'maya': 'libMaya',
    'nuke': 'libNuke',
    }


__LIB_APP__ = None     #This is overwritten at end of module
__HOST_APP__ = None    #This is overwritten at end of module

def loadLibApp():
    moduleString = _LIB_APP_LIST_[__HOST_APP__]
    moduleString = '%s.%s' %(__package__, moduleString)
    module = importlib.import_module(moduleString, package=__package__)
    # print 'LIB_APP MODULE:', module
    return module

def getLibAppModule():
    return __LIB_APP__

def getHostApp():
    hostMode = None

    for name, libs in _HOST_APP_MODULES_:
        try:
            for x in libs.keys():
                importlib.import_module(libs[x], package=__package__)
            hostMode = name
            break
        except ImportError:
            pass

    if not hostMode:
        hostMode = 'desktop'

    return hostMode

__HOST_APP__ = getHostApp()
__LIB_APP__ = loadLibApp()
