import re
import os.path
import maya.cmds as cmds
from PySide2 import QtCore, QtWidgets
from functools import partial

from maya import OpenMayaUI
import shiboken2
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

# Define the regular expression pattern to match the required elements
pattern = r'^(\w+)_(\w+)_(\w+)_(\w+)_(v\d+)_([a-zA-Z]+)(?:_(\w+))?\..+$'

# Function to extract project, version, initials, and note from the input string

class FileInfo:
    def __init__(self, file_path):
        if file_path is None:
            self.projectTag = self.fileType = self.name = self.task = self.version = self.initials = self.note = None
        else:
            self.path = file_path
            print(file_path)
            file_name = os.path.basename(file_path)
            match = re.match(pattern, file_name)
            if match:
                print(match.groups())

            self.projectTag, self.fileType, self.name, self.task, self.version, self.initials, self.note = match.groups()


def extract_info(input_str):
    match = re.match(pattern, input_str)
    if match:
        print(match.groups())
        project, version, initials, note = match.groups()
        return project, version, initials, note
    else:
        return None

def publish(file):
    if not file.projectTag and file.fileType and file.name and file.task:
        print ("Tags not found")
    publish_template = "{projectTag}_{fileType}_{name}_{task}_publish"
    publish_file = publish_template.format(projectTag=file.projectTag, fileType=file.fileType, name=file.name,
                                           task=file.task)

    baseDir = os.path.basename(os.path.dirname(file.path))
    if baseDir != 'work':
        cmds.warning('File is not in work folder')
    publish_path = os.path.dirname(os.path.dirname(file.path)) + "/publish/" + publish_file
    print(publish_path)

    #confirmation window
    confirmation = cmds.confirmDialog(title='Confirm', message='Going to publish in '+publish_path+" are you sure you want to continue?",
                       button=['Yes', 'No'], defaultButton='Yes',cancelButton='No', dismissString='No')
    if confirmation == 'Yes':
        cmds.file(publish_path, es=True, force=True, ch=False, typ="mayaAscii")

def get_file_info():
    source_file = cmds.file(query=True, sn=True)
    file = FileInfo(source_file)
    return file

#____UI_____
def get_maya_win():
    win_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(int(win_ptr), QtWidgets.QMainWindow)


def delete_workspace_control(control):
    if cmds.workspaceControl(control, q=True, exists=True):
        cmds.workspaceControl(control, e=True, close=True)
        cmds.deleteUI(control, control=True)

class MyWindow(MayaQWidgetDockableMixin, QtWidgets.QDialog):
    TOOL_NAME="Publish Script"

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


        textLayout = QtWidgets.QHBoxLayout(self)

        self.file = FileInfo(None)
        getData_button = QtWidgets.QPushButton()
        getData_button.clicked.connect(self.getData)
        textLayout.addWidget(getData_button)


        projectTag_textbox = QtWidgets.QLineEdit(self)
        #textbox.resize(280,40)
        projectTag_textbox.setText(self.file.projectTag)
        textLayout.addWidget(projectTag_textbox)

        self.fileType_textbox = QtWidgets.QLineEdit(self)

        textLayout.addWidget(self.fileType_textbox)

        name_textbox = QtWidgets.QLineEdit(self)
        name_textbox.setText(self.file.name)
        textLayout.addWidget(name_textbox)

        task_textbox = QtWidgets.QLineEdit(self)
        task_textbox.setText(self.file.task)
        textLayout.addWidget(task_textbox)

        button = QtWidgets.QPushButton()
        button.clicked.connect(publish)
        textLayout.addWidget(button)  # add button

        mainLayout.addLayout(textLayout)
    def getData(self):
        self.file = get_file_info()
        self.fileType_textbox.setText(self.file.fileType)
mywindow = MyWindow()
mywindow.show(dockable=True)

