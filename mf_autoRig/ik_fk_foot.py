import pymel.core as pm

sel = pm.selected()
#pm.addAttr(selection, longName="extraAttr", attributeType='enum', en='__________', keyable=True)
# pm.addAttr(selection, longName="outerBank", attributeType='float', min=-10, max=10, defaultValue=0, keyable=True)
# pm.addAttr(selection, longName="innerBank", attributeType='float', min=-10, max=10, defaultValue=0, keyable=True)
# pm.addAttr(selection, longName="heelLift", attributeType='float', min=-10, max=10, defaultValue=0, keyable=True)
# pm.addAttr(selection, longName="heelSwivel", attributeType='float', min=-10, max=10, defaultValue=0, keyable=True)
# pm.addAttr(selection, longName="toeLift", attributeType='float', min=-10, max=10, defaultValue=0, keyable=True)
# pm.addAttr(selection, longName="toeSwivel", attributeType='float', min=-10, max=10, defaultValue=0, keyable=True)
# pm.addAttr(selection, longName="ballRoll", attributeType='float', min=-10, max=10, defaultValue=0, keyable=True)
#
print(sel)
attrName = '.spread'
rotation = '.rotateX'

values = [(0, 0), (10, 21)]
for val in values:
    pm.setDrivenKeyframe(sel[1]+rotation, currentDriver=sel[0]+attrName,
                         driverValue=val[0], value=val[1])

# pm.setDrivenKeyframe(selection[1]+rotation, currentDriver=selection[0]+attrName,
#                      driverValue=0, value=0)
# pm.setDrivenKeyframe(selection[1]+rotation, currentDriver=selection[0]+attrName,
#                      driverValue=10, value=90)
# pm.setDrivenKeyframe(selection[1]+rotation, currentDriver=selection[0]+attrName,
#                      driverValue=-10, value=-30)