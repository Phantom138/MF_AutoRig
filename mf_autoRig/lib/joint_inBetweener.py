import pymel.core as pm
import pymel.core.datatypes as dt

import maya.cmds as cmds


def inBetweener(start_jnt, end_jnt, num, name=None, duplicate_jnts=True, suffix=None, end_suffix=None):
    """
    Function that creates joints in between two joints
    :param start_jnt: The first joint
    :param end_jnt: The last joint
    :param num: The number of joints to create
    :param duplicate_jnts: If True, the joints will be duplicated, if False, the joints will be created between the given joints
    """
    if end_suffix is None:
        suffix = end_suffix

    joints = []
    pm.select(clear=True)
    if duplicate_jnts:
        dup = [pm.joint(radius=start_jnt.radius.get()), pm.joint(radius=start_jnt.radius.get())]
        pm.matchTransform(dup[0], start_jnt, pos=True)
        pm.matchTransform(dup[1], end_jnt, pos=True)
        start_jnt = dup[0]
        end_jnt = dup[1]

    joints.append(start_jnt)

    # positions
    start_jnt_v = dt.Vector(pm.xform(start_jnt, q=True, t=True, ws=True))
    end_jnt_v = dt.Vector(pm.xform(end_jnt, q=True, t=True, ws=True))

    # rotations
    start_jnt_rot = pm.xform(start_jnt, q=True, ro=True, ws=True)

    for i in range(num):
        jnt = pm.joint()
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

    if suffix is None:
        suffix = ''

    # Rename and scale the joints
    start_radius = start_jnt.radius.get()
    print("setting to", start_radius/2)
    if name:
        for i, jnt in enumerate(joints):
            jnt.radius.set(start_radius/2)

            if i == len(joints)-1:
                # Joint is last in chain
                jnt.rename(f"{name}{i+1:02}{end_suffix}")
            else:
                jnt.rename(f"{name}{i+1:02}{suffix}")
    # Orient joints
    # TODO: Orient based on original joints
    pm.joint(joints[0], edit=True, orientJoint='yzx', secondaryAxisOrient='zup', children=True)
    pm.joint(joints[-1], edit=True, orientJoint='none')

    return joints
