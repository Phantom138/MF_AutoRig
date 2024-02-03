import pymel.core as pm

from mf_autoRig.lib.useful_functions import *
from mf_autoRig.modules.Module import Module

import mf_autoRig.lib.defaults as df


# loc = ['L_outerbank_loc', 'L_innerrbank_loc', 'L_heel_loc', 'L_toe_tip_loc', 'L_ball_loc']
# l_locators = []
#
# for locator in loc:
#     l_locators.append(pm.PyNode(locator))
#
# loc = ['R_outerbank_loc', 'R_innerrbank_loc', 'R_heel_loc', 'R_toe_tip_loc', 'R_ball_loc']
# r_locators = []
#
# for locator in loc:
#     r_locators.append(pm.PyNode(locator))
#
# locators = []
# locators.append(l_locators)
# locators.append(r_locators)


class Foot(Module):
    meta_args = {
        'guides': {'attributeType': 'message', 'm': True},
        'joints': {'attributeType': 'message', 'm': True},
        'fk_ctrls': {'attributeType': 'message', 'm': True},
        'locators': {'attributeType': 'message', 'm': True},
    }

    def __init__(self, name, meta=False):
        super().__init__(name, self.meta_args, meta)
        self.side = name.split('_')[0]
        self.guides = None
        pass

    @classmethod
    def create_from_meta(cls, metaNode):
        foot = super().create_from_meta(metaNode)
        return foot

    def create_guides(self, ankle_guide=None, pos=None):
        self.guides = []
        if pos is None:
            pos = [(0,0,0), (0,-2,5), (0,-4,10)]

        if ankle_guide is not None:
            pos = pos[1:]

        # Create joint guides at the right pos
        for i,p in enumerate(pos):
            jnt = pm.createNode('joint', name=f"{self.name}{i+1:02}_guide{df.jnt_sff}")
            pm.xform(jnt, translation=p)

            self.guides.append(jnt)

        # Locators
        locator_grp = self.__create_base_locators()

        # Group guides
        guides_grp = pm.createNode('transform', name=f"{self.name}_guide{df.grp_sff}")
        pm.parent(self.guides, guides_grp)
        pm.parent(locator_grp, guides_grp)
        pm.parent(guides_grp, get_group(df.rig_guides_grp))

        # Constraint to ankle if there
        if ankle_guide is not None:
            pm.parentConstraint(ankle_guide, guides_grp, skipRotate=['x', 'y', 'z'], maintainOffset=False)
            self.guides.insert(0,ankle_guide)


    def __create_base_locators(self):
        self.locators = []
        pos = [(2,-3,5), (-2,-3,5), (0,-3,-3)]

        locator_names = ['outer_loc', 'inner_loc', 'heel_loc']

        # Create locators
        for trs, loc_name in zip(pos, locator_names):
            loc = pm.spaceLocator(name=f'{self.name}_{loc_name}')
            pm.xform(loc, t=trs)
            self.locators.append(loc)

        # Group locator guides
        locator_grp = pm.group(self.locators, name=f"{self.name}_locator{df.grp_sff}")

        return locator_grp

    def __create_locators_from_joints(self):
        """function that creates tip and ball locators based on joints"""
        locator_names=['tip_loc', 'ball_loc']

        # Get joints without start_jnt, and reverse it
        jnts = self.joints[1:]
        jnts.reverse()

        # Create locators at the jnt positions, match rotation only for ball_loc
        for loc_name, jnt in zip(locator_names, jnts):
            loc = pm.spaceLocator(name=f'{self.name}_{loc_name}')
            self.locators.append(loc)
            pm.matchTransform(loc, jnt, pos=True)

    def create_joints(self):
        self.joints = create_joints_from_guides(self.name, self.guides)
        self.__create_locators_from_joints()

        pm.parent(self.locators, world=True)
        # Parent locators one under the other
        for i in range(len(self.locators)-1, 0, -1):
            pm.parent(self.locators[i], self.locators[i-1])

    def rig(self):
        self.skin_jnts = self.joints[:-1]

        # Create FK
        self.fk_jnts = create_fk_jnts(self.joints)
        self.fk_ctrls = create_fk_ctrls(self.fk_jnts)

        # Create ik joints for foot
        self.ik_jnts = pm.duplicate(self.joints)
        for i,jnt in enumerate(self.ik_jnts):
            pm.rename(jnt,f'{self.name}{i+1:02}{df.ik_sff}{df.jnt_sff}')

        self.ikfk_constraints = constraint_ikfk(self.joints, self.ik_jnts, self.fk_jnts)

        match = re.match('(^[A-Za-z]_)\w+', self.joints[0].name())
        side = match.group(1)

        self.ball_ikHandle = \
        pm.ikHandle(name=side + 'ball' + df.ik_sff + df.loc_sff, startJoint=self.ik_jnts[0], endEffector=self.ik_jnts[1],
                    solver='ikSCsolver')[0]
        self.toe_ikHandle = \
        pm.ikHandle(name=side + 'toe' + df.ik_sff + df.loc_sff, startJoint=self.ik_jnts[1], endEffector=self.ik_jnts[2],
                    solver='ikSCsolver')[0]

        # Hide ik and fk joints
        self.ik_jnts[0].visibility.set(0)
        self.fk_jnts[0].visibility.set(0)

        # Group joints
        jnt_grp = pm.group(self.ik_jnts[0], self.fk_jnts[0], self.joints[0], name=f'{self.name}_{df.joints_grp}')
        pm.parent(jnt_grp, get_group(df.joints_grp))

    def connectAttributes(self, leg):
        # Get ik_ctrl
        ik_ctrl = leg.ik_ctrls_grp.getChildren()[0].getChildren()[0]

        # Create tidy group for locators
        locator_grp = pm.createNode('transform', name=f'{self.name}_loc{df.grp_sff}')
        pm.matchTransform(locator_grp, ik_ctrl, position=True)
        pm.parent(self.locators[0], locator_grp)

        # Remove leg parent constraint for the ikHandle
        for constraint in pm.listRelatives(leg.ikHandle):
            if isinstance(constraint, pm.nodetypes.ParentConstraint):
                pm.delete(constraint)

        # Connect foot ik fk constraints to leg switch
        reverse_sw = leg.switch.IkFkSwitch.listConnections(type='reverse')[0]

        for constraint in self.ikfk_constraints:
            weights = constraint.getWeightAliasList()

            for weight in weights:
                name = weight.longName(fullPath=False)
                # If ik weight connect to reverse
                if df.ik_sff in name:
                    reverse_sw.outputX.connect(weight)
                # If fk weight connect to switch
                if df.fk_sff in name:
                    leg.switch.IkFkSwitch.connect(weight)

        # Parent foot fk ctrls grp under leg fk ctrls grp
        pm.parent(self.fk_ctrls[0].getParent(1), leg.fk_ctrls[-1])

        # Parent ik handles under locators
        # Locators order : outerbank, innerbank, heel, toe_tip, ball !!
        pm.parent(self.ball_ikHandle, self.locators[3])
        pm.parent(self.toe_ikHandle, self.locators[2])
        pm.parent(leg.ikHandle, self.locators[4])

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


        # Constraint leg ik_jnt to foot ik_jnt start
        pm.parentConstraint(leg.ik_jnts[-1], self.ik_jnts[0])

        # Constraint ik_ctrl to locator grp
        pm.parentConstraint(ik_ctrl, locator_grp, maintainOffset=True)

    def mirror(self):
        if self.side == 'L':
            name = self.name.replace('L_', 'R_')
        elif self.side == 'R':
            name = self.name.replace('R_', 'L_')



        mir_module=Foot(name, meta=self.meta)

        # Mirror locators
        mir_module.locators = pm.duplicate(self.locators, parentOnly=True)
        print('mirrored_locators', mir_module.locators)

        # Mirror locators
        import pymel.core as pm

        sl = pm.selected()

        dup = pm.duplicate(sl[0], renameChildren=True)

        print(dup)

        lst = pm.listRelatives(dup[0], ad=True)
        print(lst)
        lst.append(dup[0])

        res = []

        for d in lst:
            try:
                sh = d.getShape()
                if isinstance(sh, pm.nt.Locator):
                    res.append(d)
                else:
                    pm.delete(d)
            except:
                pass

        mir_grp = pm.createNode('transform')

        return mir_module