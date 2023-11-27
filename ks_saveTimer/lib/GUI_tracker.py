from __future__ import absolute_import
import six
from six.moves import range
try:
    from PySide2 import QtCore, QtWidgets, QtGui
    from PySide2.QtCore import Signal
    _PYSIDE_VERSION_ = 2
except ImportError:
    from PySide import QtCore, QtGui
    from PySide import QtGui as QtWidgets
    from PySide.QtCore import Signal
    _PYSIDE_VERSION_ = 1

from ks_saveTimer.lib import tracker

from ks_saveTimer.libApp import getLibApp as libApp
__HOST_APP__ = libApp.__HOST_APP__


class GUI_timeTracker(QtWidgets.QDialog):
    # __metaclass__ = Singleton.QtSingletonMetaclass

    def __init__(self, parent=None):
        super(GUI_timeTracker, self).__init__(parent=parent)
        self.setWindowTitle('KS_SaveTimer - History')
        self.setStyleSheet('QLabel#Header {color:Orange}')
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self._TRACKER = tracker.timeTracker()

        self.rootLayout = QtWidgets.QVBoxLayout()
        self.rootLayout.setSpacing(4)
        self.setLayout(self.rootLayout)

        self.buildUI()

        self._TRACKER.loadHistory()
        self.populate_modelView()
        self.resize(QtCore.QSize(600,400))

    def show(self):
        super(GUI_timeTracker, self).show()
        self.center()

    def buildUI(self):

        self.font_header = QtGui.QFont()
        self.font_header.setPixelSize(20)
        self.font_header.setWeight(120)

        self.label_title = QtWidgets.QLabel('KS_SaveTimer')
        self.label_title.setObjectName('Header')
        self.label_title.setFont(self.font_header)
        self.label_title.setAlignment(QtCore.Qt.AlignCenter)
        self.rootLayout.addWidget(self.label_title)

        self.font_subHeader = QtGui.QFont()
        self.font_subHeader.setPixelSize(16)
        self.font_subHeader.setWeight(120)

        self.label_subTitle = QtWidgets.QLabel('Time Tracker History')
        self.label_subTitle.setObjectName('Header')
        self.label_subTitle.setFont(self.font_subHeader)
        self.label_subTitle.setAlignment(QtCore.Qt.AlignCenter)
        self.rootLayout.addWidget(self.label_subTitle)

        #### SELECTION LAYOUT ####
        self.layout_selectionData = layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0,0,0,0)
        self.rootLayout.addLayout(self.layout_selectionData)

        label = QtWidgets.QLabel('Selection Total:')
        label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom)
        self.layout_selectionData.addWidget(label)

        totalTimeFormat = '{:01d}h {:02d}m'.format(*divmod(0, 60))
        self.label_stats_timeSelection = label = QtWidgets.QLabel(totalTimeFormat)

        label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignBottom)
        self.layout_selectionData.addWidget(label)


        self.layout_selectionData.addStretch()


        self.btn_sortOptions = btn = QtWidgets.QPushButton()
        btn.setText('Sort by')
        btn.setFixedHeight(20)
        btn.setFixedWidth(60)
        self.layout_selectionData.addWidget(btn)

        self.menu_sortOptions = QtWidgets.QMenu()
        self.btn_sortOptions.setMenu(self.menu_sortOptions)


        self.btn_deleteHistory = btn = QtWidgets.QPushButton()
        btn.setText('Delete Selected')
        btn.setFixedHeight(20)
        self.layout_selectionData.addWidget(btn)
        btn.clicked.connect(self.deleteSelected)

        #### VIEWER ####
        self.viewer_fileNameHistory = ksFileNameHistory_widget(self)
        self.rootLayout.addWidget(self.viewer_fileNameHistory)
        selectionModel = self.viewer_fileNameHistory.selectionModel()
        selectionModel.selectionChanged.connect(self.getSelectionData)

        # self.btn_sortByProject.clicked.connect(self.viewer_fileNameHistory.sortByProject)
        # self.btn_sortByTime.clicked.connect(self.viewer_fileNameHistory.sortByTime)

        self.menu_sortOptions.addAction('Project Path', lambda:self.viewer_fileNameHistory.sortBy(3, True))
        self.menu_sortOptions.addAction('FileName (A-Z)', lambda:self.viewer_fileNameHistory.sortBy(0, True))
        self.menu_sortOptions.addAction('FileName (Z-A)', lambda:self.viewer_fileNameHistory.sortBy(0, False))
        self.menu_sortOptions.addAction('Time Total (Low)', lambda:self.viewer_fileNameHistory.sortBy(4, True))
        self.menu_sortOptions.addAction('Time Total (High)', lambda:self.viewer_fileNameHistory.sortBy(4, False))
        self.menu_sortOptions.addAction('Last Save (Recent)', lambda:self.viewer_fileNameHistory.sortBy(2, False))




        #### INFO LAYOUT ####

        self.layout_info = QtWidgets.QHBoxLayout()
        self.rootLayout.addLayout(self.layout_info)


        label = QtWidgets.QLabel('FilePath:')
        label.setFixedWidth(45)
        self.layout_info.addWidget(label)

        self.field_configPath_default = field = QtWidgets.QLineEdit()
        field.setReadOnly(True)
        field.setText(self._TRACKER._SAVEPATH)
        self.layout_info.addWidget(field)


        self.commandsLayout = QtWidgets.QHBoxLayout()
        self.rootLayout.addLayout(self.commandsLayout)

        self.btn_cancel = QtWidgets.QPushButton('Close')
        self.btn_cancel.setFixedWidth(80)
        self.commandsLayout.addWidget(self.btn_cancel)
        self.btn_cancel.setFocus()
        self.btn_cancel.clicked.connect(self.close)


    def populate_modelView(self):
        rootNode = self.viewer_fileNameHistory.getRootItem()

        fileNameList = self._TRACKER.getHistory_fileNameList()
        for fileName in fileNameList:
            fileNameData = self._TRACKER.getHistory_filenameData(fileName)

            fileNameNode = node_fileHistory(rootNode)
            fileNameNode.setFileName(fileName)
            # fileNameNode.setTimeTotal(fileNameData.get('totalTime'))
            fileNameNode.setLastSave(fileNameData.get('lastSave'))
            fileNameNode.setDirPath(fileNameData.get('dirPath', ''))
            fileNameNode._topNode = True

            for versionInt, versionDict in six.iteritems(fileNameData.get('history')):
                versionNode = node_fileVersionHistory(fileNameNode)
                versionNode.setFileName(versionDict.get('fileName'))
                versionNode.setLastSave(versionDict.get('date'))

                minutes = versionDict.get('time')
                versionNode.setTimeTotal(minutes)
                versionNode.setVersionInt(versionInt)
                fileNameNode.addTotalTime(minutes)
                fileNameNode.addVersion(versionNode)



    def center(self):
        frameGm = self.frameGeometry()
        screen = QtWidgets.QApplication.desktop().screenNumber(QtWidgets.QApplication.desktop().cursor().pos())
        centerPoint = QtWidgets.QApplication.desktop().screenGeometry(screen).center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft())

    def getSelectionData(self):
        totalTime = 0
        selectedItems = self.viewer_fileNameHistory.selectedItems()
        itemSet = set(selectedItems)
        for item in selectedItems:
            if item._parent in itemSet:
                continue
            totalTime += item.getTimeTotal()

        totalTimeFormat = '{:01d}h {:02d}m'.format(*divmod(totalTime, 60))
        self.label_stats_timeSelection.setText(totalTimeFormat)

    def deleteSelected(self):

        reply = QtWidgets.QMessageBox.question(self, 'Continue?', 'Sure you wish to delete selected history?', QtWidgets.QMessageBox.Yes, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.No:
            return

        selectedItems = self.viewer_fileNameHistory.selectedItems()
        selectedItems.sort(key=lambda x: x._nodeType, reverse=False)

        versionDeleteDict = {}
        fileNameDelete = []
        for item in selectedItems:
            if item.typeInfo() == 'FILENAME_NODE':
                fileNameDelete.append(item.getFileName())
                continue

            fileNameNode = item._parent
            parentName = fileNameNode.getFileName()
            if parentName in fileNameDelete:
                continue

            if not versionDeleteDict.get(parentName, None):
                versionDeleteDict[parentName] = []
            versionDeleteDict[parentName].append(item.getVersionInt())

        self._TRACKER.removeHistoryItems(topNodes=fileNameDelete, versionNodes=versionDeleteDict)
        self.viewer_fileNameHistory._del_items()






class node_fileHistory(QtWidgets.QTreeWidgetItem):
    def __init__(self, parent):
        super(node_fileHistory, self).__init__(parent)
        self._parent = parent

        self._fileNameBase = None
        self._timeTotal = 0
        self._lastSave = "-"
        self._lastSave_QDate = None
        self._dirPath = None

        self._topNode = False
        self._versionNodes = []

        self._nodeType = "FILENAME_NODE"

        self.setFlags(self.flags())

    def flags(self):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def typeInfo(self):
        return self._nodeType

    def addVersion(self, versionItem):
        self._versionNodes.append(versionItem)

    def getDataDict(self):
        dataDict = {
                'baseName': self.fileName,
                'timeTotal': self.timeTotal,
                'lastSave': self.lastSave,
            }
        return dataDict

    def getFileName(self):
        return self._fileNameBase

    def setFileName(self, value):
        self._fileNameBase = value
        # self.setText(0, self._fileNameBase)
    fileName = property(fget=getFileName, fset=setFileName)

    def getTimeTotal(self):
        return self._timeTotal

    def setTimeTotal(self, value):
        self._timeTotal = value
        # self.setText(1, self._timeTotal)
    timeTotal = property(fget=getTimeTotal, fset=setTimeTotal)

    def getLastSave(self):
        return self._lastSave

    def setLastSave(self, value):
        self._lastSave = value
        self._lastSave_QDate = tracker.QDateTime_fromString(value)
    lastSave = property(fget=getLastSave, fset=setLastSave)


    def getDirPath(self):
        return self._dirPath

    def setDirPath(self, value):
        self._dirPath = value

    dirPath = property(fget=getDirPath, fset=setDirPath)


    def addTotalTime(self, minutes):
        self.setTimeTotal(self._timeTotal + minutes)

    def data(self, column, role):
        data = super(node_fileHistory, self).data(column, role)
        if role == QtCore.Qt.DisplayRole:
            if column is 0: return self.fileName

            if column is 1:
                minutes = self.timeTotal
                # return '{:01d}h {:02d}m'.format(*divmod(minutes, 60))
                if minutes > 60: timeFormatString = '{:01d}h {:02d}m'.format(*divmod(minutes, 60))
                else: timeFormatString = '{:01d}m'.format(minutes)
                return timeFormatString

            if column is 2:
                return self._lastSave_QDate.toString('      yyyy/MM/dd - HH:mm  ')

            if column is 3: return self.dirPath
            if column is 4: return self.timeTotal

        if role == QtCore.Qt.FontRole:
            if self._topNode == True:
                font = QtGui.QFont()
                font.setBold(True)
                return font

        if role == QtCore.Qt.TextAlignmentRole:
            if column is 1: return QtCore.Qt.AlignRight
            if column is 2: return QtCore.Qt.AlignRight

        if role == QtCore.Qt.UserRole:
            if column is 0: return self.fileName
            if column is 1: return self.timeTotal
            if column is 2: return self._lastSave_QDate
            if column is 3: return self.dirPath

        return data

    def setData(self, column, role, value):
        # if role == QtCore.Qt.EditRole:
        #     if column is 0: self.fileName = value
        #     if column is 1: self.timeTotal = value
        #     if column is 2: self.lastSave = value
        #     return
        super(node_fileHistory, self).setData(column, role, value)



class node_fileVersionHistory(node_fileHistory):
    def __init__(self, parent):
        super(node_fileVersionHistory, self).__init__(parent)
        self._versionInt = None
        self._nodeType = "FILEVERSION_NODE"

    def getVersionInt(self):
        return self._versionInt

    def setVersionInt(self, value):
        self._versionInt = value

    versionInt = property(fget=getVersionInt, fset=setVersionInt)


class ksFileNameHistory_widget(QtWidgets.QTreeWidget):

    def __init__(self, parent=None):
        super(ksFileNameHistory_widget, self).__init__(parent)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.setSortingEnabled(True)


        self.rootItem = self.invisibleRootItem()
        # header = QtWidgets.QTreeWidgetItem(["FileName", "TimeTotal", "LastSave", "timeTotalMin", "lastSaveData"])
        header = QtWidgets.QTreeWidgetItem(["FileName", "TimeTotal", "LastSave", "Dir", "minutes"])
        self.setHeaderItem(header)

        headerView = self.header()
        headerView.setStretchLastSection(False)

        if _PYSIDE_VERSION_ == 1:
            headerView.setResizeMode(0, QtWidgets.QHeaderView.Stretch)
            headerView.setResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
            headerView.setResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
            # headerView.setResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
            # headerView.setResizeMode(3, QtWidgets.QHeaderView.Interactive)
        if _PYSIDE_VERSION_ == 2:
            headerView.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
            headerView.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
            headerView.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
            # headerView.setSectionResizeMode(3, QtWidgets.QHeaderView.ResizeToContents)
            # headerView.setSectionResizeMode(3, QtWidgets.QHeaderView.Interactive)

        self.setColumnWidth(3, 40)
        self.setIndentation(10)
        headerView.setSectionHidden(3, True)
        headerView.setSectionHidden(4, True)
        self.sortByColumn(2, QtCore.Qt.DescendingOrder)

    def sortBy(self, column, ascendingOrder=True):
        if ascendingOrder:
            self.sortByColumn(column, QtCore.Qt.AscendingOrder)
        else:
            self.sortByColumn(column, QtCore.Qt.DescendingOrder)

    def sortByProject(self):
        self.sortByColumn(3, QtCore.Qt.DescendingOrder)

    def sortByTime(self):
        self.sortByColumn(4, QtCore.Qt.DescendingOrder)

    def getRootItem(self):
        return self.rootItem

    def _del_items(self):
        deletedItems = []
        selectedItems = self.selectedItems()

        for item in selectedItems:
            parent = item.parent()
            if not parent:
                parent = self.rootItem

            deletedItems += [item.text(0)]

            children = self.findAllChildren(item)
            deletedItems += children

            index = parent.indexOfChild(item)
            parent.takeChild(index)


    def findAllChildren(self, rootItem):
        children = []
        for i in range(rootItem.childCount()):
            item = rootItem.child(i)
            itemText = item.text(0)

            if not item.childCount():
                children += [itemText]
                continue

            childList = self.findAllChildren(item)
            children += childList

        return children


if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)
    win = GUI_timeTracker()
    win.show()
    sys.exit(app.exec_())
