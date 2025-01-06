try:
    from PySide2 import QtGui
    from PySide2.QtGui import QFont
    from PySide2.QtWidgets import QMenu, QAction, QTreeWidgetItem, QStyledItemDelegate
    from PySide2.QtCore import Qt
except ImportError:
    from PySide6 import QtGui
    from PySide6.QtGui import QFont, QAction
    from PySide6.QtWidgets import QMenu, QTreeWidgetItem, QStyledItemDelegate
    from PySide6.QtCore import Qt

from functools import partial
import pathlib

from mf_autoRig.UI.modifyWindow.editWidget import EditWidget
from mf_autoRig.UI.utils.UI_Template import delete_workspace_control, UITemplate
import mf_autoRig.modules.module_tools as module_tools
from mf_autoRig.utils.undo import UndoStack
from mf_autoRig import log
from mf_autoRig.UI.createWindow.modulePage import ConfigPage

WORK_PATH = pathlib.Path(__file__).parent.resolve()


def run_update_tree(func):
    """
    Decorator to update the tree after a function is called
    """
    def wrapper(self, *args, **kwargs):
        try:
            result = func(self, *args, **kwargs)
        finally:
            self.update_tree()

        return result
    return wrapper


class ModifyWindow(UITemplate):
    def __init__(self, title):
        ui_path = f'{WORK_PATH}\modifyWindow.ui'
        super().__init__(widget_title=title, ui_path=ui_path)
        self.config_widget = None

        font = QFont()
        font.setPointSize(8)

        self.ui.tree.setFont(font)
        # self.ui.list_modules.setSpacing(2)
        self.ui.tree.setIndentation(15)
        self.ui.tree.itemSelectionChanged.connect(self.on_selection_changed)

        # Enable context menu
        self.ui.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.tree.customContextMenuRequested.connect(self.context_menu)

        # Button connections
        self.ui.btn_updateLists.clicked.connect(self.update_tree)
        self.update_tree()
    
    def update_tree(self):
        print("UPDATING UI TREE")
        # Store expanded state
        expanded_items = self.get_expanded_items()

        self.ui.tree.clear()

        self.modules = module_tools.get_all_modules(create=True)


        print("FOUND MODULES", self.modules)
        if self.modules is None:
            return

        self.modules_ref = {module.name: module for module in self.modules}

        # Get root modules (the ones with no parents)
        root_modules = [module for module in self.modules if module.get_parent() is None]
        print("ROOT_MODULES", root_modules)
        def validate(tree_item, module):
            # Get information about the selected module
            is_rigged, is_connected, is_mirrored = module.get_info()

            # print(tree_item, module)
            if is_mirrored:
                # Mirrored modules are grey
                color = QtGui.QColor("#737373")
                toolTip = f"Module mirrored from {module.mirrored_from.name}, cannot be edited"
                tree_item.setText(1, f'Mirrored from {module.mirrored_from.name}')

            elif module.guides is None or len(module.guides) < 2:
                # Modules with no guides are red
                color = Qt.red
                toolTip = "Warning: No guides found, delete or recreate module"

            elif is_rigged:
                # Modules that are rigged are blue
                color = QtGui.QColor("#00deff")
                toolTip = "Module is rigged"

            else:
                # Modules that are not rigged are white
                color = Qt.white
                toolTip = "Module is not rigged, rig it to connect to other modules"

            tree_item.setForeground(0, QtGui.QBrush(color))
            tree_item.setForeground(1, QtGui.QBrush(color))
            tree_item.setToolTip(0, toolTip)
            tree_item.setToolTip(1, toolTip)

        for mdl in root_modules:
            item = QTreeWidgetItem([mdl.name, mdl.moduleType])
            self.ui.tree.addTopLevelItem(item)
            validate(item, mdl)

            # add children recursively
            def add_children(parent_item, parent_mdl):
                for child_mdl in parent_mdl.get_children():
                    child_item = QTreeWidgetItem([child_mdl.name, child_mdl.moduleType])

                    parent_item.addChild(child_item)
                    # Validate item
                    validate(child_item, child_mdl)

                    add_children(child_item, child_mdl)

            # Run the recursive function
            add_children(item, mdl)

        # Restore expanded state
        self.set_expanded_items(expanded_items)

    def get_expanded_items(self):
        expanded_items = set()
        for i in range(self.ui.tree.topLevelItemCount()):
            item = self.ui.tree.topLevelItem(i)
            if item.isExpanded():
                expanded_items.add(item.text(0))
        return expanded_items

    def set_expanded_items(self, expanded_items):
        for i in range(self.ui.tree.topLevelItemCount()):
            item = self.ui.tree.topLevelItem(i)
            if item.text(0) in expanded_items:
                item.setExpanded(True)

    def on_selection_changed(self):
        if self.config_widget is not None:
            self.ui.verticalLayout.removeWidget(self.config_widget)
            self.config_widget.deleteLater()
            self.config_widget = None

        if self.ui.tree.currentItem() is None:
            return

        key = self.ui.tree.currentItem().text(0)

        self.selected_module = self.modules_ref[key] # TODO: this could be changed to query _instances dict on Module class


        # Select the module in the scene
        if self.selected_module.guide_grp is not None:
            import maya.cmds as cmds
            cmds.select(clear=True)
            cmds.select(self.selected_module.guide_grp.name())
            cmds.select(self.selected_module.metaNode.name(), add=True)
            # pm.viewFit()

        # Create config widget
        self.config_widget = ConfigPage(self.selected_module, parent=self)
        self.ui.verticalLayout.addWidget(self.config_widget)


    def context_menu(self, position):
        if self.ui.tree.currentItem() is None:
            return

        # Get information about the selected module
        is_rigged, is_connected, is_mirrored = self.selected_module.get_info()

        # Create context menu
        self.menu = QMenu()

        if is_connected:
            # This means we cannot connect to another module, only disconnect
            self.__disconnect_menu()
        else:
            self.__connect_menu()

        if is_rigged:
            # Show rig menu
            self.__destroy_rig_menu()
        else:
            self.__rig_menu()

        if not is_mirrored:
            if self.selected_module.mirrored_to is None:
                self.__mirror_menu()


        # Delete menu is for everything
        self.__delete_menu()
        self.__print_rig_pos()

        # Show context menu
        self.menu.exec_(self.ui.tree.mapToGlobal(position))

    def __connect_menu(self):
        connect_menu = QMenu('Connect to', self)
        try:
            conn_to = self.selected_module.connectable_to
        except AttributeError:
            conn_to = []

        conn_options = module_tools.get_all_modules(module_types=conn_to, create=True)

        for option in conn_options:
            name = option.name
            mdl_type = option.moduleType

            if mdl_type == 'Spine' and self.selected_module.moduleType == 'Limb':
                # HACKY way to do the Limb to Spine connection
                # TODO: Make this more dynamic
                for i, pt in enumerate(option.attachment_pts):
                    action = QAction(f'{name} <{mdl_type}> {pt}', connect_menu)
                    connect_menu.addAction(action)

                    action.triggered.connect(partial(self.connect_module, option, i))
            else:
                action = QAction(f'{name} <{mdl_type}>', connect_menu)
                connect_menu.addAction(action)

                action.triggered.connect(partial(self.connect_module, option))

        if len(conn_to) != 0:
            self.menu.addMenu(connect_menu)

    def __disconnect_menu(self):
        disconnect_action = QAction('Disconnect', self)
        disconnect_action.triggered.connect(self.disconnect_item)
        self.menu.addAction(disconnect_action)

    def __edit_menu(self):
        edit_action = QAction('Edit', self)
        edit_action.triggered.connect(self.edit_item)
        self.menu.addAction(edit_action)

    def __delete_menu(self):
        # TODO: Add a confirmation dialog
        delete_action = QAction('Delete', self)
        delete_action.triggered.connect(self.delete_item)
        self.menu.addAction(delete_action)

    def __mirror_menu(self):
        mirror_action = QAction('Mirror', self)
        mirror_action.triggered.connect(self.mirror_item)
        self.menu.addAction(mirror_action)

    def __rig_menu(self):
        rig_action = QAction('Rig', self)
        rig_action.triggered.connect(self.recursive_rig)
        self.menu.addAction(rig_action)

    def __destroy_rig_menu(self):
        destroy_rig_action = QAction('Destroy Rig', self)
        destroy_rig_action.triggered.connect(partial(self.recursive_rig, destroy=True))
        self.menu.addAction(destroy_rig_action)

    def __print_rig_pos(self):
        print_rig_action = QAction('Print Rig Pos', self)
        print_rig_action.triggered.connect(self.selected_module.print_class)
        self.menu.addAction(print_rig_action)


    @run_update_tree
    def connect_module(self, module, index=None):
        with UndoStack(f"Connected {self.selected_module.name} to {module.name}"):
            if index is None:
                self.selected_module.connect_guides(module)
            elif isinstance(index, int):
                self.selected_module.connect_guides(module, index)

    @run_update_tree
    def mirror_item(self):
        with UndoStack(f"Mirrored {self.selected_module.name}"):
            self.selected_module.mirror_guides()

    @run_update_tree
    def disconnect_item(self):
        with UndoStack(f"Disconnected {self.selected_module.name}"):
            if self.selected_module.mirrored_from is not None:
                self.selected_module.update_mirrored(destroy=True)
            else:
                self.selected_module.destroy_rig()
                self.selected_module.create_joints()
                self.selected_module.rig()

    def edit_item(self):
        self.edit_widget = EditWidget(self.selected_module, self.update_tree, parent=self)
        mouse_pos = QtGui.QCursor.pos()
        self.edit_widget.setGeometry(mouse_pos.x(), mouse_pos.y(), self.edit_widget.width(), self.edit_widget.height() )
        self.edit_widget.show()

    # @run_update_tree
    # def rig_item(self):
    #     with UndoStack(f"Rigged {self.selected_module.name}"):
    #         self.selected_module.create_joints()
    #         self.selected_module.rig()

    @run_update_tree
    def recursive_rig(self, destroy=False):
        # Rig recursively
        mdl_to_rig = self.selected_module.get_all_children()
        mdl_to_rig.reverse()
        mdl_to_rig.append(self.selected_module)

        if destroy is True:
            log.info(f"Destroying Rig: {mdl_to_rig}")
            for module in mdl_to_rig:
                module.destroy_rig()
            return

        log.info(f"Rigging: {mdl_to_rig}")
        for module in mdl_to_rig:
            module.create_joints()
            module.rig()

    @run_update_tree
    def delete_item(self):
        with UndoStack(f"Deleted {self.selected_module.name}"):
            self.selected_module.delete()


def showWindow():
    title = 'Modify Modules'

    delete_workspace_control(title)

    ui = ModifyWindow(title)
    ui.show(dockable=True)

if __name__ == "__main__":
    showWindow()