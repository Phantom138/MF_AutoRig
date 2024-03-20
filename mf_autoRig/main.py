from unload_packages import unload_packages
unload_packages(silent=True, packages=["mf_autoRig"])
import mf_autoRig.UI.modifyWindow.modifyWindowUI as editModulesUI
import mf_autoRig.UI.createWindow.mayaUI as createModulesUI
import mf_autoRig.UI.toolsWindow.toolsWindow as toolsWindow
import mf_autoRig.UI.modifyWindow.modifyWindowUI as modifyWindow

if __name__ == '__main__':
    createModulesUI.showWindow()
    toolsWindow.showWindow()
    modifyWindow.showWindow()
