import pymel.core as pm

colors = {
    'yellow': (255, 255, 51),
    'orange': (255,140,0),
    'green': (0, 255, 0),
    'red': (255, 0, 0),
    'cyan': (0, 255, 255),
    'blue': (0, 0, 255),
    'magenta': (255, 0, 255)
}

def set_color(objs, viewport=None, outliner=None):
    """Function that colors stuff
    predefined colors: red, green, blue, yellow, cyan, magenta

    viewport -> tuple with rgp values or predefined
    outliner -> tuple with rgp values or predefined

    if there are no arguments, it returns objects to default
    """

    # If there's only one element
    if not isinstance(objs, list):
        objs = [objs]

    if viewport is None:
        disable_colors(objs)
    else:
        if isinstance(viewport, str):
            clr = colors[viewport]
        elif isinstance(viewport, (tuple, list)):
            clr = viewport

        color_objs(objs, clr)

    if outliner is None:
        disable_colors_outliner(objs)
    else:
        if isinstance(outliner, str):
            clr = colors[outliner]
        elif isinstance(outliner, (tuple, list)):
            clr = outliner

        color_outliner(objs, clr)

def auto_color(objs):
    """
    Function that colors objs automatically, based on the side
    R side -> red
    L side -> blue
    """
    if not isinstance(objs, list):
        objs = [objs]
    for obj in objs:
        side = obj.name().split('_')[0]
        if side == 'R':
            set_color(obj, viewport='red')
        if side == 'L':
            set_color(obj, viewport='blue')

def color_objs(objs, color):
    #receives color in rgb (0-255) format
    for obj in objs:

        if pm.nodeType(obj) == 'joint':
            shape = obj
        else:
            shape = pm.listRelatives(obj, shapes=True)[0]

        pm.setAttr(shape + ".overrideEnabled", 1)
        pm.setAttr(shape + ".overrideRGBColors", 1)
        pm.setAttr(shape + ".overrideColorR", color[0]/255)
        pm.setAttr(shape + ".overrideColorG", color[1]/255)
        pm.setAttr(shape + ".overrideColorB", color[2]/255)

def color_outliner(objs, color):
    for obj in objs:
        pm.setAttr(obj + ".useOutlinerColor", 1)
        pm.setAttr(obj + ".outlinerColorR", color[0]/255)
        pm.setAttr(obj + ".outlinerColorG", color[1]/255)
        pm.setAttr(obj + ".outlinerColorB", color[2] / 255)


def disable_colors(objs):
    for obj in objs:
        if pm.nodeType(obj) == 'joint':
            shape = obj
        else:
            shape = pm.listRelatives(obj, shapes=True)[0]

        pm.setAttr(shape + '.overrideEnabled', 0)  # disables color override

def disable_colors_outliner(objs):
    for obj in objs:
        pm.setAttr(obj + '.useOutlinerColor', 0)  # disables color override

