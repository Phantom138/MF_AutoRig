import pymel.core as pm

import importlib
import mf_autoRig.lib.useful_functions
importlib.reload(mf_autoRig.lib.useful_functions)
from mf_autoRig.lib.useful_functions import *

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



class Foot:
    def __init__(self, joints):
        self.skin_jnts = joints[:-1]

        self.fk_jnts = create_fk_jnts(joints)
        self.fk_ctrls = create_fk_ctrls(self.fk_jnts)

        # Create ik joints for foot
        self.ik_jnts = pm.duplicate(joints)
        for jnt in self.ik_jnts:
            match = re.search('([a-zA-Z]_[a-zA-Z]+\d*)_', jnt.name())
            name = match.group(1)
            name += df.ik_sff + df.jnt_sff

            pm.rename(jnt, name)

        self.ikfk_constraints = constraint_ikfk(joints, self.ik_jnts, self.fk_jnts)
        print(self.ikfk_constraints)
        match = re.match('(^[A-Za-z]_)\w+', joints[0].name())
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

    def connectAttributes(self, locators, leg):
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
        pm.parent(self.ball_ikHandle, locators[3])
        pm.parent(self.toe_ikHandle, locators[2])
        pm.parent(leg.ikHandle, locators[4])

        # Connect to ik_ctrl
        ik_ctrl = leg.ik_ctrls_grp.getChildren()[0].getChildren()[0]

        connections = {
            'outerBank': [locators[0], 'rotateZ', [(-10, 30), (10, -90)]],
            'innerBank': [locators[1], 'rotateZ', [(-10, 30), (10, -30)]],
            'heelLift': [locators[2], 'rotateX', [(-10, -15), (10, 30)]],
            'heelSwivel': [locators[2], 'rotateY', [(-10, -30), (10, 30)]],
            'toeLift': [locators[3], 'rotateX', [(-10, -30), (10, 50)]],
            'toeSwivel': [locators[3], 'rotateY', [(-10, -20), (10, 21)]],
            'ballRoll': [locators[4], 'rotateX', [(-10, -20), (10, 30)]],
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
        locator_grp = locators[0].getParent(1)
        pm.parentConstraint(ik_ctrl, locator_grp, maintainOffset=True)
