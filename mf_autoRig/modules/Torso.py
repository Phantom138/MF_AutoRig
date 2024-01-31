import pymel.core as pm

from mf_autoRig.lib.useful_functions import *
import mf_autoRig.lib.defaults as df
from mf_autoRig.lib.tools import set_color
import mf_autoRig.modules.meta as mdata
from mf_autoRig.modules.Module import Module



#TODO: split clavicle and Torso intro dif files
class Clavicle(Module):
    meta_args = {
        'guides': {'attributeType': 'message', 'm': True},
        'joints': {'attributeType': 'message', 'm': True},
        'clavicle_ctrl': {'attributeType': 'message', 'm': True},
    }

    def __init__(self, name, meta=True):
        self.name = name
        self.meta = meta
        self.side = name.split('_')[0]
        self.clavicle_ctrl = None
        self.joints = None
        self.guides = None
        self.all_ctrls = []

        # Create metadata node
        if meta:
            self.metaNode = mdata.create_metadata(name, 'Clavicle', self.meta_args)


    @classmethod
    def create_from_meta(cls, metaNode):
        clavicle = super().create_from_meta(metaNode)

        return clavicle


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

        # Save guides
        if self.meta and self.guides:
            for i, guide in enumerate(self.guides):
                guide.message.connect(self.metaNode.guides[i])



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

        #Save joints
        if self.meta and self.joints:
            for i, joints in enumerate(self.joints):
                joints.message.connect(self.metaNode.joints[i])

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

        if self.meta and self.clavicle_ctrl:
            self.clavicle_ctrl.message.connect(self.metaNode.clavicle_ctrl)


    def connect(self, torso):
        pm.parent(self.clavicle_ctrl.getParent(1), torso.fk_ctrls[-1])



spine_meta_args = {
    'hip_jnt': {'attributeType': 'message'},
    'hip_ctrl': {'attributeType': 'message'},
    'guides': {'attributeType': 'message', 'm': True},
    'joints': {'attributeType': 'message', 'm': True},
    'fk_ctrls': {'attributeType': 'message', 'm': True},
}

class Spine:
    def __init__(self, name, meta=True, num=4):
        self.meta = meta
        self.name = name
        self.num = num
        self.guides = None
        self.joints = None

        # Create metadata node
        if meta:
            self.metaNode = mdata.create_metadata(name, 'Spine', spine_meta_args)

    def create_guides(self, pos=None):
        if pos is None:
            pos = [(0,0,0), (0,10,0)]
        self.guides = create_joint_chain(self.num, self.name, pos[0], pos[1], defaultValue=50)

        pm.select(clear=True)
        # Add guides
        if self.meta:
            mdata.add(self.guides, self.metaNode.guides)

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
        self.hip_jnt = pm.createNode('joint', name=f'{self.name[0]}_hip{df.skin_sff}{df.jnt_sff}')
        pm.matchTransform(self.hip_jnt, self.joints[0])

        pm.select(clear=True)
        # Add joints
        if self.meta:
            mdata.add(self.hip_jnt, self.metaNode.hip_jnt)
            mdata.add(self.joints, self.metaNode.joints)

    def rig(self):


        self.fk_ctrls = create_fk_ctrls(self.joints, skipEnd=False, shape='square')
        self.hip_ctrl = create_fk_ctrls(self.hip_jnt, shape='circle')

        # Color ctrls
        set_color(self.fk_ctrls, viewport='yellow')
        set_color(self.hip_ctrl, viewport='green')

        # Parent hip ctrl grp under pelvis ctrl
        pm.parent(self.hip_ctrl.getParent(1), self.fk_ctrls[0])

        # Parent spine ctrl under Root
        pm.parent(self.fk_ctrls[0].getParent(1), get_group(df.root))

        # Parent Joints under Joint_grp
        pm.parent(self.joints[0], self.hip_jnt, get_group(df.joints_grp))

        # Add joints
        if self.meta:
            print(f'Spine fk ctrls: {self.fk_ctrls}')
            mdata.add(self.fk_ctrls, self.metaNode.fk_ctrls)
            mdata.add(self.hip_ctrl, self.metaNode.hip_ctrl)