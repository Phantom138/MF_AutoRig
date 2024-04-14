from pprint import pprint

import pymel.core as pm

from mf_autoRig.utils.color_tools import auto_color
from mf_autoRig.utils.useful_functions import *
from mf_autoRig.modules.Module import Module

import mf_autoRig.utils.defaults as df
import mf_autoRig.utils.mirrorJoint as mirrorUtils


class FKFoot(Module):
    meta_args = {
        'guides': {'attributeType': 'message', 'm': True},
        'joints': {'attributeType': 'message', 'm': True},
        'fk_ctrls': {'attributeType': 'message', 'm': True},
    }

    connectable_to = ['Limb']

    def __init__(self, name, meta=True):
        super().__init__(name, self.meta_args, meta)

        self.reset()

    def reset(self):
        super().reset()

        self.guides = None

        self.joints = None
        self.fk_ctrls = None
        self.locators_guides = None
        self.locators = None
        self.all_ctrls = []

        self.control_grp = None
        self.joints_grp = None


    def update_from_meta(self):
        super().update_from_meta()
        self.all_ctrls = self.fk_ctrls

    def create_guides(self, ankle_guide=None, pos=None):
        self.guides = []
        if pos is None:
            pos = [(0,0,0), (0,-2,5), (0,-4,10)]

        if ankle_guide is not None:
            pos = pos[1:]

        # Create joint guides at the right pos
        for i,p in enumerate(pos):
            jnt = pm.createNode('joint', name=f"{self.name}{i+1:02}_guide{df.jnt_sff}")
            pm.xform(jnt, translation=p)

            self.guides.append(jnt)

        # Group guides
        self.guides_grp = pm.createNode('transform', name=f'{self.name}_guides_grp')
        pm.parent(self.guides, self.guides_grp)
        pm.parent(self.guides_grp, get_group(df.rig_guides_grp))

        # Constraint to ankle if there
        if ankle_guide is not None:
            pm.parentConstraint(ankle_guide, self.guides_grp, skipRotate=['x', 'y', 'z'], maintainOffset=False)
            self.guides.insert(0, ankle_guide)

        if self.meta:
            self.save_metadata()

    def create_joints(self):
        # Get just the guides for the joints
        self.joints = create_joints_from_guides(self.name, self.guides)

        # Cleanup
        self.__joints_cleanup()

    def __joints_cleanup(self):
        # Group joints
        self.joints_grp = pm.createNode('transform', name=f'{self.name}_{df.joints_grp}')
        pm.parent(self.joints[0], self.joints_grp)
        pm.parent(self.joints_grp, get_group(df.joints_grp))

        if self.meta:
            self.save_metadata()


    def rig(self):
        self.skin_jnts = self.joints[:-1]

        # Create FK
        self.fk_ctrls = create_fk_ctrls(self.joints)

        # Color
        auto_color(self.fk_ctrls)

        # Group controllers
        self.control_grp = pm.createNode('transform', name=f'{self.name}{df.control_grp}')
        pm.parent(self.fk_ctrls[0].getParent(1), self.control_grp)
        pm.parent(self.control_grp, get_group(df.root))

        self.all_ctrls = self.fk_ctrls
        if self.meta:
            self.save_metadata()

    def connect(self, dest):
        if self.check_if_connected(dest):
            pm.warning(f"{self.name} already connected to {dest.name}")
            return

        ctrl_grp = self.fk_ctrls[0].getParent(1)

        pm.pointConstraint(dest.joints[-1], ctrl_grp, maintainOffset=True)

        self.connect_metadata(dest)

    def mirror(self, rig=True):
        name = self.name.replace(f'{self.side}_', f'{self.side.opposite}_')
        mir_module = self.__class__(name)

        # Mirror Joints
        mir_module.joints = mirrorUtils.mirrorJoints(self.joints, (self.side.side, self.side.opposite))
        mir_module.__joints_cleanup()


        if rig:
            mir_module.rig()

        # Mirror Ctrls
        for src, dst in zip(self.fk_ctrls, mir_module.fk_ctrls):
            control_shape_mirror(src, dst)

        # Do mirror connection for metadata
        self.metaNode.mirrored_to.connect(mir_module.metaNode.mirrored_from)

        return mir_module