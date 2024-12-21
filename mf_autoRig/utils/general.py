import pymel.core as pm
import pymel.core.datatypes as dt
import re
import maya.cmds as cmds

import mf_autoRig.utils.defaults as df

def get_group(name):
    try:
        guides_grp = pm.PyNode(name)
    except pm.MayaNodeError:
        guides_grp = pm.createNode('transform', name=name)

    return guides_grp


def get_base_name(name):
    # Get base name of first joint eg. L_joint1_skin_JNT -> L_joint1
    match = re.search('([a-zA-Z]_[a-zA-Z]+)\d*_', name)

    if match is None:
        # Joint name is not matching the pattern
        # Trying to get base_name by removing end_jnt suffix
        match = re.search(f'(.*){df.end_sff}{df.jnt_sff}', name)

    if match is None:
        match = re.search(f'(.*){df.skin_sff}{df.jnt_sff}', name)

    if match is None:
        pm.warning(f"{name} name is not matching the pattern")
        base_name = name
    else:
        base_name = match.group(1)

    # print(f"For {name} base name is {base_name}")

    return base_name

def create_offset_grp(ctrls):
    colors = [0, 255, 0]

    if not isinstance(ctrls, list):
        ctrls = [ctrls]

    offset_grps = []
    for ctl in ctrls:
        pm.select(clear=True)

        # Create name
        name = ctl.name()
        name = name.replace('_ctrl', '')
        # Create Group
        grp = pm.group(ctl, name=name + '_offset_grp', relative=False, world=False)
        # Reset pivot
        pm.xform(grp, objectSpace=True, pivots=[0, 0, 0])

        offset_grps.append(grp)
        # Set color
        pm.setAttr(grp + '.useOutlinerColor', 1)
        pm.setAttr(grp + ".outlinerColorR", colors[0] / 255)
        pm.setAttr(grp + ".outlinerColorG", colors[1] / 255)
        pm.setAttr(grp + ".outlinerColorB", colors[2] / 255)

    # Clear selection
    pm.select(clear=True)

    if len(offset_grps) == 1:
        return offset_grps[0]
    else:
        return offset_grps


def lock_and_hide(obj, translate=True, rotation=True, scale=True):
    if translate:
        for trs in ['tx', 'ty', 'tz']:
            obj.attr(trs).lock()
            obj.attr(trs).setKeyable(0)
    if rotation:
        for trs in ['rx', 'ry', 'rz']:
            obj.attr(trs).lock()
            obj.attr(trs).setKeyable(0)
    if scale:
        for trs in ['sx', 'sy', 'sz']:
            obj.attr(trs).lock()
            obj.attr(trs).setKeyable(0)
