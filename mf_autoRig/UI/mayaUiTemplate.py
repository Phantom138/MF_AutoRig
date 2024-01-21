"""
Maya/QT UI template
Maya 2023
original code by isaacoster
"""

import maya.cmds as cmds
import maya.mel as mel
from maya import OpenMayaUI as omui
from shiboken2 import wrapInstance
from PySide2 import QtUiTools, QtCore, QtGui, QtWidgets
from functools import partial  # optional, for passing args during signal function calls

import pathlib
WORK_PATH = pathlib.Path(__file__).parent.resolve()
from mf_autoRig.modules import Limb, Torso, Foot, Hand

from datetime import datetime


class_name_map = {
    'Limb': Limb.Limb,
    'Clavicle': Torso.Clavicle,
    'Spine': Torso.Spine,
    'Hand': Hand.Hand,
}

class MayaUITemplate(QtWidgets.QWidget):
    """
    Create a default tool window.
    """
    window = None

    def __init__(self, parent=None):
        """
        Initialize class.
        """
        super(MayaUITemplate, self).__init__(parent=parent)
        self.setWindowFlags(QtCore.Qt.Window)
        self.widgetPath = f'{WORK_PATH}\mainWidget.ui'
        print(f"Started UI, using {self.widgetPath} file")
        self.widget = QtUiTools.QUiLoader().load(self.widgetPath)
        self.widget.setParent(self)
        # set initial window size
        #self.resize(200, 100)
        # locate UI widgets
        self.btn_close = self.widget.findChild(QtWidgets.QPushButton, 'btn_close')

        # assign functionality to buttons
        self.btn_close.clicked.connect(self.closeWindow)

        self.mdl_combo = self.widget.findChild(QtWidgets.QComboBox, 'mdl_comboBox')
        self.mdl_name = self.widget.findChild(QtWidgets.QLineEdit, 'mdl_name')
        self.mdl_btn_guides = self.widget.findChild(QtWidgets.QPushButton, 'mdl_btn_guides')
        self.mdl_btn_rig = self.widget.findChild(QtWidgets.QPushButton, 'mdl_btn_rig')

        self.mdl_combo.currentIndexChanged.connect(self.moduleIndexChanged)
        self.mdl_name.textChanged.connect(self.nameChanged)
        self.mdl_btn_guides.clicked.connect(self.mdl_createGuides)
        self.mdl_btn_rig.clicked.connect(self.mdl_createRig)

        # Disable Buttons
        self.mdl_btn_guides.setEnabled(False)
        self.mdl_btn_rig.setEnabled(False)


    def resizeEvent(self, event):
        """
        Called on automatically generated resize event
        """
        self.widget.resize(self.width(), self.height())

    def closeWindow(self):
        """
        Close window.
        """
        print('closing window')
        self.destroy()

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


def openWindow():
    """
    ID Maya and attach tool window.
    """
    # Maya uses this so it should always return True
    if QtWidgets.QApplication.instance():
        # Id any current instances of tool and destroy
        for win in (QtWidgets.QApplication.allWindows()):
            if 'myToolWindowName' in win.objectName():  # update this name to match name below
                win.destroy()

    # QtWidgets.QApplication(sys.argv)
    mayaMainWindowPtr = omui.MQtUtil.mainWindow()
    mayaMainWindow = wrapInstance(int(mayaMainWindowPtr), QtWidgets.QWidget)
    MayaUITemplate.window = MayaUITemplate(parent=mayaMainWindow)
    MayaUITemplate.window.setObjectName('myToolWindowName')  # code above uses this to ID any existing windows
    MayaUITemplate.window.setWindowTitle('Maya UI Template')
    MayaUITemplate.window.show()



