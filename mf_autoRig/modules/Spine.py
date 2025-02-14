import pymel.core as pm
import mf_autoRig.utils as utils
import mf_autoRig.utils.defaults as df
from mf_autoRig.utils.color_tools import set_color
import mf_autoRig.modules.meta as mdata
from mf_autoRig.modules.Module import Module

class Spine(Module):
    meta_args = {
        'creation_attrs':{
            **Module.meta_args['creation_attrs'],
            'num': {'attributeType': 'long'},
        },
        'module_attrs': {
            **Module.meta_args['module_attrs'],
        },

        'config_attrs': {
            **Module.meta_args['config_attrs'],
        },
        'info_attrs':{
            **Module.meta_args['info_attrs'],
            'hip_jnt': {'attributeType': 'message'},
            'hip_ctrl': {'attributeType': 'message'},
            'guides': {'attributeType': 'message', 'm': True},
            'joints': {'attributeType': 'message', 'm': True},
            'fk_ctrls': {'attributeType': 'message', 'm': True},
        }
    }

    connectable_to = []
    attachment_pts = ['Chest', 'Hip']

    def __init__(self, name, meta=True, **kwargs):
        super().__init__(name, self.meta_args, meta)

        # Get attrs from kwargs
        default_args = {'num': 4}
        default_args.update(kwargs)

        for key, value in default_args.items():
            setattr(self, key, value)

        self.reset()
        # self.save_metadata()


    def reset(self):
        super().reset()

        self.guides = []
        self.joints = []
        self.hip_ctrl = None
        self.hip_jnt = None
        self.fk_ctrls = []

    def update_from_meta(self):
        super().update_from_meta()

        self.all_ctrls = self.fk_ctrls
    def create_guides(self, pos=None):
        if pos is None:
            pos = [(0,0,0), (0,10,0)]

        self.guide_grp = pm.createNode('transform', name=f'{self.name}_guide_grp')
        pm.parent(self.guide_grp, utils.get_group(df.rig_guides_grp))

        self.guides = utils.create_guide_chain(self.name, self.num, pos, parent=self.guide_grp)
        pm.parent(self.guides, self.guide_grp)

        pm.select(clear=True)

        # Add guides
        if self.meta:
            self.save_metadata()

    def create_joints(self):
        self.joints = []

        self.joints = utils.create_joints_from_guides(self.name, self.guides,
                                                      aimVector=self.jnt_orient_main, upVector=self.jnt_orient_secondary,
                                                      suffix=df.skin_sff, endJnt=False)

        # Create hip at the beginning of joint chain
        self.hip_jnt = pm.createNode('joint', name=f'{self.name[0]}_hip{df.skin_sff}{df.jnt_sff}')
        self.hip_jnt.radius.set(self.joints[0].radius.get())
        pm.matchTransform(self.hip_jnt, self.joints[0])

        # Parent Joints under Joint_grp
        self.joints_grp = pm.createNode('transform', name=f'{self.name}_{df.joints_grp}')
        pm.parent(self.joints[0], self.hip_jnt, self.joints_grp)
        pm.parent(self.joints_grp, utils.get_group(df.joints_grp))

        # Add joints
        if self.meta:
            self.save_metadata()

    def rig(self):
        self.fk_ctrls = utils.create_fk_ctrls(self.joints, skipEnd=False, shape='square')
        self.hip_ctrl = utils.create_fk_ctrls(self.hip_jnt, shape='star', scale=1.5)

        # Color ctrls
        set_color(self.fk_ctrls, viewport='yellow')
        set_color(self.hip_ctrl, viewport='green')

        # Parent hip ctrl grp under pelvis ctrl
        pm.parent(self.hip_ctrl.getParent(1), self.fk_ctrls[0])

        # Parent spine ctrl under Root
        pm.parent(self.fk_ctrls[0].getParent(1), utils.get_group(df.root))

        self.control_grp = self.fk_ctrls[0].getParent(1)
        self.all_ctrls = self.fk_ctrls

        self.connect_children()
        # Add joints
        if self.meta:
            self.save_metadata()