
from __future__ import absolute_import
try:
    from PySide2 import QtWidgets
except ImportError:
    from PySide import QtGui as QtWidgets

from ks_saveTimer.libApp import getLibApp as libApp
__LIB_APP__ = libApp.__LIB_APP__

from ks_saveTimer.lib import GUI_saveTimer



def checkExistingSaveTimer():
    for widget in QtWidgets.QApplication.allWidgets():
        if type(widget) == GUI_saveTimer.GUI_SaveTimer:
            return True

    return False

class nuke_saveTimer_panel(__LIB_APP__.Qt_wrapperPanel):
    def __init__(self, parent=None):
        super(nuke_saveTimer_panel, self).__init__(parent)
        saveTimerWidget = GUI_saveTimer.GUI_SaveTimer()
        self.addWidget(saveTimerWidget)

def openSaveTimer_nuke_panel():
    if not __LIB_APP__.guiCheck():
        return
    from nukescripts import panels
    panels.registerWidgetAsPanel('runNuke.nuke_saveTimer_panel', 'KS_SaveTimer', 'ks_saveTimerPanel')


def searchForWidgetByName(parent, name):
    widgets = list(parent.items())
    for x in widgets:
        if str(x.objectName) == name:
            return x
    return None

def openSaveTimer_nuke_statusbar():
    if not __LIB_APP__.guiCheck():
        return

    if checkExistingSaveTimer():
        # print 'Already one instance of KS_SaveTimer found! Preventing making another...'
        return

    targetWidget = ''
    for widget in QtWidgets.QApplication.allWidgets():
        if type(widget) == QtWidgets.QStatusBar:
            targetWidget = widget

    if not targetWidget:
        return

    targetLayout = targetWidget.layout()
    saveTimerWidget = GUI_saveTimer.GUI_SaveTimer()
    saveTimerWidget.setFixedWidth(100)
    spacer = QtWidgets.QSpacerItem(40, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
    targetLayout.insertItem(0, spacer)
    targetLayout.insertWidget(0, saveTimerWidget)


