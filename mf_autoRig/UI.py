import importlib
import sys



sys.path.append(r'C:\Users\332770\Documents\Maya-Scripts')
import importlib
from mf_autoRig import autorig_pymel_v2

import maya.cmds as cmds
from PySide2 import QtCore, QtWidgets
from functools import partial

import shiboken2
from maya import OpenMayaUI
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin



importlib.reload(autorig_pymel_v2)

def get_maya_win():
    win_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(int(win_ptr), QtWidgets.QMainWindow)


def delete_workspace_control(control):
    if cmds.workspaceControl(control, q=True, exists=True):
        cmds.workspaceControl(control, e=True, close=True)
        cmds.deleteUI(control, control=True)


def guides():
    arm.create_guides(autorig_pymel_v2.default_pos['arm'][0], autorig_pymel_v2.default_pos['arm'][1])

def rig():
    arm.create_joints()


if __name__ == '__main__':
    arm = autorig_pymel_v2.Limb('arm')
    print('running')
    # Check if the window already exists and delete it
    if cmds.window("myMayaWindow", exists=True):
        cmds.deleteUI("myMayaWindow", window=True)

    # Create a new Maya window
    maya_main_window = get_maya_win()

    # Create a PySide2 widget
    widget = QtWidgets.QWidget(parent=maya_main_window)
    widget.setWindowFlags(QtCore.Qt.Window)

    # Set window title
    widget.setWindowTitle("My Maya PySide2 Window")
    widget.resize(471, 800)

    # Create widgets
    button = QtWidgets.QPushButton("Close", widget)

    # Set layout
    layout = QtWidgets.QVBoxLayout(widget)
    layout.addWidget(button)

    # Connect button click signal to close the window
    button.clicked.connect(widget.close)

    guidesButton = QtWidgets.QPushButton("create guides", widget)
    guidesButton.clicked.connect(lambda: arm.create_guides(autorig_pymel_v2.default_pos['arm'][0], autorig_pymel_v2.default_pos['arm'][1]))

    rigButton = QtWidgets.QPushButton("Rig", widget)
    rigButton.clicked.connect(rig)

    # Show the window
    layout.addWidget(guidesButton)
    layout.addWidget(rigButton)
    widget.show()
