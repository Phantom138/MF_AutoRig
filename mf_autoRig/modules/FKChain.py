from mf_autoRig.modules.Module import Module
import pymel.core as pm
from mf_autoRig import utils
from mf_autoRig.utils import defaults as df


class FKChain(Module):
    meta_args = {
        'creation_attrs': {
            **Module.meta_args['creation_attrs'],
            'num': {'attributeType': 'long'}
        },

        'module_attrs': {
            **Module.meta_args['module_attrs'],
        },

        'config_attrs': {
            **Module.meta_args['config_attrs'],
            'end_joint': {'attributeType': 'bool'}
        },
        'info_attrs': {
            **Module.meta_args['info_attrs'],
            'guides': {'attributeType': 'message', 'm': True},
            'joints': {'attributeType': 'message', 'm': True},
            'fk_ctrls': {'attributeType': 'message', 'm': True},
        }
    }

    connectable_to = ['Spine']  # List of modules this module can connect to

    def __init__(self, name, meta=True, **kwargs):
        super().__init__(name, self.meta_args, meta)

        # Get attrs from kwargs
        default_args = {'num': 4}
        default_args.update(kwargs)

        for key, value in default_args.items():
            setattr(self, key, value)

        self.joints = []
        self.guides = []
        self.fk_ctrls = []
        self.end_joint = False

        self.reset()

    def reset(self):
        super().reset()
        self.joints = []
        self.guides = []
        self.fk_ctrls = []

    def update_from_meta(self, only=None):
        super().update_from_meta(only)
        if self.fk_ctrls:
            self.all_ctrls.extend(self.fk_ctrls)

    def create_guides(self, pos=None):
        if pos is None:
            pos = [(0, 0, 0), (0, 5, 0)]

        # Create guides
        self.guide_grp = pm.createNode('transform', name=f'{self.name}_guide_grp')
        self.guides = utils.create_guide_chain(self.name, self.num, pos, parent=self.guide_grp)

        # pm.parent(self.guides, self.guide_grp)
        pm.parent(self.guide_grp, utils.get_group(df.rig_guides_grp))

        # Save guides
        if self.meta:
            self.save_metadata()

    def create_joints(self):
        self.joints_grp = pm.createNode('transform', name=f'{self.name}_{df.joints_grp}')
        self.joints = utils.create_joints_from_guides(self.name, self.guides,
                                                      aimVector=self.jnt_orient_main,
                                                      upVector=self.jnt_orient_secondary,
                                                      endJnt=self.end_joint)

        pm.parent(self.joints_grp, utils.get_group(df.joints_grp))
        pm.parent(self.joints[0], self.joints_grp)

        # Save joints
        if self.meta:
            self.save_metadata()

    def rig(self):
        self.control_grp = pm.createNode('transform', name=f'{self.name}{df.control_grp}')
        pm.parent(self.control_grp, utils.get_group(df.root))

        self.fk_ctrls = utils.create_fk_ctrls(self.joints, skipEnd=self.end_joint)
        pm.parent(self.fk_ctrls[0].getParent(1), self.control_grp)


        utils.auto_color(self.fk_ctrls)
        self.all_ctrls = self.fk_ctrls

        if self.meta:
            self.save_metadata()

    def connect(self, dest):
        if not self.check_if_connected(dest):
            pm.warning(f"{self.name} not connected to {dest.name}")
            return

        pm.parentConstraint(dest.joints[self.attach_index], self.fk_ctrls[0].getParent(1), mo=True)