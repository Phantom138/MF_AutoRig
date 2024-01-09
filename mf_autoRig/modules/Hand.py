import re

from mf_autoRig.lib.defaults import *
import importlib

import mf_autoRig.lib.useful_functions
importlib.reload(mf_autoRig.lib.useful_functions)
from mf_autoRig.lib.useful_functions import *


class Hand:
    def __init__(self, name):
        self.name = name
        self.guides = None
        self.finger_jnts = None
        self.hand_jnts = None

    def create_guides(self, start_pos):
        finger_grps = []
        fingers_jnts = []

        # initialize constants
        side = self.name.split('_')[0]
        fingers = ['thumb', 'index', 'middle', 'ring', 'pinky']
        zPos = start_pos[2]
        spacing = 1.5

        for index, name in enumerate(fingers):
            jnt_num = 5
            if index == 0:
                # Thumb has less joints
                jnt_num = 4
            else:
                # Offset fingers
                zPos -= spacing

            # Do fingers
            fingerPos = start_pos[0], start_pos[1], zPos
            yPos = fingerPos[1]

            print(fingerPos)
            offset = 4
            finger = []
            for i in range(jnt_num):
                jnt = pm.createNode('joint', name=f'{side}_{name}_{i}{df.jnt_sff}')
                finger.append(jnt)

                # Create more space for the knuckles
                if i == 1:
                    yPos -= offset

                # Set jnt position
                pos = fingerPos[0], yPos, fingerPos[2]
                jnt.translate.set(pos)

                yPos -= offset
            fingers_jnts.append(finger)

            # Group fingers
            finger_grp = pm.createNode('transform', name=f'{side}_{name}_grp')
            finger_grps.append(finger_grp)

            pm.matchTransform(finger_grp, finger[0])
            pm.parent(finger, finger_grp)

            # Rotate Thumb
            if index == 0:
                pm.rotate(finger_grp, (-25, -30, 0))

        # Group clean-up
        hand_grp = pm.createNode('transform', name=f'{self.name}_grp')
        pm.matchTransform(hand_grp, finger_grps[int(len(fingers) / 2)])
        pm.parent(finger_grps, hand_grp)
        pm.parent(hand_grp, get_group('rig_guides_grp'))

        self.guides = fingers_jnts
        print(fingers_jnts)

    def create_joints(self):
        print(f"Creating {self.name} joints")
        self.joint_grp = pm.createNode('transform', name=f'{self.name}_{df.joints_grp}')
        pm.parent(self.joint_grp, get_group('Joints_Grp'))

        # Create finger joints
        self.finger_jnts = []
        for finger in self.guides:
            # Get finger name
            match = re.search('([a-zA-Z]_([a-zA-Z]+))\d*_', finger[0].name())
            base_name = match.group(1)

            jnts = create_joints_from_guides(base_name, finger)
            pm.parent(jnts[0], self.joint_grp)
            self.finger_jnts.append(jnts)



    def create_hand(self, wrist):
        self.hand_jnts = []
        # Create start jnt where the wrist is
        pos = pm.xform(wrist, q=True, t=True, ws=True)
        hand_start = pm.joint(name=f'{self.name}{df.skin_sff}{df.jnt_sff}', position=pos)
        self.hand_jnts.append(hand_start)

        # Create end jnt by averaging the knuckles position
        sums = [0,0,0]
        cnt = 0
        for finger in self.finger_jnts[1:]:
            pos = pm.xform(finger[1], q=True, t=True, ws=True)
            sums[0] += pos[0]
            sums[1] += pos[1]
            sums[2] += pos[2]
            cnt += 1

        average = [sums[0]/cnt, sums[1]/cnt, sums[2]/cnt]
        hand_end = pm.joint(name = f'{self.name}{df.end_sff}{df.jnt_sff}', position=average)
        self.hand_jnts.append(hand_end)

        # Parent to joint grp
        pm.parent(self.hand_jnts[0], self.joint_grp)
        print(average)

    def create_ctrls(self, curl=True, spread=True):
        # Create hand ctrl
        self.hand = CtrlGrp(self.name, shape='circle')
        self.handJnt = self.hand_jnts[0]
        # Match transforms and parent constrain controller to joint
        pm.matchTransform(self.hand.grp, self.handJnt)
        pm.parentConstraint(self.hand.ctrl, self.handJnt, maintainOffset=True)


        # Go through each finger
        all_offset_grps = []
        for finger in self.finger_jnts:
            finger_ctrls = create_fk_ctrls(finger, scale=1)
            finger_grp = finger_ctrls[0].getParent(1)

            # Create offset groups
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