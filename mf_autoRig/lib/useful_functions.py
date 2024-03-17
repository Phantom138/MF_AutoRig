import pymel.core as pm
import pymel.core.datatypes as dt
import re
import maya.cmds as cmds

import mf_autoRig.lib.defaults as df


class CtrlGrp:
    def __init__(self, name, shape, scale=df.CTRL_SCALE, axis=(0, 1, 0)):
        # Create empty grp
        self.grp = pm.createNode('transform', name=name + df.ctrl_sff + df.grp_sff)

        if shape == 'circle':
            self.ctrl = pm.circle(nr=axis, c=(0, 0, 0), radius=scale, name=name + df.ctrl_sff,
                                  constructionHistory=False)[0]
        elif shape == 'arc':
            self.ctrl = pm.circle(nr=axis, c=(0, 0, 0), radius=scale, sw=180, d=3, ut=0, tol=0.01, s=8, ch=0,
                                  name=name + df.ctrl_sff)[0]
        else:
            points = [(x * scale, y * scale, z * scale) for x, y, z in df.CTRL_SHAPES[shape][1]]
            self.ctrl = pm.curve(degree=df.CTRL_SHAPES[shape][0],
                                 point=points,
                                 name=name + df.ctrl_sff)
        # Parent ctrl and grp
        pm.parent(self.ctrl, self.grp)

def get_group(name):
    try:
        guides_grp = pm.PyNode(name)
    except pm.MayaNodeError:
        guides_grp = pm.createNode('transform', name=name)

    return guides_grp

def create_fk_jnts(joints):
    # Duplicates input joints
    fk_joints = pm.duplicate(joints, renameChildren=True)

    for jnt in fk_joints:
        name = jnt.name()
        # Names joints by removing the skin suffix and the jnt suffix
        if df.skin_sff in name:
            base_name = name[:-1].replace(df.skin_sff + df.jnt_sff, '')
        elif df.end_sff in name:
            base_name = name[:-1].replace(df.end_sff + df.jnt_sff, '')
        else:
            base_name = jnt.name()
        fk_name = base_name + df.fk_sff + df.jnt_sff

        pm.rename(jnt, fk_name)

    return fk_joints


def get_joint_orientation(firstJnt, secondJnt):
    A = pm.xform(firstJnt, worldSpace=True, matrix=True, q=True)
    A_vector = dt.Vector(pm.xform(firstJnt, worldSpace=True, rotatePivot=True, q=True))
    B_vector = dt.Vector(pm.xform(secondJnt, worldSpace=True, rotatePivot=True, q=True))

    AB = B_vector - A_vector
    AB = AB.normal()
    axis = ''
    for i in range(3):
        axis_vector = dt.Vector(A[i * 4], A[i * 4 + 1], A[i * 4 + 2])

        if axis_vector.isParallel(AB):
            axis = 'xyz'[i]

    if axis:
        #print(f'Joint orientation between {firstJnt} and {secondJnt} is {axis}')
        if axis == 'y':
            return (0, 1, 0)
        elif axis == 'z':
            return (0, 0, 1)
        else:
            return (1, 0, 0)
    else:
        pm.warning(f'{firstJnt} is not oriented properly to {secondJnt}, assuming Y axis')
        return (0, 1, 0)


def create_fk_ctrls(joints, skipEnd=True, shape='circle', scale=1):
    scale *= df.CTRL_SCALE
    # Exception case: only one joint
    if type(joints) == pm.nodetypes.Joint:
        print(f"// Running fk_ctrls for {joints}")
        jnt = joints
        base_name = jnt.replace(df.jnt_sff, '')
        if df.skin_sff in base_name:
            base_name = base_name.replace(df.skin_sff, '')
        # Create controller and controller group, parenting the two of them
        fk = CtrlGrp(base_name, shape, scale=scale)

        # Match transforms and parent constrain controller to joint
        pm.matchTransform(fk.grp, jnt)
        pm.parentConstraint(fk.ctrl, jnt, maintainOffset=True)

        return fk.ctrl

    # Skips end joints
    if skipEnd:
        joints = joints[:-1]


    # Get joint orientation and create circle controller accordingly
    # Ex. if orientation = X, circle is pointing in X
    axis = get_joint_orientation(joints[0], joints[1])

    # Initialize ctrl list
    fk_ctrls = []
    ctrl_previous = None

    for jnt in joints:
        # Creates base name by removing the joint suffix and also skin sff if present
        base_name = jnt.replace(df.jnt_sff, '')
        if df.skin_sff in base_name:
            base_name = base_name.replace(df.skin_sff, '')
        # Create controller and controller group, parenting the two of them
        fk = CtrlGrp(base_name, shape, scale=scale, axis=axis)

        # Match transforms and parent constrain controller to joint
        pm.matchTransform(fk.grp, jnt)
        pm.parentConstraint(fk.ctrl, jnt, maintainOffset=True)

        # Parent previous group to the current controller
        if ctrl_previous is not None:
            pm.parent(fk.grp, ctrl_previous)
        ctrl_previous = fk.ctrl

        # Add ctrl
        fk_ctrls.append(fk.ctrl)

    # Clear selection
    pm.select(clear=True)

    return fk_ctrls


def create_pole_vector(joints):
    A = dt.Vector(pm.xform(joints[0], worldSpace=True, rotatePivot=True, q=True))
    B = dt.Vector(pm.xform(joints[1], worldSpace=True, rotatePivot=True, q=True))
    C = dt.Vector(pm.xform(joints[2], worldSpace=True, rotatePivot=True, q=True))
    AC = C - A
    AB = B - A

    # T = AB projected onto AC
    AC_n = AC.normal()
    dotP = AB * AC_n
    T = AC_n * dotP

    # Build TB vector
    TB = AB - T
    # Create pole length
    TB = TB.normal()
    pole_len = AB.length() * 1.3
    # Create pole position
    pole = TB * pole_len + T + A

    return pole

def create_ik(joints, translation=False, create_new=True):
    if len(joints) > 3:
        pm.error("Only joint chains of 3 supported")

    if create_new:
        # Create IK joints by duplicating the joints
        ik_joints = pm.duplicate(joints, renameChildren=True)
    else:
        ik_joints = joints

    if create_new:
        for jnt in ik_joints:
            name = jnt.name()
            # Names joints by removing the skin suffix and the jnt suffix
            if df.skin_sff in name:
                base_name = name[:-1].replace(df.skin_sff + df.jnt_sff, '')
            else:
                base_name = name[:-1].replace(df.end_sff + df.jnt_sff, '')

            ik_name = base_name + df.ik_sff + df.jnt_sff
            pm.rename(jnt, ik_name)

    else:
        base_name = get_base_name(ik_joints[-1].name())

    print(base_name)
    # Create ik handle
    handle_name = base_name + '_ikHandle'
    ikHandle = pm.ikHandle(name=handle_name, startJoint=ik_joints[0], endEffector=ik_joints[2], solver='ikRPsolver')

    # Create group and controller for ikHandle
    ik = CtrlGrp(base_name + df.ik_sff, 'cube')

    # TODO: orient grp the right way
    # if translation is True, only match translation
    if translation:
        pm.matchTransform(ik.grp, ik_joints[-1], pos=True, rot=False, scale=True)
    else:
        pm.matchTransform(ik.grp, ik_joints[-1])


    pm.parentConstraint(ik.ctrl, ikHandle[0], maintainOffset=True)

    # Pole Vector
    pole_name = base_name + df.pole_sff

    # Create controller and group
    pole = CtrlGrp(pole_name, 'joint_curve')

    # Place it into position
    pole_vector = create_pole_vector(joints)
    pm.move(pole_vector.x, pole_vector.y, pole_vector.z, pole.grp, worldSpace=True)
    pm.poleVectorConstraint(pole.ctrl, ikHandle[0])

    # Clean-Up
    ik_ctrls = [ik.ctrl, pole.ctrl]
    ik_ctrl_grp = pm.group(ik.grp, pole.grp, name=base_name + df.ik_sff + '_Control_Grp')

    pm.parent(ikHandle[0], get_group('ikHandle_grp'))

    # Clear selection
    pm.select(clear=True)

    return ik_joints, ik_ctrls, ik_ctrl_grp, ikHandle[0]

def constraint_ikfk(joints, ik_joints, fk_joints):
    fkik_constraints = []
    if not (len(joints) == len(fk_joints) == len(ik_joints) == 3):
        pm.error("Ik FK Joints not matching")

    for i in range(len(joints)):
        constraint = pm.parentConstraint(ik_joints[i], fk_joints[i], joints[i])
        fkik_constraints.append(constraint)

    # Clear selection
    pm.select(clear=True)

    return fkik_constraints


def ikfk_switch(ik_ctrls_grp, fk_ctrls, ikfk_constraints, endJnt):
    """
    Method:
    ik Fk Switch = fk weight
    ik Fk Switch * (-1) = ik weight
    """
    # Get base name of the joint (L_arm01_skin_jnt -> L_arm
    base_name = get_base_name(endJnt.name())

    name = base_name + '_ikfkSwitch'

    # Create switch controller and grp
    switch = CtrlGrp(name, 'arrow')

    pm.matchTransform(switch.grp, endJnt)
    pm.parentConstraint(endJnt, switch.grp, maintainOffset=True)

    # Add ikfk switch attribute
    pm.addAttr(switch.ctrl, longName=df.ikfkSwitch_name, attributeType='float', min=0, max=1, defaultValue=1, keyable=True)

    # Reverse node
    reverse_sw = pm.createNode('reverse', name=base_name + '_Ik_Fk_reverse')
    pm.connectAttr(switch.ctrl + f'.{df.ikfkSwitch_name}', reverse_sw + '.inputX')

    # For each constraint get the weight names and connect them accrodingly
    for constraint in ikfk_constraints:
        weights = constraint.getWeightAliasList()
        for weight in weights:
            name = weight.longName(fullPath=False)
            # If ik weight connect to reverse
            if df.ik_sff in name:
                pm.connectAttr(reverse_sw + '.outputX', weight)
            # If fk weight connect to switch
            if df.fk_sff in name:
                pm.connectAttr(switch.ctrl + '.IkFkSwitch', weight)

    # Hide ik or fk ctrls based on switch
    pm.connectAttr(reverse_sw + '.outputX', ik_ctrls_grp + '.visibility')
    fk_ctrls_grp = fk_ctrls[0].getParent()
    pm.connectAttr(switch.ctrl + f'.{df.ikfkSwitch_name}', fk_ctrls_grp + '.visibility')

    # Clear selection
    pm.select(clear=True)
    return switch.ctrl

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

    #print(f"For {name} base name is {base_name}")

    return base_name

def create_offset_grp(ctrls):
    colors = [0, 255, 0]

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


def create_joint_chain(jnt_number, name, start_pos, end_pos, rot=None, defaultValue=51):
    if rot is None:
        rot = [0, 0, 0]

    # Create driven grp if not existent
    try:
        driven_grp = pm.PyNode('DONOTTOUCH_driven_guides_grp')
    except pm.MayaNodeError:
        driven_grp = pm.createNode('transform', name='DONOTTOUCH_driven_guides_grp')

    # Create plane
    plane = pm.polyPlane(name=f'tmp_{name}_Plane', w=2, h=26, sh=1, sw=1)[0]
    plane.v.set(0)
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

    # Group start and end jnt
    grp = pm.createNode('transform', name=f'{name}_grp')
    pm.matchTransform(grp, startJnt)
    pm.parent(startJnt, endJnt, grp)

    # Parent to rig grp
    pm.parent(grp, get_group(df.rig_guides_grp))



    return joints

def create_joints_from_guides(name, guides, suffix=None):
    pm.select(clear=True)
    joints = []
    for i, tmp in enumerate(guides):
        trs = pm.xform(tmp, q=True, t=True, ws=True)

        if suffix is None:
            suffix = df.skin_sff
            # Last joint has end suffix
            if i == len(guides) - 1:
                suffix = df.end_sff

        jnt = pm.joint(name=f'{name}{i + 1:02}{suffix}{df.jnt_sff}', position=trs)
        joints.append(jnt)

    # Orient joints
    pm.joint(joints[0], edit=True, orientJoint='yzx', secondaryAxisOrient='zup', children=True)
    pm.joint(joints[-1], edit=True, orientJoint='none')

    pm.select(clear = True)
    return joints

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


def mirror_default_pos(pos):
    mirrored_pos = {}
    for key, value in pos.items():
        if isinstance(value[0], list):
            mirrored_pos[key] = [[pos[0]*(-1)] + pos[1:] for pos in value]
        else:
            mirrored_pos[key] = [value[0]*(-1)] + value[1:]

    #mirrored_pos = {key: [[-pos[0]] + pos[1:] for pos in value] for key, value in default_pos.items()}
    return mirrored_pos

def control_shape_mirror(src, dst):
    targetCvList = pm.ls(f'{src.name()}.cv[:]', flatten=True)
    destCvList = pm.ls(f'{dst.name()}.cv[:]', flatten=True)

    if len(targetCvList) != len(destCvList):
        pm.error('ctrls not matching')

    for tar, des in zip(targetCvList, destCvList):  # zip target and destination list to match data
        pos = pm.xform(tar, query=True, translation=True, worldSpace=True)
        pos = [pos[0] * -1.0, pos[1], pos[2]]  # flip x value of position
        pm.xform(des, translation=pos, worldSpace=True)

def replace_ctrl(src, dst):
    src_shape = src.getShape()
    dst_shape = dst.getShape()

    if src_shape.type() != 'nurbsCurve' or dst_shape.type() != 'nurbsCurve':
        pm.error("Non-curve objects")
        return

    import mf_autoRig.lib.get_curve_info as curve_info

    deg = cmds.getAttr(f'{src}.degree')
    form = cmds.getAttr(f'{src}.form')
    cvs = cmds.getAttr(f'{src}.cv[*]')


    pm.curve(dst, r=True, point=cvs, degree=deg, per=False)

    if form == 2:
        pm.closeCurve(dst, preserveShape=False, replaceOriginal=True)


