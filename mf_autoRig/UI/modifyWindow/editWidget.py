import pathlib
from PySide2 import QtWidgets
from mf_autoRig.UI.utils.loadUI import loadUi
import mf_autoRig.modules.module_tools as crMod
from mf_autoRig.modules import module_tools


class EditWidget(QtWidgets.QDialog):
    def __init__(self, module_meta_node, parent=None):
        QtWidgets.QDialog.__init__(self, parent)

        path = pathlib.Path(__file__).parent.resolve()
        loadUi(rf"{path}\editWidget.ui", self)
        name = module_meta_node.Name.get()

        self.module = crMod.createModule(module_meta_node)

        self.label_module.setText(f'Editing {name}')
        self.btn_editMode.clicked.connect(self.edit_item)

        self.btn_apply.clicked.connect(self.apply_changes)
        self.btn_apply.setEnabled(False)

    def edit_item(self):
        highest_parent = self.module.get_connections(direction='up')[-1]
        connections = module_tools.get_connections(highest_parent.metaNode)

        self.edited_modules = connections

        for child in self.edited_modules:
            child.destroy_rig()

        self.btn_apply.setEnabled(True)

    def apply_changes(self):
        for edit_mdl in self.edited_modules:
            edit_mdl.rebuild_rig()

        # Redo connections
        for i in range(len(self.edited_modules) - 1, 0, -1):
            self.edited_modules[i].connect(self.edited_modules[i - 1])

        self.destroy()