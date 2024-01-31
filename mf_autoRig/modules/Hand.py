import re
import importlib
from itertools import chain

import mf_autoRig.lib.defaults as df
from mf_autoRig.lib.useful_functions import *
from mf_autoRig.lib.tools import set_color, auto_color
import mf_autoRig.modules.meta as mdata
from mf_autoRig.modules.Module import Module



class Hand(Module):
    meta_args = {
        'hand_ctrl': {'attributeType': 'message'},
        'hand_jnts': {'attributeType': 'message', 'm': True},
        'finger_jnts': {'attributeType': 'message', 'm': True},
        'all_ctrls': {'attributeType': 'message', 'm': True}
    }

    def __init__(self, name, meta=True):
        super().__init__(name, self.meta_args, meta)

        self.guides = None
        self.wrist = None
        self.finger_jnts = None
        self.hand_jnts = None
        self.all_ctrls = []

    @classmethod
    def create_from_meta(cls, metaNode):
        hand = super().create_from_meta(metaNode)

        return hand

    def create_guides(self, start_pos=None):
        finger_grps = []
        fingers_jnts = []

        if start_pos is None:
            start_pos = [0,0,0]

        # initialize constants
        side = self.name.split('_')[0]
        fingers = ['thumb', 'index', 'middle', 'ring', 'pinky']
        zPos = start_pos[2]
        spacing = 1.5

        # Create finger guides
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

            offset = 4
            finger = []
            for i in range(jnt_num):
                jnt = pm.createNode('joint', name=f'{self.name}_{name}_{i}{df.jnt_sff}')
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

        self.guides = fingers_jnts

        # Group clean-up
        hand_grp = pm.createNode('transform', name=f'{self.name}_grp')
        pm.matchTransform(hand_grp, finger_grps[int(len(fingers) / 2)])
        pm.parent(finger_grps, hand_grp)
        pm.parent(hand_grp, get_group('rig_guides_grp'))

        # Create Wrist
        if start_pos == [0,0,0]:
            self.wrist = pm.createNode('joint', name=f'{self.name}_wrist_{df.jnt_sff}')
            pm.xform(self.wrist, t=[0,5,0], ws=True)
            pm.parent(self.wrist, hand_grp)


        # Clear selection
        pm.select(clear=True)




    def create_joints(self, matrices = None):
        """
        matrices - None if using joints
                 - nested list with info for fingers, starting with the thumb
        """
        print(f"Creating {self.name} joints")

        # List of fingers
        finger_names = ['thumb', 'index', 'middle', 'ring', 'pinky']

        # Create hand grp
        self.joint_grp = pm.createNode('transform', name=f'{self.name}_{df.joints_grp}')
        pm.parent(self.joint_grp, get_group('Joints_Grp'))

        if matrices is None:
            # Create finger joints based on guides
            self.finger_jnts = []
            for finger in self.guides:
                # Get finger name
                match = re.search(f'({self.name}_([a-zA-Z]+))\d*_', finger[0].name())
                base_name = match.group(1)
                print(f'finger base name is {base_name}')
                jnts = create_joints_from_guides(base_name, finger)
                pm.parent(jnts[0], self.joint_grp)
                self.finger_jnts.append(jnts)
        else:
            # Create based on matrices
            self.finger_jnts = []

            for i, finger_matrices in enumerate(matrices):
                finger = []
                for j, mtx in enumerate(finger_matrices):
                    sff = df.skin_sff
                    # Last joint has end suffix
                    if j == len(matrices) - 1:
                        sff = df.end_sff

                    side = self.name[0]
                    # Create joint
                    jnt = pm.joint(name=f'{self.name}_{finger_names[i]}{j + 1:02}{sff}{df.jnt_sff}')
                    finger.append(jnt)

                    # Set position based on matrix
                    pm.xform(jnt, ws=True, m=mtx)

                pm.parent(finger[0], self.joint_grp)
                self.finger_jnts.append(finger)
                # Clear selection
                pm.select(clear=True)

        if self.meta:
            nodes = list(chain(*self.finger_jnts))  # unnest list
            mdata.add(nodes, self.metaNode.finger_jnts)


    def create_hand(self, wrist=None):
        if wrist is None:
            wrist = self.wrist

        self.hand_jnts = []

        # Create start jnt where the wrist is
        mtx = pm.xform(wrist, q=True, ws=True, t=True)
        hand_start = pm.joint(name=f'{self.name}{df.skin_sff}{df.jnt_sff}', p=mtx)

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

        # Orient Joints
        pm.joint(self.hand_jnts[0], edit=True, orientJoint='yzx', secondaryAxisOrient='zup', children=True)
        pm.joint(self.hand_jnts[-1], edit=True, orientJoint='none')

        # Parent to joint grp
        pm.parent(self.hand_jnts[0], self.joint_grp)
        print(average)

        # Add to metadata
        if self.meta:
            mdata.add(self.hand_jnts, self.metaNode.hand_jnts)

    def create_hand_with_matrix(self, matrices):
        self.hand_jnts = []

        # Hand start
        hand_start = pm.joint(name=f'{self.name}{df.skin_sff}{df.jnt_sff}')
        pm.xform(hand_start, ws=True, m=matrices[0])
        self.hand_jnts.append(hand_start)

        # Hand end
        hand_end = pm.joint(name=f'{self.name}{df.end_sff}{df.jnt_sff}')
        pm.xform(hand_end, ws=True, m=matrices[1])
        self.hand_jnts.append(hand_end)

        # Clear selection
        pm.select(clear=True)

        # Add to metadata
        if self.meta:
            mdata.add(self.hand_jnts, self.metaNode.hand_jnts)

    def rig(self, curl=True, spread=True):
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


            # Color finger ctrls
            auto_color(finger_ctrls)

            finger_grp = finger_ctrls[0].getParent(1)

            self.all_ctrls.extend(finger_ctrls)
            # Create offset groups
            offset_grps = create_offset_grp(finger_ctrls)
            all_offset_grps.append(offset_grps)
            # Connect finger to hand_ctrl
            pm.parent(finger_grp, self.hand.ctrl)

            # Do curl, spread, etc. switches
            if curl:
                self.__curl_switch(self.hand.ctrl, offset_grps)

            if spread:
                self.__spread_switch(self.hand.ctrl, offset_grps)

        # Add to metadata
        if self.meta:
            mdata.add(self.hand.ctrl, self.metaNode.hand_ctrl)
            mdata.add(self.all_ctrls, self.metaNode.all_ctrls)

        self.all_ctrls.extend(self.hand.ctrl)



    def __curl_switch(self, hand_ctrl, offset_grps):
        match = re.search(f'({self.name}_([a-zA-Z]+))\d*_', offset_grps[0].name())
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


    def __spread_switch(self, hand_ctrl, offset_grps):
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
        match = re.search(f'({self.name}_([a-zA-Z]+))\d*_', offset.name())
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
        self.handJnt = self.hand_jnts[0]
        self.hand_ctrl = self.hand.ctrl

        match = re.search('([a-zA-Z]_([a-zA-Z]+))\d*_', self.handJnt.name())
        base_name = match.group(1)

        # Point constraint
        pm.pointConstraint(arm.joints[-1], self.hand_ctrl)

        # Create locators
        # IK locator
        ik_loc = pm.spaceLocator(name=base_name + '_ik_space_loc')
        ik_loc_grp = pm.createNode('transform', name=base_name + '_ik_loc_grp')
        pm.parent(ik_loc, ik_loc_grp)
        pm.matchTransform(ik_loc_grp, self.handJnt)

        # Get ik ctrl and parent locator to it
        # TODO: make it so i don't have so many get children
        #ik_ctrl = arm.ik_ctrls_grp.getChildren()[0].getChildren()[0]

        pm.parent(ik_loc_grp, arm.ik_ctrls[0])

        # FK locator
        fk_loc = pm.spaceLocator(name=base_name + '_fk_space_loc')
        fk_loc_grp = pm.createNode('transform', name=base_name + '_ik_loc_grp')
        pm.parent(fk_loc, fk_loc_grp)
        pm.matchTransform(fk_loc_grp, self.handJnt)
        print(arm.fk_ctrls[-1])
        pm.parent(fk_loc_grp, arm.fk_ctrls[-1])

        # Create orient constraint and get weight list
        constraint = pm.orientConstraint(ik_loc, fk_loc, self.hand_ctrl)
        weights = constraint.getWeightAliasList()

        for weight in weights:
            ikfkSwitch = pm.Attribute(arm.switch + '.IkFkSwitch')
            # Get reverse node and switch
            reverseNode = pm.listConnections(arm.switch, destination=True, type='reverse')[0]

            # Connect Weights accordingly
            if df.fk_sff in weight.name():
                ikfkSwitch.connect(weight)
            elif df.ik_sff in weight.name():
                reverseNode.outputX.connect(weight)
