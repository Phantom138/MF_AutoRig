import pathlib

from PySide2 import QtWidgets
from mf_autoRig.UI.utils.loadUI import loadUi


class ModulePage(QtWidgets.QWidget):
    def __init__(self, base_module, parent=None):
        path = pathlib.Path(__file__).parent.resolve()
        QtWidgets.QWidget.__init__(self, parent)
        loadUi(rf"{path}\modulePage.ui", self)

        # number = QtWidgets.QLabel()
        # number.setText("Number")
        # self.verticalLayout.insertWidget(1, number)

        self.base_module = base_module

        self.btn_guides.clicked.connect(self.mdl_createGuides)
        self.btn_rig.clicked.connect(self.mdl_rig)
        self.mdl_name.textChanged.connect(self.nameChanged)

        self.btn_guides.setEnabled(False)
        self.btn_rig.setEnabled(False)

    def mdl_createGuides(self):
        name = self.mdl_name.text()
        print(f"//// Running create guides for {self.base_module} with name {name}")

        self.module = self.base_module(name)
        self.module.create_guides()
        self.btn_rig.setEnabled(True)

    def mdl_rig(self):
        print(f"//// Running create rig for module {self.module.name}")
        if self.base_module == 'Hand':
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