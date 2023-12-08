import pymel.core as pm
import pymel.core.datatypes as dt
import re

grp_sff = '_grp'
ctrl_sff = '_ctrl'
jnt_sff = '_jnt'
end_sff = '_end'
skin_sff = '_skin'
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

    "arrow": [1, [(0.0, 0.0, 0.0), (-1.0, 0.0, -0.33), (-1.0, 0.0, 0.33), (0.0, 0.0, 0.0), (-1.0, 0.33, 0.0), (-1.0, 0.0, 0.0), (-1.0, -0.33, 0.0), (0.0, 0.0, 0.0)]]
}

CTRL_SCALE = 10


class CtrlGrp():
    def __init__(self, name, shape, scale=CTRL_SCALE, axis=(0, 1, 0)):
        # Create empty grp
        self.grp = pm.createNode('transform', name=name + ctrl_sff + grp_sff)

        if shape == 'circle':
            self.ctrl = pm.circle(nr=axis, c=(0, 0, 0), radius=scale, name=name + ctrl_sff,
                                  constructionHistory=False)
        elif shape == 'arc':
            self.ctrl = pm.circle(nr=axis, c=(0, 0, 0), radius=scale, sw=180, d=3, ut=0, tol=0.01, s=8, ch=0,
                                  name=name + ctrl_sff)
        else:
            points = [(x * scale, y * scale, z * scale) for x, y, z in CTRL_SHAPES[shape][1]]
            self.ctrl = pm.curve(degree=CTRL_SHAPES[shape][0],
                                 point=points,
                                 name=name + ctrl_sff)
        # Parent ctrl and grp
        pm.parent(self.ctrl, self.grp)


def create_fk_jnts(joints):
    # Duplicates input joints
    fk_joints = pm.duplicate(joints, renameChildren=True)

    for jnt in fk_joints:
        name = jnt.name()
        # Names joints by removing the skin suffix and the jnt suffix
        if skin_sff in name:
            base_name = name[:-1].replace(skin_sff + jnt_sff, '')
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

    if axis:
        print(f'Joint orientation between {firstJnt} and {secondJnt} is {axis}')
        if axis == 'y':
            return (0, 1, 0)
        elif axis == 'z':
            return (0, 0, 1)
        else:
            return (1, 0, 0)
    else:
        pm.warning(f'{firstJnt} is not oriented properly to {secondJnt}, assuming Y axis')
        return (0, 1, 0)


def create_fk_ctrls(joints, scale=CTRL_SCALE):
    # Get joint orientation and create circle controller accordingly
    # Ex. if orientation = X, circle is pointing in X
    axis = get_joint_orientation(joints[0], joints[1])

    # Initialize ctrl list
    fk_ctrls = []
    ctrl_previous = None

    # Skips end joints
    for jnt in joints[:-1]:
        # Creates base name by removing the joint suffix and also skin sff if present
        base_name = jnt.replace(jnt_sff, '')
        if skin_sff in base_name:
            base_name = base_name.replace(skin_sff, '')
        # Create controller and controller group, parenting the two of them
        fk = CtrlGrp(base_name, 'circle', scale=scale, axis=axis)

        # Match transforms and parent constrain controller to joint
        pm.matchTransform(fk.grp, jnt)
        pm.parentConstraint(fk.ctrl, jnt, maintainOffset=True)

        # Parent previous group to the current controller
        if ctrl_previous is not None:
            pm.parent(fk.grp, ctrl_previous)
        ctrl_previous = fk.ctrl

        # Add ctrl
        fk_ctrls.append(fk.ctrl[0])

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
        if skin_sff in name:
            base_name = name[:-1].replace(skin_sff + jnt_sff, '')
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

    # Create group and controller for ikHandle
    ik = CtrlGrp(base_name + ik_sff, 'cube')

    # TODO: orient grp the right way
    pm.matchTransform(ik.grp, ik_joints[-1])
    pm.parentConstraint(ik.ctrl, ikHandle[0], maintainOffset=True)

    # Pole Vector
    pole_name = base_name + pole_sff

    # Create controller and group
    pole = CtrlGrp(pole_name, 'joint_curve')

    # Place it into position
    pole_vector = create_pole_vector(joints)
    pm.move(pole_vector.x, pole_vector.y, pole_vector.z, pole.grp, worldSpace=True)
    pm.poleVectorConstraint(pole.ctrl, ikHandle[0])

    # Clean-Up
    ik_ctrl_grp = pm.group(ik.grp, pole.grp, name=base_name + ik_sff + '_Control_Grp')

    ikHandle_grp = pm.PyNode('ikHandle_Grp')
    pm.parent(ikHandle[0], ikHandle_grp)

    return ik_joints, ik_ctrl_grp


def constraint_ikfk(joints, ik_joints, fk_joints):
    fkik_constraints = []
    if not (len(joints) == len(fk_joints) == len(ik_joints) == 3):
        pm.error("Ik FK Joints not matching")

    for i in range(len(joints)):
        constraint = pm.parentConstraint(ik_joints[i], fk_joints[i], joints[i])
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

    name = base_name + '_ikfkSwitch'

    # Create switch controller and grp
    switch = CtrlGrp(name, 'arrow')

    pm.matchTransform(switch.grp, endJnt)
    pm.parentConstraint(endJnt, switch.grp, maintainOffset=True)

    # Add ikfk switch attribute
    pm.addAttr(switch.ctrl, longName=ikfkSwitch_name, attributeType='float', min=0, max=1, defaultValue=1, keyable=True)

    # Reverse node
    reverse_sw = pm.createNode('reverse', name=base_name + '_Ik_Fk_reverse')
    pm.connectAttr(switch.ctrl + f'.{ikfkSwitch_name}', reverse_sw + '.inputX')

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
                pm.connectAttr(switch.ctrl + '.IkFkSwitch', weight)

    # Hide ik or fk ctrls based on switch
    pm.connectAttr(reverse_sw + '.outputX', ik_ctrls_grp + '.visibility')
    fk_ctrls_grp = fk_ctrls[0].getParent()
    pm.connectAttr(switch.ctrl + f'.{ikfkSwitch_name}', fk_ctrls_grp + '.visibility')

    return switch.ctrl


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

    return offset_grps


class Limb:
    def __init__(self, joints):
        self.joints = joints
        self.skin_jnts = joints[:-1]
        # IK
        self.ik_jnts, self.ik_ctrls_grp = create_ik(joints)
        # FK
        self.fk_jnts = create_fk_jnts(joints)
        self.fk_ctrls = create_fk_ctrls(self.fk_jnts)

        self.ikfk_constraints = constraint_ikfk(joints, self.ik_jnts, self.fk_jnts)
        self.switch = ikfk_switch(self.ik_ctrls_grp, self.fk_ctrls, self.ikfk_constraints, joints[-1])

        self.clean_up()

    def clean_up(self):
        # Get Base Name L_arm01_skin_jnt -> L_arm
        match = re.search('([a-zA-Z]_[a-zA-Z]+)\d*_', self.joints[0].name())
        base_name = match.group(1)

        # Group joints only if group isn't already there
        joint_grp_name = base_name + '_Joint_Grp'
        skin_jnt_parent = self.joints[0].getParent(1)
        if skin_jnt_parent.name() != joint_grp_name:
            pm.group(self.fk_jnts[0], self.ik_jnts[0], self.joints[0], name=joint_grp_name)

        # Hide ik fk joints
        self.fk_jnts[0].visibility.set(0)
        self.ik_jnts[0].visibility.set(0)

        # Move ik control grp under root_ctrl
        root_ctrl = pm.PyNode('Root_ctrl')
        pm.parent(self.ik_ctrls_grp, root_ctrl)

        switch_ctrl_grp = self.switch.getParent(1)
        pm.parent(switch_ctrl_grp, root_ctrl)


# class Hand():
#     def __int__(self, joints):


class Torso:
    def __init__(self, joints):
        # Skin joints are all the joint chain but without the last one (end_jnt)
        # TODO: check if the suffix of each jnt is in fact skin_jnt
        self.skin_jnts = joints[:-1]
        self.fk_ctrls = create_fk_ctrls(joints)


class Clavicle:
    def __init__(self, joints):
        if len(joints) != 2:
            pm.error('Can only create clavicle with 2 joints')

        self.joints = joints
        self.skin_jnts = joints

        match = re.search('([a-zA-Z]_([a-zA-Z]+))\d*_', joints[0].name())
        base_name = match.group(1)

        axis = get_joint_orientation(joints[0], joints[1])
        clav = CtrlGrp(base_name, 'arc', axis=axis)

        # Match ctrl to first joint
        jnt = joints[0]
        pm.matchTransform(clav.grp, jnt)
        pm.parentConstraint(clav.ctrl, jnt, maintainOffset=True)

        self.ctrl = clav.ctrl


class Hand:
    def __init__(self, hand_jnts, finger_jnts, curl=True, spread=True):
        '''
        hand_jnts = 2 joints for the hand
        finger_jnts = nested list with all the fingers eg. [[index01, index02, index03],[middle01, middle02]...]
        '''

        # Get base name and create hand ctrl and grp
        match = re.search('([a-zA-Z]_([a-zA-Z]+))\d*_', hand_jnts[0].name())
        base_name = match.group(1)
        self.hand = CtrlGrp(base_name, shape='circle')

        self.handJnt = hand_jnts[0]
        # Match transforms and parent constrain controller to joint
        pm.matchTransform(self.hand.grp, self.handJnt)
        pm.parentConstraint(self.hand.ctrl, self.handJnt, maintainOffset=True)

        # Go through each finger
        all_offset_grps = []
        for finger in finger_jnts:
            finger_ctrls = create_fk_ctrls(finger, scale=1)
            finger_grp = finger_ctrls[0].getParent(1)

            offset_grps = create_offset_grp(finger_ctrls)
            all_offset_grps.append(offset_grps)
            # Connect finger to hand_ctrl
            pm.parent(finger_grp, self.hand.ctrl)

            # Do curl, spread, etc. switches
            if curl:
                self.curl_switch(self.hand.ctrl[0], offset_grps)

            if spread:
                self.spread_switch(self.hand.ctrl[0], offset_grps)

    def curl_switch(self, hand_ctrl, offset_grps):
        match = re.search('([a-zA-Z]_([a-zA-Z]+))\d*_', offset_grps[0].name())
        base_name = match.group(1)
        finger_name = match.group(2)

        # Create Curl attribute if nonexistent
        attr = f'{finger_name}Curl'
        if not hand_ctrl.hasAttr(attr):
            pm.addAttr(hand_ctrl, ln=attr, type='double', keyable=True)

        # Create multDoubleLinear to inverse attribute
        mult = pm.createNode('multDoubleLinear', name=base_name + '_multDoubleLinear')
        pm.setAttr(mult + '.input2', -1)

        # Connect curl attribute to multDouble linear node
        pm.connectAttr(hand_ctrl + '.' + attr, mult + '.input1')

        for grp in offset_grps[1:]:
            pm.connectAttr(mult + '.output', grp + '.rotateZ')

    def spread_switch(self, hand_ctrl, offset_grps):
        values = {
            'thumb': 21,
            'index': 17,
            'middle': 0,
            'ring': -15,
            'pinky': -30
        }
        max_spread = 10

        rotation = '.rotateX'
        # values = [(0, 0), (10, 25)]

        offset = offset_grps[0]
        match = re.search('([a-zA-Z]_([a-zA-Z]+))\d*_', offset.name())
        base_name = match.group(2)

        attr = 'spread'
        if not hand_ctrl.hasAttr(attr):
            pm.addAttr(hand_ctrl, ln=attr, min=0, max=max_spread, type='double', keyable=True)

        # Set 0 driver key
        pm.setDrivenKeyframe(offset + rotation, currentDriver=hand_ctrl + f'.{attr}',
                             driverValue=0, value=0)

        # Set driver value based on value dict
        pm.setDrivenKeyframe(offset + rotation, currentDriver=hand_ctrl + f'.{attr}',
                             driverValue=max_spread, value=values[base_name])


class Foot:
    def __init__(self, joints):
        self.skin_jnts = joints[:-1]
        self.fk_ctrls = create_fk_ctrls(joints)

    def connectAttributes(self, locators, leg):
        ik_ctrl = leg.ik_ctrls_grp.getChildren()[0].getChildren()[0]

        attrs = ['outerBank', 'innerBank', 'heelLift', 'heelSwivel', 'toeLift', 'toeSwivel', 'ballRoll']

        dict = {
            'outerBank':    ['rotationX', [(-10, 30), (10, -90)]],
            'innerBank':    ['rotationX', [(-10, 30), (10, -30)]],
            'heelLift':     ['rotationX', [(-10, -15), (10, 30)]],
            'heelSwivel':   ['rotationX', [(-10, -30), (10, 30)]],
            'toeLift':      ['rotationX', [(-10, -30), (10, 50)]],
            'toeSwivel':    ['rotationX', [(-10, -20), (10, 21)]],
            'ballRoll':     ['rotationX', [(-10, 20), (10, -30)]],
        }

        for attr in dict:
            pm.addAttr(ik_ctrl, attr, min=-10, max=10, keyable=True)



################################
#### CONNECT METHODS ###########
################################

def connect_arm(arm, clavicle):
    arm_grp = arm.fk_ctrls[0].getParent(1)
    pm.parent(arm_grp, clavicle.ctrl)

    pm.parentConstraint(clavicle.joints[-1], arm.ik_jnts[0])


def connect_hand(hand, arm):
    match = re.search('([a-zA-Z]_([a-zA-Z]+))\d*_', hand.handJnt.name())
    base_name = match.group(1)

    # Point constraint
    pm.pointConstraint(arm.joints[-1], hand.hand.ctrl)

    # Create locators
    # IK locator
    ik_loc = pm.spaceLocator(name=base_name + '_ik_space_loc')
    ik_loc_grp = pm.createNode('transform', name=base_name + '_ik_loc_grp')
    pm.parent(ik_loc, ik_loc_grp)
    pm.matchTransform(ik_loc_grp, hand.handJnt)

    # Get ik ctrl and parent locator to it
    # TODO: make it so i don't have so many get children
    ik_ctrl = arm.ik_ctrls_grp.getChildren()[0].getChildren()[0]
    pm.parent(ik_loc_grp, ik_ctrl)

    # FK locator
    fk_loc = pm.spaceLocator(name=base_name + '_fk_space_loc')
    fk_loc_grp = pm.createNode('transform', name=base_name + '_ik_loc_grp')
    pm.parent(fk_loc, fk_loc_grp)
    pm.matchTransform(fk_loc_grp, handJnt)
    print(arm.fk_ctrls[-1])
    pm.parent(fk_loc_grp, arm.fk_ctrls[-1])

    # Create orient constraint and get weight list
    constraint = pm.orientConstraint(ik_loc, fk_loc, hand.hand.ctrl)
    weights = constraint.getWeightAliasList()

    for weight in weights:
        ikfkSwitch = pm.Attribute(arm.switch + '.IkFkSwitch')
        # Get reverse node and switch
        reverseNode = pm.listConnections(arm.switch, destination=True, type='reverse')[0]

        # Connect Weights accordingly
        if fk_sff in weight.name():
            ikfkSwitch.connect(weight)
        elif ik_sff in weight.name():
            reverseNode.outputX.connect(weight)




sel = pm.selected()




def getHierachy(joint):
    jnts = pm.listRelatives(joint, ad=True)
    jnts.append(joint)
    jnts.reverse()
    return jnts

joints = [pm.PyNode('L_arm01_skin_jnt'), pm.PyNode('L_clavicle01_skin_jnt')]
l_arm = Limb(getHierachy(joints[0]))
l_clavicle = Clavicle(getHierachy(joints[1]))
# connect_arm(l_arm, l_clavicle)

handJnt = pm.PyNode('L_hand_skin_jnt')
handJnts = getHierachy(handJnt)
fingerJnts = [pm.PyNode('L_thumb01_skin_jnt'), pm.PyNode('L_index01_skin_jnt'), pm.PyNode('L_middle01_skin_jnt'),
              pm.PyNode('L_ring01_skin_jnt'), pm.PyNode('L_pinky01_skin_jnt')]

fingers = []
for finger in fingerJnts:
    fingers.append(getHierachy(finger))
print(fingers)

hand = Hand(handJnts, fingers)
connect_hand(hand, l_arm)

legJnt = pm.PyNode('L_leg01_skin_jnt')
legJnts = getHierachy(legJnt)
l_leg = Limb(legJnts)

#ctrl = CtrlGrp('test','arrow', scale=1)