import pymel.core as pm

from mf_autoRig.lib.VectorNodes import VectorNodes
from mf_autoRig.lib.useful_functions import *
from mf_autoRig.modules.Module import Module
from mf_autoRig.lib.joint_inBetweener import inBetweener

from mf_autoRig.lib.color_tools import set_color

class BendyLimb(Module):
    meta_args = {
        'switch': {'attributeType': 'message'},
        'fk_ctrls': {'attributeType': 'message', 'm': True}
    }

    def __init__(self, name, meta=True):
        super().__init__(name, self.meta_args, meta)

        self.jnt_chain = None
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

        #inBetweener(first_part[0], first_part[1], 5)
        #inBetweener(second_part[0], second_part[1], 5)

    def rig(self):
        ik_joints, ik_ctrls, ik_ctrl_grp, ikHandle = create_ik(self.main_joints, create_new=False)
        pm.addAttr(ik_ctrls[0], ln="bendyWeight", at="double", min=0, max=1, dv=0.5, k=True)
        self.__create_splineIK_setup(self.name, self.main_joints, ik_ctrls[0].bendyWeight)
        main_joints_rev = self.main_joints
        main_joints_rev.reverse()
        self.__create_splineIK_setup(self.name, main_joints_rev, ik_ctrls[0].bendyWeight)

    @staticmethod
    def __create_splineIK_setup(name, joints, ik_attr):
        # Create locators for joints
        locators = []
        for jnt in joints:
            loc = pm.spaceLocator()
            locators.append(loc)
            pm.matchTransform(loc, jnt)
            pm.pointConstraint(jnt, loc)

        pm.select(cl=True)
        # Create joint chain
        first_part = [pm.joint(), pm.joint()]
        pm.matchTransform(first_part[0], joints[0])
        pm.matchTransform(first_part[1], joints[1])
        jnt_chain = inBetweener(first_part[0], first_part[1], 7)

        for obj in jnt_chain:
            obj.radius.set(0.2)
        set_color(jnt_chain, viewport='magenta')

        curve = stretchy_splineIK(jnt_chain)

        # Create Clusters for the curve
        clusters = [pm.cluster(curve.cv[0])[1],
                    pm.cluster(curve.cv[1])[1],
                    pm.cluster(curve.cv[2])[1]]

        # Get position for mid cluster with vector nodes
        A = VectorNodes(locators[0].translate)
        B = VectorNodes(locators[1].translate)
        C = VectorNodes(locators[2].translate)

        CA = A - C
        BA = A - B

        multDiv = pm.createNode('multiplyDivide')
        ik_attr.connect(multDiv.input2X)
        ik_attr.connect(multDiv.input2Y)
        ik_attr.connect(multDiv.input2Z)
        BA.attr.connect(multDiv.input1)

        BD = VectorNodes(multDiv.output)

        CA_norm = CA.norm()

        dotProd = VectorNodes.dotProduct(BD, CA_norm)
        BM = CA_norm * dotProd
        DM = BM - BD

        D = BD + B
        M = DM + D

        mid_loc = pm.spaceLocator()
        M.attr.connect(mid_loc.translate)

        # Get the cluster in position and parent it to the locator
        pm.matchTransform(clusters[1], mid_loc)
        pm.parent(clusters[1], mid_loc)

        pm.matchTransform(clusters[0], locators[0])
        pm.parent(clusters[0], locators[0])

        pm.matchTransform(clusters[2], locators[1])
        pm.parent(clusters[2], locators[1])

        #pm.orientConstraint(locators[0], mid_loc, maintainOffset=False)

        return locators

cmds.file(new=True, f=True)
test = BendyLimb("L_arm")
test.create_guides()
test.create_joints()
test.rig()
