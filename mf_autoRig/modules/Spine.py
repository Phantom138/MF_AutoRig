import pymel.core as pm

from mf_autoRig.utils.useful_functions import *
import mf_autoRig.utils.defaults as df
from mf_autoRig.utils.color_tools import set_color
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

    connectable_to = []
    attachment_pts = ['Chest', 'Hip']

    def __init__(self, name, meta=True, num=4):
        super().__init__(name, self.meta_args, meta)
        self.num = num

        self.reset()


    def reset(self):
        super().reset()

        self.guides = None
        self.joints = None
        self.hip_ctrl = None
        self.hip_jnt = None
        self.fk_ctrls = None

        self.control_grp = None
        self.joints_grp = None

    def update_from_meta(self):
        super().update_from_meta()

        self.all_ctrls = self.fk_ctrls
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

        self.joints = create_joints_from_guides(self.name, self.guides, suffix=df.skin_sff, endJnt=False)

        # Create hip at the beginning of joint chain
        self.hip_jnt = pm.createNode('joint', name=f'{self.name[0]}_hip{df.skin_sff}{df.jnt_sff}')
        self.hip_jnt.radius.set(self.joints[0].radius.get())
        pm.matchTransform(self.hip_jnt, self.joints[0])

        # Parent Joints under Joint_grp
        self.joints_grp = pm.createNode('transform', name=f'{self.name}_{df.joints_grp}')
        pm.parent(self.joints[0], self.hip_jnt, self.joints_grp)
        pm.parent(self.joints_grp, get_group(df.joints_grp))


        # Add joints
        if self.meta:
            self.save_metadata()

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

        self.control_grp = self.fk_ctrls[0].getParent(1)
        self.all_ctrls = self.fk_ctrls
        # Add joints
        if self.meta:
            self.save_metadata()