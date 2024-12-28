import pymel.core as pm
import mf_autoRig.utils.defaults as df
from mf_autoRig.utils.general import lock_and_hide, get_group
from mf_autoRig.utils.joint_tools import orient_joints


def __create_guides(pos):
    # Parent new guide shape under ctrl
    knots = [i for i in range(len(pos))]
    crv = pm.curve(d=1, p=pos, k=knots)
    pm.select(cl=True)

    joints = []
    for i, p in enumerate(pos):
        jnt = pm.joint(position=p)
        joints.append(jnt)

        mult = pm.createNode("multMatrix")
        jnt.worldMatrix[0].connect(mult.matrixIn[0])
        crv.worldInverseMatrix[0].connect(mult.matrixIn[1])

        # Decompose the matrix
        decompose = pm.createNode("decomposeMatrix")
        mult.matrixSum.connect(decompose.inputMatrix)

        decompose.outputTranslate.connect(crv.controlPoints[i])

    pm.parent(crv, joints[0])

    return joints

def create_joint_chain(jnt_number, name, start_pos, end_pos, rot=None, defaultValue=51):
    if rot is None:
        rot = [0, 0, 0]

    # Create plane
    plane = pm.polyPlane(name=f'tmp_{name}_Plane', w=2, h=26, sh=1, sw=1)[0]
    plane.v.set(0)
    driven_grp = get_group(df.driven_grp)
    pm.parent(plane, driven_grp)

    joints = []
    # Create joints and move them in position for skinning
    startJnt = pm.createNode('joint', name=f'{name}_start')
    endJnt = pm.createNode('joint', name=f'{name}_end')
    pm.move(startJnt, (-1, 0, 0))
    pm.move(endJnt, (1, 0, 0))

    pm.orientConstraint(startJnt, endJnt)

    lock_and_hide(startJnt, translate=False, rotation=False)
    lock_and_hide(endJnt, translate=False)

    joints.append(startJnt)

    # Skin plane to jnts
    influencers = [startJnt, endJnt]
    skn_cluster = pm.skinCluster(influencers, plane, name=f'tmp_{name}_skinCluster', toSelectedBones=True, bindMethod=0, skinMethod=0, normalizeWeights=1)
    pm.skinPercent(skn_cluster, plane.vtx[0], transformValue=[(startJnt, 1), (endJnt, 0)])
    pm.skinPercent(skn_cluster, plane.vtx[2], transformValue=[(startJnt, 1), (endJnt, 0)])

    pm.skinPercent(skn_cluster, plane.vtx[1], transformValue=[(startJnt, 0), (endJnt, 1)])
    pm.skinPercent(skn_cluster, plane.vtx[3], transformValue=[(startJnt, 0), (endJnt, 1)])

    planeShape = pm.listRelatives(plane)[0]
    planeOrig = pm.listRelatives(plane)[1]

    # Create middle joints and connect to uv pin
    for i in range(1, jnt_number-1):
        # Create uv pin and connect to plane
        UVpin = pm.createNode('uvPin', name=f'{name}{i}_uvPin')
        planeShape.worldMesh.connect(UVpin.deformedGeometry)
        planeOrig.outMesh.connect(UVpin.originalGeometry)

        # Create jnt and coords attributes
        jnt = pm.createNode('joint', name=f'{name}{i}')
        lock_and_hide(jnt)
        pm.parent(jnt, driven_grp)

        joints.append(jnt)
        value = 100/(jnt_number-1)*i

        for coord in ['uCoord', 'vCoord']:
            rv = pm.createNode('remapValue', name=f'{name}{i}_{coord}_RV')

            # Set min and max
            rv.inputMax.set(100)
            rv.outputMax.set(1)

            # Connect to coords
            if coord == 'uCoord':
                pm.addAttr(jnt, ln=coord, at='float', max=100, min=0, dv=value, k=True)
                jnt.uCoord.connect(rv.inputValue)
                rv.outValue.connect(UVpin.coordinate[0].coordinateU)
            elif coord == 'vCoord':
                pm.addAttr(jnt, ln=coord, at='float', max=100, min=0, dv=defaultValue, k=True)
                jnt.vCoord.connect(rv.inputValue)
                rv.outValue.connect(UVpin.coordinate[0].coordinateV)

        # Connect matrix from uv pin to jnt
        pick_mtx = pm.createNode('pickMatrix')
        pick_mtx.useScale.set(0)
        pick_mtx.useShear.set(0)

        UVpin.outputMatrix[0].connect(pick_mtx.inputMatrix)
        pick_mtx.outputMatrix.connect(jnt.offsetParentMatrix)

    startJnt.translate.set(start_pos)
    startJnt.rx.set(rot[0])
    startJnt.ry.set(rot[1])
    startJnt.rx.set(rot[2])
    endJnt.translate.set(end_pos)

    joints.append(endJnt)

    # Create curve driven by the guides
    pts = []
    for jnt in joints:
        pt = pm.xform(jnt, query=True, translation=True, worldSpace=True)
        pts.append(pt)

    curve = pm.curve(d=1, p=pts, name=f'{name}_guide_crv')

    pm.parent(curve, driven_grp)
    for i in range(curve.numCVs()):
        cluster = pm.cluster(curve.cv[i], name=f'{curve.name()}_{i + 1:02}_cluster')[1]
        cluster.visibility.set(0)
        pm.parent(cluster, joints[i])

    # color curve
    from mf_autoRig.utils.color_tools import set_color
    curve.lineWidth.set(2)
    curve.alwaysDrawOnTop.set(1)
    set_color(curve, viewport='black')

    # Color guide joints
    set_color(joints, viewport='cyan')

    # Group start and end jnt
    grp = pm.createNode('transform', name=f'{name}_grp')
    pm.matchTransform(grp, startJnt)
    pm.parent(startJnt, endJnt, grp)

    # Parent to rig grp
    pm.parent(grp, get_group(df.rig_guides_grp))

    return joints


def create_joints_from_guides(name, guides, suffix=None, endJnt=True):
    pm.select(clear=True)
    radius = guides[0].radius.get()
    joints = []
    for i, tmp in enumerate(guides):
        if suffix is None:
            suffix = df.skin_sff

        # Last joint has end suffix
        if endJnt and i == len(guides) - 1:
            suffix = df.end_sff

        jnt = pm.createNode('joint', name=f'{name}{i + 1:02}{suffix}{df.jnt_sff}')
        jnt.radius.set(radius)
        pm.matchTransform(jnt, tmp, pos=True)
        joints.append(jnt)

    orient_joints(joints, aimVector=(0, 1, 0), upVector=(1, 0, 0))
    # for i in range(len(joints) - 1, 0, -1):
    #     pm.parent(joints[i], joints[i - 1])
    #
    # # Orient joints
    # pm.joint(joints[0], edit=True, orientJoint='yzx', secondaryAxisOrient='zup', children=True)
    # pm.joint(joints[-1], edit=True, orientJoint='none')
    #
    # # HACK: sometimes the x axis of the last joint gets very minimal values. This messes up the IK
    # # This is more of a bandaid, the problem is somewhere in the code above
    # # TODO: Fix this
    # joints[-1].translateX.set(0)

    pm.select(clear = True)
    return joints
