"""
Created this based on info from:
https://www.riggingdojo.com/2014/10/03/everything-thought-knew-maya-joint-orient-wrong/

Main purpose of this is to get clean elbow/knee rotation for ik.
IDK if this is really necessary, but it seems like a good idea. And it shouldn't hurt.
"""

import pymel.core as pm
import pymel.core.datatypes as dt

def get_plane_normal(plane):
    """
    Get the normal of a plane.
    Returns a tuple with the normal.
    """
    # Uses a closestPointOnMesh node to get the normal. it gets deleted after use.
    pnt = pm.createNode('closestPointOnMesh')
    plane.getShape().worldMesh.connect(pnt.inMesh)
    normal = pnt.normal.get()
    pm.delete(pnt)

    return normal

def get_joint_normal(joints):
    """
    Gets the normal of three joints.
    Returns a tuple with the normal vector.
    """
    # This function gets the perpendicular vector of the plane created by the three joints.
    # In 3D terms, this is the normal of that "plane". This is a much more elegant way, compared to the get_plane_normal function.
    v1 = dt.Vector(joints[1].getTranslation(space='world') - joints[0].getTranslation(space='world'))
    v2 = dt.Vector(joints[1].getTranslation(space='world') - joints[2].getTranslation(space='world'))

    normal = dt.cross(v1, v2).normal()

    return normal

def orient_joints(joints, aimVector, upVector):
    if len(joints) < 2:
        raise ValueError("Need at least two joints to orient")

    parent = joints[0].getParent()
    # Unparent all joints
    for jnt in joints:
        pm.parent(jnt, parent)

    # Get the world up vector
    if len(joints) >= 3:
        worldUpVector = get_joint_normal(joints[0:3])
    else:
        worldUpVector = (0, 1, 0)

    # Orient joints
    for i in range(len(joints) - 1):
        jnt = joints[i]
        aimTarget = joints[i + 1]

        tmp_constraint = pm.aimConstraint(aimTarget, jnt, weight=1, aimVector=aimVector, upVector=upVector, worldUpVector=worldUpVector, worldUpType='vector')
        pm.delete(tmp_constraint)

        # Freeze rotation
        pm.makeIdentity(jnt, apply=True, r=True)

    # Reparent joints
    for i in range(len(joints) - 1, 0, -1):
        pm.parent(joints[i], joints[i - 1])

    # Orient last joint to world
    pm.joint(joints[-1], edit=True, orientJoint='none')
