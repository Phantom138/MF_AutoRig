import re

import pathlib

import mf_autoRig.UI.createWindow.modulePage as modPages
from mf_autoRig.UI.utils.UI_Template import UITemplate, delete_workspace_control
from mf_autoRig.modules import Limb, Spine, Clavicle, Hand, Body, FKFoot
from mf_autoRig.modules.Toon import BendyLimb
import mf_autoRig.modules.module_tools as crMod
import mf_autoRig.lib.defaults as df

WORK_PATH = pathlib.Path(__file__).parent.resolve()

#TODO: create separate window for module management

class_name_map = {
    'Spine': Spine.Spine,
    'Clavicle': Clavicle.Clavicle,
    'Limb': Limb.Limb,
    'BendyLimb': BendyLimb.BendyLimb,
    'Hand': Hand.Hand,
    'FKFoot': FKFoot.FKFoot,
}


class MayaUI(UITemplate):
    def __init__(self, title):
        ui_path = f'{WORK_PATH}\mainWidget.ui'

        super().__init__(widget_title=title, ui_path=ui_path)

        self.create_module_tabs()
        self.ui.tabWidget.removeTab(0)
        self.ui.tabWidget.removeTab(1)

    def create_module_tabs(self):
        for module in class_name_map:
            self.ui.mdl_comboBox.addItem(module)

            if module == 'Hand':
                module_tab = modPages.HandPage(class_name_map.get(module))
            elif module == 'BendyLimb':
                module_tab = modPages.BendyLimbPage(class_name_map.get(module))
            elif module == 'Spine':
                module_tab = modPages.SpinePage(class_name_map.get(module))
            else:
                module_tab = modPages.ModulePage(class_name_map.get(module))
            self.ui.mdl_stackedTabs.addWidget(module_tab)

        self.ui.mdl_comboBox.activated.connect(self.ui.mdl_stackedTabs.setCurrentIndex)

    def auto_guides(self):
        self.body = Body.Body(
            do_hands=self.ui.box_hands.isChecked(),
            do_clavicles=self.ui.box_clavicles.isChecked(),
            do_feet=self.ui.box_feet.isChecked()
        )
        self.body.create_guides(df.default_pos)

    def auto_rig(self):
        self.body.create_joints()
        self.body.rig()


def showWindow():
    title = 'Auto Rig'

    delete_workspace_control(title)

    ui = MayaUI(title)
    ui.show(dockable=True)
