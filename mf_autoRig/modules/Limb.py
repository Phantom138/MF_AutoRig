from mf_autoRig.utils.controllers_tools import save_curve_info, apply_curve_info
from mf_autoRig.utils.general import *
from mf_autoRig.utils.color_tools import set_color

from mf_autoRig.modules.Module import Module

import mf_autoRig.utils as utils
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
        default_pin_value (int): Default pin value fo joint creation.

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
        'creation_attrs': {
            **Module.meta_args['creation_attrs']
        },

        'module_attrs': {
            **Module.meta_args['module_attrs'],
        },

        'config_attrs': {
            **Module.meta_args['config_attrs'],
            'forearm_twist': {'attributeType': 'bool'},
            'world_ik': {'attributeType': 'bool'}
        },
        'info_attrs':{
            **Module.meta_args['info_attrs'],
            'switch': {'attributeType': 'message'},
            'guides': {'attributeType': 'message', 'm': True},
            'joints': {'attributeType': 'message', 'm': True},
            'ik_joints': {'attributeType': 'message', 'm': True},
            'ik_ctrls': {'attributeType': 'message', 'm': True},
            'fk_joints': {'attributeType': 'message', 'm': True},
            'fk_ctrls': {'attributeType': 'message', 'm': True}
        }
    }

    connectable_to = ['Clavicle', 'Spine']

    def __init__(self, name, meta=True):
        super().__init__(name, self.meta_args, meta)
        self.parent = None

        self.joints = []
        self.guides = []

        # IK FK stuff
        self.ik_joints = []
        self.ik_ctrls = []
        self.fk_joints = []
        self.fk_ctrls = []
        self.switch = []
        self.world_ik = False

        self.forearm_twist = False

        self.reset()


    def reset(self):
        super().reset()
        self.joints = []
        self.guides = []

        # IK FK stuff
        self.ik_joints = []
        self.ik_ctrls = []
        self.fk_joints = []
        self.fk_ctrls = []
        self.switch = []

        self.forearm_twist = False


    def update_from_meta(self):
        super().update_from_meta()

        if len(self.guides) != 3:
            log.warning(f"For {self.name}, couldn't find all guides. Found only: {self.guides}")
            self.guides = []

        #print(self.__dict__)
        if len(self.joints) != 0:
            # Get ikHandle
            iks = self.ik_joints[0].message.listConnections(d=True, type='ikHandle')
            if len(iks) == 1:
                self.ikHandle = iks[0]
            else:
                log.warning(f"{self.name} has {len(iks)} IKHandles")

            # Recreate all_ctrls
            self.all_ctrls = self.fk_ctrls + self.ik_ctrls
            self.all_ctrls.append(self.switch)

    def create_guides(self, pos=None):
        """
        Creates guides at positions specified by pos.
        """
        if pos is None:
            pos = [(0, 10, 0), (0, 5, 1), (0, 0, 0)]
        self.guide_grp = pm.createNode('transform', name=f'{self.name}_guide_grp')
        pm.parent(self.guide_grp, get_group(df.rig_guides_grp))

        self.guides = utils.create_guide_chain(self.name, 3, pos, parent=self.guide_grp)
        pm.parent(self.guides, self.guide_grp)


        pm.select(cl=True)

        if self.meta:
            self.save_metadata()

    def mirror_guides(self):
        mir_module = super().mirror_guides()
        # Particularity for Limb, secondary axis stays the same
        mir_module.jnt_orient_secondary = self.jnt_orient_secondary
        self.save_metadata()
        return mir_module

    def create_joints(self, mirror_from = None):
        self.joints = utils.create_joints_from_guides(self.name, self.guides,
                                                      aimVector=self.jnt_orient_main, upVector=self.jnt_orient_secondary)

        if self.meta:
            self.save_metadata()

    def rig(self):
        self.skin_jnts = self.joints[:-1]
        # IK
        self.ik_joints, self.ik_ctrls, self.ik_ctrls_grp, self.ikHandle = utils.create_ik(self.joints, world_ik=self.world_ik)
        # FK
        self.fk_joints = utils.create_fk_jnts(self.joints)
        self.fk_ctrls = utils.create_fk_ctrls(self.fk_joints)

        self.ikfk_constraints = utils.constraint_ikfk(self.joints, self.ik_joints, self.fk_joints)
        self.switch = utils.ikfk_switch(self.ik_ctrls_grp, self.fk_ctrls, self.ikfk_constraints, self.joints[-1])

        self.all_ctrls.extend(self.fk_ctrls)
        self.all_ctrls.extend(self.ik_ctrls)
        self.all_ctrls.append(self.switch)

        self.__clean_up()

        if self.forearm_twist:
            self.__do_forearm_twist()

        self.connect_children()

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
        self.joints_grp = get_group(joint_grp_name)
        pm.parent(self.fk_joints[0], self.ik_joints[0], self.joints[0], self.joints_grp)

        # Group joint grp under Joints grp
        pm.parent(self.joints_grp, get_group(df.joints_grp))

        # Hide ik fk joints
        self.fk_joints[0].visibility.set(0)
        self.ik_joints[0].visibility.set(0)

        # Create Control Group with ik, fk ctrls and switch
        self.control_grp = pm.createNode('transform', name=f'{self.name}{df.control_grp}')
        pm.parent(self.ik_ctrls_grp, self.fk_ctrls[0].getParent(1), self.switch.getParent(1), self.control_grp)

        # Parent group under root
        root_ctrl = get_group(df.root)
        pm.parent(self.control_grp, root_ctrl)

        # Clear selection
        pm.select(clear=True)

    def __do_forearm_twist(self):
        # Get first hand from the children
        hand = None
        for child in self.children:
            if child.moduleType == 'Hand':
                hand = child
                break
        if hand is None:
            log.warning(f'Cannot do forearm twist for {self.name}, no hand found in children')
            return

        # Create twist joint and parent it under the elbow
        twist_jnt = pm.createNode('joint', n=self.name + '_twist_skin_jnt')
        twist_jnt.radius.set(self.joints[1].radius.get())

        _tmp_const = pm.parentConstraint(self.joints[1], self.joints[-1], twist_jnt)
        pm.delete(_tmp_const)

        pm.parent(twist_jnt, self.joints[1])
        pm.makeIdentity(twist_jnt, apply=True, r=True)
        # pm.joint(twist_jnt, orientation=(0,0,0), edit=True)
        # twist_jnt.jointOrient.set(0,0,0)

        # Create locator at arm end
        wrist_aim_loc = pm.spaceLocator(name = self.name + '_wrist_aim_loc')
        pm.matchTransform(wrist_aim_loc, self.joints[-1])
        # Offset on Z axis
        pm.move(wrist_aim_loc, self.jnt_orient_third * -2, relative=True, objectSpace=True)

        # Parent to hand
        pm.parentConstraint(hand.hand_jnts[0], wrist_aim_loc, maintainOffset=True)

        pm.select(clear=True)

        # Create aim constraint and aim jnt
        aim_jnt = pm.createNode('joint', n=self.name + '_wrist_aim_jnt')
        aim_jnt.radius.set(self.joints[-1].radius.get())
        pm.matchTransform(aim_jnt, self.joints[-1])
        pm.makeIdentity(aim_jnt, apply=True, r=True)
        pm.parent(aim_jnt, self.joints[-1])

        pm.aimConstraint(self.joints[1], aim_jnt, aimVector=self.jnt_orient_main * -1, upVector=self.jnt_orient_third * -1, worldUpType='object', worldUpObject=wrist_aim_loc)

        # Connect aim_jnt rotataion to twist jnt
        mult_divide = pm.createNode('multiplyDivide', n=self.name + '_twist_mult')
        mult_divide.input2Y.set(0.5) # divide by 2

        aim_jnt.rotateY.connect(mult_divide.input1Y)
        mult_divide.outputY.connect(twist_jnt.rotateY)

        # Create drivers grp
        self.drivers_grp = pm.createNode('transform', name=f'{self.name}_{df.drivers_grp}')
        pm.parent(self.drivers_grp, get_group(df.drivers_grp))
        pm.parent(wrist_aim_loc, self.drivers_grp)



    def connect(self, dest):
        if not self.check_if_connected(dest):
            log.warning(f"{self.name} not connected to {dest.name}")
            return

        dest_class = dest.__class__.__name__

        if dest_class == 'Spine':
            log.info(f"Connecting {self.name} to {dest_class}.{self.attach_index}")

            if self.attach_index != 0:
                pm.parentConstraint(dest.joints[-1], self.ik_joints[0], maintainOffset=True)
                pm.parentConstraint(dest.joints[-1], self.fk_ctrls[0].getParent(1), maintainOffset=True)

            else:
                # Connecting hip
                pm.parentConstraint(dest.joints[0], self.fk_ctrls[0].getParent(1), maintainOffset=True)
                pm.parentConstraint(dest.hip_ctrl, self.ik_joints[0], maintainOffset=True)

            # else:
            #     raise NotImplementedError(f"Method for attaching {self.name} to point {attach_pt} from {dest_class} not implemented yet.")

        # Connect to clavicle
        if dest_class == 'Clavicle':
            log.info(f"Connecting {self.name} to {dest.name}")

            ctrl_grp = self.fk_ctrls[0].getParent(1)

            # pm.matchTransform(ctrl_grp, dest.joints[-1], position=True)
            pm.parentConstraint(dest.clavicle_ctrl, ctrl_grp, maintainOffset=True)
            pm.parentConstraint(dest.joints[-1], self.ik_joints[0])


