
from __future__ import absolute_import
import six
try:
    from PySide2 import QtCore, QtWidgets
    from PySide2.QtCore import Signal
except ImportError:
    from PySide import QtCore
    from PySide import QtGui as QtWidgets
    from PySide.QtCore import Signal

import nuke
from nukescripts import panels


# import os

from ks_saveTimer.lib import Singleton


##
## ------------------ FUNCTIONALITY ------------------
##

# def getUserConfigLocation():
#     return 'F:/'
#     # return os.environ['MAYA_APP_DIR']


def displayStatusMessage(message):
    nuke.message(message)

def displayWarningMessage(message):
    nuke.note_warn(message)
    # cmds.note_warn(message)
    return

def get_projectDir():
    return nuke.root().knob('project_directory').value()


def get_filePath():
    return nuke.root().knob('name').value()

def guiCheck():
    # not running in interactive mode so don't have menus or shortcuts!
    if nuke.env.get("gui"):
        return True
    return False


##
## ------------------ QT GUI ------------------
##

def set_widget_margins_to_zero(widget_object):

    if widget_object:
        target_widgets = set()
        target_widgets.add(widget_object.parentWidget().parentWidget())
        target_widgets.add(widget_object.parentWidget().parentWidget().parentWidget().parentWidget())

        for widget_layout in target_widgets:
            try:
                widget_layout.layout().setContentsMargins(0, 0, 0, 0)
            except:
                pass

class Qt_wrapperPanel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.rootLayout = QtWidgets.QVBoxLayout()
        self.rootLayout.setContentsMargins(0,0,0,0)
        self.setLayout(self.rootLayout)

        expandingPolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setSizePolicy(expandingPolicy)

    def addWidget(self, widget):
        self.rootLayout.addWidget(widget)

    def event(self, event):
        if event.type() == QtCore.QEvent.Type.Show:

            try:
                set_widget_margins_to_zero(self)
            except:
                pass

        return QtWidgets.QWidget.event(self, event)



# class nuke_makePanel(Qt_wrapperPanel):
#     def __init__(self, parent=None):
#         super(nuke_makePanel, self).__init__(parent)
#         saveTimerWidget = GUI_saveTimer.GUI_SaveTimer()

#         saveTimerWidget.setFixedHeight(22)
#         saveTimerWidget.setFixedWidth(60)
#         self.addWidget(saveTimerWidget)


##
## ------------------ Callbacks ------------------
##


#### https://learn.foundry.com/nuke/developers/105/pythondevguide/callbacks.html

@six.add_metaclass(Singleton.QtSingletonMetaclass)
class appCallbacks(QtCore.QObject):
    fileSaved = Signal()
    fileOpened = Signal()

    def __init__(self, parent=None):
        super(appCallbacks, self).__init__()
        self.parent = parent
        nuke.addOnScriptLoad(lambda:self.fileOpened.emit())
        nuke.addOnScriptClose(lambda:self.fileOpened.emit())
        nuke.addOnScriptSave(lambda:self.fileSaved.emit())

        # print 'KS_SaveTimer - Made callbacks!'


