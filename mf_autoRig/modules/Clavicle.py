from mf_autoRig.lib.useful_functions import *
import mf_autoRig.lib.defaults as df
from mf_autoRig.lib.color_tools import set_color
import mf_autoRig.modules.meta as mdata
from mf_autoRig.modules.Module import Module

class Clavicle(Module):
    meta_args = {
        'guides': {'attributeType': 'message', 'm': True},
        'joints': {'attributeType': 'message', 'm': True},
        'clavicle_ctrl': {'attributeType': 'message'},
    }

    connectable_to = ['Spine']

    def __init__(self, name, meta=True):
        super().__init__(name, self.meta_args, meta)

        self.clavicle_ctrl = None
        self.joints = None
        self.guides = None
        self.all_ctrls = []

        self.control_grp = None
        self.joints_grp = None


    def update_from_meta(self):
        super().update_from_meta()
        if self.clavicle_ctrl is not None:
            self.all_ctrls.append(self.clavicle_ctrl)


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

        # Clear Selection
        pm.select(clear=True)

        # Save guides
        if self.meta:
            self.save_metadata()

    def create_joints(self, shoulder=None):
        """
        Create joints from starting guide to shoulder
        """
        if shoulder is not None:
            # Add shoulder to guides
            self.guides.append(shoulder)

        # Create joints
        self.joints = create_joints_from_guides(self.name, self.guides)

        # Parent Joints under Joint_grp
        pm.parent(self.joints[0], get_group(df.joints_grp))

        #Save joints
        if self.meta:
            self.save_metadata()

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

        # Create clavicle Control group for the controllers
        self.control_grp = pm.createNode('transform', name=f'{self.name}{df.control_grp}')
        pm.parent(clav.grp, self.control_grp)

        # Group control_grp under root
        pm.parent(self.control_grp, get_group(df.root))

        self.joints_grp = self.joints[0]

        if self.meta:
            self.save_metadata()


    def connect(self, torso, force=False):
        if self.check_if_connected(torso) and not force:
            pm.warning(f"{self.name} already connected to {torso.name}")
            return

        pm.parentConstraint(torso.fk_ctrls[-1], self.clavicle_ctrl.getParent(1), maintainOffset=True)

        self.connect_metadata(torso)

    def mirror(self):
        """
        Return a class of the same type that is mirrored on the YZ plane
        """
        name = self.name.replace(f'{self.side}_', f'{self.side.opposite}_')
        mir_module = self.__class__(name)

        # Mirror Joints
        mirrored_jnts = pm.mirrorJoint(self.joints[0], mirrorYZ=True, mirrorBehavior=True,
                                       searchReplace=(self.side, self.side.opposite))
        mir_joints = list(map(pm.PyNode, mirrored_jnts))
        mir_module.joints = []
        for obj in mir_joints:
            if isinstance(obj, pm.nt.Joint):
                mir_module.joints.append(obj)
            else:
                pm.delete(obj)

        mir_module.rig()

        # Mirror Ctrls
        for src, dst in zip(self.all_ctrls, mir_module.all_ctrls):
            control_shape_mirror(src, dst)

        # Do mirror connection for metadata
        self.metaNode.message.connect(mir_module.metaNode.mirrored_from)

        return mir_module

