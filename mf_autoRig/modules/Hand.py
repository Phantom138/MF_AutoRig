import re
import importlib
from itertools import chain
from pprint import pprint

import mf_autoRig.lib.defaults as df
from mf_autoRig.lib.useful_functions import *
from mf_autoRig.lib.color_tools import set_color, auto_color
import mf_autoRig.modules.meta as mdata
from mf_autoRig.modules.Module import Module
import mf_autoRig.lib.mirrorJoint as mirrorUtils
from mf_autoRig import log

class Hand(Module):
    meta_args = {
        'finger_num': {'attributeType': 'long'},
        'finger_joints': {'attributeType': 'long'},
        'thumb_joints': {'attributeType': 'long'},
        'hand_ctrl': {'attributeType': 'message'},
        'wrist_guide': {'attributeType': 'message'},
        'guides': {'attributeType': 'message', 'm': True},
        'hand_jnts': {'attributeType': 'message', 'm': True},
        'finger_jnts': {'attributeType': 'message', 'm': True},
        'all_ctrls': {'attributeType': 'message', 'm': True}
    }

    connectable_to = ['Arm', 'Limb']

    def __init__(self, name, meta=True, finger_num: int=5, finger_joints: int=5, thumb_joints: int=4):
        super().__init__(name, self.meta_args, meta)

        # Validate finger_num
        if finger_num > 5:
            log.warning(f"For {self.name} too many fingers, setting to 5")
            finger_num = 5

        elif finger_num < 1:
            log.warning(f"For {self.name} too few fingers, setting to 1")
            finger_num = 1

        elif not isinstance(finger_num, int):
            log.warning(f"For {self.name} invalid finger number, setting to 5")
            finger_num = 5

        if finger_joints < 3:
            log.warning(f"For {self.name} too few finger joints, setting to 3")
            finger_joints = 3

        # Parameters
        self.finger_num = finger_num
        self.finger_joints = finger_joints
        self.thumb_joints = thumb_joints

        # Guides
        self.orient_guides = None
        self.jnt_guides = None
        self.wrist_guide = None
        self.guides = None

        # Controllers
        self.hand_ctrl = None
        self.all_ctrls = []

        # Joints
        self.joints = None
        self.finger_jnts = None
        self.hand_jnts = None

        # Groups - for deletion
        self.control_grp = None
        self.joints_grp = None


    def update_from_meta(self):
        super().update_from_meta()

        if self.all_ctrls is None:
            self.all_ctrls = []

        if self.guides is None:
            return

        # Get orient_guides from guides
        self.orient_guides = self.guides[:self.finger_num]

        # Get jnt_guides from guides
        tmp_jnt_guides = self.guides[self.finger_num:]

        # The code expects the guides to be nested [[finger1_guides], [finger2_guides] .. ]
        # But the guides are in a flat list, so we need to split them up
        self.jnt_guides = []

        # Thumb has less digits!
        # TODO: make this less hardcoded, now it's based on the fact that thumb has 4 joints and the rest have 5
        self.jnt_guides.append(tmp_jnt_guides[:4])
        tmp_jnt_guides = tmp_jnt_guides[4:]
        increment = int(len(tmp_jnt_guides) / (self.finger_num - 1))

        if increment != 0:
            for i in range(0, len(tmp_jnt_guides), increment):
                self.jnt_guides.append(tmp_jnt_guides[i:i+increment])

    def create_guides(self, start_pos=None):
        # TODO: better default placement for wrist guide
        # TODO: Heavy rewrite, maybe having separate modules for each finger
        finger_grps = []
        fingers_jnts = []
        self.guides = []

        if start_pos is None:
            start_pos = [0,0,0]

        # initialize constants
        fingers = ['thumb', 'index', 'middle', 'ring', 'pinky']
        fingers = fingers[:self.finger_num]

        zPos = start_pos[2]
        spacing = 1.5
        # Create finger guides
        for index, name in enumerate(fingers):
            jnt_num = self.finger_joints
            if index == 0:
                # Thumb has less joints
                jnt_num = self.thumb_joints
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
            finger_grp = pm.createNode('transform', name=f'{self.side}_{name}_grp')
            finger_grps.append(finger_grp)

            pm.matchTransform(finger_grp, finger[0])
            pm.parent(finger, finger_grp)

            # Rotate Thumb
            if index == 0:
                pm.rotate(finger_grp, (-25, -30, 0))

        self.jnt_guides = fingers_jnts

        # Create prettier guides
        for finger_guide in self.jnt_guides:
            # Get transforms for each guide
            transforms = []
            for guide in finger_guide:
                trs = pm.xform(guide, q=True, ws=True, t=True)
                transforms.append(trs)

            # Create nurbs curve
            curve = pm.curve(name=f'{finger_guide[0].name()}_crv' ,d=1, p=transforms)

            # Create clusters for each point and parent them under the guide
            for i in range(curve.numCVs()):
                cluster = pm.cluster(curve.cv[i], name=f'{curve.name()}_{i + 1:02}_cluster')[1]
                cluster.visibility.set(0)
                pm.parent(cluster, finger_guide[i])
            pm.parent(curve, get_group(df.driven_grp))

        # Group clean-up
        hand_grp = pm.createNode('transform', name=f'{self.name}_grp')
        pm.matchTransform(hand_grp, finger_grps[int(len(fingers) / 2)])
        pm.parent(finger_grps, hand_grp)
        pm.parent(hand_grp, get_group(df.rig_guides_grp))

        # Create Wrist
        if start_pos == [0,0,0]:
            self.wrist_guide = pm.createNode('joint', name=f'{self.name}_wrist_{df.jnt_sff}')
            pm.xform(self.wrist_guide, t=[0, 5, 0], ws=True)
            pm.parent(self.wrist_guide, hand_grp)

        self.__create_orient_guides()

        # Add orient guides to guides
        from itertools import chain
        self.guides = self.orient_guides + list(chain.from_iterable(self.jnt_guides))

        if self.meta:
            print(f"{self.name} guides: {self.guides}")
            self.save_metadata()

        # Clear selection
        pm.select(clear=True)

    def __create_orient_guides(self):
        self.orient_guides = []
        for finger_guide in self.jnt_guides:
            orient_guide = pm.nurbsPlane(name=f'{finger_guide[1].name()}_orient',lengthRatio=3)[0]

            set_color(orient_guide, viewport='red')

            # Move where and parent where knuckles are
            pm.matchTransform(orient_guide, finger_guide[1], pos=True, rot=True, scale=False)
            pm.rotate(orient_guide, [90, -90, 0], objectSpace=True, relative=True)

            pm.parent(orient_guide, finger_guide[1])

            self.orient_guides.append(orient_guide)

    def create_joints(self, wrist = None):
        """
        mirror_from - nested list with info for fingers, starting with the thumb
        """
        # TODO: orient joints based on orientation guide

        # List of fingers
        finger_names = ['thumb', 'index', 'middle', 'ring', 'pinky']

        self.__create_fingers()
        self.__create_hand(wrist=wrist)

        self.__clean_up_joints()

        self.joints = [self.finger_jnts + self.hand_jnts]

        if self.meta:
            self.save_metadata()

    def __create_fingers(self):
        pm.select(clear=True)
        # Create finger joints based on guides
        self.finger_jnts = []
        obj = self.jnt_guides[0][0]
        scale = pm.xform(obj, q=True, ws=True, scale=True)[0]
        radius = obj.radius.get() * scale
        print("RADIUS FOR FINGERS", radius, scale)
        for i, finger_guide in enumerate(self.jnt_guides):
            # Get finger name
            match = re.search(f'({self.name}_([a-zA-Z]+))\d*_', finger_guide[0].name())
            base_name = match.group(1)
            #jnts = create_joints_from_guides(base_name, finger)

            # Create joints for guides
            jnts = []

            for k, guide in enumerate(finger_guide):
                # Suffix is end if k is last
                suff = df.skin_sff
                if k == len(finger_guide) - 1:
                    suff = df.end_sff

                jnt = pm.createNode('joint', name=f'{base_name}{k + 1:02}{suff}{df.jnt_sff}')
                jnt.radius.set(radius)
                pm.matchTransform(jnt, guide, pos=True, rot=False, scale=False)
                jnts.append(jnt)

            # Orient joints based on orient guide
            for j in range(len(jnts)-1):
                jnt = jnts[j]
                next_jnt = jnts[j+1]

                # Set right orientation
                constraint = pm.aimConstraint(next_jnt, jnt, aim = [0,1,0], upVector=[1,0,0], worldUpObject=self.orient_guides[i], worldUpType="objectrotation", worldUpVector=[0,1,0])
                pm.delete(constraint)

                # Freeze rotation of jnt
                pm.makeIdentity(jnt, apply=True, r=True)

                # Parent
                pm.parent(next_jnt, jnt)

            # Orient last joint
            pm.joint(jnts[-1], edit=True, orientJoint='none')

            self.finger_jnts.append(jnts[0])

    def __create_hand(self, wrist=None):
        if wrist is None:
            wrist = self.wrist_guide

        self.hand_jnts = []
        obj = self.wrist_guide
        scale = pm.xform(obj, q=True, ws=True, scale=True)[0]
        radius = obj.radius.get() * scale

        # Create start jnt where the wrist is
        mtx = pm.xform(wrist, q=True, ws=True, t=True)
        hand_start = pm.joint(name=f'{self.name}{df.skin_sff}{df.jnt_sff}', p=mtx, radius=radius)

        self.hand_jnts.append(hand_start)

        # Create end jnt by averaging the knuckles position
        sums = [0,0,0]
        cnt = 0
        for finger in self.finger_jnts[1:]:
            jnts = get_joint_hierarchy(finger)
            pos = pm.xform(jnts[1], q=True, t=True, ws=True)
            sums[0] += pos[0]
            sums[1] += pos[1]
            sums[2] += pos[2]
            cnt += 1

        average = [sums[0]/cnt, sums[1]/cnt, sums[2]/cnt]
        hand_end = pm.joint(name = f'{self.name}{df.end_sff}{df.jnt_sff}', position=average, radius=radius)
        self.hand_jnts.append(hand_end)

        # Orient Joints
        pm.joint(self.hand_jnts[0], edit=True, orientJoint='yzx', secondaryAxisOrient='zup', children=True)
        pm.joint(self.hand_jnts[-1], edit=True, orientJoint='none')

    def __clean_up_joints(self):
        # Create hand grp
        self.joints_grp = pm.createNode('transform', name=f'{self.name}_{df.joints_grp}')
        pm.parent(self.joints_grp, get_group('Joints_Grp'))

        # Parent fingers under joint_grp
        for finger in self.finger_jnts:
            pm.parent(finger, self.joints_grp)

        # Parent hand joints under joint_grp
        pm.parent(self.hand_jnts[0], self.joints_grp)

        pm.select(clear=True)

    def rig(self, curl=True, spread=True):
        # Create hand ctrl
        self.hand = CtrlGrp(self.name, shape='circle')
        self.handJnt = self.hand_jnts[0]

        auto_color(self.hand.ctrl)

        # Match transforms and parent constrain controller to joint
        pm.matchTransform(self.hand.grp, self.handJnt)
        pm.parentConstraint(self.hand.ctrl, self.handJnt, maintainOffset=True)

        # Go through each finger
        all_offset_grps = []
        for finger_start in self.finger_jnts:
            # Get finger hierarchy
            finger = get_joint_hierarchy(finger_start)
            finger_ctrls = create_fk_ctrls(finger, scale=0.2)

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

        self.hand_ctrl = self.hand.ctrl
        # Add to metadata
        if self.meta:
            self.save_metadata()

        self.all_ctrls.append(self.hand.ctrl)

        # Parent hand ctrl under root
        pm.parent(self.hand.grp, get_group(df.root))
        self.control_grp = self.hand.grp

        if self.meta:
            self.save_metadata()

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

    def mirror(self):
        # TODO: add possibility to mirror on different plane
        # TODO: mirror ctrls instead of recreating them
        """
        Mirrors everything from the module across the YZ plane
        Method: mirrors joints and then recreates default ctrls
        Return a class of the same type that is mirrored on the YZ plane
        """

        name = self.name.replace(f'{self.side}_', f'{self.side.opposite}_')
        mir_module = self.__class__(name, meta=self.meta)

        # Mirror finger_jnts
        mir_module.finger_jnts = []
        for finger_start in self.finger_jnts:
            finger = get_joint_hierarchy(finger_start)
            mir_finger = mirrorUtils.mirrorJoints(finger, (f'{self.side}_', f'{self.side.opposite}_'))
            mir_module.finger_jnts.append(mir_finger[0])

        # Mirror hand_jnts
        mir_module.hand_jnts = mirrorUtils.mirrorJoints(self.hand_jnts, (f'{self.side}_', f'{self.side.opposite}_'))

        mir_module.__clean_up_joints()
        # Rig hand
        mir_module.rig()

        if mir_module.meta:
            mir_module.save_metadata()

        # Do mirror connection for metadata
        self.metaNode.message.connect(mir_module.metaNode.mirrored_from)

        return mir_module

    def connect(self, arm, force=False):
        if self.check_if_connected(arm) and not force:
            pm.warning(f"{self.name} already connected to {arm.name}")
            return

        self.handJnt = self.hand_jnts[0]
        hand_grp = self.hand_ctrl.getParent(1)

        match = re.search('([a-zA-Z]_([a-zA-Z]+))\d*_', self.handJnt.name())
        base_name = match.group(1)

        # Point constraint
        pm.pointConstraint(arm.joints[-1], hand_grp)

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
        pm.parent(fk_loc_grp, arm.fk_ctrls[-1])

        # Create orient constraint and get weight list
        constraint = pm.orientConstraint(ik_loc, fk_loc, hand_grp)
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

        super().connect_metadata(arm)
