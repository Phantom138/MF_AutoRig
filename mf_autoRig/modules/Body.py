import pymel.core as pm
import pymel.core.datatypes as dt
import re

from mf_autoRig.lib.defaults import *
import importlib

from mf_autoRig.lib.useful_functions import *

# Import Modules

from mf_autoRig.modules.Hand import Hand
from mf_autoRig.modules.Limb import Arm, Leg
from mf_autoRig.modules.Spine import Spine
from mf_autoRig.modules.Clavicle import Clavicle

from mf_autoRig.lib.mirrorJoint import xformMirror


class Body:
    def __init__(self, meta=True):
        self.arms = [Arm('L_arm', meta), Arm('R_arm', meta)]
        self.hands = [Hand('L_hand', meta), Hand('R_hand', meta)]
        self.legs = [Leg('L_leg', meta), Leg('R_leg', meta)]
        self.clavicles = [Clavicle('L_clavicle', meta), Clavicle('R_Clavicle', meta)]
        self.spine = Spine('M_spine', num = 3, meta=meta)

    def create_guides(self, positions):
        mirror_pos = mirror_default_pos(positions)

        self.arms[0].create_guides(positions['arm'])
        self.legs[0].create_guides(positions['leg'])
        self.hands[0].create_guides(positions['hand_start'])
        self.clavicles[0].create_guides(positions['clavicle'])

        self.spine.create_guides(positions['torso'])


    def create_joints(self):
        # Limbs
        create_pair(self.arms[0], self.arms[1])
        create_pair(self.legs[0], self.legs[1])

        # Hands
        self.hands[0].create_joints()
        self.hands[0].create_hand(self.arms[0].joints[-1])

        fingers_mtx = []
        for finger in self.hands[0].finger_jnts:
            fingers_mtx.append(xformMirror(finger))

        self.hands[1].create_joints(matrices = fingers_mtx)
        self.hands[1].create_hand_with_matrix(xformMirror(self.hands[0].hand_jnts))

        # Clavicles
        self.clavicles[0].create_joints(self.arms[0].joints[0])

        self.clavicles[1].joints = pm.mirrorJoint(self.clavicles[0].joints[0],
                                                  mirrorYZ=True, mirrorBehavior=True, searchReplace=('L_', 'R_'))
        pm.select(clear=True)

        # Torso
        self.spine.create_joints()


    def rig(self):
        self.spine.rig()

        for arm, hand, leg, clavicle in zip(self.arms, self.hands, self.legs, self.clavicles):
            arm.rig()
            hand.rig()
            leg.rig()
            clavicle.rig()

            arm.connect(clavicle)
            hand.connect(arm)
            leg.connect(self.spine)
            clavicle.connect(self.spine)

        self.mirror_ctrls(side='L')

    def mirror_ctrls(self, side: str):
        src = 0
        dst = 1

        if side == 'L':
            src = 0
            dst = 1
        elif side == 'R':
            src = 1
            dst = 0
        else:
            pm.error("Source should be either R or L")

        src_ctrls = self.arms[src].all_ctrls + self.legs[src].all_ctrls + self.clavicles[src].all_ctrls
        dst_ctrls = self.arms[dst].all_ctrls + self.legs[dst].all_ctrls + self.clavicles[dst].all_ctrls

        for src, dst in zip(src_ctrls, dst_ctrls):
            control_shape_mirror(src, dst)

def create_pair(left, right):
    left.create_joints()
    right.create_joints(matrices = xformMirror(left.joints))
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

