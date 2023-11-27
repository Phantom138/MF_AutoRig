import maya.cmds as cmds
from PySide2 import QtCore, QtWidgets
from functools import partial

from maya import OpenMayaUI
import shiboken2
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin


def color_selection(color):
    #receives color in rgb (0-255) format
    selection = cmds.ls(sl=True)
    print(selection)
    if len(selection) == 0:
        cmds.error("Nothing is selected")
        return

    for sl in selection:
        print(cmds.nodeType(sl))
        if cmds.nodeType(sl) == 'joint':
            print("AAA")
            shape = sl
        else:
            shape = cmds.listRelatives(sl, shapes=True)[0]
        print(shape)
        cmds.setAttr(shape + ".overrideEnabled", 1)
        cmds.setAttr(shape + ".overrideRGBColors", 1)
        cmds.setAttr(shape + ".overrideColorR", color[0]/255)
        cmds.setAttr(shape + ".overrideColorG", color[1]/255)
        cmds.setAttr(shape + ".overrideColorB", color[2]/255)



def disable_colors():
    selection = cmds.ls(sl=True)
    if cmds.nodeType(selection) == 'joint':
        shapes = selection
    else:
        shapes = cmds.listRelatives(selection, shapes=True)

    for shape in shapes:
        cmds.setAttr(shape + '.overrideEnabled', 0) # disables color override

def get_maya_win():
    win_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(int(win_ptr), QtWidgets.QMainWindow)


def delete_workspace_control(control):
    if cmds.workspaceControl(control, q=True, exists=True):
        cmds.workspaceControl(control, e=True, close=True)
        cmds.deleteUI(control, control=True)

class MyWindow(MayaQWidgetDockableMixin, QtWidgets.QDialog):
    TOOL_NAME="Color Selector"

    def __init__(self, parent=None):
        #____UI____
        delete_workspace_control(self.TOOL_NAME + 'WorkspaceControl')
        super(self.__class__, self).__init__(parent=parent)
        self.mayaMainWindow = get_maya_win()
        self.setObjectName(self.__class__.TOOL_NAME)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowTitle(self.TOOL_NAME)

        #Set layout of window

        mainLayout = QtWidgets.QVBoxLayout(self)

        #Create button for each color
        buttonLayout = QtWidgets.QHBoxLayout(self)
        colors = [[255, 0, 0], [255, 255, 0],[21,203,3], [0,65,153],[44, 219, 210],[219, 0, 193]]
        for color in colors:
            button = QtWidgets.QPushButton()
            button.setGeometry(200, 150, 100, 40)
            # self.button.setStyleSheet(f'background-color: rgb({color[0] * 255},{color[1] * 255},{color[2] * 255})')
            button.setStyleSheet(f'background-color: rgb({color[0]},{color[1]},{color[2]})')
            button.clicked.connect(partial(color_selection, color))
            #adds button to layout
            buttonLayout.addWidget(button)

        #Button for disabling color override
        disableButton = QtWidgets.QPushButton("Default Color for Selection")
        disableButton.clicked.connect(disable_colors)

        mainLayout.addLayout(buttonLayout)
        mainLayout.addWidget(disableButton)

mywindow = MyWindow()
mywindow.show(dockable=True)

# rgb = ["R","G","B"]
# for channel in rgb:
#     print(channel)
#     cmds.setAttr(shape + ".overrideColor%s" %channel,.5)
