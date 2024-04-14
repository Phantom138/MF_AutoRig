from mf_autoRig.modules.Module import Module
from mf_autoRig.utils.useful_functions import *
import pymel.core as pm

class EyeAim(Module):
    meta_args = {
        'guides': {'attributeType': 'message', 'm': True},
        # 'joints': {'attributeType': 'message', 'm': True},
        # 'clavicle_ctrl': {'attributeType': 'message'},
    }

    def __init__(self, name, meta=True):
        super().__init__(name, self.meta_args, meta)
        self.guide = None
        self.joint = None


    def create_guides(self, object = None):
        self.guide = pm.spaceLocator()
        if object is not None:
            pm.matchTransform(self.guide, object)

    def create_joints(self):
        self.joint = pm.createNode('joint')
        pm.matchTransform(self.joint, self.guide)

    def rig(self):
        # Create close-up eye ctrl
        eye_ctrl = CtrlGrp(self.name+"_offset", 'circle')
        pm.matchTransform(eye_ctrl.grp, self.joint)
        pm.parentConstraint(eye_ctrl.ctrl, self.joint)

        # Create eye aim ctrl and move it
        eye_aim = CtrlGrp(self.name+"_aim", 'circle', axis=(0,0,1))
        pm.matchTransform(eye_aim.grp, self.joint)
        pm.move(eye_aim.grp, [0,0,10])
        pm.aimConstraint(eye_aim.ctrl, eye_ctrl.grp, maintainOffset=True, aimVector=[0,0,1], upVector=[0,1,0], worldUpType="none")

        pass
