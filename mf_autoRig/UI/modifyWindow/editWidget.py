import pathlib
from PySide2 import QtWidgets

from mf_autoRig import log
from mf_autoRig.UI.utils.loadUI import loadUi
import mf_autoRig.lib.defaults as df
from mf_autoRig.modules import module_tools


class EditWidget(QtWidgets.QDialog):
    def __init__(self, module, run_when_finished, parent=None):
        QtWidgets.QDialog.__init__(self, parent)

        path = pathlib.Path(__file__).parent.resolve()
        loadUi(rf"{path}\editWidget.ui", self)

        self.run_when_finished = run_when_finished
        self.module = module

        self.label_module.setText(f'Editing {self.module.name}')

        self.edited_modules = [self.module]
        self.edited_modules.extend(self.module.get_all_children())

        print(self.edited_modules)

        self.btn_editMode.clicked.connect(self.edit_item)

        self.btn_apply.clicked.connect(self.apply_changes)
        self.btn_apply.setEnabled(False)

    def edit_item(self):


        for child in self.edited_modules:
            if child.mirrored_from is None:
                child.destroy_rig(disconnect=False)

        self.btn_apply.setEnabled(True)

    def apply_changes(self):
        log.info(f"Applied changes for {self.edited_modules}")

        for edit_mdl in self.edited_modules:
            # The rebuild rig function automatically skips the mirrored modules
            edit_mdl.rebuild_rig()

        def reconnect_module(module):
            connect_to = module.get_parent()
            if connect_to is None:
                return

            # Get the index of the connection, this is relevant for connecting the limbs to the spine
            meta_connect_to = module.metaNode.connected_to.listConnections(p=True)[0]
            index = meta_connect_to.logicalIndex()

            if index == 0:
                module.connect(connect_to, force=True)
            else:
                module.connect(connect_to, index=index, force=True)


        not_mirrored_mdls = [module for module in self.edited_modules if module.mirrored_from is None]

        # Redo connections
        for module in not_mirrored_mdls:
            reconnect_module(module)

            # If existing, also connect the mirrored module
            if module.mirrored_to is not None:
                reconnect_module(module_tools.createModule(module.mirrored_to))


        self.run_when_finished()
        self.destroy()