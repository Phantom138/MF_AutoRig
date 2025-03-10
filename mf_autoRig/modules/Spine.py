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
            'ctrls_in_world': {'attributeType': 'bool'}
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

        self.ctrls_in_world = False
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
        pm.matchTransform(self.hip_jnt, self.joints[0], pos=True, rot=not self.ctrls_in_world)

        # Parent Joints under Joint_grp
        self.joints_grp = pm.createNode('transform', name=f'{self.name}_{df.joints_grp}')
        pm.parent(self.joints[0], self.hip_jnt, self.joints_grp)
        pm.parent(self.joints_grp, utils.get_group(df.joints_grp))

        # Add joints
        if self.meta:
            self.save_metadata()

    def __fk_spine(self):
        # Duplicate and name properly
        self.fk_joints = utils.duplicate_joints(self.joints,"_dup")
        for i,jnt in enumerate(self.fk_joints):
            jnt.rename(f'{self.name}{i+1:02}{df.fk_sff}{df.jnt_sff}')
        pm.parent(self.fk_joints[0], self.drivers_grp)

        # Todo: fk_joints[1:] is needed with the cog setup rn. Maybe theres a better way to do this?
        self.fk_ctrls = utils.create_fk_ctrls(self.fk_joints[1:], skipEnd=True, shape='square', match_rot=not self.ctrls_in_world)
        set_color(self.fk_ctrls, viewport='yellow')

        self.fk_ctrl_grp = self.fk_ctrls[0].getParent(1)
        pm.parent(self.fk_ctrl_grp, self.control_grp)
        # # Parent spine ctrl under Root
        # pm.parent(self.fk_ctrls[0].getParent(1), utils.get_group(df.root))

    def __ik_spine(self):
        # Duplicate and name properly
        self.ik_joints = utils.duplicate_joints(self.joints,"_tmp")
        for i,jnt in enumerate(self.ik_joints):
            jnt.rename(f'{self.name}{i+1:02}{df.ik_sff}{df.jnt_sff}')

        pm.parent(self.ik_joints[0], self.drivers_grp)
        # Create ik_ctrl_grp
        self.ik_ctrl_grp = pm.createNode('transform',name=f'{self.name}{df.ik_sff}{df.control_grp}')
        pm.parent(self.ik_ctrl_grp, self.control_grp)

        # Ik Handle
        ikHandle, _, curve = pm.ikHandle(startJoint=self.ik_joints[0], endEffector=self.ik_joints[-1], solver='ikSplineSolver',
                                         scv=False, pcv=False)
        ikHandle.rename(f'{self.name}_ikHandle')
        pm.parent(ikHandle,utils.get_group(df.ikHandle_grp))

        curve.rename(f'{self.name}_spine_ik_crv')
        pm.parent(curve, self.drivers_grp)


        guide_jnts = []
        self.ik_ctrls = []
        # Create locators for pos (ik_spine)
        # This is for connecting other modules to it
        # the reason this is to allow to offset the pivot of the ctrl
        self.ik_locators = []

        # self.ik_joints[len(self.ik_joints) // 2]
        for i,jnt in enumerate([self.ik_joints[0], self.ik_joints[-1]]):
            guide_jnt = pm.createNode('joint', name=f'{self.name}{df.ik_sff}_driver{i+1:02}_jnt')

            pm.matchTransform(guide_jnt, jnt)
            pm.parent(guide_jnt, self.drivers_grp)

            ctrl = utils.CtrlGrp(name=f'{self.name}{df.ik_sff}_driver{i+1:02}', shape='cube')
            # ctrl = utils.create_fk_ctrls(guide_jnt)
            pm.matchTransform(ctrl.grp, guide_jnt, pos=True, rotation = not self.ctrls_in_world)
            pm.parent(ctrl.grp, self.ik_ctrl_grp)

            loc = pm.spaceLocator(name=f'{self.name}{df.ik_sff}_driver{i+1:02}_loc')
            loc.v.set(0)
            pm.matchTransform(loc, ctrl.ctrl)
            pm.parent(loc, ctrl.ctrl)
            pm.parent(guide_jnt, loc)

            self.ik_locators.append(loc)
            self.ik_ctrls.append(ctrl.ctrl)
            guide_jnts.append(guide_jnt)

        pm.skinCluster(guide_jnts, curve, toSelectedBones=True)

        # Configure ik Handle
        ikHandle.dTwistControlEnable.set(1)
        ikHandle.dWorldUpType.set(4)
        ikHandle.dForwardAxis.set(2)
        ikHandle.dWorldUpAxis.set(3)
        ikHandle.dWorldUpVectorY.set(0)
        ikHandle.dWorldUpVectorEndY.set(0)
        ikHandle.dWorldUpVectorZ.set(1)
        ikHandle.dWorldUpVectorEndZ.set(1)

        guide_jnts[0].worldMatrix.connect(ikHandle.dWorldUpMatrix)
        guide_jnts[1].worldMatrix.connect(ikHandle.dWorldUpMatrixEnd)


    def __ik_fk_switch(self, switch_obj):
        # if not isinstance(other_constraints, list):
        #     other_constraints = [other_constraints]

        # Add ikfk switch attribute default: ik
        pm.addAttr(switch_obj, longName=df.ikfkSwitch_name, attributeType='float', min=0, max=1, defaultValue=0,
                   keyable=True)

        # Reverse node
        reverse_sw = pm.createNode('reverse', name=f'{self.name}_Ik_Fk_reverse')
        getattr(switch_obj, df.ikfkSwitch_name).connect(reverse_sw.inputX)

        # Get ports
        ik_port = reverse_sw.outputX
        fk_port = switch_obj.attr(df.ikfkSwitch_name)

        constraints = []
        for skin_jnt, fk_jnt, ik_jnt in zip(self.joints[:-1], self.fk_joints[:-1], self.ik_joints[:-1]):
            constraints.append(pm.parentConstraint(fk_jnt, ik_jnt, skin_jnt))

        # Do last joint
        point_cst = pm.pointConstraint(self.fk_joints[-1], self.ik_joints[-1], self.joints[-1])
        orient_cst = pm.orientConstraint(self.fk_joints[-1], self.ik_ctrls[-1], self.joints[-1])
        constraints.append(point_cst)
        constraints.append(orient_cst)

        for cst in constraints:
            weights = cst.getWeightAliasList()
            for weight in weights:
                name = weight.longName(fullPath=False)
                if df.ik_sff in name:
                    ik_port.connect(weight)
                if df.fk_sff in name:
                    fk_port.connect(weight)

        # Hide ik or fk ctrls based on switch
        ik_port.connect(self.ik_ctrl_grp.v)
        fk_port.connect(self.fk_ctrl_grp.v)


    def rig(self):
        # Todo: the part with the cog controller could be cleaned up a bit
        # Create drivers grp
        self.drivers_grp = pm.createNode('transform', name=f"{self.name}_{df.drivers_grp}")
        pm.parent(self.drivers_grp, utils.get_group(df.drivers_grp))

        # Create control grp
        self.control_grp = pm.createNode('transform', name=f'{self.name}{df.control_grp}')
        pm.parent(self.control_grp, utils.get_group(df.root))

        # Create cog ctrl
        cog = utils.CtrlGrp("M_cog", "square", 4)
        pm.parent(cog.grp, self.control_grp)
        pm.matchTransform(cog.grp, self.joints[0], position=True)
        self.cog_ctrl = cog.ctrl

        # Create Hip
        self.hip_ctrl = utils.create_fk_ctrls(self.hip_jnt, shape='star', scale=1.5, match_rot=not self.ctrls_in_world)
        set_color(self.hip_ctrl, viewport='green')
        pm.parent(self.hip_ctrl.getParent(1), self.control_grp)
        print("HIP", self.hip_ctrl.getParent(1))
        print("JOINT", self.joints[0])
        pm.select(cl=True)
        pm.parentConstraint(self.joints[0], self.hip_ctrl.getParent(1), maintainOffset=True)


        self.__fk_spine()
        self.__ik_spine()

        self.__ik_fk_switch(self.cog_ctrl)
        # Cog is the first fk ctrl
        pm.parentConstraint(self.cog_ctrl, self.fk_joints[0], maintainOffset=True)
        pm.parent(self.fk_ctrls[0].getParent(1), self.cog_ctrl)
        pm.parent(self.ik_ctrl_grp, self.cog_ctrl)

        # cst = pm.parentConstraint(self.fk_ctrls[0], self.ik_locators[0], self.hip_ctrl.getParent(1))

        # self.control_grp = self.fk_ctrls[0].getParent(1)
        self.all_ctrls = self.fk_ctrls

        self.connect_children()
        # Add joints
        if self.meta:
            self.save_metadata()