import re

from mf_autoRig.lib.defaults import *
import importlib

import mf_autoRig.lib.useful_functions
importlib.reload(mf_autoRig.lib.useful_functions)
from mf_autoRig.lib.useful_functions import *


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


