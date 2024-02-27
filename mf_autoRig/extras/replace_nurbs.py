import maya.cmds as cmds

'''
Replaces second nurbs curve selected with the first one
'''

selection = cmds.ls(selection=True)

replacer_trs = selection[0] # Get replacer transfom
replacer_shape = cmds.listRelatives(replacer_trs, shapes=True)

target_trs = selection[1] # Get target transfom
target_shape = cmds.listRelatives(target_trs, shapes=True)

#Check if selection is only nurbs curves
if cmds.nodeType(replacer_shape) != 'nurbsCurve' or cmds.nodeType(target_shape) != 'nurbsCurve':
    cmds.error("Please select NURBS curves!")
    exit()

cmds.parent(replacer_shape, target_trs, relative=True, shape=True)
#Clean-Up
cmds.delete(target_shape)
cmds.delete(replacer_trs)
cmds.rename(replacer_shape, target_trs+'Shape')
