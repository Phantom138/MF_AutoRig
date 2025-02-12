from mf_autoRig import log
from mf_autoRig.utils.general import *
import mf_autoRig.utils.defaults as df
import mf_autoRig.utils as utils
from mf_autoRig.utils.color_tools import set_color
from mf_autoRig.modules.Module import Module

class Clavicle(Module):
    meta_args = {
        'creation_attrs':{
            **Module.meta_args['creation_attrs']
        },

        'module_attrs': {
            **Module.meta_args['module_attrs'],
        },

        'config_attrs':{
            **Module.meta_args['config_attrs'],
            'auto_clavicle': {'attributeType': 'bool'}
        },
        'info_attrs':{
            **Module.meta_args['info_attrs'],
            'guides': {'attributeType': 'message', 'm': True},
            'joints': {'attributeType': 'message', 'm': True},
            'clavicle_ctrl': {'attributeType': 'message'},
        }
    }

    connectable_to = ['Spine']

    def __init__(self, name, meta=True):
        super().__init__(name, self.meta_args, meta)

        self.reset()

    def reset(self):
        super().reset()
        self.auto_clavicle = False

        self.clavicle_ctrl = None
        self.joints = []
        self.guides = []

        self.control_grp = None
        self.joints_grp = None

    def update_from_meta(self):
        super().update_from_meta()
        if self.clavicle_ctrl is not None:
            self.all_ctrls.append(self.clavicle_ctrl)

    def create_guides(self, pos = None):
        """
        Creates clavicle guides at pos, pos should be a list of xyz values
        """
        # self.guides = []
        if pos is None:
            pos = [(0,0,0), (5,0,0)]

        self.guides = utils.create_guide_chain(self.name, 2, pos)

        self.guide_grp = pm.group(self.guides, name=f'{self.name}_guides{df.grp_sff}')
        pm.parent(self.guide_grp, get_group(df.rig_guides_grp))

        # Clear Selection
        pm.select(clear=True)

        # Save guides
        if self.meta:
            self.save_metadata()

    def create_joints(self, shoulder=None):
        """
        Create joints from starting guide to shoulder
        """
        if shoulder is not None:
            # Add shoulder to guides
            self.guides.append(shoulder)

        # Create joints
        self.joints = utils.create_joints_from_guides(self.name, self.guides,
                                                      aimVector=self.jnt_orient_main, upVector=self.jnt_orient_secondary)

        # Parent Joints under Joint_grp
        pm.parent(self.joints[0], get_group(df.joints_grp))

        #Save joints
        if self.meta:
            self.save_metadata()

    def rig(self):
        if len(self.joints) != 2:
            pm.error('Can only create clavicle with 2 joints')

        # Create ctrl and group
        axis = utils.get_joint_orientation(self.joints[0], self.joints[1])
        clav = utils.CtrlGrp(self.name, 'arc', axis=axis)

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

        pm.select(clear=True)

        # Create clavicle Control group for the controllers
        self.control_grp = pm.createNode('transform', name=f'{self.name}{df.control_grp}')
        pm.parent(clav.grp, self.control_grp)

        # Group control_grp under root
        pm.parent(self.control_grp, get_group(df.root))

        self.joints_grp = self.joints[0]

        if self.auto_clavicle:
            self.__auto_clavicle()

        self.connect_children()
        if self.meta:
            self.save_metadata()
    
    def __auto_clavicle(self):
        # Get first arm from the children
        arm = None
        for child in self.children:
            if child.moduleType == 'Limb':
                arm = child
                break
                
        if arm is None:
            log.warning(f'Cannot do auto clavicle for {self.name}, no arm found in children')
            return
        
        # Auto clavicle setup
        # Duplicate arm ik chain
        self.ik_jnts_guides = utils.duplicate_joints(arm.ik_joints, '_guide')
        if len(self.ik_jnts_guides) != 3:
            log.error("Only joint chains of 3 supported")

        # Do ik for duplicated joints
        handle_name = get_base_name(self.ik_jnts_guides[0].name()) + "_guides" + "_ikHandle"
        dup_ikHandle = pm.ikHandle(name=handle_name, startJoint=self.ik_jnts_guides[0],
                                   endEffector=self.ik_jnts_guides[2], solver='ikRPsolver')

        ik_ctrl = arm.ik_ctrls[0]
        pole_ctrl = arm.ik_ctrls[1]
        pm.parentConstraint(ik_ctrl, dup_ikHandle[0])
        pm.poleVectorConstraint(pole_ctrl, dup_ikHandle[0])

        # AUTO CLAVICLE LOGIC
        # Create joint at clavicle start
        clav_pos = self.joints[0].getTranslation(space='world')
        self.clav_aim_jnt = pm.createNode("joint", name=self.name + '_aim')
        self.clav_aim_jnt.setTranslation(clav_pos)

        # Create group for clav aim jnt
        clav_aim_grp = pm.createNode('transform', name=self.name + '_aim_grp')
        pm.matchTransform(clav_aim_grp, self.clav_aim_jnt)
        pm.parent(self.clav_aim_jnt, clav_aim_grp)

        # Clavicle aim end locator
        elbow_posV = dt.Vector(self.ik_jnts_guides[1].getTranslation(space='world'))
        clav_posV = dt.Vector(clav_pos)
        clav_aim_end_pos = (elbow_posV - clav_posV) / 2 + clav_posV
        self.clav_aim_end_loc = pm.spaceLocator(name=self.name + '_aim_end_loc')
        self.clav_aim_end_loc.setTranslation(clav_aim_end_pos.get())

        # Elbow locator
        self.elbow_loc = pm.spaceLocator(name='elbow_loc')
        pm.matchTransform(self.elbow_loc, self.ik_jnts_guides[1], position=True)
        pm.parent(self.elbow_loc, self.ik_jnts_guides[1])

        self.clav_aim_loc = pm.spaceLocator(name=self.name + '_aim_loc')
        pointConst = pm.pointConstraint(self.elbow_loc, self.clav_aim_end_loc, self.clav_aim_loc)

        # Add attribute for auto clavicle strength
        self.clavicle_ctrl.addAttr("autoClavicle", attributeType="float", defaultValue=1,
                                            minValue=0, maxValue=1, keyable=True)

        # Multiply with ikfk switch reverse
        ikfk_reverse = arm.switch.IkFkSwitch.listConnections(type='reverse')[0]
        mult_divide = pm.createNode('multiplyDivide', name=self.name + '_mult')

        ikfk_reverse.outputX.connect(mult_divide.input1X)
        self.clavicle_ctrl.autoClavicle.connect(mult_divide.input2X)

        mult_divide.outputX.connect(pointConst.getWeightAliasList()[0])

        # Clavicle aim
        pm.aimConstraint(self.clav_aim_loc, self.clav_aim_jnt, aim=(0, 1, 0), upVector=(1, 0, 0),
                         worldUpVector=(0, 1, 0))

        # Connect aim to offset group of main clav controller
        clavicle_offset = create_offset_grp(self.clavicle_ctrl)
        pm.orientConstraint(self.clav_aim_jnt, clavicle_offset, maintainOffset=True)
        
        
    def connect(self, torso, force=False):
        if not self.check_if_connected(torso):
            pm.warning(f"{self.name} not connected to {torso.name}")
            return

        pm.parentConstraint(torso.fk_ctrls[-1], self.control_grp.getChildren()[0], maintainOffset=True)

        if self.auto_clavicle:
            # Connect Guide Ik arm
            pm.parentConstraint(torso.joints[-1], self.ik_jnts_guides[0], maintainOffset=True)

            pm.parentConstraint(torso.joints[-1], self.clav_aim_jnt.getParent(1), maintainOffset=True)
            pm.parent(self.clav_aim_end_loc, torso.joints[-1])
