from mf_autoRig.lib.useful_functions import *
from mf_autoRig.lib.color_tools import set_color

from mf_autoRig.modules.Limb import Limb

class ToonLimb(Limb):
    def __init__(self, name, meta=True):
        super().__init__(name, meta)
        self.aux_joints = None

    def create_joints(self, mirror_from = None):
        self.joints = []
        self.aux_joints = []

        # Create first jnt
        trs = pm.xform(self.guides[0], q=True, t=True, ws=True)
        jnt = pm.joint(name=f'{self.name}{1:02}{df.skin_sff}{df.jnt_sff}', position=trs)

        self.joints.append(jnt)
        self.aux_joints.append(jnt)

        # Create joints in between guides
        jnt_index = 1
        for i in range(len(self.guides)-1):
            # Get average between the two joints
            start_trs = pm.xform(self.guides[i], q=True, t=True, ws=True)
            end_trs = pm.xform(self.guides[i+1], q=True, t=True, ws=True)

            mid_trs = [0, 0, 0]
            for index, (a, b) in enumerate(zip(start_trs, end_trs)):
                mid_trs[index] = (a+b)/2

            sff = df.skin_sff
            # Last joint has end suffix
            if i == len(self.guides) - 1:
                sff = df.end_sff

            jnt_index += 1
            mid_jnt = pm.joint(name=f'{self.name}{jnt_index:02}{sff}{df.jnt_sff}', position=mid_trs)
            self.aux_joints.append(mid_jnt)
            jnt_index += 1
            jnt = pm.joint(name=f'{self.name}{jnt_index:02}{sff}{df.jnt_sff}', position=end_trs)
            self.aux_joints.append(jnt)
            self.joints.append(jnt)

        print(self.joints)
        print(self.aux_joints)

test = ToonLimb('L_test')
test.create_guides()
test.create_joints()
test.rig()
