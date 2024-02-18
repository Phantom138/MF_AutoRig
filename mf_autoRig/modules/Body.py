import pymel.core as pm
import pymel.core.datatypes as dt
import re

from mf_autoRig.lib.defaults import *
import importlib

from mf_autoRig.lib.useful_functions import *

# Import Modules

from mf_autoRig.modules.Hand import Hand
from mf_autoRig.modules.Limb import Arm, Leg
from mf_autoRig.modules.Module import Module
from mf_autoRig.modules.Spine import Spine
from mf_autoRig.modules.Clavicle import Clavicle

from mf_autoRig.lib.mirrorJoint import xformMirror


class Body():
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
        self.hands[0].create_hand(wrist = self.arms[0].joints[-1])

        self.hands[1].create_joints(mirror_from = self.hands[0].finger_jnts)
        self.hands[1].create_hand(mirror_from = self.hands[0].hand_jnts)

        # Clavicles
        self.clavicles[0].create_joints(self.arms[0].joints[0])
        mirrored_jnts = pm.mirrorJoint(self.clavicles[0].joints[0], mirrorYZ=True, mirrorBehavior=True, searchReplace=('L_', 'R_'))
        self.clavicles[1].joints = list(map(pm.PyNode, mirrored_jnts))
        print(self.clavicles[1].joints)
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
    left.mirror(right)

    #right.create_joints(matrices = xformMirror(left.joints))

