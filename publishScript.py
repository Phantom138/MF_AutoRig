import re
import os.path
import maya.cmds as cmds
from maya import OpenMayaUI
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from PySide2 import QtCore, QtWidgets
import shiboken2
from datetime import datetime
from shutil import copy2
from functools import partial


# Constants
PUBLISH_SET = "publish_SET"

# Define the regular expression pattern to match the required elements
pattern = r'^(\w+)_(\w+)_(\w+)_(\w+)_v(\d+)_([a-zA-Z]+)(?:_(\w+))?\..+$'

#TODO: create an inputBox class in the mainWindow

class FileInfo:
    def __init__(self, file_path):
        if file_path is None:
            self.projectTag = self.fileType = self.name = self.task = self.version = self.initials = self.note = None
        else:
            self.path = file_path
            print(file_path)
            self.file_name = os.path.basename(file_path)
            match = re.match(pattern, self.file_name)
            if match:
                print(match.groups())

            self.projectTag, self.fileType, self.name, self.task, self.version, self.initials, self.note = match.groups()

            self.version = int(self.version)


def get_file_info():
    source_file = cmds.file(query=True, sn=True)
    file = FileInfo(source_file)
    return file


def publish_log(work_file, publish_file, project_path):
    file = open(f'{project_path}/publish_log.txt', "a")

    now = datetime.now()
    timestamp = now.strftime("%d-%m-%Y %H:%M:%S")
    info = f'{timestamp} {work_file} -> {publish_file}\n'

    print(info)
    file.write(info)
    file.close()


def publish_backup(publish_path, versions=3):
    # publish_path comes in with no file extension!!
    # Function assumes .ma extension is used!!
    # TODO: create a more robust backup system that doesn't assume file extension

    publish_path = publish_path + '.ma'
    # Check if there is another file or not
    if not os.path.exists(publish_path):
        print("Skipping Backup.. no already existing publish file to backup")
        return
    print("Running backup")
    # Create archive path based on the publish_path
    baseDir = os.path.dirname(publish_path)
    archive_path = f'{baseDir}/_archive'

    # Check if archive_path exists and create it if not
    if not os.path.exists(archive_path):
        os.makedirs(archive_path)
        print(f"Created archive path {archive_path}")

    name,extension = os.path.splitext(os.path.basename(publish_path))

    # Add timestamp to file name
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    new_name = f'{name}_{timestamp}{extension}'

    copy2(publish_path, f'{archive_path}/{new_name}') # uses shutil to copy, attempts to keep metadata

    archive_files = sorted(os.listdir(archive_path))

    # Keep only the last 'versions' files
    if len(archive_files) > versions:
        files_to_remove = archive_files[:-versions]
        for file_to_remove in files_to_remove:
            file_path_to_remove = os.path.join(archive_path, file_to_remove)
            os.remove(file_path_to_remove)


def publish(selection=False, logging=True, backup=False):
    file = get_file_info()
    project_path = cmds.workspace(q=True, rootDirectory=True)

    # Check if it got information
    if not file.projectTag and file.fileType and file.name and file.task:
        print("Tags not found")

    # Making sure that the file is a work file
    baseDir = os.path.basename(os.path.dirname(file.path))
    if baseDir != 'work':
        cmds.warning('File is not in work folder')

    # Creating publish file name and path
    publish_file = f'{file.projectTag}_{file.fileType}_{file.name}_{file.task}_publish'
    publish_path = os.path.dirname(os.path.dirname(file.path)) + "/publish/" + publish_file

    # Confirmation window
    confirmation = cmds.confirmDialog(title='Confirm',
                                      message=f'Going to publish in {publish_path} are you sure you want to continue?',
                                      button=['Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')
    if confirmation == 'Yes':
        if not selection:
            cmds.select(PUBLISH_SET)
        if logging:
            publish_log(file.file_name, publish_file, project_path)
        if backup:
            publish_backup(publish_path)
        cmds.file(publish_path, exportSelected=True, force=True, ch=False, typ="mayaAscii")


def increment_save(initials, note):
    file = get_file_info()
    file.initials = initials
    # Check if note is not empty
    if note:
        file.note = '_' + note
    else:
        file.note = ''
    # Increase increment
    increment = file.version + 1

    save_path = os.path.dirname(file.path)
    file_name = os.path.basename(file.path)

    # Keep only part before v001
    pos = re.search(r'_v\d+_', file_name).start()
    file_name = file_name[:pos]

    # Create new save_path with updated version and initials
    save_path += f'/{file_name}_v{increment:03}_{file.initials}{file.note}'
    print(save_path)

    cmds.file(rename=save_path)
    cmds.file(save=True, force=True, type='mayaAscii')


# ____UI_____
def get_maya_win():
    win_ptr = OpenMayaUI.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(int(win_ptr), QtWidgets.QMainWindow)


def delete_workspace_control(control):
    if cmds.workspaceControl(control, q=True, exists=True):
        cmds.workspaceControl(control, e=True, close=True)
        cmds.deleteUI(control, control=True)


class MyWindow(MayaQWidgetDockableMixin, QtWidgets.QDialog):
    TOOL_NAME = "Publish Script"

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
        main_layout = QtWidgets.QVBoxLayout(self)
        button_layout = QtWidgets.QHBoxLayout(self)

        # Dropdown
        dropdown_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("Publish Method:")
        self.comboBox = QtWidgets.QComboBox()
        self.comboBox.addItem("Selection")
        self.comboBox.addItem(PUBLISH_SET)
        self.comboBox.currentIndexChanged.connect(self.on_item_selected)
        self.publish_method = "Selection"

        dropdown_layout.addWidget(label, stretch=1)
        dropdown_layout.addWidget(self.comboBox, stretch=3)

        # Backup option
        self.backup_toggle = QtWidgets.QCheckBox('Backup existing publish file',self)
        self.backup_toggle.stateChanged.connect(self.toggle_button_state_changed)

        self.backup = False

        # Publish button
        publish_btn = QtWidgets.QPushButton()
        publish_btn.setText("Publish Scene")
        publish_btn.clicked.connect(self.publishButton)

        self.publishLayout = QtWidgets.QVBoxLayout()
        self.publishLayout.addWidget(publish_btn)

        self.warning = QtWidgets.QLabel()
        self.warning.setText(f"{PUBLISH_SET} not found")

        # Initials box
        initials_layout = QtWidgets.QVBoxLayout()
        initials_label = QtWidgets.QLabel()
        initials_label.setText('Initials:')
        self.file_info = get_file_info()
        self.initials_box = QtWidgets.QLineEdit()
        self.initials_box.setText(self.file_info.initials)

        self.initials_warn = QtWidgets.QLabel()
        self.initials_warn.setText('')

        initials_layout.addWidget(initials_label)
        initials_layout.addWidget(self.initials_box)
        initials_layout.addWidget(self.initials_warn)

        # Note box
        self.noteLayout = QtWidgets.QVBoxLayout()
        note_label = QtWidgets.QLabel()
        note_label.setText('Note:')
        self.note_box = QtWidgets.QLineEdit()

        self.note_warn = QtWidgets.QLabel()
        self.note_warn.setText('')

        self.noteLayout.addWidget(note_label)
        self.noteLayout.addWidget(self.note_box)
        self.noteLayout.addWidget(self.note_warn)

        # Increment save button
        increment_btn = QtWidgets.QPushButton()
        increment_btn.setText("Increment Save")

        increment_btn.clicked.connect(self.incrementButton)

        # Add everything to the main layout
        #button_layout.addWidget(publish_btn)
        button_layout.addLayout(initials_layout, stretch = 1)
        button_layout.addLayout(self.noteLayout, stretch = 3)
        button_layout.addWidget(increment_btn)

        # Separator
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        # line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setStyleSheet("background-color: #7d7d7d;")

        main_layout.addLayout(dropdown_layout)
        main_layout.addWidget(self.backup_toggle)
        main_layout.addLayout(self.publishLayout)
        main_layout.addWidget(line)
        main_layout.addLayout(button_layout)

    def on_item_selected(self, index):
        self.publish_method = self.comboBox.currentText()
        print(f"Selected item: {self.publish_method}")


    def toggle_button_state_changed(self, state):
        # function to handle the stateChanged signal
        if state == QtCore.Qt.Checked:
            self.backup = True

    def publishButton(self):
        # backup is a boolean saying wether the backup option is enabled or not
        if self.publish_method == "Selection":
            print(f'publishing selection, backup is {self.backup}')
            publish(selection=True, backup=self.backup)

        elif self.publish_method == "publish_SET":
            if cmds.objExists(PUBLISH_SET):
                print(f'publishing set, backup is {self.backup}')
                # Clear warning
                self.warning.setParent(None)
                publish(backup=self.backup)
            else:
                # Warn that the set could not be found
                self.publishLayout.addWidget(self.warning)


    def incrementButton(self):
        # Validate Note
        self.note_warn.setText('')
        self.note_warn.setStyleSheet("color: yellow;")
        note = self.note_box.text()

        if not re.match('^[A-Za-z0-9]*$',note):
            self.note_warn.setText("Only Letters or numbers!")
            return

        # Validate Initials
        self.initials_warn.setText('')
        self.note_warn.setStyleSheet("color: yellow;")
        initials = self.initials_box.text()

        if not re.match('^[A-Za-z0-9]*$', initials):
            self.initials_warn.setText("Only Letters or numbers!")
            return

        increment_save(initials,note)

        # Empty note box
        self.note_box.setText('')



mywindow = MyWindow()
mywindow.show(dockable=True)
