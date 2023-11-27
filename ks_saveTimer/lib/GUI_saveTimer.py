# -*- coding: utf-8 -*-
from __future__ import absolute_import
try:
    from PySide2 import QtCore, QtWidgets, QtGui
    QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)
except ImportError:
    from PySide import QtCore, QtGui
    from PySide import QtGui as QtWidgets

import ks_saveTimer
from ks_saveTimer.lib import timer, timerWidget, tracker, GUI_tracker, GUI_config


class GUI_SaveTimer(timerWidget.saveTimer_widget):

    def __init__(self, parent=None):
        super(GUI_SaveTimer, self).__init__(parent)
        self.setObjectName('KS_SaveTimer_Widget')

        self._TRACKER = tracker.timeTracker()

        self.contextMenu.addSeparator()
        self.contextMenu.addAction("Options", self.openConfig)
        self.contextMenu.addSeparator()
        self.contextMenu.addAction("History", self.openHistory)
        self.contextMenu.addAction("About/Stats", self.openAbout)

    def openConfig(self):
        dialog = GUI_config.saveTimer_config_GUI(self)
        dialog.show()

    def openHistory(self):
        dialog = GUI_tracker.GUI_timeTracker(self)
        dialog.exec_()

    def openAbout(self):
        dialog = aboutDialog_ksSaveTimer(self)
        dialog.exec_()




class aboutDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, **kwargs):
        super(aboutDialog, self).__init__(parent=parent, **kwargs)
        self.setWindowTitle('About')
        self.setStyleSheet('QLabel#Header {color:Orange}')
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setModal(True)
        self.rootLayout = QtWidgets.QVBoxLayout()
        self.rootLayout.setSpacing(2)
        self.rootLayout.setContentsMargins(20,20,20,20)
        self.setLayout(self.rootLayout)

        self.buildUI()
        self.setMaximumSize(self.rootLayout.sizeHint())
        self._URL = None

    def buildUI(self):
        self.font_header = QtGui.QFont()
        self.font_header.setPixelSize(20)
        self.font_header.setWeight(120)

        self.label_title = QtWidgets.QLabel()
        self.label_title.setObjectName('Header')
        self.label_title.setFont(self.font_header)
        self.label_title.setAlignment(QtCore.Qt.AlignCenter)
        self.rootLayout.addWidget(self.label_title)

        self.label_version = QtWidgets.QLabel()
        self.label_version.setAlignment(QtCore.Qt.AlignCenter)
        self.rootLayout.addWidget(self.label_version)


        self.label_copyright = QtWidgets.QLabel()
        self.label_copyright.setAlignment(QtCore.Qt.AlignCenter)
        self.rootLayout.addWidget(self.label_copyright)

        self.widgetLayout = QtWidgets.QVBoxLayout()
        self.rootLayout.addLayout(self.widgetLayout)

        self.label_contactInfo = QtWidgets.QLabel()
        self.label_contactInfo.setAlignment(QtCore.Qt.AlignCenter)
        self.rootLayout.addWidget(self.label_contactInfo)

        self.btn_website = QtWidgets.QPushButton('Open Website')
        self.btn_website.setFixedHeight(40)
        self.rootLayout.addWidget(self.btn_website)
        self.btn_website.clicked.connect(lambda: self.openUrl(self._URL))

    def insertWidget(self, widget):
        self.widgetLayout.addWidget(widget)

    def openUrl(self, linkStr):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(linkStr))

    def setLabel_copyright(self, txt):
        self.label_copyright.setText(txt)

    def setLabel_version(self, txt):
        self.label_version.setText(txt)

    def setLabel_title(self, txt):
        self.label_title.setText(txt)

    def setLabel_contactInfo(self, txt):
        self.label_contactInfo.setText(txt)

    def setUrl(self, string):
        self._URL = string


class aboutDialog_ksSaveTimer(aboutDialog):
    def __init__(self, parent=None, **kwargs):
        super(aboutDialog_ksSaveTimer, self).__init__(parent=parent, **kwargs)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.statsWidget = GUI_statsWidget()
        self.statsWidget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.insertWidget(self.statsWidget)
        self.setUrl(ks_saveTimer._URL_)
        self.setLabel_title(ks_saveTimer._TOOLNAME_)
        self.setLabel_version(ks_saveTimer._VERSION_)
        self.setLabel_copyright(ks_saveTimer._COPYRIGHT_)
        self.setLabel_contactInfo(ks_saveTimer._INFO_)
        self.setMaximumSize(self.rootLayout.sizeHint())

    def exec_(self):
        self.statsWidget.updateSaveStats()
        self.statsWidget.updateTimer()
        super(aboutDialog_ksSaveTimer, self).exec_()




class GUI_statsWidget(QtWidgets.QFrame):
    def __init__(self, parent=None):
        super(GUI_statsWidget, self).__init__(parent=parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        self.setFrameStyle(QtWidgets.QFrame.Box | QtWidgets.QFrame.Raised)

        self.rootLayout = QtWidgets.QGridLayout()
        self.rootLayout.setContentsMargins(4, 4, 4, 4)
        self.rootLayout.setSpacing(0)
        self.setLayout(self.rootLayout)

        self.buildUI()

        self.TIMER = timer.timerObject(self)

        self.updateTimer()
        self.updateSaveStats()

    def buildUI(self):
        label = QtWidgets.QLabel('Time Active:')
        self.label_totalActive = field = QtWidgets.QLabel('0')
        field.setAlignment(QtCore.Qt.AlignRight)
        self.rootLayout.addWidget(label, 1,0)
        self.rootLayout.addWidget(self.label_totalActive, 1,1)

        label = QtWidgets.QLabel('Time Idle:')
        self.label_totalIdle = field = QtWidgets.QLabel('0')
        field.setAlignment(QtCore.Qt.AlignRight)
        self.rootLayout.addWidget(label, 2,0)
        self.rootLayout.addWidget(self.label_totalIdle, 2,1)


        spacerLabel = QtWidgets.QLabel()
        self.rootLayout.addWidget(spacerLabel, 3,0)


        label = QtWidgets.QLabel('Total Saves:')
        self.label_totalSaves = field = QtWidgets.QLabel('0')
        field.setAlignment(QtCore.Qt.AlignRight)
        self.rootLayout.addWidget(label, 4,0)
        self.rootLayout.addWidget(self.label_totalSaves, 4,1)
        # self.rootLayout.addRow(label, field)

        label = QtWidgets.QLabel('Activity Per Save:')
        self.label_minutesPerSave = field = QtWidgets.QLabel('0m')
        field.setAlignment(QtCore.Qt.AlignRight)
        self.rootLayout.addWidget(label, 5,0)
        self.rootLayout.addWidget(self.label_minutesPerSave, 5,1)
        # self.rootLayout.addRow(label, field)

    def updateSaveStats(self):
        saveCount = self.TIMER.saveCount
        self.label_totalSaves.setText(str(saveCount))

        if not saveCount:
            return

        minutesPerSave = (self.TIMER.counterTotal/saveCount)
        minutesPerSave = self.formatTimeToString(minutesPerSave)
        self.label_minutesPerSave.setText(minutesPerSave)

    def updateTimer(self):
        totalActive = self.TIMER.counterTotal
        totalActive_time = self.formatTimeToString(totalActive)
        self.label_totalActive.setText(totalActive_time)

        totalIdle = self.TIMER.counterIdleTotal
        totalIdle_time = self.formatTimeToString(totalIdle)
        self.label_totalIdle.setText(str(totalIdle_time))

    def formatTimeToString(self, minutes):
        if minutes > 60:
            timeFormatString = '{:01d}h {:01d}m'.format(*divmod(minutes, 60))
        else:
            timeFormatString = '{:01d}m'.format(minutes)
        return timeFormatString


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    main = GUI_SaveTimer()
    # main = aboutDialog()
    main.show()
    sys.exit(app.exec_())
