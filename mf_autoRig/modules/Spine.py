import pymel.core as pm

from mf_autoRig.lib.useful_functions import *
import mf_autoRig.lib.defaults as df
from mf_autoRig.lib.color_tools import set_color
import mf_autoRig.modules.meta as mdata
from mf_autoRig.modules.Module import Module

class Spine(Module):
    meta_args = {
        'hip_jnt': {'attributeType': 'message'},
        'hip_ctrl': {'attributeType': 'message'},
        'guides': {'attributeType': 'message', 'm': True},
        'joints': {'attributeType': 'message', 'm': True},
        'fk_ctrls': {'attributeType': 'message', 'm': True},
    }
    def __init__(self, name, meta=True, num=4):
        super().__init__(name, self.meta_args, meta)

        self.num = num
        self.guides = None
        self.joints = None

    @classmethod
    def create_from_meta(cls, metaNode):
        obj = super().create_from_meta(metaNode)

        return obj

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
        pm.select(clear=True)

        # Orient joints
        pm.joint(self.joints[0], edit=True, orientJoint='yzx', secondaryAxisOrient='zup', children=True)
        pm.joint(self.joints[-1], edit=True, orientJoint='none')

        # Create hip at the beginning of joint chain
        self.hip_jnt = pm.createNode('joint', name=f'{self.name[0]}_hip{df.skin_sff}{df.jnt_sff}')
        pm.matchTransform(self.hip_jnt, self.joints[0])

        # Parent Joints under Joint_grp
        pm.parent(self.joints[0], self.hip_jnt, get_group(df.joints_grp))
        pm.group(self.joints[0], self.hip_jnt, name=f'{self.name}_{df.joints_grp}')

        # Add joints
        if self.meta:
            mdata.add(self.hip_jnt, self.metaNode.hip_jnt)
            mdata.add(self.joints, self.metaNode.joints)

    def rig(self):
        self.fk_ctrls = create_fk_ctrls(self.joints, skipEnd=False, shape='square')
        self.hip_ctrl = create_fk_ctrls(self.hip_jnt, shape='star', scale=1.5)

        # Color ctrls
        set_color(self.fk_ctrls, viewport='yellow')
        set_color(self.hip_ctrl, viewport='green')

        # Parent hip ctrl grp under pelvis ctrl
        pm.parent(self.hip_ctrl.getParent(1), self.fk_ctrls[0])

        # Parent spine ctrl under Root
        pm.parent(self.fk_ctrls[0].getParent(1), get_group(df.root))

        # Add joints
        if self.meta:
            mdata.add(self.fk_ctrls, self.metaNode.fk_ctrls)
            mdata.add(self.hip_ctrl, self.metaNode.hip_ctrl)