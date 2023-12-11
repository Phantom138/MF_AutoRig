import pymel.core as pm

def parent_switch(object, drivers, jnt):
    # Create Locators
    locators = []
    for driver in drivers:
        loc = pm.spaceLocator(name=f'{object.name()}_{driver.name()}_space_loc')
        pm.matchTransform(loc, jnt)

        locators.append(loc)
    for locator in locators:
        pm.parent()
    pm.addAttr(object, ln='parentSwitch', type='enum', k=True)

    #for locator in locators:
    print(locators)

obj = pm.PyNode('M_eye_aim_ctrl')
jnt = pm.PyNode('M_head_skin_jnt')
drivers = [pm.PyNode("M_head_skin_jnt"), pm.PyNode("Root_Ctrl")]
parent_switch(obj, drivers, jnt)