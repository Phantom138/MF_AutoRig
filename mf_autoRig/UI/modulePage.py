from PySide2 import QtWidgets
from mf_autoRig.UI.utils.loadUI import loadUi


class ModulePage(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        loadUi(r"M:\Quick Acces\Projects\04_MayaScripts\mf_autoRig\UI\modulePage.ui", self)


a = ModulePage()
a.show()