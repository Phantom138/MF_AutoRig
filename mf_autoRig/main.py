from unload_packages import unload_packages
unload_packages(silent=True, packages=["mf_autoRig"])
import mf_autoRig
import maya.cmds as cmds
import mf_autoRig.UI.mayaUI as uiTemplate
from mf_autoRig.modules.Foot import Foot

if __name__ == '__main__':
    cmds.file(new=True, f=True)
    # foot = Foot("L_foot")
    # foot.create_guides()
    # foot.create_joints()
    # foot.rig()
    uiTemplate.openWindow()
