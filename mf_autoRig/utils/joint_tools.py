import pymel.core as pm
import pymel.core.datatypes as dt

def get_joint_hierarchy(joint):
    """
    Returns joint children of the passed object, including it
    The order is parent -> children
    """
    #jnt = pm.PyNode(joint)
    jnts = pm.listRelatives(joint, typ='joint', ad=True)
    jnts.append(joint)
    jnts.reverse()
    return jnts

def __get_plane_normal(plane):
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

def __get_joint_normal(joints):
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
    """
    Created this based on info from:
    https://www.riggingdojo.com/2014/10/03/everything-thought-knew-maya-joint-orient-wrong/

    Main purpose of this is to get clean elbow/knee rotation for ik.
    IDK if this is really necessary, but it seems like a good idea. And it shouldn't hurt.
    """

    if len(joints) < 2:
        raise ValueError("Need at least two joints to orient")

    parent = joints[0].getParent()

    # Unparent all joints
    for jnt in joints:
        pm.parent(jnt, parent)

    # Get the world up vector
    if len(joints) >= 3:
        worldUpVector = __get_joint_normal(joints[0:3])
    else:
        worldUpVector = (0, 1, 0) #Orient so that z is facing forward

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

def mirrorJoints(joints, searchReplace, plane='YZ'):
    """
    Wrapper for pm.mirrorJoint that deletes redundant constraints or leftovers
    Returns mirrored joints PyNodes
    """
    if not isinstance(joints, list):
        joints = [joints]

    if plane == 'YZ':
        mirrored_jnts = pm.mirrorJoint(joints[0], mirrorYZ=True, mirrorBehavior=True,
                                       searchReplace=searchReplace)
    #TODO: add other planes

    # objs = list(map(pm.PyNode, mirrored_jnts))
    #
    # print(objs)
    # print(joints)

    joints_newNames = []
    for jnt in joints:
        name = jnt.name().replace(searchReplace[0], searchReplace[1])
        joints_newNames.append(name)

    dup_joints = []
    for mir_jnt in mirrored_jnts:
        if mir_jnt in joints_newNames:
            obj = pm.PyNode(mir_jnt)
            dup_joints.append(obj)
        else:
            try:
                obj = pm.PyNode(mir_jnt)
                pm.delete(obj)
            except pm.MayaNodeError:
                pass

    return dup_joints

def duplicate_joints(joints, suffix):
        orig_names = []
        for joint in joints:
            orig_names.append(joint.name())

        dup_joints = pm.duplicate(joints, parentOnly=True)

        # iterate over duplicates and rename them
        for joint,name in zip(dup_joints, orig_names):
            joint.rename(name + suffix)

        return dup_joints

def joint_inbetweener(start_jnt, end_jnt, num, name=None, duplicate_jnts=True, suffix=None, end_suffix=None):
    """
    Function that creates joints in between two joints
    :param start_jnt: The first joint
    :param end_jnt: The last joint
    :param num: The number of joints to create
    :param name: The name of the newly created joints
    :param suffix: The suffix of the newly created joints
    :param end_suffix: The suffix of the last joint
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
