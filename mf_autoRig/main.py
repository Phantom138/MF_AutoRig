from unload_packages import unload_packages
unload_packages(silent=False, packages=["mf_autoRig"])
import mf_autoRig
import mf_autoRig.UI.mainWindow as ui
import mf_autoRig.UI.mayaUiTemplate as uiTemplate

if __name__ == '__main__':
    uiTemplate.openWindow()
