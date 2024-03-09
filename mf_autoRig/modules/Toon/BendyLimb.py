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
        self.main_joints = create_joints_from_guides(f"{self.name}", self.guides, suffix='_driver')

        #inBetweener(first_part[0], first_part[1], 5)
        #inBetweener(second_part[0], second_part[1], 5)

    def rig(self):
        ik_joints, ik_ctrls, ik_ctrl_grp, ikHandle = create_ik(self.main_joints, create_new=False)

        # Add bendy attribute to the ik_ctrl
        pm.addAttr(ik_ctrls[0], ln="bendyWeight", at="double", min=0, max=1, dv=0.5, k=True)
        self.bendy_attr =  ik_ctrls[0].bendyWeight

        self.__create_splineIK_setup(self.main_joints)


    def __create_splineIK_setup(self, joints):
        # Create locators for main joints
        self.main_locators = []
        for i,jnt in enumerate(joints):
            loc = pm.spaceLocator(n=f"{self.name}{i+1:02}{df.loc_sff}")
            self.main_locators.append(loc)
            pm.matchTransform(loc, jnt)
            pm.pointConstraint(jnt, loc)

        pm.select(cl=True)

        # Create joint chain between Shoulder and Elbow
        shoulder_chain = inBetweener(joints[0], joints[1], 7, name=f"{self.name}", suffix='_bendy01'+df.skin_sff+df.jnt_sff)
        wrist_chain = inBetweener(joints[1], joints[2], 7, name=f"{self.name}", suffix='_bendy02'+df.skin_sff+df.jnt_sff)

        # Set color and radius
        for obj in shoulder_chain + wrist_chain:
            obj.radius.set(0.2)
            set_color(obj, viewport='magenta')

        shoulder_curve = stretchy_splineIK(shoulder_chain)
        wrist_curve = stretchy_splineIK(wrist_chain)

        shoulder_mid_loc, elbow_mid_loc = self.__get_mid_position()

        self.bendy_locators = [self.main_locators[0], shoulder_mid_loc, self.main_locators[1],
                               elbow_mid_loc, self.main_locators[2]]

        # Create clusters for the curves
        for i in range(shoulder_curve.numCVs()):
            loc = self.bendy_locators[i]
            cluster = pm.cluster(shoulder_curve.cv[i])[1]
            pm.matchTransform(cluster, loc)
            pm.pointConstraint(loc, cluster)

        for i in range(wrist_curve.numCVs()):
            loc = self.bendy_locators[i+2]
            cluster = pm.cluster(wrist_curve.cv[i])[1]
            pm.matchTransform(cluster, loc)
            pm.pointConstraint(loc, cluster)


    def __get_mid_position(self):
        # Get position for mid clusters with vector nodes
        A = VectorNodes(self.main_locators[0].translate)
        B = VectorNodes(self.main_locators[1].translate)
        C = VectorNodes(self.main_locators[2].translate)

        BA = A - B
        BC = C - B
        CA_norm = (A - C).norm()

        # Shoulder side
        BD = BA * (self.bendy_attr, self.bendy_attr, self.bendy_attr)
        dotProd = VectorNodes.dotProduct(BD, CA_norm)
        M = CA_norm * dotProd + B

        # Wrist side
        BE = BC * (self.bendy_attr, self.bendy_attr, self.bendy_attr)
        dotProd = VectorNodes.dotProduct(BE, CA_norm)
        N = CA_norm * dotProd + B

        # Apply transformations to new locators
        shoulder_mid_loc = pm.spaceLocator()
        M.attr.connect(shoulder_mid_loc.translate)

        elbow_mid_loc = pm.spaceLocator()
        N.attr.connect(elbow_mid_loc.translate)

        return shoulder_mid_loc, elbow_mid_loc

cmds.file(new=True, f=True)
test = BendyLimb("L_arm")
test.create_guides()
test.create_joints()
test.rig()
