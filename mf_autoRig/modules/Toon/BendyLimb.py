import pymel.core as pm
from mf_autoRig.lib.useful_functions import *
from mf_autoRig.modules.Module import Module
from mf_autoRig.lib.joint_inBetweener import inBetweener


class VectorNodes():
    def __init__(self, vector):
        self.vector = vector.translate

    def __add__(self, other):
        plus_minus = pm.createNode('plusMinusAverage')

        self.vector.connect(plus_minus.input3D[0])
        other.translate.connect(plus_minus.input3D[1])

        return plus_minus.output3D

    def __sub__(self, other):
        plus_minus = pm.createNode('plusMinusAverage')
        plus_minus.operation.set(2)

        self.vector.connect(plus_minus.input3D[0])
        other.connect(plus_minus.input3D[1])

        return plus_minus.output3D


class BendyLimb(Module):
    meta_args = {
        'switch': {'attributeType': 'message'},
        'fk_ctrls': {'attributeType': 'message', 'm': True}
    }

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

        self.guides = create_joint_chain(3, self.name, pos[0], pos[1], defaultValue=51)

        pm.select(cl=True)

    def create_joints(self):
        self.main_joints = create_joints_from_guides(f"{self.name}", self.guides)

        first_part = pm.duplicate(self.main_joints)
        pm.delete(first_part[-1])

        for obj in first_part:
            obj.radius.set(0.2)

        second_part = pm.duplicate(self.main_joints)
        pm.parent(second_part[1], None)
        pm.delete(second_part[0])
        second_part.pop(0)

        for obj in first_part:
            obj.radius.set(0.2)

        inBetweener(first_part[0], first_part[1], 5)
        inBetweener(second_part[0], second_part[1], 5)

    def rig(self):
        pass

test = BendyLimb("L_arm")
test.create_guides()
test.create_joints()