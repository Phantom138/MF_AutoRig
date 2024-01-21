import pymel.core as pm

from mf_autoRig.lib.useful_functions import *
import mf_autoRig.lib.defaults as df
from mf_autoRig.lib.tools import set_color

class Clavicle:
    def __init__(self, name):
        self.name = name
        self.side = name.split('_')[0]
        self.clavicle_ctrl = None
        self.joints = None
        self.guides = None
        self.all_ctrls = []

        # Create script node
        node = pm.createNode('script', name = df.tool_prf + self.name)
        node.addAttr('moduleType', type='string')
        node.moduleType.set('Clavicle')
        node.addAttr('joints', at='message')
        node.addAttr('ik_joints', type='string')
        node.addAttr('fk_joints', type='string')

    def create_guides(self, pos = None):
        """
        Creates clavicle guides at pos, pos should be a list of xyz values
        """
        self.guides = []
        # If there are no guides, it means that the class is ran individually, so there is no guide for the shoulder
        if pos is None:
            pos = [(0,0,0), (5,0,0)]
            for p in pos:
                self.guides.append(pm.joint(name=f'{self.name}', position=p))
        else:
            # Create new joint at pos
            self.guides.append(pm.joint(name=f'{self.name}', position=pos))
        pm.parent(self.guides, get_group('rig_guides_grp'))

        print(f'Clavicle guides {self.guides}')

        # Clear Selection
        pm.select(clear=True)

    def create_joints(self, shoulder=None):
        """
        Create joints from starting guide to shoulder
        """
        if shoulder is not None:
            # Add shoulder to guides
            self.guides.append(shoulder)

        # Create joints
        self.joints = []
        for i, tmp in enumerate(self.guides):
            # Create joints where the guides where
            trs = pm.xform(tmp, q=True, t=True, ws=True)
            sff = df.skin_sff
            if i == len(self.guides):
                sff = df.end_sff
            jnt = pm.joint(name=f'{self.name}{i + 1:02}{sff}{df.jnt_sff}', position=trs)

            self.joints.append(jnt)

        print(f'Created {self.joints} for Clavicle')

        # Orient joints
        pm.joint(self.joints[0], edit=True, orientJoint='yzx', secondaryAxisOrient='zup', children=True)
        pm.joint(self.joints[-1], edit=True, orientJoint='none')

        # Clear Selection
        pm.select(clear=True)

    def rig(self):
        if len(self.joints) != 2:
            pm.error('Can only create clavicle with 2 joints')

        # Create ctrl and group
        axis = get_joint_orientation(self.joints[0], self.joints[1])
        clav = CtrlGrp(self.name, 'arc', axis=axis)

        # Match ctrl to first joint
        jnt = self.joints[0]
        pm.matchTransform(clav.grp, jnt)
        pm.parentConstraint(clav.ctrl, jnt, maintainOffset=True)

        self.clavicle_ctrl = clav.ctrl

        self.all_ctrls.append(self.clavicle_ctrl)

        # Color clavicle
        if self.side == 'R':
            set_color(self.clavicle_ctrl, viewport='red')
        elif self.side == 'L':
            set_color(self.clavicle_ctrl, viewport='blue')


        # Parent Joints under Joint_grp
        pm.parent(self.joints[0], get_group(df.joints_grp))

        pm.select(clear=True)

    def connect(self, torso):
        pm.parent(self.clavicle_ctrl.getParent(1), torso.fk_ctrls[-1])


class Spine:
    def __init__(self, name, num=4):
        self.name = name
        self.num = num
        self.guides = None
        self.joints = None

    def create_guides(self, pos=None):
        if pos is None:
            pos = [(0,0,0), (0,10,0)]
        self.guides = create_joint_chain(self.num, self.name, pos[0], pos[1], defaultValue=50)

        pm.select(clear=True)

    def create_joints(self):
        self.joints = []

        # Create a joint for all the guides
        for i, guide in enumerate(self.guides):
            trs = pm.xform(guide, q=True, t=True, ws=True)
            jnt = pm.joint(name=f'{self.name}{i + 1:02}{df.skin_sff}{df.jnt_sff}', position=trs)

            self.joints.append(jnt)

        # Orient joints
        pm.joint(self.joints[0], edit=True, orientJoint='yzx', secondaryAxisOrient='zup', children=True)
        pm.joint(self.joints[-1], edit=True, orientJoint='none')

        # Create hip at the beginning of joint chain
        self.hip = pm.createNode('joint', name=f'{self.name[0]}_hip{df.skin_sff}{df.jnt_sff}')
        pm.matchTransform(self.hip, self.joints[0])

        pm.select(clear=True)

    def rig(self):
        # Create ctrls
        self.fk_ctrls = create_fk_ctrls(self.joints, skipEnd=False, shape='square')
        self.hip_ctrl = create_fk_ctrls(self.hip, shape='circle')

        # Color ctrls
        set_color(self.fk_ctrls, viewport='yellow')
        set_color(self.hip_ctrl, viewport='green')

        # Parent hip ctrl grp under pelvis ctrl
        pm.parent(self.hip_ctrl.getParent(1), self.fk_ctrls[0])

        # Parent spine ctrl under Root
        pm.parent(self.fk_ctrls[0].getParent(1), get_group(df.root))

        # Parent Joints under Joint_grp
        pm.parent(self.joints[0], self.hip, get_group(df.joints_grp))
