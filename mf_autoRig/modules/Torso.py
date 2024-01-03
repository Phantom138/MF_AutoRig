import pymel.core as pm

from mf_autoRig.lib.useful_functions import *
import mf_autoRig.lib.defaults as df


class Clavicle:
    def __init__(self, name):
        self.name = name
        self.joints = None
        self.guides = None

    def create_guides(self, pos):
        """
        Creates clavicle guides at pos, pos should be a list of xyz values
        """
        self.guides = []
        # Create new joint at pos
        self.guides.append(pm.joint(name=f'{self.name}', position=pos))
        pm.parent(self.guides, get_group('rig_guides_grp'))

        print(f'Clavicle guides {self.guides}')

        # Clear Selection
        pm.select(clear=True)

    def create_joints(self, shoulder):
        """
        Create joints from starting guide to shoulder
        """
        # Add shoulder to guides
        self.guides.append(shoulder)

        # Create joints
        self.joints = []
        for i, tmp in enumerate(self.guides):
            # Create joints where the guides where
            trs = pm.xform(tmp, q=True, t=True, ws=True)
            jnt = pm.joint(name=f'{self.name}{i + 1:02}{df.skin_sff}{df.jnt_sff}', position=trs)

            self.joints.append(jnt)

        print(f'Created {self.joints} for Clavicle')

        # Orient joints
        pm.joint(self.joints[0], edit=True, orientJoint='yzx', secondaryAxisOrient='zup', children=True)
        pm.joint(self.joints[-1], edit=True, orientJoint='none')

        if len(self.joints) != 2:
            pm.error('Can only create clavicle with 2 joints')

        # Create ctrl and group
        axis = get_joint_orientation(self.joints[0], self.joints[1])
        clav = CtrlGrp(self.name, 'arc', axis=axis)

        # Match ctrl to first joint
        jnt = self.joints[0]
        pm.matchTransform(clav.grp, jnt)
        pm.parentConstraint(clav.ctrl, jnt, maintainOffset=True)

        self.ctrl = clav.ctrl

        # Parent Joints under Joint_grp
        pm.parent(self.joints[0], get_group(df.joints_grp))

        pm.select(clear=True)

    def connect(self, torso):
        pm.parent(self.ctrl.getParent(1), torso.fk_ctrls[-1])


class Spine:
    def __init__(self, name, num):
        self.name = name
        self.num = num
        self.guides = None
        self.joints = None

    def create_guides(self, pos):
        self.guides = create_joint_chain(self.num, self.name, pos[0], pos[1], defaultValue=50)

        pm.select(clear=True)

    def create_joints(self):
        self.joints = []

        # Create a joint for all the guides
        for i, guide in enumerate(self.guides):
            trs = pm.xform(guide, q=True, t=True, ws=True)
            jnt = pm.joint(name=f'{self.name}{i + 1:02}{df.skin_sff}{df.jnt_sff}', position=trs)

            self.joints.append(jnt)

        pm.select(clear=True)

        # Orient joints
        pm.joint(self.joints[0], edit=True, orientJoint='yzx', secondaryAxisOrient='zup', children=True)
        pm.joint(self.joints[-1], edit=True, orientJoint='none')

        # Create hip at the beginning of joint chain
        trs = pm.xform(self.joints[0], q=True, t=True, ws=True)
        self.hip = pm.joint(name=f'{self.name[0]}_hip{df.skin_sff}{df.jnt_sff}', position=trs)

        # Create ctrls
        self.fk_ctrls = create_fk_ctrls(self.joints, skipEnd=False, shape='square')
        self.hip_ctrl = create_fk_ctrls(self.hip, shape='circle')

        # Parent hip ctrl grp under pelvis ctrl
        pm.parent(self.hip_ctrl.getParent(1), self.fk_ctrls[0])

        # Parent spine ctrl under Root
        pm.parent(self.fk_ctrls[0].getParent(1), get_group(df.root))

        # Parent Joints under Joint_grp
        pm.parent(self.joints[0], self.hip, get_group(df.joints_grp))
