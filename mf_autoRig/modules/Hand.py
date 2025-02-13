import mf_autoRig.utils.defaults as df
from mf_autoRig.utils.general import *
from mf_autoRig.utils.color_tools import set_color, auto_color
from mf_autoRig.modules.Module import Module
import mf_autoRig.utils as utils
from mf_autoRig import log

class Hand(Module):
    meta_args = {
        'creation_attrs': {
            **Module.meta_args['creation_attrs'],
            'finger_num': {'attributeType': 'long'},
            'finger_joints_num': {'attributeType': 'long'},
            'thumb_joints_num': {'attributeType': 'long'},
        },

        'module_attrs': {
            **Module.meta_args['module_attrs'],
        },

        'config_attrs': {
            **Module.meta_args['config_attrs'],
            'curl': {'attributeType': 'bool'},
            'spread': {'attributeType': 'bool'},
        },

        'info_attrs': {
            **Module.meta_args['info_attrs'],
            'hand_ctrl': {'attributeType': 'message'},
            'wrist_guide': {'attributeType': 'message'},
            'guides': {'attributeType': 'message', 'm': True},
            'hand_jnts': {'attributeType': 'message', 'm': True},
            'finger_jnts': {'attributeType': 'message', 'm': True},
        }
    }

    connectable_to = ['Arm', 'Limb']

    def __init__(self, name, meta=True, **kwargs):
        super().__init__(name, self.meta_args, meta)

        # Get attrs from kwargs
        default_args = {'finger_num': 5, 'finger_joints_num': 5, 'thumb_joints_num': 4}
        default_args.update(kwargs)

        for key, value in default_args.items():
            setattr(self, key, value)

        # Validate finger_num
        if self.finger_num > 5:
            log.warning(f"For {self.name} too many fingers, setting to 5")
            self.finger_num = 5

        elif self.finger_num < 1:
            log.warning(f"For {self.name} too few fingers, setting to 1")
            self.finger_num = 1

        elif not isinstance(self.finger_num, int):
            log.warning(f"For {self.name} invalid finger number, setting to 5")
            self.finger_num = 5

        if self.finger_joints_num < 3:
            log.warning(f"For {self.name} too few finger joints, setting to 3")
            self.finger_joints_num = 3

        self.reset()
        # self.save_metadata()

    def reset(self):
        super().reset()

        # From config
        self.curl = True
        self.spread = True

        # Guides
        self.orient_guides = []
        self.jnt_guides = []
        self.wrist_guide = None
        self.guides = []

        # Controllers
        self.hand_ctrl = None

        # Joints
        self.joints = []
        self.finger_jnts = []
        self.hand_jnts = []


    def update_from_meta(self):
        super().update_from_meta()

        if not self.guides:
            return

        # Get orient_guides from guides
        self.orient_guides = self.guides[:self.finger_num]

        # Get jnt_guides from guides
        tmp_jnt_guides = self.guides[self.finger_num:]

        # The code expects the guides to be nested [[finger1_guides], [finger2_guides] .. ]
        # But the guides are in a flat list, so we need to split them up
        self.jnt_guides = []

        # Get thumb joints
        self.jnt_guides.append(tmp_jnt_guides[:self.thumb_joints_num])
        tmp_jnt_guides = tmp_jnt_guides[self.thumb_joints_num:]

        # Get the rest of the fingers
        for i in range(0, len(tmp_jnt_guides), self.finger_joints_num):
            self.jnt_guides.append(tmp_jnt_guides[i:i + self.finger_joints_num])

    def create_guides(self, pos: dict = None):
        # TODO: better default placement for wrist guide
        # TODO: rewrite, maybe having separate modules for each finger
        if pos is None:
            pos = {
                'wrist': [0,0,0],
                'guides': [],
                'orient_guides_rot': []
            }

        # initialize constants
        fingers = ['thumb', 'index', 'middle', 'ring', 'pinky']
        fingers = fingers[:self.finger_num]

        guides_pos = pos['guides']
        wrist_pos = pos['wrist']
        # Create positions array
        if len(guides_pos) == 0:
            # TODO: i think all of the code below could be in a dict with values directly
            hand_pos = wrist_pos[0], wrist_pos[1] - 5, wrist_pos[2]
            zPos = hand_pos[2]
            spacing = 1.5

            finger_positions = []
            for index, name in enumerate(fingers):
                jnt_num = self.finger_joints_num
                if index == 0:
                    jnt_num = self.thumb_joints_num
                else:
                    # Offset fingers
                    zPos -= spacing

                # Do fingers
                fingerPos = hand_pos[0], hand_pos[1], zPos
                yPos = fingerPos[1]
                offset = 4

                positions = []
                for i in range(jnt_num):
                    # Create more space for the knuckles
                    if i == 1:
                        yPos -= offset

                    # Set jnt position
                    p = fingerPos[0], yPos, fingerPos[2]
                    yPos -= offset
                    positions.append(p)

                finger_positions.append(positions)
        else:
            finger_positions = guides_pos

        # Create guides
        guide_finger_grps = []
        for index, name in enumerate(fingers):
            guide_finger_grp = pm.createNode('transform', name=f'{self.side}_{name}_guide_grp')

            guide = utils.create_guide_chain(f'{self.name}_{name}', len(finger_positions[index]), finger_positions[index], parent= guide_finger_grp)
            # pm.parent(guide, guide_finger_grp)
            guide_finger_grps.append(guide_finger_grp)

            self.jnt_guides.append(guide)

        # Create wrist guide
        self.wrist_guide = utils.Guide(f'{self.name}_wrist_guide', wrist_pos).guide

        # Create guide grp
        self.guide_grp = pm.createNode('transform', name=f'{self.name}_guide_grp')
        pm.matchTransform(self.guide_grp, self.wrist_guide)
        pm.parent(self.wrist_guide, self.guide_grp)
        pm.parent(guide_finger_grps, self.guide_grp)
        pm.parent(self.guide_grp, get_group(df.rig_guides_grp))

        self.__create_orient_guides(pos['orient_guides_rot'])
        from itertools import chain
        self.guides = self.orient_guides + list(chain.from_iterable(self.jnt_guides))


        if self.meta:
            self.save_metadata()

        # Clear selection
        pm.select(clear=True)

    def __create_orient_guides(self, rot: list):
        self.orient_guides = []
        if len(rot) == 0:
            rot_is_empty = True
        else:
            rot_is_empty = False

        for i, finger_guide in enumerate(self.jnt_guides):
            # Move where and parent where knuckles are
            orient_guide = pm.nurbsPlane(name=f'{finger_guide[1].name()}_orient',lengthRatio=3)[0]
            pm.matchTransform(orient_guide, finger_guide[1], pos=True, rot=True, scale=False)

            if rot_is_empty:
                r = [90, -90, 0]
            else:
                r = rot[i]
            pm.rotate(orient_guide, r, objectSpace=True, relative=True)
            pm.parent(orient_guide, finger_guide[1])

            set_color(orient_guide, viewport='red')
            self.orient_guides.append(orient_guide)

    def create_joints(self, wrist = None):
        # List of fingers
        finger_names = ['thumb', 'index', 'middle', 'ring', 'pinky']
        print(self.jnt_guides)
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

        # Get joint radius from guide
        obj = self.jnt_guides[0][0]
        scale = pm.xform(obj, q=True, ws=True, scale=True)[0]
        radius = obj.radius.get() * scale

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
                constraint = pm.aimConstraint(next_jnt, jnt, aim = self.jnt_orient_main, upVector=self.jnt_orient_secondary, worldUpObject=self.orient_guides[i],
                                              worldUpType="objectrotation", worldUpVector = [1,0,0])
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
            jnts = utils.get_joint_hierarchy(finger)
            pos = pm.xform(jnts[1], q=True, t=True, ws=True)
            sums[0] += pos[0]
            sums[1] += pos[1]
            sums[2] += pos[2]
            cnt += 1

        average = [sums[0]/cnt, sums[1]/cnt, sums[2]/cnt]
        hand_end = pm.joint(name = f'{self.name}{df.end_sff}{df.jnt_sff}', position=average, radius=radius)
        self.hand_jnts.append(hand_end)

        # Orient Joints
        utils.orient_joints(self.hand_jnts, self.jnt_orient_main, self.jnt_orient_secondary)


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

    def rig(self):
        curl = self.curl
        spread = self.spread

        # Create hand ctrl
        self.hand = utils.CtrlGrp(self.name, shape='circle')
        self.handJnt = self.hand_jnts[0]

        auto_color(self.hand.ctrl)

        # Match transforms and parent constrain controller to joint
        pm.matchTransform(self.hand.grp, self.handJnt)
        pm.parentConstraint(self.hand.ctrl, self.handJnt, maintainOffset=True)

        # Go through each finger
        all_offset_grps = []
        for finger_start in self.finger_jnts:
            # Get finger hierarchy
            finger = utils.get_joint_hierarchy(finger_start)
            finger_ctrls = utils.create_fk_ctrls(finger, scale=0.2)

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
            finger = utils.get_joint_hierarchy(finger_start)
            mir_finger = utils.mirrorJoints(finger, (f'{self.side}_', f'{self.side.opposite}_'))
            mir_module.finger_jnts.append(mir_finger[0])

        # Mirror hand_jnts
        mir_module.hand_jnts = utils.mirrorJoints(self.hand_jnts, (f'{self.side}_', f'{self.side.opposite}_'))

        mir_module.__clean_up_joints()
        # Rig hand
        mir_module.rig()

        if mir_module.meta:
            mir_module.save_metadata()

        # Do mirror connection for metadata
        self.metaNode.mirrored_to.connect(mir_module.metaNode.mirrored_from)

        return mir_module

    def connect(self, arm, force=False):
        if not self.check_if_connected(arm):
            pm.warning(f"{self.name} not connected to {arm.name}")
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
        pm.hide(ik_loc, fk_loc)
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

