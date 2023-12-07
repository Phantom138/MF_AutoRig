import pymel.core as pm

#f = pm.newFile(f=1)
print(pm.ls(type='camera'))
cam = pm.ls(type='camera')[0]
print(cam.getAspectRatio())


class Arm():
    def __init__(self,joints):
        self.skin_jnts = joints[:-1]
        self.ik_jnts, self.ik_ctrls = create_ik(joints)
        self.fk_jnts, self.fk_ctrls = create_fk(joints)

        self.ikfk_constraints = constraint_ikfk(joints, self.ik_jnts, self.fk_jnts)
        self.switch = ikfk_switch(ik_ctrl_grp, self.fk_ctrls, self.ikfk_constraints)

class Hand():
    def __int__(self, joints):


class Torso():
    def __init__(self, joints):
        # Skin joints are all the joint chain but without the last one (end_jnt)
        # TODO: check if the suffix of each jnt is in fact skin_jnt
        self.skin_jnts = joints[:-1]
        self.fk_ctrls = create_fk_ctrls(joints)


class Clavicle():
    def __init__(self,joints):
        self.skin_jnts = joints

        self.fk_ctrls = create_fk_ctrls(joints)


def connect_arm(arm, clavicle):