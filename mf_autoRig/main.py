from unload_packages import unload_packages
unload_packages(silent=True, packages=["mf_autoRig"])
import mf_autoRig.UI.modifyWindow.modifyWindowUI as editModulesUI
import mf_autoRig.UI.createWindow.mayaUI as createModulesUI

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
    editModulesUI.showWindow()
    createModulesUI.showWindow()
