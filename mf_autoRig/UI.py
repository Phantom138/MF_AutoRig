import sys
sys.path.append(r'C:\Users\332770\Documents\Maya-Scripts\mf_autoRig')

from autorig_pymel_v2 import *
import maya.cmds as cmds
from PySide2 import QtCore, QtWidgets
from functools import partial

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


def clicked(self):
    self.arm = Limb('arm', default_pos['arm'][0], default_pos['arm'][1])


def rig(self):
    self.arm.create_joints()


if __name__ == '__main__':

    TOOL_NAME="Color Selector"

    def __init__(self, parent=None):
        #____UI____
        delete_workspace_control(self.TOOL_NAME + 'WorkspaceControl')
        super(self.__class__, self).__init__(parent=parent)
        mayaMainWindow = get_maya_win()
        QtWidgets.QDialog.setObjectName(self.__class__.TOOL_NAME)
        QtWidgets.QDialog.setWindowFlags(QtCore.Qt.Window)
        QtWidgets.QDialog.setWindowTitle(self.TOOL_NAME)

        #Set layout of window

        mainLayout = QtWidgets.QVBoxLayout(self)

        guidesButton = QtWidgets.QPushButton(self)
        guidesButton.clicked.connect(self.clicked)


        rigButton = QtWidgets.QPushButton(self)
        rigButton.clicked.connect(self.rig)

        mainLayout.addWidget(guidesButton)
        mainLayout.addWidget(rigButton)




mywindow = MyWindow()
mywindow.show(dockable=True)