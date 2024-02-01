from mf_autoRig.lib.useful_functions import *
import mf_autoRig.lib.defaults as df
from mf_autoRig.lib.color_tools import set_color
import mf_autoRig.modules.meta as mdata
from mf_autoRig.modules.Module import Module

class Clavicle(Module):
    meta_args = {
        'guides': {'attributeType': 'message', 'm': True},
        'joints': {'attributeType': 'message', 'm': True},
        'clavicle_ctrl': {'attributeType': 'message', 'm': True},
    }

    def __init__(self, name, meta=True):
        super().__init__(name, self.meta_args, meta)

        self.side = name.split('_')[0]
        self.clavicle_ctrl = None
        self.joints = None
        self.guides = None
        self.all_ctrls = []


    @classmethod
    def create_from_meta(cls, metaNode):
        clavicle = super().create_from_meta(metaNode)

        return clavicle


    def create_guides(self, pos = None):
        """
        Creates clavicle guides at pos, pos should be a list of xyz values
        """
        self.guides = []
        # If there are no guides, it means that the class is ran individually, so there is no guide for the shoulder
        if pos is None:
            pos = [(0,0,0), (5,0,0)]
            for p in pos:
                self.guides.append(pm.joint(name=f'{self.name}', position=p))
        else:
            # Create new joint at pos
            self.guides.append(pm.joint(name=f'{self.name}', position=pos))
            
        grp = pm.group(self.guides, name=f'{self.name}_guides{df.grp_sff}')
        pm.parent(grp, get_group(df.rig_guides_grp))

        print(f'Clavicle guides {self.guides}')

        # Clear Selection
        pm.select(clear=True)

        # Save guides
        if self.meta and self.guides:
            for i, guide in enumerate(self.guides):
                guide.message.connect(self.metaNode.guides[i])

    def create_joints(self, shoulder=None):
        """
        Create joints from starting guide to shoulder
        """
        if shoulder is not None:
            # Add shoulder to guides
            self.guides.append(shoulder)

        # Create joints
        self.joints = []
        for i, tmp in enumerate(self.guides):
            # Create joints where the guides where
            trs = pm.xform(tmp, q=True, t=True, ws=True)
            sff = df.skin_sff
            if i == len(self.guides):
                sff = df.end_sff
            jnt = pm.joint(name=f'{self.name}{i + 1:02}{sff}{df.jnt_sff}', position=trs)

            self.joints.append(jnt)

        print(f'Created {self.joints} for Clavicle')

        # Orient joints
        pm.joint(self.joints[0], edit=True, orientJoint='yzx', secondaryAxisOrient='zup', children=True)
        pm.joint(self.joints[-1], edit=True, orientJoint='none')

        # Clear Selection
        pm.select(clear=True)

        # Parent Joints under Joint_grp
        pm.parent(self.joints[0], get_group(df.joints_grp))

        #Save joints
        if self.meta and self.joints:
            for i, joints in enumerate(self.joints):
                joints.message.connect(self.metaNode.joints[i])

    def rig(self):
        if len(self.joints) != 2:
            pm.error('Can only create clavicle with 2 joints')

        # Create ctrl and group
        axis = get_joint_orientation(self.joints[0], self.joints[1])
        clav = CtrlGrp(self.name, 'arc', axis=axis)

        # Match ctrl to first joint
        jnt = self.joints[0]
        pm.matchTransform(clav.grp, jnt)
        pm.parentConstraint(clav.ctrl, jnt, maintainOffset=True)

        self.clavicle_ctrl = clav.ctrl

        self.all_ctrls.append(self.clavicle_ctrl)

        # Color clavicle
        if self.side == 'R':
            set_color(self.clavicle_ctrl, viewport='red')
        elif self.side == 'L':
            set_color(self.clavicle_ctrl, viewport='blue')


        pm.select(clear=True)

        if self.meta and self.clavicle_ctrl:
            self.clavicle_ctrl.message.connect(self.metaNode.clavicle_ctrl)


    def connect(self, torso):
        if self.check_if_connected(torso):
            pm.warning(f"{self.name} already connected to {torso.name}")
            return

        pm.parent(self.clavicle_ctrl.getParent(1), torso.fk_ctrls[-1])

        self.connect_metadata(torso)

