from mf_autoRig.utils.general import *
import mf_autoRig.utils.joint_tools as jnt_tools
from mf_autoRig.utils.color_tools import set_color
import mf_autoRig.utils.defaults as df
from mf_autoRig import log

from mf_autoRig.modules.Module import Module
from mf_autoRig.modules.Limb import Limb
from mf_autoRig.modules.Clavicle import Clavicle
from mf_autoRig import utils

class AutoClavicleArm(Module):
    meta_args = {
        'ik_jnts_guides': {'attributeType': 'message', 'm': True},
        # 'joints': {'attributeType': 'message', 'm': True},
        # 'clavicle_ctrl': {'attributeType': 'message'},
    }

    connectable_to = ['Spine']

    def __init__(self, name, meta=True):
        super().__init__(name, self.meta_args, meta)

        self.reset()

    def reset(self):
        self.arm = Limb('L_Arm')
        self.clavicle = Clavicle('L_Clavicle')
        self.ik_jnts_guides = None


        pass

    def create_guides(self):
        # Create the clavicle and arm guides
        self.arm.create_guides()
        self.clavicle.create_guides(pos=(0,10,-5))

        # Add shoulder guide to clavicle
        #pm.delete(self.clavicle.guides[1])
        self.clavicle.guides.append(self.arm.guides[0])
        self.clavicle.save_metadata()


    def create_joints(self):
        self.arm.create_joints()
        self.clavicle.create_joints()

    def rig(self):
        self.arm.rig()
        self.clavicle.rig()

        # Duplicate arm ik chain
        self.ik_jnts_guides = jnt_tools.duplicate_joints(self.arm.ik_joints, '_guide')
        if len(self.ik_jnts_guides) != 3:
            log.error("Only joint chains of 3 supported")

        # Do ik for duplicated joints
        handle_name = get_base_name(self.ik_jnts_guides[0].name()) + "_guides" + "_ikHandle"
        dup_ikHandle = pm.ikHandle(name=handle_name, startJoint=self.ik_jnts_guides[0],
                               endEffector=self.ik_jnts_guides[2], solver='ikRPsolver')

        ik_ctrl = self.arm.ik_ctrls[0]
        pole_ctrl = self.arm.ik_ctrls[1]
        pm.parentConstraint(ik_ctrl, dup_ikHandle[0])
        pm.poleVectorConstraint(pole_ctrl, dup_ikHandle[0])

        # AUTO CLAVICLE LOGIC
        # Create joint at clavicle start
        clav_pos = self.clavicle.joints[0].getTranslation(space='world')
        self.clav_aim_jnt = pm.createNode("joint", name='clavicle_aim')
        self.clav_aim_jnt.setTranslation(clav_pos)

        # Create group for clav aim jnt
        clav_aim_grp = pm.createNode('transform', name='clavicle_aim_grp')
        pm.matchTransform(clav_aim_grp, self.clav_aim_jnt)
        pm.parent(self.clav_aim_jnt, clav_aim_grp)

        # Clavicle aim end locator
        elbow_posV = dt.Vector(self.ik_jnts_guides[1].getTranslation(space='world'))
        clav_posV = dt.Vector(clav_pos)
        clav_aim_end_pos = (elbow_posV - clav_posV)/2 + clav_posV
        self.clav_aim_end_loc = pm.spaceLocator(name='clavicle_aim_end_loc')
        self.clav_aim_end_loc.setTranslation(clav_aim_end_pos.get())

        # Elbow locator
        self.elbow_loc = pm.spaceLocator(name='elbow_loc')
        pm.matchTransform(self.elbow_loc, self.ik_jnts_guides[1], position=True)
        pm.parent(self.elbow_loc, self.ik_jnts_guides[1])

        self.clav_aim_loc = pm.spaceLocator(name='clavicle_aim_loc')
        pm.pointConstraint(self.elbow_loc, self.clav_aim_end_loc, self.clav_aim_loc)

        # Clavicle aim
        pm.aimConstraint(self.clav_aim_loc, self.clav_aim_jnt, aim=(0, 1, 0), upVector=(1, 0, 0),
                         worldUpVector=(0, 1, 0))

        # Connect aim to offset group of main clav controller
        clavicle_offset = create_offset_grp(self.clavicle.clavicle_ctrl)
        pm.orientConstraint(self.clav_aim_jnt, clavicle_offset, maintainOffset=True)

        # Connect arm to clavicle
        self.arm.connect(self.clavicle)

    def connect(self, torso, force=False):
        if self.check_if_connected(torso) and not force:
            pm.warning(f"{self.name} already connected to {torso.name}")
            return
        # Connect Guide Ik arm
        pm.parentConstraint(torso.joints[-1], self.ik_jnts_guides[0], maintainOffset=True)

        # Connect clavicle
        pm.parentConstraint(torso.fk_ctrls[-1], self.clavicle.clavicle_ctrl.getParent(2), maintainOffset=True)
        pm.parentConstraint(torso.joints[-1], self.clav_aim_jnt.getParent(1), maintainOffset=True)

        pm.parent(self.clav_aim_end_loc, torso.joints[-1])



## TESTING

if __name__ == '__main__':
    from unload_packages import unload_packages
    unload_packages(silent=True, packages=["mf_autoRig"])

    arm = AutoClavicleArm('L_AutoClavicleArm')
    arm.create_guides()
    arm.create_joints()
    arm.rig()

    from mf_autoRig.modules.Spine import Spine
    spine = Spine('M_Spine')
    spine.create_guides(pos=[(0,0,-7), (0,10,-7)])
    spine.create_joints()
    spine.rig()

    arm.connect(spine)