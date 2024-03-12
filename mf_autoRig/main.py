import logging
from unload_packages import unload_packages
unload_packages(silent=True, packages=["mf_autoRig"])
import mf_autoRig
import maya.cmds as cmds
import mf_autoRig.UI.mayaUI as UI
from mf_autoRig.modules.Body import Body
import mf_autoRig.lib.defaults as df

if __name__ == '__main__':
    # cmds.file(new=True, f=True)
    # foot = Foot("L_foot")
    # foot.create_guides()
    # foot.create_joints()
    # foot.rig()
    # body = Body()
    # body.create_guides(df.default_pos)
    # body.create_joints()
    # body.rig()

    UI.showWindow()
