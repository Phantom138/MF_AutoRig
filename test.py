import pymel.core as pm
import re

grp_sff = '_grp'
ctrl_sff = '_ctrl'
jnt_sff = '_jnt'
end_sff = '_end'
skin = '_skin'
ik_sff = '_ik'
fk_sff = '_fk'
pole_sff = '_pole'
attr_sff = '_attr'


CTRL_SCALE = 2

def connect_hand(handJnt, arm_end_jnt, arm_ik_ctrl, arm_fk_ctrl):
    match = re.search('([a-zA-Z]_([a-zA-Z]+))\d*_', handJnt.name())
    base_name = match.group(1)

    # Create controller and controller group, parenting the two of them
    grp = pm.createNode('transform', name=base_name + ctrl_sff + grp_sff)
    hand_ctrl = pm.circle(nr=(0, 1, 0), c=(0, 0, 0), radius=CTRL_SCALE, name=base_name + ctrl_sff, constructionHistory=False)
    pm.parent(hand_ctrl, grp)

    # Match transforms and parent constrain controller to joint
    pm.matchTransform(grp, handJnt)
    pm.parentConstraint(hand_ctrl, handJnt, maintainOffset=True)

    # Point constraint
    pm.pointConstraint(arm_end_jnt, hand_ctrl)

    # Create locators
    # IK locator
    ik_loc = pm.spaceLocator(name=base_name+'_ik_space_loc')
    ik_loc_grp = pm.createNode('transform', name = base_name+'_ik_loc_grp')
    pm.parent(ik_loc, ik_loc_grp)
    pm.matchTransform(ik_loc_grp, handJnt)
    pm.parent(ik_loc_grp, arm_ik_ctrl)

    constraint = pm.orientConstraint(ik_loc, hand_ctrl)
    print(pm.listAttr(constraint))
    print(constraint.listAliases())

    # FK locator
    fk_loc = pm.spaceLocator(name=base_name+'_fk_space_loc')
    fk_loc_grp = pm.createNode('transform', name=base_name + '_ik_loc_grp')
    pm.parent(fk_loc, fk_loc_grp)
    pm.matchTransform(fk_loc_grp, handJnt)
    pm.parent(fk_loc_grp, arm_fk_ctrl)


handJnt = pm.PyNode('R_hand_skin_jnt')
arm_ik_ctrl = pm.PyNode('R_arm01_ik_ctrl')
arm_fk_ctrl = pm.PyNode('R_arm02_fk_ctrl')
arm_end_jnt = pm.PyNode('R_arm03_end_jnt')

connect_hand(handJnt, arm_end_jnt, arm_ik_ctrl, arm_fk_ctrl)