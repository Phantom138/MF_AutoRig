from dataclasses import dataclass

import pymel.core as pm

import importlib
import mf_autoRig.lib.useful_functions

importlib.reload(mf_autoRig.lib.useful_functions)
from mf_autoRig.lib.useful_functions import *
from mf_autoRig.lib.color_tools import set_color
import mf_autoRig.modules.meta as mdata
from mf_autoRig.modules.Module import Module
from mf_autoRig.modules.Foot import Foot

class Limb(Module):
    meta_args = {
        'switch': {'attributeType': 'message'},
        'guides': {'attributeType': 'message', 'm': True},
        'joints': {'attributeType': 'message', 'm': True},
        'ik_joints': {'attributeType': 'message', 'm': True},
        'ik_ctrls': {'attributeType': 'message', 'm': True},
        'fk_joints': {'attributeType': 'message', 'm': True},
        'fk_ctrls': {'attributeType': 'message', 'm': True}
    }

    def __init__(self, name, meta=True):
        super().__init__(name, self.meta_args, meta)

        self.joints = None
        self.guides = None

        # IK FK stuff
        self.ik_joints = None
        self.ik_ctrls = None
        self.fk_joints = None
        self.fk_ctrls = None
        self.switch = None

        self.all_ctrls = []

        self.default_pin_value = 51

    @classmethod
    def create_from_meta(cls, metaNode):
        obj = super().create_from_meta(metaNode)
        # Get ikHandle
        iks = obj.ik_joints[0].message.listConnections(d=True, type='ikHandle')
        if len(iks) == 1:
            obj.ikHandle = iks[0]
        else:
            raise ValueError(f"{obj.name} has {len(iks)} IKHandles")

        # Recreate all_ctrls
        obj.all_ctrls = obj.fk_ctrls + obj.ik_ctrls
        obj.all_ctrls.append(obj.switch)

        return obj

    def create_guides(self, pos=None):
        """
        Creates guides between pos[0] and pos[1]
        Pos should be a list with two elements!
        """
        if pos is None:
            pos = [(0, 10, 0), (0, 0, 0)]

        self.guides = create_joint_chain(3, self.name, pos[0], pos[1], defaultValue=self.default_pin_value)

        pm.select(cl=True)

        if self.meta:
            self.save_metadata()

    def create_joints(self, mirror_from = None):
        self.joints = []

        # Create based on guides
        for i, tmp in enumerate(self.guides):
            trs = pm.xform(tmp, q=True, t=True, ws=True)

            sff = df.skin_sff
            # Last joint has end suffix
            if i == len(self.guides) - 1:
                sff = df.end_sff

            jnt = pm.joint(name=f'{self.name}{i + 1:02}{sff}{df.jnt_sff}', position=trs)

            self.joints.append(jnt)

        # Orient joints
        pm.joint(self.joints[0], edit=True, orientJoint='yzx', secondaryAxisOrient='zup', children=True)
        pm.joint(self.joints[-1], edit=True, orientJoint='none')

        # Clear Selection
        pm.select(clear=True)

        if self.meta:
            self.save_metadata()

    def rig(self, ik_ctrl_trans=False):
        self.skin_jnts = self.joints[:-1]
        # IK
        self.ik_joints, self.ik_ctrls, self.ik_ctrls_grp, self.ikHandle = create_ik(self.joints, ik_ctrl_trans)
        # FK
        self.fk_joints = create_fk_jnts(self.joints)
        self.fk_ctrls = create_fk_ctrls(self.fk_joints)

        self.ikfk_constraints = constraint_ikfk(self.joints, self.ik_joints, self.fk_joints)
        self.switch = ikfk_switch(self.ik_ctrls_grp, self.fk_ctrls, self.ikfk_constraints, self.joints[-1])

        self.all_ctrls.extend(self.fk_ctrls)
        self.all_ctrls.extend(self.ik_ctrls)
        self.all_ctrls.append(self.switch)

        self.__clean_up()

        if self.meta:
            self.save_metadata()

        pm.select(clear=True)

    def __clean_up(self):
        # Color ctrls based on side
        if self.side == 'R':
            set_color(self.fk_ctrls, viewport='red')
            set_color(self.ik_ctrls, viewport='red')
            set_color(self.switch, viewport='orange')

        elif self.side == 'L':
            set_color(self.fk_ctrls, viewport='blue')
            set_color(self.ik_ctrls, viewport='blue')
            set_color(self.switch, viewport='cyan')

        # Group joints only if group isn't already there
        joint_grp_name = f'{self.name}_{df.joints_grp}'
        joint_grp = get_group(joint_grp_name)
        pm.parent(self.fk_joints[0], self.ik_joints[0], self.joints[0], joint_grp)

        # Group joint grp under Joints grp
        pm.parent(joint_grp, get_group(df.joints_grp))

        # Hide ik fk joints
        self.fk_joints[0].visibility.set(0)
        self.ik_joints[0].visibility.set(0)

        # Move ik control grp under root_ctrl
        root_ctrl = get_group(df.root)
        pm.parent(self.ik_ctrls_grp, root_ctrl)

        switch_ctrl_grp = self.switch.getParent(1)
        pm.parent(switch_ctrl_grp, root_ctrl)

        pm.parent(self.fk_ctrls[0].getParent(1), root_ctrl)

        # Clear selection
        pm.select(clear=True)

    def mirror(self, rig=True):
        """
        Return a class of the same type that is mirrored on the YZ plane
        """
        #TODO: add possibility to mirror on different plane
        name = self.name.replace(f'{self.side}_', f'{self.side.opposite}_')
        mir_module = self.__class__(name)

        # Mirror Joints
        mirrored_jnts = pm.mirrorJoint(self.joints[0], mirrorYZ=True, mirrorBehavior=True,
                                       searchReplace=(self.side, self.side.opposite))
        mir_joints = list(map(pm.PyNode, mirrored_jnts))
        mir_module.joints = []
        for obj in mir_joints:
            if isinstance(obj, pm.nt.Joint):
                mir_module.joints.append(obj)
            else:
                pm.delete(obj)
        if rig:
            mir_module.rig()

        # Mirror Ctrls
        for src, dst in zip(self.all_ctrls, mir_module.all_ctrls):
            control_shape_mirror(src, dst)

        return mir_module



class Arm(Limb):
    def __init__(self, name, meta=True):
        super().__init__(name, meta)
        self.default_pin_value = 51

    def connect(self, dest):
        if self.check_if_connected(dest):
            pm.warning(f"{self.name} already connected to {dest.name}")
            return

        ctrl_grp = self.fk_ctrls[0].getParent(1)

        pm.parent(ctrl_grp, dest.clavicle_ctrl)
        pm.parentConstraint(dest.joints[-1], self.ik_joints[0])

        self.connect_metadata(dest)


class Leg(Limb):
    def __init__(self, name, meta=True):
        super().__init__(name, meta)
        self.default_pin_value = 49
        self.foot = Foot(f'{self.name}_foot', meta)

    @classmethod
    def create_from_meta(cls, metaNode):
        obj = super().create_from_meta(metaNode)

        # Get metadata for foot
        foot_metaNode = metaNode.affects.get()[0]
        obj.foot = Foot.create_from_meta(foot_metaNode)

        return obj

    def create_guides(self, pos=None):
        super().create_guides(pos)
        self.foot.create_guides(ankle_guide=self.guides[-1])

    def create_joints(self, mirror_from = None):
        super().create_joints(mirror_from)
        if mirror_from is None:
            self.foot.create_joints()

    def rig(self):
        super().rig(ik_ctrl_trans=True)
        self.foot.rig()
        self.foot.connect(self)

    def connect(self, dest):
        if self.check_if_connected(dest):
            pm.warning(f"{self.name} already connected to {dest.name}")
            return

        ctrl_grp = self.fk_ctrls[0].getParent(1)

        pm.parent(ctrl_grp, dest.hip_ctrl)
        pm.parentConstraint(dest.hip_ctrl, self.ik_joints[0], maintainOffset=True)

        self.connect_metadata(dest)

    def mirror(self):
        mir_module = super().mirror(rig=False)
        mir_module.foot = self.foot.mirror(rig=False)
        mir_module.rig()

        return mir_module
