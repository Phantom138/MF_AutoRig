import pymel.core as pm

import importlib
import mf_autoRig.lib.useful_functions
importlib.reload(mf_autoRig.lib.useful_functions)
from mf_autoRig.lib.useful_functions import *

class Limb:
    def __init__(self, name):
        self.name = name
        self.joints = None
        self.guides = None

    def create_guides(self, pos):
        """
        Creates guides between pos[0] and pos[1]
        Pos should be a list with two elements!
        """
        self.guides = create_joint_chain(3, self.name, pos[0], pos[1])

        pm.select(cl=True)

    def create_joints(self):
        self.joints = []
        for i, tmp in enumerate(self.guides):
            trs = pm.xform(tmp, q=True, t=True, ws=True)

            suff = df.skin_sff
            # Last joint has end suffix
            if i == len(self.guides)-1:
                suff = df.end_sff

            jnt = pm.joint(name=f'{self.name}{i + 1:02}{suff}{df.jnt_sff}', position=trs)

            self.joints.append(jnt)

        # Orient joints
        pm.joint(self.joints[0], edit=True, orientJoint='yzx', secondaryAxisOrient='zup', children=True)
        pm.joint(self.joints[-1], edit=True, orientJoint='none')


        self.skin_jnts = self.joints[:-1]
        # IK
        self.ik_jnts, self.ik_ctrls_grp, self.ikHandle = create_ik(self.joints)
        # FK
        self.fk_jnts = create_fk_jnts(self.joints)
        self.fk_ctrls = create_fk_ctrls(self.fk_jnts)

        self.ikfk_constraints = constraint_ikfk(self.joints, self.ik_jnts, self.fk_jnts)
        self.switch = ikfk_switch(self.ik_ctrls_grp, self.fk_ctrls, self.ikfk_constraints, self.joints[-1])

        self.clean_up()

    def clean_up(self):
        # Group joints only if group isn't already there
        joint_grp_name = self.name + '_Joint_Grp'
        joint_grp = get_group(joint_grp_name)
        pm.parent(self.fk_jnts[0], self.ik_jnts[0], self.joints[0], joint_grp)

        # Group joint grp under Joints grp
        pm.parent(joint_grp, get_group(df.joints_grp))

        # Hide ik fk joints
        self.fk_jnts[0].visibility.set(0)
        self.ik_jnts[0].visibility.set(0)

        # Move ik control grp under root_ctrl
        root_ctrl = get_group(df.root)
        pm.parent(self.ik_ctrls_grp, root_ctrl)

        switch_ctrl_grp = self.switch.getParent(1)
        pm.parent(switch_ctrl_grp, root_ctrl)

        pm.parent(self.fk_ctrls[0].getParent(1), root_ctrl)

        # Clear selection
        pm.select(clear=True)

    def connect(self, dest, method):
        ctrl_grp = self.fk_ctrls[0].getParent(1)

        if method == 'arm':
            pm.parent(ctrl_grp, dest.ctrl)
            pm.parentConstraint(dest.joints[-1], self.ik_jnts[0])

        elif method == 'leg':
            pm.parent(ctrl_grp, dest.hip_ctrl)
            pm.parentConstraint(dest.hip_ctrl, self.ik_jnts[0], maintainOffset=True)

