import maya.cmds as cmds
from PySide2 import QtCore, QtWidgets
from functools import partial

import shiboken2
from maya import OpenMayaUI
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

colors = {
    'red': (255, 0, 0),
    'orange': (255,140,0),
    'yellow': (255, 255, 51),
    'green': (0, 255, 0),
    'cyan': (0, 255, 255),
    'blue': (0, 0, 255),
    'magenta': (255, 0, 255),
}


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

def color_outliner(color):
    selection = cmds.ls(sl=True)

    if len(selection) == 0:
        cmds.error("Nothing is selected")
        return

    for sl in selection:
        cmds.setAttr(sl + ".useOutlinerColor", 1)
        cmds.setAttr(sl + ".outlinerColorR", color[0]/255)
        cmds.setAttr(sl + ".outlinerColorG", color[1]/255)
        cmds.setAttr(sl + ".outlinerColorB", color[2] / 255)


def disable_colors():
    selection = cmds.ls(sl=True)
    shapes=[]
    for sl in selection:
        if cmds.nodeType(sl) == 'joint':
            shp = sl
        else:
            shp = cmds.listRelatives(sl, shapes=True)[0]
        shapes.append(shp)
    print(shapes)
    for shape in shapes:
        cmds.setAttr(shape + '.overrideEnabled', 0) # disables color override

def disable_colors_outliner():
    selection = cmds.ls(sl=True)

    for sl in selection:
        cmds.setAttr(sl + '.useOutlinerColor', 0)  # disables color override


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
        buttonLayout.setSpacing(0)

        for color in colors.values():
            button = QtWidgets.QPushButton()
            button.setGeometry(200, 150, 100, 40)
            # self.button.setStyleSheet(f'background-color: rgb({color[0] * 255},{color[1] * 255},{color[2] * 255})')
            button.setStyleSheet(
                f'background-color: rgb({color[0]},{color[1]},{color[2]}); border: none; min-height:30px')
            #button.clicked.connect(partial(color_selection, color))
            button.clicked.connect(partial(self.onColorClicked, color))
            #adds button to layout
            buttonLayout.addWidget(button,)

        # Dropdown options
        dropdown_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Set color to:")
        self.comboBox = QtWidgets.QComboBox()
        self.comboBox.addItem("Viewport")
        self.comboBox.addItem("Outliner")
        self.comboBox.currentIndexChanged.connect(self.on_item_selected)
        self.color_method = "Viewport"

        dropdown_layout.addWidget(label)
        dropdown_layout.addWidget(self.comboBox)

        #Button for disabling color override
        disableButton = QtWidgets.QPushButton("Default Color for Selection")
        disableButton.clicked.connect(self.disableColors)

        mainLayout.addLayout(dropdown_layout)
        mainLayout.addLayout(buttonLayout)
        mainLayout.addWidget(disableButton)


    def onColorClicked(self, color):
        if self.color_method == "Viewport":
            color_selection(color)
        else:
            color_outliner(color)

    def on_item_selected(self, index):
        self.color_method = self.comboBox.currentText()
        print(f"Selected item: {self.color_method}")

    def disableColors(self):
        if self.color_method == "Viewport":
            disable_colors()
        else:
            disable_colors_outliner()

def showWindow():
    mywindow = MyWindow()
    mywindow.show(dockable=True)


# rgb = ["R","G","B"]
# for channel in rgb:
#     print(channel)
#     cmds.setAttr(shape + ".overrideColor%s" %channel,.5)
