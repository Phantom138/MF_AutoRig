import pymel.core as pm
import pymel.core.datatypes as dt
import maya.cmds as cmds
import maya.api.OpenMaya as om


grp_sff = '_GRP'
ctrl_sff = '_CTRL'
jnt_sff = '_JNT'
end_sff = '_end'
skin = '_skin'
ik_sff = '_ik'
fk_sff = '_fk'
pole_sff = '_pole'
attr_sff = '_attr'

CUBE = [1, [(1, 1, 1), (1, 1, -1), (-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, -1, 1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, -1), (1, -1, -1),
            (-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, -1, 1), (1, -1, 1)], [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]]

JOINT_CURVE = [1, [(0, 1, 0), (0, 0.92388000000000003, 0.382683), (0, 0.70710700000000004, 0.70710700000000004), (0, 0.382683, 0.92388000000000003), (0, 0, 1), (0, -0.382683, 0.92388000000000003),
        (0, -0.70710700000000004, 0.70710700000000004), (0, -0.92388000000000003, 0.382683), (0, -1, 0), (0, -0.92388000000000003, -0.382683),(0, -0.70710700000000004, -0.70710700000000004),(0, -0.382683, -0.92388000000000003),
        (0, 0, -1), (0, 0.382683, -0.92388000000000003), (0, 0.70710700000000004, -0.70710700000000004), (0, 0.92388000000000003, -0.382683), (0, 1, 0), (0.382683, 0.92388000000000003, 0),
        (0.70710700000000004, 0.70710700000000004, 0), (0.92388000000000003, 0.382683, 0), (1, 0, 0), (0.92388000000000003, -0.382683, 0), (0.70710700000000004, -0.70710700000000004, 0),
        (0.382683, -0.92388000000000003, 0), (0, -1, 0), (-0.382683, -0.92388000000000003, 0), (-0.70710700000000004, -0.70710700000000004, 0), (-0.92388000000000003, -0.382683, 0),
        (-1, 0, 0), (-0.92388000000000003, 0.382683, 0), (-0.70710700000000004, 0.70710700000000004, 0), (-0.382683, 0.92388000000000003, 0), (0, 1, 0), (0, 0.92388000000000003, -0.382683),
        (0, 0.70710700000000004, -0.70710700000000004),(0, 0.382683, -0.92388000000000003), (0, 0, -1), (-0.382683, 0, -0.92388000000000003), (-0.70710700000000004, 0, -0.70710700000000004),
        (-0.92388000000000003, 0, -0.382683), (-1, 0, 0), (-0.92388000000000003, 0, 0.382683), (-0.70710700000000004, 0, 0.70710700000000004), (-0.382683, 0, 0.92388000000000003), (0, 0, 1), (0.382683, 0, 0.92388000000000003),
        (0.70710700000000004, 0, 0.70710700000000004),(0.92388000000000003, 0, 0.382683), (1, 0, 0), (0.92388000000000003, 0, -0.382683), (0.70710700000000004, 0, -0.70710700000000004),(0.382683, 0, -0.92388000000000003), (0, 0, -1)],
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52]]

ARROW = [1, [(-2, 0, 0), (1, 0, 1), (1, 0, -1), (-2, 0, 0), (1, 1, 0), (1, 0, 0), (1, -1, 0), (-2, 0, 0)], [0, 1, 2, 3, 4, 5, 6, 7]]

def create_fk_joints(joints):
    jnts = cmds.duplicate(joints, renameChildren=True)
    fk_joints = []
    for jnt in jnts:
        # Names them by removing the skin suffix and the jnt suffix
        if skin in jnt:
            base_name = jnt[:-1].replace(skin + jnt_sff, '')
        elif end_sff in jnt:
            base_name = jnt[:-1].replace(end_sff + jnt_sff, '')
        fk_name = base_name + fk_sff + jnt_sff
        cmds.rename(jnt, fk_name)
        fk_joints.append(fk_name)
    return fk_joints

def pm_create_fk_joint(joints):
    # Duplicates input joints
    jnts = pm.duplicate(joints, renameChildren=True)
    fk_joints = []
    for jnt in jnts:
        # Names them by removing the skin suffix and the jnt suffix

        if skin in jnt:
            base_name = jnt[:-1].replace(skin + jnt_sff, '')
        elif end_sff in jnt:
            base_name = jnt[:-1].replace(end_sff + jnt_sff, '')
        fk_name = base_name + fk_sff + jnt_sff
        pm.rename(jnt, fk_name)


def get_joint_orientation(firstJnt, secondJnt):
    A = pm.xform(firstJnt, worldSpace=True, matrix=True, q=True)
    A_vector = dt.Vector(pm.xform(firstJnt, worldSpace=True, rotatePivot=True, q=True))
    B_vector = dt.Vector(pm.xform(secondJnt,worldSpace=True, rotatePivot=True, q=True))
    print(A)

    AB = B_vector - A_vector
    AB = AB.normal()
    print(AB)
    axis = ''
    for i in range(3):
        axis_vector = dt.Vector(A[i * 4], A[i * 4 + 1], A[i * 4 + 2])
        dotP = axis_vector * AB
        print(dotP)

        if axis_vector.isParallel(AB):
            axis = 'xyz'[i]
            print(axis)
    if axis:
        return axis
    else:
        cmds.warning(f'{firstJnt} is not oriented properly to {secondJnt}, assuming Y axis')
        return 'y'


def fk_controllers(joints):
    # Get joint orientation and create circle controller accordingly
    # Ex. if orientation = X, circle is pointing in X
    orientation = get_joint_orientation(joints[0], joints[1])
    if orientation == 'y':
        axis = (0, 1, 0)
    elif orientation == 'z':
        axis = (0, 0, 1)
    else:
        axis = (1, 0, 0)
    #print(axis)

    ctrl_previous = None
    for jnt in joints:
        # Creates base name by removing the joint suffix
        base_name = jnt.replace(jnt_sff, '')

        # Create controller and controller group, parenting the two of them
        grp = pm.createNode('transform', name=base_name + ctrl_sff + grp_sff)
        ctrl = pm.circle(nr=axis, c=(0, 0, 0), name=base_name + ctrl_sff)
        pm.parent(ctrl, grp)

        # Match transforms and parent constrain controller to joint
        pm.matchTransform(grp, jnt)
        pm.parentConstraint(ctrl, jnt, maintainOffset = True)

        # Parent previous group to the current controller
        if ctrl_previous is not None:
            pm.parent(grp, ctrl_previous)
        ctrl_previous = ctrl


def create_pole_vector(joints):
    print(joints)
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
    pole_len = AB.length() + 1
    # Create pole position
    pole = TB * pole_len + T + A

    return pole

def create_ik_joints(joints):
    if len(joints) > 3:
        pm.error("Only joint chains of 3 supported")

    # Create IK joints by duplicating the joints
    jnts = pm.duplicate(joints, renameChildren=True)
    ik_joints = []
    for jnt in jnts:
        name = jnt.name()
        # Names joints by removing the skin suffix and the jnt suffix
        if skin in name:
            base_name = name[:-1].replace(skin + jnt_sff, '')
        else:
            base_name = name[:-1].replace(end_sff + jnt_sff, '')

        ik_name = base_name + ik_sff + jnt_sff
        ik_jnt = pm.rename(jnt, ik_name)
        # Add joints to ik_joints list
        ik_joints.append(ik_jnt)

    # Get base name of first joint eg. joint1_skin_JNT -> joint1
    first_jnt_name = joints[0].name().replace(skin + jnt_sff, '')

    # Create ik handle
    handle_name = first_jnt_name + '_ikHandle'
    ikHandle = pm.ikHandle(name=handle_name, startJoint=ik_joints[0], endEffector=ik_joints[2], solver='ikRPsolver')

    # Create group and controller for ik
    grp = pm.createNode('transform', name=first_jnt_name + ik_sff + ctrl_sff + grp_sff)
    ctrl = pm.curve(degree=CUBE[0], point=CUBE[1], knot=CUBE[2], name=first_jnt_name + ik_sff + ctrl_sff)
    pm.parent(ctrl, grp)
    pm.matchTransform(grp, ikHandle, position=True)

    pm.parentConstraint(ctrl, ikHandle[0], maintainOffset=True)

    # Pole Vector
    pole_name = base_name + pole_sff + ctrl_sff

    # Create controller and group
    pole_grp = pm.createNode('transform', name=pole_name + grp_sff)
    pole_ctrl = pm.curve(degree=JOINT_CURVE[0], point=JOINT_CURVE[1], knot=JOINT_CURVE[2], name = pole_name)
    pm.parent(pole_ctrl, pole_grp)

    # Place it into position
    pole_vector = create_pole_vector(joints)
    pm.move(pole_vector.x, pole_vector.y, pole_vector.z, pole_grp, worldSpace=True)
    pm.poleVectorConstraint(pole_ctrl, ikHandle[0])

    return ik_joints

def constraint_fkik(skin_joints, ik_joints, fk_joints):

    fkik_constraints = []
    if len(skin_joints) is not len(fk_joints) is not len(ik_joints) is not 3:
        pm.error("Ik FK Joints not matching")

    for i in range(len(skin_joints)):
        constraint = pm.parentConstraint(ik_joints[i], fk_joints[i], skin_joints[i])
        fkik_constraints.append(constraint)
        print(pm.listConnections(constraint, destination=True, source=True))
    return fkik_constraints

def create_fkik(joints):
    fk_joints = create_fk_joints(joints)
    fk_controllers(fk_joints)
    ik_joints = create_ik_joints(joints)
    fkik_constraints = constraint_fkik(joints, ik_joints, fk_joints)
    #fkik_switch(joints, fkik_constraints)


selection = pm.selected()
create_fkik(selection)



