import pymel.core as pm
import pymel.core.datatypes as dt

import maya.cmds as cmds


def inBetweener(start_jnt, end_jnt, num):
    joints = []
    pm.select(clear=True)
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

    return joints
