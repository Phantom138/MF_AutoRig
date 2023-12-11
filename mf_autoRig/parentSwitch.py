import re

import pymel.core as pm


def parent_switch(object, drivers, jnt, hasGroup=True):
    # Get nice name for object
    object_match = re.search(r'^[a-zA-Z]_*[a-zA-Z]+\d*', object.name())
    object_name = object_match.group(0)

    # Create Locators
    locators = []
    enum_names = ''

    if hasGroup:
        grp = object.getParent(1)
    else:
        grp = object

    for driver in drivers:
        # Get nice name for drivers, to be used in enum
        # If it has a prefix, take only what is after
        if re.search(r'^[a-zA-Z]_', driver.name()):
            print(f'{driver.name()} starts with prefix')
            driver_match = re.search(r'^[a-zA-Z]_([a-zA-Z]+\d*)', driver.name())
            driver_name = driver_match.group(1)
        else:
            driver_match = re.search('^([a-zA-Z]+)_', driver.name())
            driver_name = driver_match.group(1)

        enum_names += driver_name+':'

        # Create locator and parent it in the right place
        loc = pm.spaceLocator(name=f'{object_name}_{driver_name}_space_loc')
        pm.matchTransform(loc, jnt)
        pm.parent(loc, driver)
        locators.append(loc)

    # Create enum attributs, enum_names = Root:World:...
    pm.addAttr(object, ln='parentSwitch', attributeType='enum', en=enum_names, k=True)

    # Create parent constriant
    print(locators)
    constraint = pm.parentConstraint(locators, grp, maintainOffset=True)
    weights = constraint.getWeightAliasList()

    for index, weight in enumerate(weights):
        # Get weight name for the condition
        weight_match = re.search(r'([a-zA-Z]+_[a-zA-Z]+)_space_loc', weight.name())
        weight_name = weight_match.group(1)

        # Create condition and connect it accordingly
        condition = pm.createNode('condition', name=weight_name+'_condition')

        object.parentSwitch.connect(condition.firstTerm)

        condition.secondTerm.set(index)
        condition.colorIfTrueR.set(1)
        condition.colorIfFalseR.set(0)
        condition.outColorR.connect(weight)


obj = pm.PyNode('M_eyeAim_ctrl')
jnt = pm.PyNode('M_head_skin_jnt')
drivers = [pm.PyNode("M_head_ctrl"), pm.PyNode("Root_Ctrl"), pm.PyNode("World_Ctrl")]

parent_switch(obj, drivers, jnt)
