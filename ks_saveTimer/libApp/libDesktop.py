from __future__ import absolute_import
from __future__ import print_function
import six
try:
    from PySide2 import QtCore
    from PySide2.QtCore import Signal
except ImportError:
    from PySide import QtCore
    from PySide.QtCore import Signal

import os
from ks_saveTimer.lib import Singleton

def QT_getMainWindow():
    return None

def getUserConfigLocation():
    return os.path.expanduser("~")

def displayWarningMessage(message):
    print(message)

def displayStatusMessage(message):
    print(message)


##
## ------------------ Callbacks ------------------
##



class appCallbacks(six.with_metaclass(Singleton.QtSingletonMetaclass, QtCore.QObject)):
    fileSaved = Signal()
    fileOpened = Signal()

    currentWatchFolder = ''
    currentWatchFile = ''
    currentFileExt = ''

    dirContent = []

    def __init__(cls):
        super(appCallbacks, cls).__init__()

        cls.systemWatcher = QtCore.QFileSystemWatcher()
        cls.systemWatcher.directoryChanged.connect(cls.checkNewFiles)
        cls.systemWatcher.fileChanged.connect(cls.emitSaveSignal)


    def emitSaveSignal(cls):
        cls.fileSaved.emit()
        cls.signalPrint()

    def checkNewFiles(cls):
        files = cls.listDirectory(cls.currentWatchFolder)
        newFiles = list(set(files) - set(cls.dirContent))
        if newFiles:
            for file in newFiles:
                print('newFile:', file)
                cls.systemWatcher.addPath(os.path.normpath(os.path.join(cls.currentWatchFolder, file)))
            cls.emitSaveSignal()
        print('nowWatching - Files:', cls.systemWatcher.files())
        print('nowWatching - Dirs:', cls.systemWatcher.directories())

        cls.dirContent = files



    def setWatchFile(cls, path):
        try:
            cls.systemWatcher.removePaths(cls.systemWatcher.files())
            cls.systemWatcher.removePaths(cls.systemWatcher.directories())
        except:
            print('Failed removing files from systemWatcher!')


        fileExt = os.path.splitext(path)
        cls.currentFileExt = fileExt

        dirPath, fileName = os.path.split(path)
        print('dirPath:', dirPath)
        print('fileName:', fileName)
        cls.currentWatchFolder = dirPath

        files = cls.listDirectory(dirPath)
        print('dir files:', files)
        cls.dirContent = files

        cls.systemWatcher.addPath(dirPath)
        cls.systemWatcher.addPath(path)

        print('Now Watching:', path)

    def listDirectory(cls, path):
        files = []
        for item in os.listdir(path):
            if item.endswith(cls.currentFileExt):
                files.append(item)
        return files

    def signalPrint(cls):
        print('signal has been triggered!', cls.fileSaved)