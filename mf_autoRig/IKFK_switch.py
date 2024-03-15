from mf_autoRig.lib.useful_functions import *
import mf_autoRig.lib.defaults as df

def create_IKFK_switch(joints):
    # IK
    ik_joints, ik_ctrls, ik_ctrls_grp, ikHandle = create_ik(joints)
    # FK
    fk_joints = create_fk_jnts(joints)
    fk_ctrls = create_fk_ctrls(fk_joints)

    ikfk_constraints = constraint_ikfk(joints, ik_joints, fk_joints)
    switch = ikfk_switch(ik_ctrls_grp, fk_ctrls, ikfk_constraints, joints[-1])

    # Group joints only if group isn't already there
    # pm.parent(self.fk_joints[0], self.ik_joints[0], self.joints[0], joint_grp)

    # Group joint grp under Joints grp
    #pm.parent(joint_grp, get_group(df.joints_grp))

    # Hide ik fk joints
    fk_joints[0].visibility.set(0)
    ik_joints[0].visibility.set(0)

    # Move ik control grp under root_ctrl
    root_ctrl = get_group(df.root)
    pm.parent(ik_ctrls_grp, root_ctrl)

    switch_ctrl_grp = switch.getParent(1)
    pm.parent(switch_ctrl_grp, root_ctrl)

    pm.parent(fk_ctrls[0].getParent(1), root_ctrl)

    # Clear selection
    pm.select(clear=True)


create_IKFK_switch(pm.selected())