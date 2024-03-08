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

        # Create joint where shoulder and elbow are
        first_part = [pm.joint(), pm.joint()]
        pm.matchTransform(first_part[0], self.main_joints[0])
        pm.matchTransform(first_part[1], self.main_joints[1])
        self.jnt_chain = inBetweener(first_part[0], first_part[1], 5)

        set_color(self.main_joints, viewport='cyan')
        set_color(self.jnt_chain, viewport='magenta')

        for obj in first_part:
            obj.radius.set(0.2)

        #inBetweener(first_part[0], first_part[1], 5)
        #inBetweener(second_part[0], second_part[1], 5)

    def rig(self):
        # Create locators for joints
        self.locators = []
        for jnt in self.main_joints:
            loc = pm.spaceLocator()
            self.locators.append(loc)
            pm.matchTransform(loc, jnt)
            pm.parentConstraint(jnt, loc)


        # Make Stretchy Ik spline
        splineHandle = pm.ikHandle(sj = self.jnt_chain[0], ee = self.jnt_chain[-1], solver = "ikSplineSolver",
                                    parentCurve=False, rootOnCurve = True, simplifyCurve=True, ns = 1, createCurve = True)
        curve = splineHandle[2]

        # Get curve distance
        curveInfo = pm.createNode('curveInfo')
        curveShape = curve.getShape()
        curveShape.worldSpace[0].connect(curveInfo.inputCurve)
        curveLength = curveInfo.arcLength.get()

        # Divide arc length by curveLength
        multDiv = pm.createNode('multiplyDivide')
        multDiv.operation.set(2)
        curveInfo.arcLength.connect(multDiv.input1X)
        multDiv.input2X.set(curveLength)

        # Set scale for each joint based on the curve length
        # Joints are oriented in the Y axis
        for jnt in self.jnt_chain:
            multDiv.outputX.connect(jnt.scaleY)

        # Create Clusters for the curve
        clusters = [pm.cluster(curve.cv[0])[1],
                    pm.cluster(curve.cv[1:2])[1],
                    pm.cluster(curve.cv[3])[1]]


        # Get position for mid cluster with vector nodes
        A = VectorNodes(self.locators[0].translate)
        B = VectorNodes(self.locators[1].translate)
        C = VectorNodes(self.locators[2].translate)

        CA = A - C
        BA = A - B
        BD = BA * (0.5, 0.5, 0.5)
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

        pm.matchTransform(clusters[0], self.locators[0])
        pm.parent(clusters[0], self.locators[0])

        pm.matchTransform(clusters[2], self.locators[1])
        pm.parent(clusters[2], self.locators[1])

        pm.orientConstraint(self.locators[0], mid_loc, maintainOffset = False)

        print(splineHandle)


cmds.file(new=True, force=True)
test = BendyLimb("L_arm")
test.create_guides()
test.create_joints()
test.rig()
