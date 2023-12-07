import pymel.core as pm
import pymel.core.datatypes as dt
import maya.cmds as cmds
import maya.api.OpenMaya as om
import re

grp_sff = '_grp'
ctrl_sff = '_ctrl'
jnt_sff = '_jnt'
end_sff = '_end'
skin = '_skin'
ik_sff = '_ik'
fk_sff = '_fk'
pole_sff = '_pole'
attr_sff = '_attr'
ikfkSwitch_name = 'IkFkSwitch'

# CTRL Shapes structure: Degree, Points, Knots
CTRL_SHAPES = {
    'cube': [1, [(1, 1, 1), (1, 1, -1), (-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, -1, 1), (1, -1, -1), (1, 1, -1),
                 (-1, 1, -1),
                 (-1, -1, -1), (1, -1, -1),
                 (-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, -1, 1), (1, -1, 1)],
             [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]],

    "joint_curve": [1, [(0, 1, 0), (0, 0.92388000000000003, 0.382683), (0, 0.70710700000000004, 0.70710700000000004),
                        (0, 0.382683, 0.92388000000000003), (0, 0, 1), (0, -0.382683, 0.92388000000000003),
                        (0, -0.70710700000000004, 0.70710700000000004), (0, -0.92388000000000003, 0.382683), (0, -1, 0),
                        (0, -0.92388000000000003, -0.382683), (0, -0.70710700000000004, -0.70710700000000004),
                        (0, -0.382683, -0.92388000000000003),
                        (0, 0, -1), (0, 0.382683, -0.92388000000000003), (0, 0.70710700000000004, -0.70710700000000004),
                        (0, 0.92388000000000003, -0.382683), (0, 1, 0), (0.382683, 0.92388000000000003, 0),
                        (0.70710700000000004, 0.70710700000000004, 0), (0.92388000000000003, 0.382683, 0), (1, 0, 0),
                        (0.92388000000000003, -0.382683, 0), (0.70710700000000004, -0.70710700000000004, 0),
                        (0.382683, -0.92388000000000003, 0), (0, -1, 0), (-0.382683, -0.92388000000000003, 0),
                        (-0.70710700000000004, -0.70710700000000004, 0), (-0.92388000000000003, -0.382683, 0),
                        (-1, 0, 0), (-0.92388000000000003, 0.382683, 0), (-0.70710700000000004, 0.70710700000000004, 0),
                        (-0.382683, 0.92388000000000003, 0), (0, 1, 0), (0, 0.92388000000000003, -0.382683),
                        (0, 0.70710700000000004, -0.70710700000000004), (0, 0.382683, -0.92388000000000003), (0, 0, -1),
                        (-0.382683, 0, -0.92388000000000003), (-0.70710700000000004, 0, -0.70710700000000004),
                        (-0.92388000000000003, 0, -0.382683), (-1, 0, 0), (-0.92388000000000003, 0, 0.382683),
                        (-0.70710700000000004, 0, 0.70710700000000004), (-0.382683, 0, 0.92388000000000003), (0, 0, 1),
                        (0.382683, 0, 0.92388000000000003),
                        (0.70710700000000004, 0, 0.70710700000000004), (0.92388000000000003, 0, 0.382683), (1, 0, 0),
                        (0.92388000000000003, 0, -0.382683), (0.70710700000000004, 0, -0.70710700000000004),
                        (0.382683, 0, -0.92388000000000003), (0, 0, -1)],
                    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26,
                     27,
                     28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51,
                     52]],

    "arrow": [1, [(-2, 0, 0), (1, 0, 1), (1, 0, -1), (-2, 0, 0), (1, 1, 0), (1, 0, 0), (1, -1, 0), (-2, 0, 0)],
              [0, 1, 2, 3, 4, 5, 6, 7]]
}

CTRL_SCALE = 10

for shape in CTRL_SHAPES:
    CTRL_SHAPES[shape][1] = [(x * CTRL_SCALE, y * CTRL_SCALE, z * CTRL_SCALE) for x, y, z in CTRL_SHAPES[shape][1]]


def create_fk_joints(joints, ):
    # Duplicates input joints
    fk_joints = pm.duplicate(joints, renameChildren=True)

    for jnt in fk_joints:
        name = jnt.name()
        # Names joints by removing the skin suffix and the jnt suffix
        if skin in name:
            base_name = name[:-1].replace(skin + jnt_sff, '')
        else:
            base_name = name[:-1].replace(end_sff + jnt_sff, '')

        fk_name = base_name + fk_sff + jnt_sff

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
    print(f'Joint orientation is {axis}')
    if axis:
        if axis == 'y':
            return (0, 1, 0)
        elif axis == 'z':
            return (0, 0, 1)
        else:
            return (1, 0, 0)
    else:
        cmds.warning(f'{firstJnt} is not oriented properly to {secondJnt}, assuming Y axis')
        return (0,1,0)


def fk_controllers(joints):
    # Get joint orientation and create circle controller accordingly
    # Ex. if orientation = X, circle is pointing in X
    axis = get_joint_orientation(joints[0], joints[1])

    # Initialize ctrl list
    fk_ctrls = []
    ctrl_previous = None

    # Skips end joints
    for jnt in joints[:-1]:
        # Creates base name by removing the joint suffix
        base_name = jnt.replace(jnt_sff, '')

        # Create controller and controller group, parenting the two of them
        grp = pm.createNode('transform', name=base_name + ctrl_sff + grp_sff)
        ctrl = pm.circle(nr=axis, c=(0, 0, 0), radius=CTRL_SCALE, name=base_name + ctrl_sff, constructionHistory=False)
        pm.parent(ctrl, grp)

        # Match transforms and parent constrain controller to joint
        pm.matchTransform(grp, jnt)
        pm.parentConstraint(ctrl, jnt, maintainOffset=True)

        # Parent previous group to the current controller
        if ctrl_previous is not None:
            pm.parent(grp, ctrl_previous)
        ctrl_previous = ctrl

        # Add ctrl
        fk_ctrls.append(ctrl[0])

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
    pole_len = AB.length() * 2
    # Create pole position
    pole = TB * pole_len + T + A

    return pole


def create_ik(joints):
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
    match = re.search('([a-zA-Z]_[a-zA-Z]+)\d*_', joints[-1].name())
    base_name = match.group(1)

    # Create ik handle
    handle_name = base_name + '_ikHandle'
    ikHandle = pm.ikHandle(name=handle_name, startJoint=ik_joints[0], endEffector=ik_joints[2], solver='ikRPsolver')

    ik_ctrls = []
    # Create group and controller for ikHandle
    grp = pm.createNode('transform', name=base_name + ik_sff + ctrl_sff + grp_sff)
    ctrl = pm.curve(degree=CTRL_SHAPES['cube'][0], point=CTRL_SHAPES['cube'][1], knot=CTRL_SHAPES['cube'][2],
                    name=base_name + ik_sff + ctrl_sff)
    pm.parent(ctrl, grp)
    # TODO: orient grp the right way
    pm.matchTransform(grp, ik_joints[-1])

    pm.parentConstraint(ctrl, ikHandle[0], maintainOffset=True)

    # Pole Vector
    pole_name = base_name + pole_sff + ctrl_sff

    # Create controller and group
    pole_grp = pm.createNode('transform', name=pole_name + grp_sff)
    pole_ctrl = pm.curve(degree=CTRL_SHAPES['joint_curve'][0], point=CTRL_SHAPES['joint_curve'][1],
                         knot=CTRL_SHAPES['joint_curve'][2], name=pole_name)
    pm.parent(pole_ctrl, pole_grp)

    # Place it into position
    pole_vector = create_pole_vector(joints)
    pm.move(pole_vector.x, pole_vector.y, pole_vector.z, pole_grp, worldSpace=True)
    pm.poleVectorConstraint(pole_ctrl, ikHandle[0])


    # Clean-Up
    ik_ctrl_grp = pm.group(grp, pole_grp, name = base_name + ik_sff + '_Control_Grp')
    return ik_joints, ik_ctrl_grp


def ikfk_constraint(skin_joints, ik_joints, fk_joints):
    fkik_constraints = []
    if len(skin_joints) is not len(fk_joints) is not len(ik_joints) is not 3:
        pm.error("Ik FK Joints not matching")

    for i in range(len(skin_joints)):
        constraint = pm.parentConstraint(ik_joints[i], fk_joints[i], skin_joints[i])
        fkik_constraints.append(constraint)

    return fkik_constraints


def ikfk_switch(ik_ctrls_grp, fk_ctrls, ikfk_constraints, endJnt):
    '''
    Method:
    ik Fk Switch = fk weight
    ik Fk Switch * (-1) = ik weight
    '''
    # Get base name of the joint (L_arm01_skin_jnt -> L_arm
    match = re.search('([a-zA-Z]_[a-zA-Z]+)\d*_', endJnt.name())
    base_name = match.group(1)

    name = base_name + '_ikfkSwitch' + ctrl_sff

    # Create switch controller and grp
    switch_grp = pm.createNode('transform', name=name + '_grp')
    switch_ctrl = pm.curve(degree=CTRL_SHAPES['arrow'][0], point=CTRL_SHAPES['arrow'][1], knot=CTRL_SHAPES['arrow'][2],
                           name=name)
    pm.parent(switch_ctrl, switch_grp)
    pm.matchTransform(switch_grp, endJnt)
    pm.parentConstraint(endJnt, switch_grp, maintainOffset=True)

    # Add ikfk switch attribute
    pm.addAttr(switch_ctrl, longName=ikfkSwitch_name, attributeType='float', min=0, max=1, defaultValue=1, keyable=True)

    # Reverse node
    reverse_sw = pm.createNode('reverse', name=base_name + '_Ik_Fk_reverse')
    pm.connectAttr(switch_ctrl + f'.{ikfkSwitch_name}', reverse_sw + '.inputX')

    # For each constraint get the weight names and connect them accrodingly
    for constraint in ikfk_constraints:
        weights = constraint.getWeightAliasList()
        for weight in weights:
            name = weight.longName(fullPath=False)
            # If ik weight connect to reverse
            if ik_sff in name:
                pm.connectAttr(reverse_sw + '.outputX', weight)
            # If fk weight connect to switch
            if fk_sff in name:
                pm.connectAttr(switch_ctrl + '.IkFkSwitch', weight)

    # Hide ik or fk ctrls based on switch
    pm.connectAttr(reverse_sw + '.outputX', ik_ctrls_grp + '.visibility')
    print(fk_ctrls)
    fk_ctrls_grp = fk_ctrls[0].getParent()
    pm.connectAttr(switch_ctrl + f'.{ikfkSwitch_name}', fk_ctrls_grp + '.visibility')

    return switch_ctrl

def create_fkik(joints, method = None):
    # FK
    fk_joints = create_fk_joints(joints)
    fk_ctrls = fk_controllers(fk_joints)
    # IK
    ik_joints, ik_ctrls_grp = create_ik(joints)
    # Constraints
    fkik_constraints = ikfk_constraint(joints, ik_joints, fk_joints)
    # Switch
    switch_ctrl = ikfk_switch(ik_ctrls_grp, fk_ctrls, fkik_constraints, joints[-1])

    # Clean-up
    # Get Base Name L_arm01_skin_jnt -> L_arm
    match = re.search('([a-zA-Z]_[a-zA-Z]+)\d*_', joints[0].name())
    base_name = match.group(1)

    # Group joints only if group isn't already there
    joint_grp_name = base_name + '_Joint_Grp'
    skin_jnt_parent = joints[0].getParent(1)
    if skin_jnt_parent.name() != joint_grp_name:
        pm.group(fk_joints[0], ik_joints[0], joints[0], name=joint_grp_name)

    # Hide ik fk joints
    fk_joints[0].visibility.set(0)
    ik_joints[0].visibility.set(0)

    # Move ik control grp under root_ctrl
    root_ctrl = pm.PyNode('Root_ctrl')
    pm.parent(ik_ctrls_grp, root_ctrl)

    switch_ctrl_grp = switch_ctrl.getParent(1)
    pm.parent(switch_ctrl_grp, root_ctrl)

    # Parent fk ctrls under the right stuff
    if method == 'arm':
        # Parent fk_ctrl_grp to clavicle
        pm.parent(fk_ctrls[0])

class Module():
    def __init__(self, skin_jnts, type):
        self.type = type
        if type == 'arm' or type == 'leg':
            self.skin_jnts = skin_jnts
            self.fk_jnts = create_fk_joints(skin_jnts)
            self.fk_ctrls = fk_controllers(self.fk_jnts)
            self.ik_jnts, self.ik_ctrls_grp = create_ik(skin_jnts)
            self.ikfkSwitch = ikfk_switch(self.ik_ctrls_grp, self.fk_ctrls, self.ikfk_constraints, endJnt)


def attach_limbs(method):
    if method == 'arm':
    # Parent fk_ctrl_grp to clavicle
        pm.setAttr()
    elif method == 'leg':
        # Parent fk_ctrl_grp to hip
        pm.pare


def make_ctrl_bigger(selection):
    for sl in selection:
        if sl.getShape().type() == 'nurbsCurve':
            cvs = sl.getCVs()
            cvs = [cv * 1.25 for cv in cvs]
            sl.setCVs(cvs)
            sl.updateCurve()


def create_offset_grp(ctrls):
    colors = [0, 255, 0]

    offset_grps = []
    for ctl in ctrls:
        print(ctl)
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

    return offset_grps


def curl_switch(ikfkSwitch, offset_grps):
    match = re.search('([a-zA-Z]_([a-zA-Z]+))\d*_', offset_grps[0].name())
    base_name = match.group(1)
    finger_name = match.group(2)
    # Create multDoubleLinear
    mult = pm.createNode('multDoubleLinear', name=base_name + '_multDoubleLinear')
    pm.setAttr(mult + '.input2', -1)

    # Connect attrs based on finger name
    attr = f'{finger_name}Curl'
    if ikfkSwitch.hasAttr(attr):
        pm.connectAttr(ikfkSwitch + '.' + attr, mult + '.input1')

    for grp in offset_grps[1:]:
        pm.connectAttr(mult + '.output', grp + '.rotateZ')


def spread_switch(ikfkSwitch, offset_grps):
    values = {
        'thumb': 21,
        'index': 17,
        'middle': 0,
        'ring': -15,
        'pinky': -30
    }

    rotation = '.rotateX'
    # values = [(0, 0), (10, 25)]

    baseJnt = offset_grps[0]
    match = re.search('([a-zA-Z]_([a-zA-Z]+))\d*_', baseJnt.name())
    base_name = match.group(2)

    # Set 0 driver key
    pm.setDrivenKeyframe(baseJnt + rotation, currentDriver=ikfkSwitch + '.spread',
                         driverValue=0, value=0)

    # Set driver value bassed on value dict
    pm.setDrivenKeyframe(baseJnt + rotation, currentDriver=ikfkSwitch + '.spread',
                         driverValue=10, value=values[base_name])


def connect_hand(handJnt, arm_end_jnt, arm_ik_ctrl, arm_fk_ctrl, ikfkController):
    match = re.search('([a-zA-Z]_([a-zA-Z]+))\d*_', handJnt.name())
    base_name = match.group(1)

    # Create controller and controller group, parenting the two of them
    grp = pm.createNode('transform', name=base_name + ctrl_sff + grp_sff)
    hand_ctrl = pm.circle(nr=(0, 1, 0), c=(0, 0, 0), radius=CTRL_SCALE, name=base_name + ctrl_sff, constructionHistory=False)
    pm.parent(hand_ctrl, grp)

    # Match transforms and parent constrain controller to joint
    pm.matchTransform(grp, handJnt)
    pm.parentConstraint(hand_ctrl, handJnt, maintainOffset=True)

    # Point constraint
    pm.pointConstraint(arm_end_jnt, hand_ctrl)

    # Create locators
    # IK locator
    ik_loc = pm.spaceLocator(name=base_name+'_ik_space_loc')
    ik_loc_grp = pm.createNode('transform', name = base_name+'_ik_loc_grp')
    pm.parent(ik_loc, ik_loc_grp)
    pm.matchTransform(ik_loc_grp, handJnt)
    pm.parent(ik_loc_grp, arm_ik_ctrl)

    # FK locator
    fk_loc = pm.spaceLocator(name=base_name+'_fk_space_loc')
    fk_loc_grp = pm.createNode('transform', name=base_name + '_ik_loc_grp')
    pm.parent(fk_loc, fk_loc_grp)
    pm.matchTransform(fk_loc_grp, handJnt)
    pm.parent(fk_loc_grp, arm_fk_ctrl)

    constraint = pm.orientConstraint(ik_loc, fk_loc, hand_ctrl)
    weights = constraint.getWeightAliasList()
    print(weights)

    for weight in weights:
        ikfkSwitch = pm.Attribute(ikfkController + '.IkFkSwitch')
        # Get reverse node and switch
        reverseNode = pm.listConnections(ikfkSwitch, destination=True, type='reverse')[0]


        # Connect Weights accordingly
        if fk_sff in weight.name():
            ikfkSwitch.connect(weight)
        elif ik_sff in weight.name():
            reverseNode.outputX.connect(weight)

def create_clavicle(joints):
    match = re.search('([a-zA-Z]_([a-zA-Z]+))\d*_', joints[0].name())
    base_name = match.group(1)

    axis = get_joint_orientation(joints[0], joints[1])


    grp = pm.createNode('transform', name=base_name + ctrl_sff + grp_sff)
    ctrl = pm.circle(c=(0,0,0), nr=axis, sw=180, r=1, d=3, ut=0, tol=0.01, s=8, ch=0, name=base_name + ctrl_sff) # Create arc
    pm.parent(ctrl, grp)

    # Match transforms and parent constrain controller to joint
    jnt = joints[0]
    pm.matchTransform(grp, jnt)
    pm.parentConstraint(ctrl, jnt, maintainOffset=True)


selection = pm.selected()


def ikfk_selectedChain():
    for sl in selection:
        joints = pm.listRelatives(sl, ad=True)
        joints.append(sl)
        joints.reverse()

        print(f'Creating ikfk for {joints}')
        # fk_joints = create_fk_joints(joints)
        # fk_controllers(fk_joints)
        create_fkik(joints)

    '''
    # Create ctrls
    ctrls = fk_controllers(joints)
    # Create offset grps
    offset_grps = create_offset_grp(ctrls)
    ikfkSwitch = pm.PyNode('R_arm_ikfkSwitch_ctrl')

    # Curl switch
    curl_switch(ikfkSwitch, offset_grps)
    spread_switch(ikfkSwitch, offset_grps)
    '''


'''
if(len(selection)==1):
    cmds.error("oly one joint selected")
else:
    ctrls = fk_controllers(selection)
    print(ctrls)
    create_offset_grp(ctrls)
'''
# create_fkik(selection)

ikfk_selectedChain()
#create_clavicle(selection)
#####################
# ________UI__________
#####################
