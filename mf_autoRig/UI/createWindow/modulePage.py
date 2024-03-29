import pathlib

from PySide2 import QtWidgets
from PySide2.QtGui import QIntValidator
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

        self.fingers_label = QtWidgets.QLabel("Fingers:")
        self.fingers = QtWidgets.QSpinBox()
        self.fingers.setValue(5)
        self.fingers.setRange(1,5)

        self.spread = QtWidgets.QCheckBox("Spread")
        self.spread.setChecked(True)

        self.curl = QtWidgets.QCheckBox("Curl")
        self.curl.setChecked(True)

        options.addWidget(self.fingers_label)
        options.addWidget(self.fingers)
        options.addWidget(self.spread)
        options.addWidget(self.curl)

        self.verticalLayout.insertLayout(1, options)

    def mdl_createGuides(self):
        name = self.mdl_name.text()

        self.module = self.base_module(name, finger_num = self.fingers.value())
        self.module.create_guides()
        self.btn_rig.setEnabled(True)

    def mdl_rig(self):
        self.module.create_joints()
        self.module.rig(spread = self.spread.isChecked(), curl = self.curl.isChecked())

class BendyLimbPage(ModulePage):
    def __init__(self, base_module, parent=None):
        super().__init__(base_module, parent)
        options = QtWidgets.QHBoxLayout()

        self.input_label = QtWidgets.QLabel("Number of bend joints:")
        self.bend_joints_input = QtWidgets.QLineEdit()

        self.bend_joints_input.textChanged.connect(self.validate_input)

        options.addWidget(self.input_label)
        options.addWidget(self.bend_joints_input)


        self.verticalLayout.insertLayout(2, options)

    def validate_input(self):
        text = self.bend_joints_input.text()
        try:
            value = int(text)
            if 2 <= value <= 10:
                self.bend_joints_input.setStyleSheet("color: white;")
            else:
                self.bend_joints_input.setStyleSheet("color: red;")
        except ValueError:
            self.bend_joints_input.setStyleSheet("color: red;")


    def mdl_rig(self):
        self.module.create_joints()
        self.module.rig(bend_joints=int(self.bend_joints_input.text()))
