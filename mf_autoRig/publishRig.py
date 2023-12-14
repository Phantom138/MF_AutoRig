"""
Publish rig by deleting all keyframes, and resetting controllers

"""

import maya.cmds as cmds


def reset_ctrls():
    ctrls = cmds.ls('*_ctrl')
    print(ctrls)
    if len(ctrls) == 0:
        return

    for ctrl in ctrls:
        # Rotation and Translate
        for trs in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']:
            attr = f'{ctrl}.{trs}'
            attrValue = cmds.getAttr(attr)

            if attrValue != 0:
                print(f'{ctrl} has {attrValue} in {trs}, setting to 0')
                cmds.setAttr(attr, 0)

        # Scale
        for scl in ['sx', 'sy', 'sz']:
            scale = f'{ctrl}.{scl}'
            scaleValue = round(cmds.getAttr(scale), 7)
            if scaleValue != 1:
                print(f'{ctrl} has {scaleValue} in {scl}, setting to 0')
                cmds.setAttr(scale, 1)


def delete_keys():
    keys = []
    try:
        keys += cmds.ls(type="animCurveTU")
    except:
        pass
    try:
        keys += cmds.ls(type="animCurveTL")
    except:
        pass
    try:
        keys += cmds.ls(type="animCurveTA")
    except:
        pass

    # Set time to 0
    cmds.currentTime(0, edit=True)
    if len(keys) != 0:
        cmds.delete(keys)


reset_ctrls()
