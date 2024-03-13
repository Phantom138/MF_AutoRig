import pathlib

from PySide2 import QtWidgets
from mf_autoRig.UI.utils.loadUI import loadUi


class ModulePage(QtWidgets.QWidget):
    def __init__(self, base_module, parent=None):
        path = pathlib.Path(__file__).parent.resolve()
        QtWidgets.QWidget.__init__(self, parent)
        # TODO: proper path joining
        loadUi(rf"{path}\modulePage.ui", self)

        self.base_module = base_module
        # number = QtWidgets.QLabel()
        # number.setText("Number")
        # self.verticalLayout.insertWidget(1, number)

        self.__create_connections()

    def __create_connections(self):

        self.btn_guides.clicked.connect(self.mdl_createGuides)
        self.btn_rig.clicked.connect(self.mdl_rig)
        self.mdl_name.textChanged.connect(self.nameChanged)

        self.btn_guides.setEnabled(False)
        self.btn_rig.setEnabled(False)

    def mdl_createGuides(self):
        name = self.mdl_name.text()

        self.module = self.base_module(name)
        self.module.create_guides()
        self.btn_rig.setEnabled(True)

    def mdl_rig(self):
        if self.module.moduleType == 'Hand':
            self.module.create_joints()
            self.module.create_hand()
            self.module.rig()
            return None

        self.module.create_joints()
        self.module.rig()

    def nameChanged(self):
        name = self.mdl_name.text()
        if not name:
            self.btn_guides.setEnabled(False)
            self.btn_rig.setEnabled(False)
            return None

        self.btn_guides.setEnabled(True)

class HandPage(ModulePage):
    def __init__(self, base_module, parent=None):
        super().__init__(base_module, parent)

        options = QtWidgets.QHBoxLayout()
        self.spread = QtWidgets.QCheckBox("Spread")
        self.spread.setChecked(True)

        self.curl = QtWidgets.QCheckBox("Curl")
        self.curl.setChecked(True)

        options.addWidget(self.spread)
        options.addWidget(self.curl)

        self.verticalLayout.insertLayout(2, options)

    def mdl_rig(self):
        self.module.create_joints()
        self.module.create_hand()
        self.module.rig(spread = self.spread.isChecked(), curl = self.curl.isChecked())