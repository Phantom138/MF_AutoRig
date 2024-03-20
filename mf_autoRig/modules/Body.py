import logging

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

from mf_autoRig import log

class Body():
    meta_args = {
        'spine': {'attributeType': 'message'},
        'arms': {'attributeType': 'message', 'm': True},
        'hands': {'attributeType': 'message', 'm': True},
        'legs': {'attributeType': 'message', 'm': True},
        'clavicles': {'attributeType': 'message', 'm': True},
    }

    def __init__(self, meta=True, do_hands=True, do_feet=True, do_clavicles=True):
        self.do_hands = do_hands
        self.do_feet = do_feet
        self.do_clavicles = do_clavicles
        self.spine = Spine('M_spine', num=3, meta=meta)

        self.arms = [Arm('L_arm', meta)]
        self.legs = [Leg('L_leg', meta)]

        if self.do_hands:
            self.hands = [Hand('L_hand', meta)]
        else:
            self.hands = None

        if self.do_clavicles:
            self.clavicles = [Clavicle('L_clavicle', meta)]
        else:
            self.clavicles = None



    def create_guides(self, positions):
        log.info("Creating Guides for Body")

        self.arms[0].create_guides(positions['arm'])
        self.legs[0].create_guides(positions['leg'])

        if self.do_hands:
            self.hands[0].create_guides(positions['hand_start'])
            # Add wrist
            self.hands[0].wrist_guide = self.arms[0].guides[-1]

        if self.do_clavicles:
            self.clavicles[0].create_guides(positions['clavicle'])
            # Add shoulder
            self.clavicles[0].guides.append(self.arms[0].guides[0])

        self.spine.create_guides(positions['torso'])


    def create_joints(self):
        log.info("Creating Joints")
        self.spine.create_joints()

        self.arms[0].create_joints()
        self.legs[0].create_joints()

        if self.do_clavicles:
            self.clavicles[0].create_joints()

        if self.do_hands:
            self.hands[0].create_joints(wrist=self.arms[0].joints[-1])


    def rig(self):
        log.info("Rigging Body")
        self.spine.rig()

        self.arms[0].rig()
        self.legs[0].rig()

        if self.do_hands:
            self.hands[0].rig()
        else:
            # HACK: add empty list to avoid errors
            self.hands = [1,2]

        if self.do_clavicles:
            self.clavicles[0].rig()
        else:
            # HACK: add empty list to avoid errors
            self.clavicles = [1,2]


        self.mirror_modules()
        for arm, leg, hand, clavicle in zip(self.arms, self.legs, self.hands, self.clavicles):
            if self.do_clavicles:
                arm.connect(clavicle)
                clavicle.connect(self.spine)
            else:
                arm.connect(self.spine)

            if self.do_hands:
                hand.connect(arm)

            leg.connect(self.spine)


    def mirror_modules(self):
        self.arms.insert(1, self.arms[0].mirror())
        self.legs.insert(1, self.legs[0].mirror())

        if self.do_hands:
            self.hands.insert(1, self.hands[0].mirror())
        if self.do_clavicles:
            self.clavicles.insert(1, self.clavicles[0].mirror())

    def mirror_ctrls(self, side: str):
        log.info("Mirroring ctrls")

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

