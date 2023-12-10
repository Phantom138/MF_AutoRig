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
loc_sff = '_loc'
ikfkSwitch_name = 'IkFkSwitch'

# CTRL Shapes structure: Degree, Points, Knots
CTRL_SHAPES = {
    'cube': [1, [(1, 1, 1), (1, 1, -1), (-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, -1, 1), (1, -1, -1), (1, 1, -1),
                 (-1, 1, -1),
                 (-1, -1, -1), (1, -1, -1),
                 (-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, -1, 1), (1, -1, 1)],[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]],
    'square': [1, [(-1.0, 0.0, -1.0), (1.0, 0.0, -1.0), (1.0, 0.0, 1.0), (-1.0, 0.0, 1.0), (-1.0, 0.0, -1.0)]],
    'joint_curve': [1, [(0, 1, 0), (0, 0.92388000000000003, 0.382683), (0, 0.70710700000000004, 0.70710700000000004),
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
                        (0.382683, 0, -0.92388000000000003), (0, 0, -1)],[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52]],
    'arrow': [1, [(0.0, 0.0, 0.0), (-1.0, 0.0, -0.33), (-1.0, 0.0, 0.33), (0.0, 0.0, 0.0), (-1.0, 0.33, 0.0), (-1.0, 0.0, 0.0), (-1.0, -0.33, 0.0), (0.0, 0.0, 0.0)]]
}

CTRL_SCALE = 10


class CtrlGrp():
    def __init__(self, name, shape, scale=CTRL_SCALE, axis=(0, 1, 0)):
        # Create empty grp
        self.grp = pm.createNode('transform', name=name + ctrl_sff + grp_sff)

        if shape == 'circle':
            self.ctrl = pm.circle(nr=axis, c=(0, 0, 0), radius=scale, name=name + ctrl_sff,
                                  constructionHistory=False)[0]
        elif shape == 'arc':
            self.ctrl = pm.circle(nr=axis, c=(0, 0, 0), radius=scale, sw=180, d=3, ut=0, tol=0.01, s=8, ch=0,
                                  name=name + ctrl_sff)[0]
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


def create_fk_ctrls(joints, skipEnd=True, shape='circle', scale=CTRL_SCALE):
    print(f"// Running fk_ctrls for {joints}")
    # Exception case: only one joint
    if type(joints) == pm.nodetypes.Joint:
        jnt = joints
        base_name = jnt.replace(jnt_sff, '')
        if skin_sff in base_name:
            base_name = base_name.replace(skin_sff, '')
        # Create controller and controller group, parenting the two of them
        fk = CtrlGrp(base_name, shape, scale=scale)

        # Match transforms and parent constrain controller to joint
        pm.matchTransform(fk.grp, jnt)
        pm.parentConstraint(fk.ctrl, jnt, maintainOffset=True)

        return fk.ctrl

    # Get joint orientation and create circle controller accordingly
    # Ex. if orientation = X, circle is pointing in X
    axis = get_joint_orientation(joints[0], joints[1])

    # Initialize ctrl list
    fk_ctrls = []
    ctrl_previous = None

    if skipEnd:
        joints = joints[:-1]

    # Skips end joints
    for jnt in joints:
        # Creates base name by removing the joint suffix and also skin sff if present
        base_name = jnt.replace(jnt_sff, '')
        if skin_sff in base_name:
            base_name = base_name.replace(skin_sff, '')
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

    return ik_joints, ik_ctrl_grp, ikHandle[0]


def constraint_ikfk(joints, ik_joints, fk_joints):
    fkik_constraints = []
    if not (len(joints) == len(fk_joints) == len(ik_joints) == 3):
        pm.error("Ik FK Joints not matching")

    for i in range(len(joints)):
        constraint = pm.parentConstraint(ik_joints[i], fk_joints[i], joints[i])
        fkik_constraints.append(constraint)

    return fkik_constraints


def ikfk_switch(ik_ctrls_grp, fk_ctrls, ikfk_constraints, endJnt):
    """
    Method:
    ik Fk Switch = fk weight
    ik Fk Switch * (-1) = ik weight
    """
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
        self.ik_jnts, self.ik_ctrls_grp, self.ikHandle = create_ik(joints)
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
        root_ctrl = pm.PyNode('Root_Ctrl')
        pm.parent(self.ik_ctrls_grp, root_ctrl)

        switch_ctrl_grp = self.switch.getParent(1)
        pm.parent(switch_ctrl_grp, root_ctrl)

    def connect(self, dest, method):
        ctrl_grp = self.fk_ctrls[0].getParent(1)

        if method == 'arm':
            pm.parent(ctrl_grp, dest.ctrl)
            pm.parentConstraint(dest.joints[-1], self.ik_jnts[0])

        elif method == 'leg':
            pm.parent(ctrl_grp, dest.hip_ctrl)
            pm.parentConstraint(dest.hip_ctrl, self.ik_jnts[0], maintainOffset=True)



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

    def connect(self, torso):
        pm.parent(self.ctrl.getParent(1), torso.fk_ctrls[-1])


class Hand:
    def __init__(self, hand_jnts, finger_jnts, curl=True, spread=True):
        '''
        hand_jnts = 2 joints for the hand
        finger_jnts =  list with all the beginning fingers eg. [index01,middle01...]
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
        for finger_jnt in finger_jnts:
            finger = getHierachy(finger_jnt)

            finger_ctrls = create_fk_ctrls(finger, scale=1)
            finger_grp = finger_ctrls[0].getParent(1)

            offset_grps = create_offset_grp(finger_ctrls)
            all_offset_grps.append(offset_grps)
            # Connect finger to hand_ctrl
            pm.parent(finger_grp, self.hand.ctrl)

            # Do curl, spread, etc. switches
            if curl:
                self.curl_switch(self.hand.ctrl, offset_grps)

            if spread:
                self.spread_switch(self.hand.ctrl, offset_grps)

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

    def connect(self, arm):
        match = re.search('([a-zA-Z]_([a-zA-Z]+))\d*_', self.handJnt.name())
        base_name = match.group(1)

        # Point constraint
        pm.pointConstraint(arm.joints[-1], self.hand.ctrl)

        # Create locators
        # IK locator
        ik_loc = pm.spaceLocator(name=base_name + '_ik_space_loc')
        ik_loc_grp = pm.createNode('transform', name=base_name + '_ik_loc_grp')
        pm.parent(ik_loc, ik_loc_grp)
        pm.matchTransform(ik_loc_grp, self.handJnt)

        # Get ik ctrl and parent locator to it
        # TODO: make it so i don't have so many get children
        ik_ctrl = arm.ik_ctrls_grp.getChildren()[0].getChildren()[0]
        pm.parent(ik_loc_grp, ik_ctrl)

        # FK locator
        fk_loc = pm.spaceLocator(name=base_name + '_fk_space_loc')
        fk_loc_grp = pm.createNode('transform', name=base_name + '_ik_loc_grp')
        pm.parent(fk_loc, fk_loc_grp)
        pm.matchTransform(fk_loc_grp, self.handJnt)
        print(arm.fk_ctrls[-1])
        pm.parent(fk_loc_grp, arm.fk_ctrls[-1])

        # Create orient constraint and get weight list
        constraint = pm.orientConstraint(ik_loc, fk_loc, self.hand.ctrl)
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


class Foot:
    def __init__(self, joints):
        self.skin_jnts = joints[:-1]

        self.fk_jnts = create_fk_jnts(joints)
        self.fk_ctrls = create_fk_ctrls(self.fk_jnts)

        # Create ik joints for foot
        self.ik_jnts = pm.duplicate(joints)
        for jnt in self.ik_jnts:
            match = re.search('([a-zA-Z]_[a-zA-Z]+\d*)_', jnt.name())
            name = match.group(1)
            name += ik_sff + jnt_sff

            pm.rename(jnt, name)

        self.ikfk_constraints = constraint_ikfk(joints, self.ik_jnts, self.fk_jnts)
        print(self.ikfk_constraints)
        match = re.match('(^[A-Za-z]_)\w+', joints[0].name())
        side = match.group(1)

        self.ball_ikHandle = \
        pm.ikHandle(name=side + 'ball' + ik_sff + loc_sff, startJoint=self.ik_jnts[0], endEffector=self.ik_jnts[1],
                    solver='ikSCsolver')[0]
        self.toe_ikHandle = \
        pm.ikHandle(name=side + 'toe' + ik_sff + loc_sff, startJoint=self.ik_jnts[1], endEffector=self.ik_jnts[2],
                    solver='ikSCsolver')[0]

        # Hide ik and fk joints
        self.ik_jnts[0].visibility.set(0)
        self.fk_jnts[0].visibility.set(0)

    def connectAttributes(self, locators, leg):
        # Remove leg parent constraint for the ikHandle
        for constraint in pm.listRelatives(leg.ikHandle):
            if isinstance(constraint, pm.nodetypes.ParentConstraint):
                pm.delete(constraint)

        # Connect foot ik fk constraints to leg switch
        reverse_sw = leg.switch.IkFkSwitch.listConnections(type='reverse')[0]

        for constraint in self.ikfk_constraints:
            weights = constraint.getWeightAliasList()

            for weight in weights:
                name = weight.longName(fullPath=False)
                # If ik weight connect to reverse
                if ik_sff in name:
                    reverse_sw.outputX.connect(weight)
                # If fk weight connect to switch
                if fk_sff in name:
                    leg.switch.IkFkSwitch.connect(weight)

        # Parent foot fk ctrls grp under leg fk ctrls grp
        pm.parent(self.fk_ctrls[0].getParent(1), leg.fk_ctrls[-1])

        # Parent ik handles under locators
        # Locators order : outerbank, innerbank, heel, toe_tip, ball !!
        pm.parent(self.ball_ikHandle, locators[3])
        pm.parent(self.toe_ikHandle, locators[2])
        pm.parent(leg.ikHandle, locators[4])

        # Connect to ik_ctrl
        ik_ctrl = leg.ik_ctrls_grp.getChildren()[0].getChildren()[0]

        connections = {
            'outerBank': [locators[0], 'rotateZ', [(-10, 30), (10, -90)]],
            'innerBank': [locators[1], 'rotateZ', [(-10, 30), (10, -30)]],
            'heelLift': [locators[2], 'rotateX', [(-10, -15), (10, 30)]],
            'heelSwivel': [locators[2], 'rotateY', [(-10, -30), (10, 30)]],
            'toeLift': [locators[3], 'rotateX', [(-10, -30), (10, 50)]],
            'toeSwivel': [locators[3], 'rotateY', [(-10, -20), (10, 21)]],
            'ballRoll': [locators[4], 'rotateX', [(-10, -20), (10, 30)]],
        }

        # Create driven keys and attributes
        for attr in connections:
            pm.addAttr(ik_ctrl, longName=attr, min=-10, max=10, keyable=True)

            # Get rotation and values from dictionary
            locator = connections[attr][0]
            rotation = f'.{connections[attr][1]}'
            values = connections[attr][2]

            # Set 0 driven key
            pm.setDrivenKeyframe(locator + rotation, currentDriver=ik_ctrl + f'.{attr}', driverValue=0, value=0)
            # Set the rest
            for value in values:
                pm.setDrivenKeyframe(locator + rotation, currentDriver=ik_ctrl + f'.{attr}', driverValue=value[0],
                                     value=value[1])

        # Constraint leg ik_jnt to foot ik_jnt start
        pm.parentConstraint(leg.ik_jnts[-1], self.ik_jnts[0])

        # Constraint ik_ctrl to locator grp
        locator_grp = locators[0].getParent(1)
        pm.parentConstraint(ik_ctrl, locator_grp, maintainOffset=True)


class Torso:
    def __init__(self, joints, hip):
        self.fk_ctrls = create_fk_ctrls(joints, skipEnd=False, shape='square')
        self.hip_ctrl = create_fk_ctrls(hip, shape='circle')

        # Parent hip ctrl grp under pelvis ctrl
        pm.parent(self.hip_ctrl.getParent(1), self.fk_ctrls[0])


################################
#### CONNECT METHODS ###########
################################


def getHierachy(joint):
    #jnt = pm.PyNode(joint)
    jnts = pm.listRelatives(joint, ad=True)
    jnts.append(joint)
    jnts.reverse()
    return jnts


loc = ['L_outerbank_loc', 'L_innerrbank_loc', 'L_heel_loc', 'L_toe_tip_loc', 'L_ball_loc']
l_locators = []

for locator in loc:
    l_locators.append(pm.PyNode(locator))

loc = ['R_outerbank_loc', 'R_innerrbank_loc', 'R_heel_loc', 'R_toe_tip_loc', 'R_ball_loc']
r_locators = []

for locator in loc:
    r_locators.append(pm.PyNode(locator))

locators = []
locators.append(l_locators)
locators.append(r_locators)


def search_and_create(name, func):
    jnts = pm.ls(regex=f'(L|l|R|r)_{name}(01)*{skin_sff}{jnt_sff}', type='joint')
    objects = []
    for jnt in jnts:
        object = func(getHierachy(jnt))
        objects.append(object)

    if len(objects) == 1:
        return objects[0]

    return objects

def create_rig():
    # IMPORTANT, MIGHT BREAK STUFF:
    # I think ls returns alphabetical order
    arms = search_and_create('arm', Limb)
    legs = search_and_create('leg', Limb)
    clavicles = search_and_create('clavicle', Clavicle)
    feet = search_and_create('foot', Foot)

    # Torso
    torso_jnt = pm.ls(regex=f'(M|m)_pelvis(01)*{skin_sff}{jnt_sff}', type='joint')[0]
    hip_jnt = pm.ls(regex=f'(M|m)_hip(01)*{skin_sff}{jnt_sff}', type='joint')[0]
    torso = Torso(getHierachy(torso_jnt), hip_jnt)

    # Hand
    hand_jnts = pm.ls(regex=f'(R|r|L|l)_hand(01)*{skin_sff}{jnt_sff}', type='joint')
    # Add fingers in a nested list having the left side as the first element and the right side as the second
    fingers = []
    l_fingers = pm.ls(regex=f'(L|l)_(thumb|index|middle|ring|pinky)(01)*{skin_sff}{jnt_sff}', type='joint')
    r_fingers = pm.ls(regex=f'(R|r)_(thumb|index|middle|ring|pinky)(01)*{skin_sff}{jnt_sff}', type='joint')
    fingers.append(l_fingers)
    fingers.append(r_fingers)
    print(fingers)

    hands = []
    for jnts, side in zip(hand_jnts, fingers):
        hand = Hand(getHierachy(jnts), side)
        hands.append(hand)

    print(hands)

    # Connections
    for arm, clavicle, hand in zip(arms, clavicles, hands):
        arm.connect(clavicle, method='arm')
        clavicle.connect(torso)
        hand.connect(arm)

    for leg in legs:
        leg.connect(torso, method='leg')

    for foot, locator, leg in zip(feet, locators, legs):
         foot.connectAttributes(locator, leg)


create_rig()