import pymel.core as pm
import pymel.core.datatypes as dt
import re

from mf_autoRig.lib.defaults import *
import importlib

import mf_autoRig.lib.useful_functions
importlib.reload(mf_autoRig.lib.useful_functions)
from mf_autoRig.lib.useful_functions import *

# Import Modules
importlib.reload(mf_autoRig.modules.Hand)
from mf_autoRig.modules.Hand import Hand
from mf_autoRig.modules.Limb import Limb
from mf_autoRig.modules.Torso import Spine, Clavicle



class Body:
    def __init__(self):
        self.arms = [Limb('L_arm'), Limb('R_arm')]
        self.hands = [Hand('L_hand'), Hand('R_hand')]
        self.legs = [Limb('L_leg'), Limb('R_leg')]
        self.clavicles = [Clavicle('L_clavicle'), Clavicle('R_Clavicle')]
        self.torso = Spine('M_spine', num = 3)

    def create_guides(self, positions):
        mirror_pos = mirror_default_pos(positions)
        # Arms
        self.arms[0].create_guides(positions['arm'])
        self.arms[1].create_guides(mirror_pos['arm'])
        # Hands
        self.hands[0].create_guides(positions['hand_start'])
        print(mirror_pos['hand_start'])
        self.hands[1].create_guides(mirror_pos['hand_start'])

        # Legs
        self.legs[0].create_guides(positions['leg'])
        self.legs[1].create_guides(mirror_pos['leg'])
        # Clavicles
        self.clavicles[0].create_guides(positions['clavicle'])
        self.clavicles[1].create_guides(mirror_pos['clavicle'])

        self.torso.create_guides(positions['torso'])


    def create_joints(self):

        # Create joints
        for arm, hand, leg, clavicle in zip(self.arms, self.hands, self.legs, self.clavicles):
            arm.create_joints()
            # Hands
            hand.create_joints()
            hand.create_hand(arm.joints[-1])
            hand.create_ctrls()

            leg.create_joints()
            clavicle.create_joints(arm.joints[0])

        self.torso.create_joints()

        # Connect modules
        for arm, hand, leg, clavicle in zip(self.arms, self.hands, self.legs, self.clavicles):
            arm.connect(clavicle, method='arm')
            hand.connect(arm)
            leg.connect(self.torso, method='leg')
            clavicle.connect(self.torso)

################################
#### CONNECT METHODS ###########
################################





# loc = ['L_outerbank_loc', 'L_innerrbank_loc', 'L_heel_loc', 'L_toe_tip_loc', 'L_ball_loc']
# l_locators = []
#
# for locator in loc:
#     l_locators.append(pm.PyNode(locator))
#
# loc = ['R_outerbank_loc', 'R_innerrbank_loc', 'R_heel_loc', 'R_toe_tip_loc', 'R_ball_loc']
# r_locators = []
#
# for locator in loc:
#     r_locators.append(pm.PyNode(locator))
#
# locators = []
# locators.append(l_locators)
# locators.append(r_locators)


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


def create_rig_jnts():
    print('a')

def create_joints(tmp_joints, name):
    joints = []
    for i, tmp in enumerate(tmp_joints):
        trs = pm.xform(tmp, q=True, t=True, ws=True)
        jnt = pm.joint(name=f'L_{name}{i+1}_skin_jnt', position=trs)

        joints.append(jnt)

    # Orient joints
    pm.joint(joints[0], edit=True, orientJoint='yzx', secondaryAxisOrient='zup', children=True)
    pm.joint(joints[-1], edit=True, orientJoint='none')

    return joints

