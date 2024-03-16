"""
File adapted from tanaydimri
"""

import maya.cmds as cmds
from shiboken2 import wrapInstance
from PySide2 import QtGui, QtCore, QtUiTools, QtWidgets
import maya.OpenMayaUI as omui
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

from mf_autoRig import log
from mf_autoRig.UI.utils.loadUI import loadUi

def maya_main_window():
    """
    This function gets the pointer to the Maya's Main window.
    Our window will be parented under this.
    """
    pointer = omui.MQtUtil.mainWindow()
    return wrapInstance(int(pointer), QtWidgets.QWidget)

def delete_workspace_control(name):
    control = name + 'WorkspaceControl'
    if cmds.workspaceControl(control, q=True, exists=True):
        log.info("Deleting workspace Control")
        cmds.workspaceControl(control, e=True, close=True)
        cmds.deleteUI(control, control=True)

class UITemplate(MayaQWidgetDockableMixin, QtWidgets.QDialog):
    def __init__(self, widget_title, ui_path):
        """
        Init method for the UI class.
        Initializes and sets up the UI.
        :param string widget_title: Title of the widget that needs to be loaded.
        :param string ui_file: Path to the UI file that is to be loaded.
        :param PySide2.QtWidgets.QWidget parent: Maya main window object to parent our widget to.
        """
        parent = maya_main_window()
        super(UITemplate, self).__init__(parent)
        self.widget_title = widget_title
        self.ui_path = ui_path

        # loadUi(ui_path, self)

        uifile = QtCore.QFile(ui_path)
        uifile.open(QtCore.QFile.ReadOnly)
        self.ui = QtUiTools.QUiLoader().load(uifile, parentWidget=self)
        uifile.close()

        self.resize(400, 500)

        self.centralLayout = QtWidgets.QVBoxLayout()
        self.centralLayout.setContentsMargins(0, 0, 0, 0)
        self.centralLayout.addWidget(self.ui)
        self.setLayout(self.centralLayout)


        self.setObjectName(widget_title)
        self.setWindowTitle(widget_title)

