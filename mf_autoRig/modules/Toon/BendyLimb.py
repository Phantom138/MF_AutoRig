import pymel.core as pm
from mf_autoRig.lib.useful_functions import *
from mf_autoRig.modules.Module import Module


class VectorNodes():
    def __init__(self, vector):
        self.vector = vector

    def __add__(self, other):
        plus_minus = pm.createNode('plusMinusAverage')

        self.vector.translate.connect(plus_minus.input3D[0])
        other.translate.connect(plus_minus.input3D[1])

        return plus_minus.output3D

    def __sub__(self, other):
        plus_minus = pm.createNode('plusMinusAverage')
        plus_minus.operation.set(2)

        self.vector.translate.connect(plus_minus.input3D[0])
        other.translate.connect(plus_minus.input3D[1])

        return plus_minus.output3D


class BendyLimb(Module):
    def __init__(self, name, meta=True):
        super().__init__(name, self.meta_args, meta)

        self.guides = None

    def create_guides(self, pos=None):
        """
        Creates guides between pos[0] and pos[1]
        Pos should be a list with two elements!
        """
        if pos is None:
            pos = [(0, 10, 0), (0, 0, 0)]

        self.guides = create_joint_chain(3, self.name, pos[0], pos[1], defaultValue=self.default_pin_value)

        pm.select(cl=True)

    def create_joints(self):
        self.main_joints = create_joints_from_guides(f"{self.name}", self.guides)
        

    def rig(self):
        pass
