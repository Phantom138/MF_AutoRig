filepath_template = "{projectRoot}/assets/{assetType}/{assetName}/{task}/publish/{assetType}_{assetName}_{task}_publish.ma"
publishSet = 'publishGrp'

if not cmds.objExists(publishSet):
    print('Cant find publish group, cancelling publish')

projectRoot = "R:/myName"
assetType = cmds.getAttr(publishSet + '.assetType')
assetName = cmds.getAttr(publishSet + '.assetName')
task = cmds.getAttr(publishSet + '.task')

publishPath = filepath_template.format(projectRoot=projectRoot, assetType=assetType, assetName=assetName, task=task)
print(publishPath)