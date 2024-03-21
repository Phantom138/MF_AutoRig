import pymel.core as pm


def xformMirror(transforms=[], across='YZ'):
    """ Mirrors transform across hyperplane.

    transforms -- list of Transform or string.
    across -- plane which to mirror across.

    """
    flipped_matricies = []
    # No specified transforms, so will get selection
    if not transforms:
        transforms = pm.selected(type='transform')

    # Check to see all provided objects is an instance of pymel transform node,
    if not all(map(lambda x: isinstance(x, pm.nt.Transform), transforms)):
        raise ValueError("Passed node which wasn't of type: Transform")

    # Validate plane which to mirror across,
    if not across in ('XY', 'YZ', 'XZ'):
        raise ValueError("Keyword Argument: 'across' not of accepted value ('XY', 'YZ', 'XZ').")

    for transform in transforms:

        # Get the worldspace matrix, as a list of 16 float values
        mtx = pm.xform(transform, q=True, ws=True, m=True)

        # Invert rotation columns,
        rx = [n * -1 for n in mtx[0:9:4]]
        ry = [n * -1 for n in mtx[1:10:4]]
        rz = [n * -1 for n in mtx[2:11:4]]

        # Invert translation row,
        t = [n * -1 for n in mtx[12:15]]

        # Set matrix based on given plane, and whether to include behaviour or not.
        if across is 'XY':
            mtx[14] = t[2]  # set inverse of the Z translation

            # Set inverse of all rotation columns but for the one we've set translate to.
            mtx[0:9:4] = rx
            mtx[1:10:4] = ry

        elif across is 'YZ':
            mtx[12] = t[0]  # set inverse of the X translation

            mtx[1:10:4] = ry
            mtx[2:11:4] = rz
        else:
            mtx[13] = t[1]  # set inverse of the Y translation

            mtx[0:9:4] = rx
            mtx[2:11:4] = rz

        flipped_matricies.append(mtx)

    return flipped_matricies
    cp = pm.duplicate(transforms)
    print(cp)
    # Finally set matrix for transform
    for i,transform in enumerate(cp):
        pm.xform(transform, ws=True, m=flipped_matricies[i])

def mirrorJoints(joints, searchReplace, plane='YZ'):
    """
    Wrapper for pm.mirrorJoint that deletes redundant constraints or leftovers
    Returns mirrored joints PyNodes
    """
    if plane == 'YZ':
        mirrored_jnts = pm.mirrorJoint(joints[0], mirrorYZ=True, mirrorBehavior=True,
                                       searchReplace=searchReplace)
    #TODO: add other planes

    objs = list(map(pm.PyNode, mirrored_jnts))

    dup_joints = []
    for obj in objs:
        if obj in joints:
            dup_joints.append(obj)
        else:
            pm.delete(obj)

    return dup_joints
