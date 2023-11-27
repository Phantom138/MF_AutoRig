import maya.cmds as cmds
#Maya Python API 2.0
import maya.api.OpenMaya as om


'''
TODO:
IK/FK limbs
    Nice names for the shapes
    Parent ik, fk to skin
    Create switch
    Create properly oriented fk controllers
'''


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


class ControlerGroup:
    def __init__(self, name, shape):
        self.grp = cmds.createNode('transform', name=name + grp_sff)
        if shape == 'CIRCLE':
            self.ctrl = cmds.circle(nr=(0, 1, 0), c=(0, 0, 0), name=name+ctrl_sff)
        else:
            self.ctrl = cmds.curve(degree=shape[0], point=shape[1], knot=shape[2], name = name+ctrl_sff)
        cmds.parent(self.ctrl, self.grp)


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

def fk_controllers(joints):
    #Receives joints starting with the grandchildren; maintains the same hierarchy;
    #Constrains the controllers to the right joints

    # Get joint orientation and create circle controller accordingly
    # Ex. if orientation = X, circle is pointing in X
    orientation = get_joint_orientation(joints[0], joints[1])
    if orientation == 'y':
        axis = (0, 1, 0)
    elif orientation == 'z':
        axis = (0, 0, 1)
    else:
        axis = (1, 0, 0)

    grp_previous = ''
    # Skips end joints
    for jnt in reversed(joints[:-1]):
        #Creates base name by removing the joint suffix
        base_name = jnt.replace(jnt_sff, '')
        grp = cmds.createNode('transform', name=base_name + ctrl_sff + grp_sff)

        ctrl = cmds.circle(nr=axis, c=(0, 0, 0), name=base_name + ctrl_sff)

        # Parent controller to group
        cmds.parent(ctrl, grp)
        # Match transforms and parent constrain controller to joint
        cmds.matchTransform(grp, jnt)
        cmds.parentConstraint(ctrl, jnt, maintainOffset=True)
        # Parent previous group to the current controller, maintaining the hierarchy
        if len(grp_previous) is not 0:
            cmds.parent(grp_previous, ctrl)
        grp_previous = grp


def create_ik_joints(joints):
    if len(joints) > 3:
        cmds.error("Only joint chains of 3 supported")

    #Create IK joints by duplicating the joints
    jnts = cmds.duplicate(joints, renameChildren=True)
    ik_joints = []
    for jnt in jnts:
        #Names them by removing the skin suffix and the jnt suffix
        if skin in jnt:
            base_name = jnt[:-1].replace(skin+jnt_sff, '')
        else:
            base_name = jnt[:-1].replace(end_sff + jnt_sff, '')

        ik_name = base_name + ik_sff + jnt_sff
        cmds.rename(jnt, ik_name)
        ik_joints.append(ik_name)

    handle_name = ik_joints[0].replace(ik_sff + jnt_sff, '_ikHandle')
    ikHandle = cmds.ikHandle(name=handle_name, startJoint=ik_joints[0], endEffector=ik_joints[2], solver='ikRPsolver')

    base_name=ik_joints[0].replace(jnt_sff,'')

    grp = cmds.createNode('transform', name=base_name + ctrl_sff + grp_sff)
    ctrl = cmds.curve(degree=CUBE[0], point=CUBE[1], knot=CUBE[2], name=base_name+ctrl_sff)
    cmds.parent(ctrl, grp)
    cmds.matchTransform(grp, ikHandle, position=True)

    cmds.parentConstraint(ctrl, ikHandle[0], maintainOffset=True)

    #Pole Vector
    pole_pos = create_pole_vector(joints)
    pole_name = base_name + pole_sff + ctrl_sff
    pole_grp = cmds.createNode('transform', name=pole_name + grp_sff)
    pole_ctrl = cmds.curve(degree=JOINT_CURVE[0], point=JOINT_CURVE[1], knot=JOINT_CURVE[2], name = pole_name)
    cmds.parent(pole_ctrl, pole_grp)

    pole_vector = create_pole_vector(joints)
    cmds.move(pole_vector.x, pole_vector.y, pole_vector.z, pole_grp, worldSpace=True)
    cmds.poleVectorConstraint(pole_ctrl, ikHandle[0])

    return ik_joints


def create_pole_vector(joints):
    A = om.MVector(cmds.xform(joints[0], worldSpace=True, rotatePivot=True, q=True))
    B = om.MVector(cmds.xform(joints[1], worldSpace=True, rotatePivot=True, q=True))
    C = om.MVector(cmds.xform(joints[2], worldSpace=True, rotatePivot=True, q=True))
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


def constraint_fkik(skin_joints, ik_joints, fk_joints):
    print(skin_joints)
    print(ik_joints)
    print(fk_joints)
    fkik_constraints = []
    if len(skin_joints) is not len(fk_joints) is not len(ik_joints) is not 3:
        cmds.error("Ik FK Joints not matching")
    for i in range(len(skin_joints)):
        constraint = cmds.parentConstraint(ik_joints[i], fk_joints[i], skin_joints[i])
        fkik_constraints.append(constraint)
        print(cmds.listConnections(constraint, destination=True, source=True))
    return fkik_constraints


def fkik_switch(joints, fkik_constraints):
    #receives skin joints
    base_name = joints[-1].replace(end_sff+jnt_sff,'') + attr_sff
    switch = ControlerGroup(base_name, ARROW)
    cmds.matchTransform(switch.grp, joints[-1])
    cmds.parentConstraint(joints[-1], switch.ctrl)
    cmds.addAttr(switch.ctrl, shortName="FKIK", attributeType="float",minValue=0, maxValue=1, keyable=True)

    #Connect attribute to the fkik constraints
    print(fkik_constraints)


def create_fkik(joints):
    fk_joints = create_fk_joints(joints)
    fk_controllers(fk_joints)
    ik_joints = create_ik_joints(joints)
    fkik_constraints = constraint_fkik(joints, ik_joints, fk_joints)
    fkik_switch(joints, fkik_constraints)


def get_joint_orientation(firstJnt, secondJnt):
    A = cmds.xform(firstJnt, worldSpace=True, matrix=True, q=True)
    A_vector = om.MVector(cmds.xform(firstJnt, worldSpace=True, rotatePivot=True, q=True))
    B_vector = om.MVector(cmds.xform(secondJnt, worldSpace=True, rotatePivot=True, q=True))

    AB = B_vector - A_vector
    AB = AB.normal()
    axis = ''
    for i in range(3):
        axis_vector = om.MVector(A[i*4],A[i*4+1],A[i*4+2])
        axis_vector = axis_vector
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


if __name__ == "__main__":
    selection = cmds.ls(selection = True)
    for sel in selection:
        #List hierarchy of selection
        joints = cmds.listRelatives(sel, allDescendents=True, type='joint')
        #Add selection to the list
        joints.append(sel)
        joints.reverse()
        print(get_joint_orientation(joints[0], joints[1]))
        create_fkik(joints)
