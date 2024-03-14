from pprint import pprint

import pymel.core as pm

from mf_autoRig.lib.get_curve_info import save_curve_info, apply_curve_info
from mf_autoRig.lib.useful_functions import *
from mf_autoRig.lib.color_tools import set_color
import mf_autoRig.modules.meta as mdata
from mf_autoRig.modules import module_tools
from mf_autoRig.modules.Module import Module
from mf_autoRig.modules.Foot import Foot
import mf_autoRig.lib.mirrorJoint as mirrorUtils
from mf_autoRig import log

class Limb(Module):
    """
    Class representing a limb module for character rigging.

    Attributes:
        meta_args (dict): Metadata attributes for the limb.
        joints (list): List of joint objects for the limb.
        guides (list): List of guide objects for the limb.
        ik_joints (list): List of joints for the inverse kinematics (IK) setup.
        ik_ctrls (list): List of controls for the IK setup.
        fk_joints (list): List of joints for the forward kinematics (FK) setup.
        fk_ctrls (list): List of controls for the FK setup.
        switch (pymel.core.PyNode): Control used for switching between IK and FK setups.
        all_ctrls (list): List of all controls in the limb.
        default_pin_value (int): Default pin value for joint creation.

    Methods:
        __init__(self, name, meta=True):
            Initializes a Limb instance.

        create_from_meta(cls, metaNode):
            Creates a Limb instance from existing metadata node.

        create_guides(self, pos=None):
            Creates guides for the limb based on the specified positions.

        create_joints(self, mirror_from=None):
            Creates joints for the limb based on the guides.

        rig(self, ik_ctrl_trans=False):
            Sets up the rigging for the limb, including IK and FK setups.

        __clean_up(self):
            Performs clean-up operations for the limb rigging.

        mirror(self, rig=True):
            Creates a mirrored instance of the Limb class.

    """
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
        mir_module.joints = mirrorUtils.mirrorJoints(self.joints[0], (self.side, self.side.opposite))

        if rig:
            mir_module.rig()

        # Mirror Ctrls
        for src, dst in zip(self.all_ctrls, mir_module.all_ctrls):
            control_shape_mirror(src, dst)

        return mir_module

    def delete(self, preview=False, keep_meta_node=False):
        """
        Deletes the limb and its associated objects.
        """
        # TODO: make sure that it doesn't delete extra stuff that is parented to the ctrls
        # Get ikfk_switch group
        switch_grp = self.switch.getParent(1)

        # Get ik control group
        ik_control_grp = self.ik_ctrls[0].getParent(2)

        # Get fk control group
        fk_ctrl_grp = self.fk_ctrls[0].getParent(1)

        # Get joint group
        joint_grp = self.joints[0].getParent(1)

        # Get guides
        try:
            guides = self.guides
        except:
            guides = []

        if keep_meta_node:
            # HACK: Create empty transform and connect it to metaNode so that when deleting the module,
            #       the metaNode is not deleted
            tmp = pm.createNode('transform', name=f'{self.name}_TEMP_NODE')
            self.metaNode.addAttr('TEMP_NODE', at='message')
            tmp.message.connect(self.metaNode.TEMP_NODE)

        # Delete stuff
        to_delete = [switch_grp, ik_control_grp, fk_ctrl_grp, joint_grp, guides]
        if preview is False:
            pm.delete(to_delete)
        else:
            print(to_delete)

        if keep_meta_node:
            # Disconnect tmp from metaNode
            tmp.message.disconnect(self.metaNode.TEMP_NODE)
            pm.delete(tmp)
            self.metaNode.deleteAttr('TEMP_NODE')

    def edit(self):
        # TODO: Make sure all controls are zeored out!!
        self.edit_mode = True
        # Save edited curves
        self.curves_info = save_curve_info(self.all_ctrls)

        # Create guides where joints are
        edit_locators = []
        for jnt in self.joints:
            loc = pm.spaceLocator(name='temp_loc')
            pm.matchTransform(loc, jnt)
            edit_locators.append(loc)

        for i in range(len(edit_locators) - 1, 0, -1):
            pm.parent(edit_locators[i], edit_locators[i - 1])

        # Destroy rig
        self.delete(keep_meta_node=True)

        # Recreates class
        self.__init__(self.name, meta=self.metaNode)

        # Create guides
        self.guides = edit_locators

    def apply_edit(self):
        if self.edit_mode is False:
            log.warning(f"{self.name} not in edit mode!")
            return

        self.create_joints()
        self.rig()
        apply_curve_info(self.all_ctrls, self.curves_info)
        # Delete guides
        pm.delete(self.guides)
        self.guides = []


class Arm(Limb):

    connectable_to = ['Clavicle']
    def __init__(self, name, meta=True):
        super().__init__(name, meta)
        self.default_pin_value = 51

    def connect(self, dest):
        if self.check_if_connected(dest):
            log.warning(f"{self.name} already connected to {dest.name}")
            return

        ctrl_grp = self.fk_ctrls[0].getParent(1)
        print(ctrl_grp, dest.joints[-1])
        pm.matchTransform(ctrl_grp, dest.joints[-1], position=True)
        pm.parent(ctrl_grp, dest.clavicle_ctrl)
        pm.parentConstraint(dest.joints[-1], self.ik_joints[0])

        self.connect_metadata(dest)

    def apply_edit(self):
        super().apply_edit()
        # Re-do connections
        if len(self.metaNode.affectedBy.get()) != 1:
            return

        connection = self.metaNode.affectedBy.get()[0]
        self.metaNode.affectedBy.disconnect()
        self.connect(module_tools.createModule(connection))

class Leg(Limb):
    """
    Class representing a leg module for character rigging, inheriting from Limb.

    Attributes:
        foot (Foot): Instance of the Foot class associated with the leg.

    Methods:
        __init__(self, name, meta=True):
            Initializes a Leg instance.

        create_from_meta(cls, metaNode):
            Creates a Leg instance from existing metadata node.

        create_guides(self, pos=None):
            Creates guides for the leg, including the foot guide.

        create_joints(self, mirror_from=None):
            Creates joints for the leg, including the foot joints.

        rig(self):
            Sets up the rigging for the leg, including the foot rigging.

        connect(self, dest):
            Connects the leg to the specified destination module.

        mirror(self):
            Creates a mirrored instance of the Leg class.
    """
    connectable_to = ['Spine']
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
        self.foot.mirror(rig=False, outputModule=mir_module.foot)
        mir_module.rig()

        return mir_module
