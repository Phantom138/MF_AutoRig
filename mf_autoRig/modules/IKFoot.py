from pprint import pprint

import pymel.core as pm

from mf_autoRig.utils.general import *
from mf_autoRig.modules.Module import Module
from mf_autoRig import log

import mf_autoRig.utils.defaults as df
import mf_autoRig.utils as utils
import mf_autoRig.utils.color_tools as color

class IKFoot(Module):
    meta_args = {
        'creation_attrs':{
            **Module.meta_args['creation_attrs']
        },

        'module_attrs': {
            **Module.meta_args['module_attrs'],
        },

        'config_attrs':{
            **Module.meta_args['config_attrs'],
        },
        'info_attrs':{
            **Module.meta_args['info_attrs'],
            'guides': {'attributeType': 'message', 'm': True},
            'locators_guides': {'attributeType': 'message', 'm': True},
            'joints': {'attributeType': 'message', 'm': True},
            'all_ctrls': {'attributeType': 'message', 'm': True},
        }
    }
    connectable_to = ['Limb']
    def __init__(self, name, meta=True):
        super().__init__(name, self.meta_args, meta)

        self.guides = []
        self.locators_guides = []

        self.joints = []
        self.fk_ctrls = []
        self.ik_jnts = []
        self.fk_jnts = []
        self.locators = []
        self.all_ctrls = []

        self.reset()

    def reset(self):
        super().reset()
        self.guides = []
        self.locators_guides = []

        self.joints = []
        self.fk_ctrls = []
        self.ik_jnts = []
        self.fk_jnts = []
        self.locators = []

        self.all_ctrls = []


    def create_guides(self, pos: dict=None):
        self.guides = []
        if pos is None:
            pos = {
                'guides': [(0,0,0), (0,-2,5), (0,-4,10)],
                'locators': [(2,-3,5), (-2,-3,5), (0,-3,-3)]
            }

        self.guide_grp = pm.createNode('transform', name=f'{self.name}_guide_grp')
        pm.parent(self.guide_grp, get_group(df.rig_guides_grp))

        self.guides = utils.create_guide_chain(self.name, 3, pos['guides'], parent=self.guide_grp)

        # Locators
        loc_guides_grp = self.__create_locators_guides(pos)

        # Group guides
        pm.parent(self.guides, self.guide_grp)
        pm.parent(loc_guides_grp, self.guide_grp)
        pm.parent(self.guide_grp, get_group(df.rig_guides_grp))

        if self.meta:
            self.save_metadata()

    def __create_locators_guides(self, pos: dict):
        self.locators_guides = []

        loc_pos = pos['locators']
        locator_names = ['outer_loc', 'inner_loc', 'heel_loc']

        # Create locators
        for trs, loc_name in zip(loc_pos, locator_names):
            loc = pm.spaceLocator(name=f'{self.name}_{loc_name}')
            pm.xform(loc, t=trs)
            self.locators_guides.append(loc)

        # Group locator guides
        locator_grp = pm.group(self.locators_guides, name=f"{self.name}_locators_guides{df.grp_sff}")

        color.set_color(self.locators_guides, "red")
        return locator_grp

    def __create_locators(self):
        """function that creates tip and ball locators based on joints"""
        self.locators = []
        # create first from guides
        for loc_guide in self.locators_guides:
            loc = pm.spaceLocator(name=f'{loc_guide.name()}')
            pm.matchTransform(loc, loc_guide, pos=True)
            self.locators.append(loc)

        # create from joints
        locator_names=['tip_loc', 'ball_loc']

        # Get joints without start_jnt, and reverse it
        jnts = self.joints[1:]
        jnts.reverse()

        # Create locators at the jnt positions
        for loc_name, jnt in zip(locator_names, jnts):
            loc = pm.spaceLocator(name=f'{self.name}_{loc_name}')
            self.locators.append(loc)
            pm.matchTransform(loc, jnt, pos=True)


    def create_joints(self):
        # Get just the guides for the joints
        self.joints = utils.create_joints_from_guides(self.name, self.guides, aimVector=self.jnt_orient_main, upVector=self.jnt_orient_secondary)

        self.__create_locators()

        pm.parent(self.locators, world=True)
        # Parent locators one under the other
        for i in range(len(self.locators)-1, 0, -1):
            pm.parent(self.locators[i], self.locators[i-1])

        # Create tidy group for locators
        self.locator_grp = pm.createNode('transform', name=f'{self.name}_loc{df.grp_sff}')
        pm.matchTransform(self.locator_grp, self.joints[0], position=True)
        pm.parent(self.locators[0], self.locator_grp)

        # Create drivers grp
        self.drivers_grp = pm.createNode('transform', name=f'{self.name}_{df.drivers_grp}')
        pm.parent(self.drivers_grp, get_group(df.drivers_grp))
        pm.parent(self.locator_grp, self.drivers_grp)

        if self.meta:
            self.save_metadata()

    def rig(self):
        # Create FK
        self.fk_jnts = utils.create_fk_jnts(self.joints)
        self.fk_ctrls = utils.create_fk_ctrls(self.fk_jnts)
        self.all_ctrls.extend(self.fk_ctrls)
        color.auto_color(self.fk_ctrls)

        # Create ik joints for foot
        self.ik_jnts = pm.duplicate(self.joints)
        for i,jnt in enumerate(self.ik_jnts):
            pm.rename(jnt,f'{self.name}{i+1:02}{df.ik_sff}{df.jnt_sff}')

        self.ikfk_constraints = utils.constraint_ikfk(self.joints, self.ik_jnts, self.fk_jnts)

        match = re.match('(^[A-Za-z]_)\w+', self.joints[0].name())
        side = match.group(1)

        self.ball_ikHandle = \
        pm.ikHandle(name=side + 'ball' + df.ik_sff + df.loc_sff, startJoint=self.ik_jnts[0], endEffector=self.ik_jnts[1],
                    solver='ikSCsolver')[0]
        self.toe_ikHandle = \
        pm.ikHandle(name=side + 'toe' + df.ik_sff + df.loc_sff, startJoint=self.ik_jnts[1], endEffector=self.ik_jnts[2],
                    solver='ikSCsolver')[0]

        # Parent iks to ikHandle grp
        pm.parent(self.ball_ikHandle, self.toe_ikHandle, get_group(df.ikHandle_grp))

        # Hide ik and fk joints
        self.ik_jnts[0].visibility.set(0)
        self.fk_jnts[0].visibility.set(0)

        # Group joints
        self.joints_grp = pm.group(self.ik_jnts[0], self.fk_jnts[0], self.joints[0], name=f'{self.name}_{df.joints_grp}')
        pm.parent(self.joints_grp, get_group(df.joints_grp))

        # Create control grp
        self.control_grp = pm.createNode('transform', name=f'{self.name}{df.control_grp}')
        pm.parent(self.fk_ctrls[0].getParent(1), self.control_grp)

        # Group under root
        pm.parent(self.control_grp, get_group(df.root))

        if self.meta:
            self.save_metadata()

    def __create_driven_keys(self, ik_ctrl):
        connections = {
            'outerBank': [self.locators[0], 'rotateZ', [(-10, 30), (10, -90)]],
            'innerBank': [self.locators[1], 'rotateZ', [(-10, 30), (10, -30)]],
            'heelLift': [self.locators[2], 'rotateX', [(-10, -15), (10, 30)]],
            'heelSwivel': [self.locators[2], 'rotateY', [(-10, -30), (10, 30)]],
            'toeLift': [self.locators[3], 'rotateX', [(-10, -30), (10, 50)]],
            'toeSwivel': [self.locators[3], 'rotateY', [(-10, -20), (10, 21)]],
            'ballRoll': [self.locators[4], 'rotateX', [(-10, -20), (10, 30)]],
        }

        # Create driven keys and attributes
        for attr in connections:
            pm.addAttr(ik_ctrl, longName=attr, min=-10, max=10, keyable=True)

            # Get rotation and values from dictionary
            locator = connections[attr][0]
            rotation = f'.{connections[attr][1]}'
            values = connections[attr][2]

            # Set 0 driven key
            pm.setDrivenKeyframe(locator + rotation, currentDriver=ik_ctrl + f'.{attr}', driverValue=0, value=0)
            # Set the rest
            for value in values:
                pm.setDrivenKeyframe(locator + rotation, currentDriver=ik_ctrl + f'.{attr}', driverValue=value[0],
                                     value=value[1])


    def connect(self, leg):
        if not self.check_if_connected(leg):
            log.warning(f"{self.name} not connected to {leg.name}")
            return

        # Get ik_ctrl
        ik_ctrl = leg.ik_ctrls[0]

        # Remove leg parent constraint for the ikHandle
        for constraint in pm.listRelatives(leg.ikHandle):
            if isinstance(constraint, pm.nodetypes.ParentConstraint):
                pm.delete(constraint)

        # Connect foot ik fk constraints to leg switch
        reverse_sw = leg.switch.IkFkSwitch.listConnections(type='reverse')[0]

        for constraint in self.ikfk_constraints:
            weights = constraint.getWeightAliasList()
            print(weights)
            for weight in weights:
                name = weight.longName(fullPath=False)
                # If ik weight connect to reverse
                if df.ik_sff in name:
                    reverse_sw.outputX.connect(weight)
                # If fk weight connect to switch
                if df.fk_sff in name:
                    leg.switch.IkFkSwitch.connect(weight)

        # Connect switch to visibility
        leg.switch.IkFkSwitch.connect(self.fk_ctrls[0].getParent(1).v)

        # Parent foot fk ctrls grp under leg fk ctrls grp
        pm.parentConstraint(leg.fk_ctrls[-1], self.fk_ctrls[0].getParent(1), maintainOffset=True)

        # Parent ik handles under locators
        # Locators order : outerbank, innerbank, heel, toe_tip, ball !!
        pm.parent(self.ball_ikHandle, self.locators[3])
        pm.parent(self.toe_ikHandle, self.locators[2])
        pm.parent(leg.ikHandle, self.locators[4])

        self.__create_driven_keys(ik_ctrl)

        # Constraint leg ik_jnt to foot ik_jnt start
        pm.parentConstraint(leg.ik_joints[-1], self.ik_jnts[0])

        # Constraint ik_ctrl to locator grp
        pm.parentConstraint(ik_ctrl, self.locator_grp, maintainOffset=True)