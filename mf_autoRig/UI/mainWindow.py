from PySide2 import QtCore, QtWidgets
import shiboken2
from maya import OpenMayaUI
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

import maya.cmds as cmds

from mf_autoRig.modules.Body import Body
import mf_autoRig.lib.defaults as df


print(__file__)

def get_maya_win():
    win_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(int(win_ptr), QtWidgets.QMainWindow)


def delete_workspace_control(control):
    if cmds.workspaceControl(control, q=True, exists=True):
        cmds.workspaceControl(control, e=True, close=True)
        cmds.deleteUI(control, control=True)

def setup():
    body = Body()
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

    jointsButton = QtWidgets.QPushButton("Joints", widget)
    jointsButton.clicked.connect(lambda: body.create_joints())

    rigButton = QtWidgets.QPushButton("Rig", widget)
    rigButton.clicked.connect(lambda: body.rig())

    mirrorButton = QtWidgets.QPushButton("Mirror", widget)
    mirrorButton.clicked.connect(lambda: body.mirror_ctrls(side='L'))

    # Show the window
    layout.addWidget(guidesButton)
    layout.addWidget(jointsButton)
    layout.addWidget(rigButton)
    layout.addWidget(button)
    widget.show()
