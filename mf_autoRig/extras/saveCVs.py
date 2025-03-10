from maya import cmds
import pymel.core as pm
import json
from pathlib import Path
import time

from maya import OpenMayaUI
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
try:
    from PySide2 import QtGui, QtCore, QtUiTools, QtWidgets
    from shiboken2 import wrapInstance
except ImportError:
    from PySide6 import QtGui, QtCore, QtUiTools, QtWidgets
    from shiboken6 import wrapInstance

file = 'C:/Users/332770/Documents/Maya-Scripts/mf_autoRig/cvsInfo.json'


def save_cvs():
        start = time.time()
        ctrls = cmds.ls(type='nurbsCurve')
        info = {}
        for ctrl in ctrls:
                cvs = []
                # Get transformation info for each ctrl cv
                targetCvList = cmds.ls(f'{ctrl}.cv[:]', flatten=True)
                for tar in targetCvList:
                        cv = cmds.xform(tar, query = True, translation = True, objectSpace = True)
                        cvs.append(cv)
                # Add to dictionary
                info[ctrl] = cvs

        # Save to json
        json_file = open(file,"w")
        json.dump(info, json_file, indent=6)
        json_file.close()

        # Check how long it took
        end = time.time()
        print("The time of execution of above program is :",
              (end - start) * 10 ** 3, "ms")


def load_cvs():
        start = time.time()

        ctrls = cmds.ls(type='nurbsCurve')

        # Open json
        with open(file, 'r') as j:
                saved_cvs = json.loads(j.read())

        # Iterate through controllers
        for ctrl in ctrls:
                # Check if there's saved information for that controller
                if ctrl not in saved_cvs:
                        print(f'{ctrl} not in saved list, skipping...')
                        continue

                # Get cvs to modify
                target_cvs = cmds.ls(f'{ctrl}.cv[:]', flatten=True)

                # If length doesn't match don't do anything
                if len(target_cvs) != len(saved_cvs[ctrl]):
                        print(f'{ctrl} changed, skipping...')
                        continue

                for i in range(len(target_cvs)):
                        sav = saved_cvs[ctrl][i]
                        tar = target_cvs[i]

                        # Check if it's already in place
                        if cmds.xform(tar, query=True, translation=True) != sav:
                                cmds.xform(tar, translation=sav, objectSpace = True)

        # End time
        end = time.time()
        print("The time of execution of above program is :",
              (end - start) * 10 ** 3, "ms")


##### UI ######

def get_maya_win():
    win_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(int(win_ptr), QtWidgets.QMainWindow)


def delete_workspace_control(control):
    if cmds.workspaceControl(control, q=True, exists=True):
        cmds.workspaceControl(control, e=True, close=True)
        cmds.deleteUI(control, control=True)



class MyWindow(MayaQWidgetDockableMixin, QtWidgets.QDialog):
    TOOL_NAME = "Save CVs"

    def __init__(self, parent=None):
        # initialize
        delete_workspace_control(self.TOOL_NAME + 'WorkspaceControl')
        super(self.__class__, self).__init__(parent=parent)

        self.initUI()

    def initUI(self):
        self.mayaMainWindow = get_maya_win()
        self.setObjectName(self.__class__.TOOL_NAME)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowTitle(self.TOOL_NAME)

        # Add UI Elements
        self.createLayout()

    def createLayout(self):
        # Set layout of window
        main_layout = QtWidgets.QHBoxLayout(self)

        # Save button
        save_btn = QtWidgets.QPushButton()
        save_btn.setText("Save CVs")
        save_btn.clicked.connect(save_cvs)

        # Load button
        load_btn = QtWidgets.QPushButton()
        load_btn.setText("Apply saved CVs")
        load_btn.clicked.connect(load_cvs)

        main_layout.addWidget(save_btn)
        main_layout.addWidget(load_btn)


mywindow = MyWindow()
mywindow.show(dockable=True)

