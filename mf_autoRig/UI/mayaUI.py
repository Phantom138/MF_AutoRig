import re

from PySide2 import QtWidgets

import pathlib

import mf_autoRig.UI.modulePage as modPages
from mf_autoRig.UI.utils.UI_Template import UITemplate, delete_workspace_control
from mf_autoRig.modules import Limb, Spine, Clavicle, Hand, Body, Foot
import mf_autoRig.modules.createModule as crMod
import mf_autoRig.lib.defaults as df
from mf_autoRig.UI.utils.loadUI import loadUi

WORK_PATH = pathlib.Path(__file__).parent.resolve()

#TODO: create separate window for module management

class_name_map = {
    'Limb': Limb.Limb,
    'Arm': Limb.Arm,
    'Leg': Limb.Leg,
    'Clavicle': Clavicle.Clavicle,
    'Spine': Spine.Spine,
    'Hand': Hand.Hand,
    'Foot': Foot.Foot
}


class MayaUI(UITemplate):
    def __init__(self, title):
        ui_path = f'{WORK_PATH}\mainWidget.ui'

        super().__init__(widget_title=title, ui_path=ui_path)

        self.connect_widgets()


        self.create_module_tabs()


    def connect_widgets(self):
        self.ui.btn_close.clicked.connect(self.closeWindow)

        # Auto rig Tab
        self.ui.auto_btn_guides.clicked.connect(self.auto_guides)
        self.ui.auto_btn_rig.clicked.connect(self.auto_rig)

        # Connect Tab
        self.ui.btn_updateLists.clicked.connect(self.updateLists)
        self.ui.conn_source.itemSelectionChanged.connect(self.show_destinations)
        self.ui.btn_connect.clicked.connect(self.connect_selection)

    def create_module_tabs(self):
        for module in class_name_map:
            self.ui.mdl_comboBox.addItem(module)

            if module == 'Hand':
                module_tab = modPages.HandPage(class_name_map.get(module))
            else:
                module_tab = modPages.ModulePage(class_name_map.get(module))

            self.ui.mdl_stackedTabs.addWidget(module_tab)

        self.ui.mdl_comboBox.activated.connect(self.ui.mdl_stackedTabs.setCurrentIndex)

    def closeWindow(self):
        """
        Close window.
        """
        print('closing window')
        self.destroy()

    def auto_guides(self):
        print("Running auto guides")
        self.body = Body.Body()
        self.body.create_guides(df.default_pos)

    def auto_rig(self):
        print("Running auto rig")
        self.body.create_joints()
        self.body.rig()

    def updateLists(self):
        self.ui.conn_source.clear()
        self.ui.conn_destination.clear()


        self.modules = crMod.get_all_modules()
        if self.modules is not None:
            for module in self.modules:
                # Get base name for adding to item
                name = module.name()
                search = re.search('META_(.*)', name)
                base_name = search.group(1)

                moduleType = module.moduleType.get()

                # Add item to list
                item = f'{base_name} <{moduleType}>'
                self.ui.conn_source.addItem(item)
                self.ui.conn_destination.addItem(item)

    def show_destinations(self):
        # Get source from modules list
        source_index = self.conn_source.currentRow()
        source = self.modules[source_index]

        return
        # Show only good connections
        moduleType = source.moduleType.get()
        if moduleType == 'Arm':
            self.enable_items('Clavicle')
        if moduleType == 'Leg':
            self.enable_items('Spine')
        if moduleType == 'Clavicle':
            self.enable_items('Spine')
        if moduleType == 'Hand':
            self.enable_items('Limb')
        if moduleType == 'Spine' or moduleType == 'Limb':
            self.enable_items('all of them')

    def enable_items(self, mtype):
        """
        function that disables elements from conn_destination that don't have the moduleType passed
        """
        self.dest_modules = []
        self.conn_destination.clear()
        for module in self.modules:
            moduleType = module.moduleType.get()
            if moduleType == mtype:
                print(module)
                # Get base name for adding to item
                name = module.name()
                search = re.search('META_(.*)', name)
                base_name = search.group(1)

                # Add item to list
                item = f'{base_name} <{moduleType}>'
                self.conn_destination.addItem(item)

                # Save modules to dest list
                self.dest_modules.append(module)

    def connect_selection(self):
        print("called connect_selection")
        dest_index = self.ui.conn_destination.currentRow()
        source_index = self.ui.conn_source.currentRow()

        metaNode = self.modules[source_index]
        obj = crMod.createModule(metaNode)
        print(obj)
        obj.mirror()
        return
        source = crMod.createModule(self.modules[source_index])
        dest = crMod.createModule(self.dest_modules[dest_index])
        print(f'Connecting {source} -> {dest}')
        source.connect(dest)

def showWindow():
    title = 'Auto Rig 2'

    delete_workspace_control(title)

    ui = MayaUI(title)
    ui.show(dockable=True)
