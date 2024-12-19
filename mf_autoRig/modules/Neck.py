from mf_autoRig.modules.Module import Module
from mf_autoRig.utils.general import *
import pymel.core as pm

class Neck(Module):
    meta_args = {
        'guides': {'attributeType': 'message', 'm': True},
        # 'joints': {'attributeType': 'message', 'm': True},
        # 'clavicle_ctrl': {'attributeType': 'message'},
    }
    def __init__(self, name, meta):
        super().__init__(name, self.meta_args, meta)

    def create_guides(self):
        pass

    def create_joints(self):
        pass

    def rig(self):
        pass

