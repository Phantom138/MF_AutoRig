import pathlib
from PySide2 import QtWidgets
from mf_autoRig.UI.utils.loadUI import loadUi
import mf_autoRig.modules.module_tools as crMod

class EditWidget(QtWidgets.QDialog):
    def __init__(self, module_meta_node, parent=None):
        QtWidgets.QDialog.__init__(self, parent)

        path = pathlib.Path(__file__).parent.resolve()
        loadUi(rf"{path}\editWidget.ui", self)
        name = module_meta_node.Name.get()

        self.module_meta_node = module_meta_node

        self.label_module.setText(f'Editing {name}')
        self.btn_editMode.clicked.connect(self.edit_item)

        self.btn_apply.clicked.connect(self.apply_changes)
        self.btn_apply.setEnabled(False)

    def edit_item(self):
        self.btn_apply.setEnabled(True)
        print('Edit item')
        self.module = crMod.createModule(self.module_meta_node)
        self.module.edit()

    def apply_changes(self):
        self.module.apply_edit()
        self.destroy()