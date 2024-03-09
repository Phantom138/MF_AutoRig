import pymel.core as pm
import pymel.core.datatypes as dt

import maya.cmds as cmds


def inBetweener(start_jnt, end_jnt, num, name=None, duplicate_jnts=True, suffix=None):
    """
    Function that creates joints in between two joints
    :param start_jnt: The first joint
    :param end_jnt: The last joint
    :param num: The number of joints to create
    :param duplicate_jnts: If True, the joints will be duplicated, if False, the joints will be created between the given joints
    """
    joints = []
    pm.select(clear=True)
    if duplicate_jnts:
        dup = [pm.joint(), pm.joint()]
        pm.matchTransform(dup[0], start_jnt)
        pm.matchTransform(dup[1], end_jnt)
        start_jnt = dup[0]
        end_jnt = dup[1]

    joints.append(start_jnt)

    # positions
    start_jnt_v = dt.Vector(pm.xform(start_jnt, q=True, t=True, ws=True))
    end_jnt_v = dt.Vector(pm.xform(end_jnt, q=True, t=True, ws=True))

    # rotations
    start_jnt_rot = pm.xform(start_jnt, q=True, ro=True, ws=True)

    for i in range(num):
        jnt = pm.joint(radius=start_jnt.radius.get())
        jnt.radius.set(0.2)
        joints.append(jnt)

        w = (i + 1) / (num + 1)

        # get position
        inbtwn_jnt_v = (end_jnt_v - start_jnt_v) * w + start_jnt_v

        # set position
        pm.xform(jnt, t=inbtwn_jnt_v, ws=True)
        pm.xform(jnt, ro=start_jnt_rot, ws=True)

    # Parent the joints back to the original chain
    pm.parent(joints[1], start_jnt)
    pm.parent(end_jnt, joints[-1])

    # Add end joint to the list
    joints.append(end_jnt)

    # Rename the joints
    if name:
        for i, jnt in enumerate(joints):
            if suffix is None:
                suffix = ''
            jnt.rename(f"{name}{i+1:02}{suffix}")

    return joints
