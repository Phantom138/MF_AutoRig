import pymel.core as pm
import mf_autoRig.utils.defaults as df
from mf_autoRig.utils.general import lock_and_hide, get_group
from mf_autoRig.utils.joint_tools import orient_joints
from mf_autoRig.utils.general import lock_and_hide
from mf_autoRig.utils.color_tools import set_color

def mirror_guides_old(guides, new_name, plane='YZ'):
    """
    Mirror guides in X axis
    """
    yz_mirror_mtx = [-1, 0, 0, 0,
                     0, 1, 0, 0,
                     0, 0, 1, 0,
                     0, 0, 0, 1]
    new_group = pm.createNode('transform', name=f'{new_name}_mir_grp')
    pm.parent(new_group, get_group("rig_guides_grp"))
    lock_and_hide(new_group)

    new_guides = []
    for i,guide in enumerate(guides):
        new_guide = pm.createNode('joint', name=f'{new_name}_mir_guide_{i}')
        pm.parent(new_guide, new_group)
        lock_and_hide(new_guide)

        mult_mtx = pm.createNode('multMatrix', name=f'{new_guide.name()}_mirror_{plane}')

        guide.worldMatrix[0].connect(mult_mtx.matrixIn[0])
        mult_mtx.matrixIn[1].set(yz_mirror_mtx)

        mult_mtx.matrixSum.connect(new_guide.offsetParentMatrix)


    return new_guides

def mirror_guides_transforms(guides, mir_guides, plane='YZ'):
    """
    Mirror guides in X axis
    """
    identity_mtx = [1, 0, 0, 0,
                   0, 1, 0, 0,
                   0, 0, 1, 0,
                   0, 0, 0, 1]

    yz_mirror_mtx = [-1, 0, 0, 0,
                     0, 1, 0, 0,
                     0, 0, 1, 0,
                     0, 0, 0, 1]

    for guide, mir_guide, in zip(guides, mir_guides):
        # mir_guide.setMatrix(identity_mtx)
        pm.xform(mir_guide, m=identity_mtx)
        mult_mtx = pm.createNode('multMatrix', name=f'{mir_guide.name()}_mirror_{plane}')

        guide.xformMatrix.connect(mult_mtx.matrixIn[0])
        mult_mtx.matrixIn[1].set(yz_mirror_mtx)

        mult_mtx.matrixSum.connect(mir_guide.offsetParentMatrix)
        lock_and_hide(mir_guide)

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


class Guide:
    def __init__(self, name, pos):
        self.guide = pm.createNode('joint', name=name)
        pm.move(self.guide, pos)
        self.guide.radius.set(0.5)
        set_color(self.guide, viewport='cyan')


class GuideCurve:
    def __init__(self, name, guides):
        # Create curve driven by the guides
        crv_pts = []
        for guide in guides:
            crv_pt = pm.xform(guide, query=True, translation=True, worldSpace=True)
            crv_pts.append(crv_pt)

        self.curve = pm.curve(d=1, p=crv_pts, name=f'{name}_guide_crv')

        # Parent under driven grp
        driven_grp = get_group(df.driven_grp)
        pm.parent(self.curve, driven_grp)

        # Create clusters
        for i in range(self.curve.numCVs()):
            cluster = pm.cluster(self.curve.cv[i], name=f'{self.curve.name()}_{i + 1:02}_cluster')[1]
            cluster.visibility.set(0)
            pm.parent(cluster, guides[i])

        self.curve.lineWidth.set(2)
        self.curve.alwaysDrawOnTop.set(1)
        self.curve.overrideEnabled.set(1)
        self.curve.overrideDisplayType.set(2) # Reference
        # set_color(self.curve, viewport='black')
        lock_and_hide(self.curve)


def create_guide_chain(name: str, number: int, pos: list, interpolate=True):
    if interpolate and len(pos) == 2:
        new_pos = []
        start = pm.dt.Vector(pos[0])
        end = pm.dt.Vector(pos[1])
        # interpolate between two points
        for i in range(number):
            p = start + (end - start) * i / (number - 1)
            new_pos.append(p.get())

        pos = new_pos

    if len(pos) != number:
        raise ValueError(f"Number of positions {len(pos)} does not match the number of guides {number}")

    guides = []
    for i in range(number):
        guide = Guide(f'{name}_{i}_guide', pos[i])
        guides.append(guide.guide)

    GuideCurve(name, guides)
    pm.select(clear=True)
    return guides

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

    orient_joints(joints, aimVector=(0, 1, 0), upVector=(1, 0, 0), useNormal=True)
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
