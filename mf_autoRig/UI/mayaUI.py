"""
Maya/QT UI template
Maya 2023
original code by isaacoster
"""
import re

from maya import OpenMayaUI as omui
from shiboken2 import wrapInstance
from PySide2 import QtUiTools, QtCore, QtGui, QtWidgets
from PySide2.QtCore import Qt
from functools import partial  # optional, for passing args during signal function calls

import pathlib

from mf_autoRig.UI.UI_Template import UITemplate, delete_workspace_control
from mf_autoRig.modules import Limb, Spine, Clavicle, Hand, Body, Foot
import mf_autoRig.modules.createModule as crMod
import mf_autoRig.lib.defaults as df


WORK_PATH = pathlib.Path(__file__).parent.resolve()

class_name_map = {
    'Limb': Limb.Limb,
    'Clavicle': Clavicle.Clavicle,
    'Spine': Spine.Spine,
    'Hand': Hand.Hand,
    'Arm': Limb.Arm,
    'Leg': Limb.Leg,
    'Foot': Foot.Foot
}


class MayaUI(UITemplate):
    def __init__(self, title):
        ui_path = f'{WORK_PATH}\mainWidget.ui'

        super().__init__(widget_title=title, ui_path=ui_path)

        self.connect_widgets()

    def connect_widgets(self):
        # locate UI widgets
        self.btn_close = self.ui.findChild(QtWidgets.QPushButton, 'btn_close')
        self.btn_close.clicked.connect(self.closeWindow)

        # Auto rig Tab
        self.ui.auto_btn_guides.clicked.connect(self.auto_guides)
        self.ui.auto_btn_rig.clicked.connect(self.auto_rig)

        # Modules Tab
        self.mdl_combo = self.ui.findChild(QtWidgets.QComboBox, 'mdl_comboBox')
        self.mdl_combo.currentIndexChanged.connect(self.moduleIndexChanged)

        self.mdl_name = self.ui.findChild(QtWidgets.QLineEdit, 'mdl_name')
        self.mdl_name.textChanged.connect(self.nameChanged)

        self.mdl_btn_guides = self.ui.findChild(QtWidgets.QPushButton, 'mdl_btn_guides')
        self.mdl_btn_guides.clicked.connect(self.mdl_createGuides)

        self.mdl_btn_rig = self.ui.findChild(QtWidgets.QPushButton, 'mdl_btn_rig')
        self.mdl_btn_rig.clicked.connect(self.mdl_createRig)

        # Connect Tab
        self.btn_updateLists = self.ui.findChild(QtWidgets.QPushButton, 'btn_updateLists')
        self.btn_updateLists.clicked.connect(self.updateLists)

        self.conn_source = self.ui.findChild(QtWidgets.QListWidget, 'conn_source')
        self.conn_source.itemSelectionChanged.connect(self.show_destinations)
        self.conn_destination = self.ui.findChild(QtWidgets.QListWidget, 'conn_destination')

        self.btn_connect = self.ui.findChild(QtWidgets.QPushButton, 'btn_connect')
        self.btn_connect.clicked.connect(self.connect_selection)

        # Disable Buttons
        self.mdl_btn_guides.setEnabled(False)
        self.mdl_btn_rig.setEnabled(False)

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

    def moduleIndexChanged(self):
        self.mdl_name.clear()
        self.mdl_btn_guides.setEnabled(False)
        self.mdl_btn_rig.setEnabled(False)

    def nameChanged(self):
        name = self.mdl_name.text()
        if not name:
            self.mdl_btn_guides.setEnabled(False)
            self.mdl_btn_rig.setEnabled(False)
            return None

        self.mdl_btn_guides.setEnabled(True)

    def mdl_createGuides(self):
        name = self.mdl_name.text()
        option = self.mdl_combo.currentText()

        # init class
        selected_class = class_name_map.get(option)
        self.module = selected_class(name)

        self.module.create_guides()
        self.mdl_btn_rig.setEnabled(True)

    def mdl_createRig(self):
        if self.mdl_combo.currentText() == 'Hand':
            self.module.create_joints()
            self.module.create_hand()
            self.module.rig()
            return None

        self.module.create_joints()
        self.module.rig()

    def updateLists(self):
        self.conn_destination.clear()
        self.conn_source.clear()

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
                self.conn_source.addItem(item)
                self.conn_destination.addItem(item)

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
        dest_index = self.conn_destination.currentRow()
        source_index = self.conn_source.currentRow()

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
    title = 'Auto Rig'

    delete_workspace_control(title)

    ui = MayaUI(title)
    ui.show(dockable=True)
