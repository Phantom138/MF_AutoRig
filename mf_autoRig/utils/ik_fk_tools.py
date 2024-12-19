import pymel.core as pm
import pymel.core.datatypes as dt
import mf_autoRig.utils.defaults as df
from mf_autoRig.utils.controllers_tools import CtrlGrp
from mf_autoRig.utils.general import get_base_name, get_group

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
            return 0, 1, 0
        elif axis == 'z':
            return 0, 0, 1
        else:
            return 1, 0, 0
    else:
        pm.warning(f'{firstJnt} is not oriented properly to {secondJnt}, assuming Y axis')
        return 0, 1, 0


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

    # Get joint orientation and create circle controller accordingly
    # Ex. if orientation = X, circle is pointing in X
    axis = get_joint_orientation(joints[0], joints[1])

    # Skips end joints
    if skipEnd:
        joints = joints[:-1]

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

    # Place pole into position
    pole_vector = create_pole_vector(joints)
    pole.grp.translate.set(pole_vector)
    pm.poleVectorConstraint(pole.ctrl, ikHandle[0])

    # Add guide for pole vector
    create_guide_curve_for_pole(pole.ctrl, ik_joints[1])

    # Clean-Up
    ik_ctrls = [ik.ctrl, pole.ctrl]
    ik_ctrl_grp = pm.group(ik.grp, pole.grp, name=base_name + df.ik_sff + '_Control_Grp')

    pm.parent(ikHandle[0], get_group('ikHandle_grp'))

    # Clear selection
    pm.select(clear=True)

    return ik_joints, ik_ctrls, ik_ctrl_grp, ikHandle[0]


def create_guide_curve_for_pole(ctrl, joint):
    # Parent new guide shape under ctrl
    crv = pm.curve(d=1, p=[(0, 0, 0), (0, 0, 0)], k=[0, 1], name=f'{ctrl.name()}_guide')
    shape = crv.getShape()
    pm.parent(shape, ctrl, r=True, s=True)

    # Delete old transform node
    pm.delete(crv)

    # Set shape to template and change width
    shape.overrideEnabled.set(1)
    shape.overrideDisplayType.set(1)
    shape.lineWidth.set(1.5)

    # Get end point position
    # This has to be local position, so relative to the parent(ctrl) position.
    # To do this, we get the joint position in world space and then multiply it by the ctrl inverse matrix
    mult = pm.createNode("multMatrix")
    joint.worldMatrix[0].connect(mult.matrixIn[0])
    ctrl.worldInverseMatrix[0].connect(mult.matrixIn[1])

    # Decompose the matrix
    decompose = pm.createNode("decomposeMatrix")
    mult.matrixSum.connect(decompose.inputMatrix)

    decompose.outputTranslate.connect(shape.controlPoints[1])

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
