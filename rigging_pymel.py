import pymel.core as pm

#f = pm.newFile(f=1)
print(pm.ls(type='camera'))
cam = pm.ls(type='camera')[0]
print(cam.getAspectRatio())