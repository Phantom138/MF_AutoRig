from __future__ import absolute_import
from __future__ import print_function
import six
try:
    from PySide2 import QtCore, QtWidgets
    from PySide2.QtCore import Signal
    from shiboken2 import wrapInstance
except ImportError:
    from PySide import QtCore
    from PySide import QtGui as QtWidgets
    from PySide.QtCore import Signal
    from shiboken import wrapInstance

import os

from maya import cmds, mel
from maya import OpenMaya
from maya import OpenMayaUI as omui
# from maya.app.general.mayaMixin import MayaQWidgetBaseMixin

from ks_saveTimer.lib import Singleton


##
## ------------------ FUNCTIONALITY ------------------
##


# def getUserConfigLocation():
#     return os.environ['MAYA_APP_DIR']

def displayStatusMessage(message):
    return OpenMaya.MGlobal.displayInfo(message)

def displayWarningMessage(message):
    cmds.warning(message)
    return

def get_filePath():
    filePath = cmds.file(q=1, sn=1)
    if filePath is '':
        return None
    return filePath

def get_projectDir():
    return cmds.workspace(q=True, rootDirectory=True)

##
## ------------------ UI / QT COMMANDS ------------------
##


def QT_getMainWindow():
    ptr = omui.MQtUtil.mainWindow()
    if ptr is not None:
        return wrapInstance(int(ptr), QtWidgets.QWidget)


def findLayout_statusLine():
    layerEditorBtn = mel.eval('$tmpVar=$gLayerEditorButton')
    buttonLayout = cmds.iconTextCheckBox(layerEditorBtn, q=1, p=1)
    maya_parentLayout = cmds.formLayout(buttonLayout, q=1, p=1)
    return maya_parentLayout

def deleteLayoutFromUI(uiName):
    layoutName = "%s_rootLayout" %(uiName)
    try:
        cmds.deleteUI(layoutName)
    except:
        pass


def QT_embedUItoInterface(uiName, widget, target='statusLine'):
    maya_parentLayout = None
    if target == 'statusLine':
        maya_parentLayout = findLayout_statusLine()

    if not maya_parentLayout:
        cmds.warning('No Parent Layout found!')
        return

    rootLayoutName = "%s_rootLayout" %(uiName)
    if rootLayoutName in cmds.formLayout(maya_parentLayout, q=1, childArray=True):
        try:
            cmds.deleteUI(rootLayoutName)
        except:
            pass


    #Find the first UI element in the layout, so you can attach new UI-element to its left side.
    attachTo = cmds.formLayout(maya_parentLayout, q=1, childArray=True)[-1]

    cmds.setParent(maya_parentLayout)
    rootLayout = cmds.rowLayout(rootLayoutName)

    cmds.formLayout(maya_parentLayout, e=1,
        attachControl=[(rootLayout, 'right', 10, attachTo)],
        attachNone=[(rootLayout, 'left')])

    # QT separates Widgets from Layouts, but Maya does not, and require objectNames for all widgets.
    # To work around this, Maya parents layouts under dummy-widgets with identical names, so its visible in
    # UI hierarchy names. So we search for the wrapper-widget, and search for children of that widget to find the actual layout.
    rootLayoutWidget_qtMayaPath = omui.MQtUtil_findLayout(rootLayout)
    rootLayoutWidget_qt = wrapInstance(int(rootLayoutWidget_qtMayaPath), QtWidgets.QWidget)

    rootLayout_Qt = rootLayoutWidget_qt.findChildren(QtWidgets.QHBoxLayout)[0]
    rootLayout_Qt.addWidget(widget)
    # widget.setParent(rootLayout_Qt)



##
## ------------------ Callbacks ------------------
##



@six.add_metaclass(Singleton.QtSingletonMetaclass)
class appCallbacks(QtCore.QObject):
    fileSaved = Signal()
    fileOpened = Signal()
    SCRIPTJOB_IDS = []

    def __init__(self, parent=None):
        super(appCallbacks, self).__init__()
        self.parent = parent
        jobID = cmds.scriptJob(runOnce=False, event=['SceneOpened', lambda:self.fileOpened.emit()])
        self.SCRIPTJOB_IDS.append(jobID)

        jobID = cmds.scriptJob(runOnce=False, event=['SceneSaved', lambda:self.fileSaved.emit()])
        self.SCRIPTJOB_IDS.append(jobID)

        print(self.SCRIPTJOB_IDS, '(scriptJob IDs for KS_SaveTools)')


