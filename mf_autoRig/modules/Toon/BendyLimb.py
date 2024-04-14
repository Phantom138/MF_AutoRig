import pymel.core as pm

from mf_autoRig.utils.VectorNodes import VectorNodes
from mf_autoRig.utils.useful_functions import *
from mf_autoRig.modules.Module import Module
from mf_autoRig.utils.joint_inBetweener import inBetweener

from mf_autoRig.utils.color_tools import set_color
import mf_autoRig.utils.mirrorJoint as mirrorUtils

def stretchy_splineIK(joints, name=None):
    # Create 2 degree curve
    start_trs = joints[0].getTranslation(space='world')
    end_trs = joints[-1].getTranslation(space='world')

    mid_trs = [(start_trs[0]+end_trs[0])/2, (start_trs[1]+end_trs[1])/2, (start_trs[2]+end_trs[2])/2]

    # Make Stretchy Ik spline
    if name is None:
        handle_name='ikHandle'
        crv_name='curve'
    else:
        crv_name = name + '_crv'
        handle_name = name + '_ikHandle'

    curve = pm.curve(n=crv_name, d=2, p=[start_trs, mid_trs, end_trs])
    pm.select(cl=True)
    splineHandle = pm.ikHandle(n=handle_name, sj=joints[0], ee=joints[-1], solver="ikSplineSolver",
                               parentCurve=False, rootOnCurve=False, c=curve, ccv=False)

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

    trans_div = pm.createNode('multiplyDivide')
    trans_div.operation.set(1)
    multDiv.outputX.connect(trans_div.input1X)
    trans_div.input2X.set(joints[1].translateY.get())


    # Set scale for each joint based on the curve length
    # Joints are oriented in the Y axis
    for jnt in joints[1:]:
        trans_div.outputX.connect(jnt.translateY)

    return curve, splineHandle[0]


class BendyLimb(Module):
    meta_args = {
        'guides': {'attributeType': 'message', 'm': True},
        'joints': {'attributeType': 'message', 'm': True},
    }

    def __init__(self, name, meta=True):
        super().__init__(name, self.meta_args, meta)

        self.joints = None

        self.control_grp = None
        self.joints_grp = None
        self.jnt_chain = None
        self.guides = None

    @classmethod
    def create_from_meta(cls, metaNode):
        obj = super().create_from_meta(metaNode)


        ctrls = obj.control_grp.listRelatives(allDescendents=True, type='nurbsCurve')
        obj.all_ctrls = []
        print(ctrls)
        for ctrl in ctrls:
            if ctrl.name().endswith(f'{df.ctrl_sff}Shape'):
                obj.all_ctrls.append(ctrl)

        print("Created Object", obj)
        return obj

    def create_guides(self, pos=None):
        """
        Creates guides between pos[0] and pos[1]
        Pos should be a list with two elements!
        """
        if pos is None:
            pos = [(0, 10, 0), (0, 0, 0)]

        self.guides = create_joint_chain(3, self.name, pos[0], pos[1], defaultValue=51)

        pm.select(cl=True)
        if self.meta:
            self.save_metadata()

    def create_joints(self):
        self.joints = create_joints_from_guides(f"{self.name}", self.guides, suffix='_driver')

        #inBetweener(first_part[0], first_part[1], 5)
        #inBetweener(second_part[0], second_part[1], 5)
        if self.meta:
            self.save_metadata()

    def rig(self, bend_joints=7):
        self.bend_joints = bend_joints
        ik_joints, ik_ctrls, ik_ctrl_grp, ikHandle = create_ik(self.joints, create_new=False)

        # Add bendy attribute to the ik_ctrl
        pm.addAttr(ik_ctrls[0], ln="upperArmBendyWeight", at="double", min=0, max=1, dv=0.5, k=True)
        pm.addAttr(ik_ctrls[0], ln="forearmBendyWeight", at="double", min=0, max=1, dv=0.5, k=True)
        self.first_bendy_attr = ik_ctrls[0].upperArmBendyWeight
        self.second_bendy_attr = ik_ctrls[0].forearmBendyWeight

        # Create Control Grp
        self.control_grp = pm.createNode('transform', name=f'{self.name}_Control{df.grp_sff}')
        pm.parent(ik_ctrl_grp, self.control_grp)

        self.__create_splineIK_setup(self.joints)

        # Get all ctrls by getting all nurbs curves and then filtering out only those that end in _ctrl
        ctrls = self.control_grp.listRelatives(allDescendents=True, type='nurbsCurve')
        self.all_ctrls = []

        for ctrl in ctrls:
            if ctrl.name().endswith(f'{df.ctrl_sff}Shape'):
                self.all_ctrls.append(ctrl)

        if self.meta:
            self.save_metadata()


    def __create_splineIK_setup(self, joints):
        # Create locators for main joints
        self.main_locators = []
        for i,jnt in enumerate(joints):
            loc = pm.spaceLocator(n=f"{self.name}{i+1:02}{df.loc_sff}")
            self.main_locators.append(loc)
            pm.matchTransform(loc, jnt)
            pm.parentConstraint(jnt, loc)

        pm.select(cl=True)

        # Create joint chain between Shoulder and Elbow
        shoulder_chain = inBetweener(joints[0], joints[1], self.bend_joints, name=f"{self.name}",
                                     suffix='_bendy01'+df.skin_sff+df.jnt_sff, end_suffix='_bendy01'+df.end_sff+df.jnt_sff)
        wrist_chain = inBetweener(joints[1], joints[2], self.bend_joints, name=f"{self.name}",
                                  suffix='_bendy02'+df.skin_sff+df.jnt_sff, end_suffix='_bendy01'+df.end_sff+df.jnt_sff)


        # Set color
        for obj in shoulder_chain + wrist_chain:
            set_color(obj, viewport='magenta')


        shoulder_curve, shoulder_handle = stretchy_splineIK(shoulder_chain, name=f"{self.name}_bendy01")
        wrist_curve, wrist_handle = stretchy_splineIK(wrist_chain, name=f"{self.name}_bendy02")

        shoulder_mid_loc, elbow_mid_loc = self.__get_mid_position()

        self.bendy_locators = [self.main_locators[0], shoulder_mid_loc, self.main_locators[1],
                               elbow_mid_loc, self.main_locators[2]]

        # Create clusters for the curves
        for i in range(shoulder_curve.numCVs()):
            loc = self.bendy_locators[i]
            cluster = pm.cluster(shoulder_curve.cv[i])[1]
            pm.matchTransform(cluster, loc)
            pm.parent(cluster, loc)

        for i in range(wrist_curve.numCVs()):
            loc = self.bendy_locators[i+2]
            cluster = pm.cluster(wrist_curve.cv[i])[1]
            pm.matchTransform(cluster, loc)
            pm.parent(cluster, loc)

        # Clean-up
        # Parent bendy joints to driver joints so they get rotation info
        pm.parent(shoulder_chain[0], self.joints[0])
        pm.parent(wrist_chain[0], self.joints[1])

        # Create Locator grp
        loc_grp = pm.group(em=True, n=f"{self.name}_Locators{df.grp_sff}")
        pm.parent(self.bendy_locators, loc_grp)

        # Create Joint Grp
        self.joints_grp = pm.group(em=True, n=f"{self.name}_Joints{df.grp_sff}")
        pm.parent(self.joints[0], self.joints_grp)

        # Parent to Control Grp
        pm.parent(loc_grp, shoulder_curve, wrist_curve, self.control_grp)

        # Parent Handles under ikHandle grp
        grp = get_group(df.ikHandle_grp)
        pm.parent(wrist_handle, shoulder_handle, grp)

        if self.meta:
            self.save_metadata()

    def __get_mid_position(self):
        # Get position for mid clusters with vector nodes
        A = VectorNodes(self.main_locators[0].translate)
        B = VectorNodes(self.main_locators[1].translate)
        C = VectorNodes(self.main_locators[2].translate)

        BA = A - B
        BC = C - B
        CA_norm = (A - C).norm()

        # Shoulder side
        BD = BA * (self.first_bendy_attr, self.first_bendy_attr, self.first_bendy_attr)
        dotProd = VectorNodes.dotProduct(BD, CA_norm)
        M = CA_norm * dotProd + B

        # Wrist side
        BE = BC * (self.second_bendy_attr, self.second_bendy_attr, self.second_bendy_attr)
        dotProd = VectorNodes.dotProduct(BE, CA_norm)
        N = CA_norm * dotProd + B

        # Apply transformations to new locators
        shoulder_mid_loc = pm.spaceLocator(n=f'{self.name}_bendy01{df.loc_sff}')
        M.attr.connect(shoulder_mid_loc.translate)

        elbow_mid_loc = pm.spaceLocator(n=f'{self.name}_bendy02{df.loc_sff}')
        N.attr.connect(elbow_mid_loc.translate)

        return shoulder_mid_loc, elbow_mid_loc

    def mirror(self):
        name = self.name.replace(f'{self.side}_', f'{self.side.opposite}_')
        mir_module = self.__class__(name)

        # Mirror Joints
        mir_module.joints = mirrorUtils.mirrorJoints(self.joints, (self.side.side, self.side.opposite))
        print("Mirrored joints:", mir_module.joints)
        mir_module.rig()

        # Mirror Ctrls
        for src, dst in zip(self.all_ctrls, mir_module.all_ctrls):
            control_shape_mirror(src, dst)

        return mir_module