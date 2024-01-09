import sys
import importlib
sys.path.append(r'C:\Users\mihai\Documents\Projects\Maya-Scripts\mf_autoRig')

import maya.cmds as cmds
from PySide2 import QtCore, QtWidgets
from functools import partial
import shiboken2
from maya import OpenMayaUI
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

import mf_autoRig.autorig as autorig
import mf_autoRig.lib.defaults as df

importlib.reload(autorig)
importlib.reload(df)

def get_maya_win():
    win_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(int(win_ptr), QtWidgets.QMainWindow)


def delete_workspace_control(control):
    if cmds.workspaceControl(control, q=True, exists=True):
        cmds.workspaceControl(control, e=True, close=True)
        cmds.deleteUI(control, control=True)



if __name__ == '__main__':

    arm = autorig.Limb('arm')
    body = autorig.Body()
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


    # Connect button click signal to close the window
    button.clicked.connect(widget.close)

    guidesButton = QtWidgets.QPushButton("create guides", widget)
    guidesButton.clicked.connect(lambda: body.create_guides(df.default_pos))

    rigButton = QtWidgets.QPushButton("Rig", widget)
    rigButton.clicked.connect(lambda: body.create_joints())

    # Show the window
    layout.addWidget(guidesButton)
    layout.addWidget(rigButton)
    layout.addWidget(button)
    widget.show()
