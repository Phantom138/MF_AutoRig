import pathlib
from PySide2 import QtWidgets
from mf_autoRig.UI.utils.loadUI import loadUi
import mf_autoRig.modules.module_tools as crMod
from mf_autoRig.modules import module_tools


class EditWidget(QtWidgets.QDialog):
    def __init__(self, module, run_when_finished, parent=None):
        QtWidgets.QDialog.__init__(self, parent)

        path = pathlib.Path(__file__).parent.resolve()
        loadUi(rf"{path}\editWidget.ui", self)

        self.run_when_finished = run_when_finished
        self.module = module

        highest_parent = self.module.get_connections(direction='up')[-1]
        self.edited_modules = module_tools.get_connections(highest_parent.metaNode)
        self.label_module.setText(f'Editing {highest_parent.name}')

        self.btn_editMode.clicked.connect(self.edit_item)

        self.btn_apply.clicked.connect(self.apply_changes)
        self.btn_apply.setEnabled(False)

    def edit_item(self):
        for child in self.edited_modules:
            if child.mirrored_from is None:
                child.destroy_rig()

        self.btn_apply.setEnabled(True)

    def apply_changes(self):
        print("Applying changes")
        print(self.edited_modules)
        modules = [module for module in self.edited_modules if module.mirrored_from is None]

        for edit_mdl in modules:
            print(f"Rebuilding {edit_mdl.name}")
            edit_mdl.rebuild_rig()

        # # Redo connections
        # for module in modules:
        #     meta_connect_to = module.metaNode.affectedBy.get()
        #     print(meta_connect_to)
        #     if len(meta_connect_to) == 1:
        #         connect_to = module_tools.createModule(meta_connect_to[0])
        #         module.connect(connect_to, force=True)


        self.run_when_finished()
        self.destroy()