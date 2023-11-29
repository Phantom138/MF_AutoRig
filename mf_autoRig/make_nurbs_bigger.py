import pymel.core as pm
import maya.cmds as cmds
from functools import partial

from PySide2 import QtCore, QtWidgets

import shiboken2
from maya import OpenMayaUI
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

def get_maya_win():
    win_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(int(win_ptr), QtWidgets.QMainWindow)

def delete_workspace_control(control):
    if cmds.workspaceControl(control, q=True, exists=True):
        cmds.workspaceControl(control, e=True, close=True)
        cmds.deleteUI(control, control=True)

class MyWindow(MayaQWidgetDockableMixin, QtWidgets.QDialog):
    TOOL_NAME="Nurbs Controllers Scale"

    def __init__(self, parent=None):
        #____UI____
        delete_workspace_control(self.TOOL_NAME + 'WorkspaceControl')
        super(self.__class__, self).__init__(parent=parent)
        self.mayaMainWindow = get_maya_win()
        self.setObjectName(self.__class__.TOOL_NAME)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowTitle(self.TOOL_NAME)

        mainLayout = QtWidgets.QVBoxLayout(self)

        incrementLayout = QtWidgets.QHBoxLayout()
        increment_label = QtWidgets.QLabel()
        increment_label.setText('Increment:')
        self.increment_box = QtWidgets.QLineEdit()
        self.increment_box.setText('0.75')

        incrementLayout.addWidget(increment_label)
        incrementLayout.addWidget(self.increment_box)

        button = QtWidgets.QPushButton()
        button.setText("Scale nurbs")
        button.clicked.connect(self.buttonClicked)

        mainLayout.addLayout(incrementLayout)
        mainLayout.addWidget(button)

    def buttonClicked(self):
        increment = float(self.increment_box.text())
        make_ctrl_bigger(increment)

def make_ctrl_bigger(increment):
    selection = pm.selected()
    for sl in selection:
        if sl.getShape().type() == 'nurbsCurve':
            cvs = sl.getCVs()
            cvs = [cv * increment for cv in cvs]
            sl.setCVs(cvs)
            sl.updateCurve()


mywindow = MyWindow()
mywindow.show(dockable=True)