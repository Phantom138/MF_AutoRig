try:
    from PySide2 import QtGui
    from PySide2.QtGui import QFont
    from PySide2.QtWidgets import QMenu, QAction, QTreeWidgetItem, QStyledItemDelegate, QObject
    from PySide2.QtCore import Qt, QEvent
except ImportError:
    from PySide6 import QtGui
    from PySide6.QtGui import QFont, QAction
    from PySide6.QtWidgets import QMenu, QTreeWidgetItem, QStyledItemDelegate
    from PySide6.QtCore import Qt, QObject, QEvent

from functools import partial
import pathlib
import gc

from mf_autoRig.UI.modifyWindow.editWidget import EditWidget
from mf_autoRig.UI.utils.UI_Template import delete_workspace_control, UITemplate
import mf_autoRig.modules.module_tools as module_tools
from mf_autoRig.utils.undo import UndoStack
from mf_autoRig import log
from mf_autoRig.UI.createWindow.modulePage import ConfigPage
from mf_autoRig.modules.Module import Module
import pymel.core as pm
import mf_autoRig.utils.defaults as df

WORK_PATH = pathlib.Path(__file__).parent.resolve()


class TreeViewEventFilter(QObject):
    """ Event filter to catch mouse clicks outside items in a QTreeWidget """
    def __init__(self, tree_widget):
        super().__init__(tree_widget)
        self.tree_widget = tree_widget
        self.tree_widget.viewport().installEventFilter(self)  # Install event filter on viewport

    def eventFilter(self, obj, event):
        if obj == self.tree_widget.viewport() and event.type() == QEvent.MouseButtonPress:
            index = self.tree_widget.indexAt(event.pos())  # Check if clicked on an item

            if not index.isValid():  # Clicked outside any item
                self.tree_widget.selectionModel().clearSelection()  # Deselect all items
                self.tree_widget.setCurrentItem(None)

        return super().eventFilter(obj, event)  # Default event processing


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
        TreeViewEventFilter(self.ui.tree)

        # Enable context menu
        self.ui.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.tree.customContextMenuRequested.connect(self.context_menu)

        # Button connections
        self.ui.btn_updateLists.clicked.connect(self.update_tree)
        self.update_tree()
    
    def update_tree(self):
        # if force:
        #     print("reset instances")
        #     # force update
        #     Module.instances = {}

        # Store expanded state
        expanded_items = self.get_expanded_items()

        self.ui.tree.clear()

        self.modules = module_tools.get_all_modules(create=True)
        if self.modules is None:
            return

        self.modules_ref = {module.name: module for module in self.modules}

        # Get root modules (the ones with no parents)
        root_modules = [module for module in self.modules if module.get_parent() is None]

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

        def add_children(parent_item, parent_mdl):
            for child_mdl in parent_mdl.get_children():
                child_item = QTreeWidgetItem([child_mdl.name, child_mdl.moduleType])
                parent_item.addChild(child_item)
                # Validate item
                validate(child_item, child_mdl)

                add_children(child_item, child_mdl)

        for mdl in root_modules:

            item = QTreeWidgetItem([mdl.name, mdl.moduleType])
            self.ui.tree.addTopLevelItem(item)
            validate(item, mdl)

            # Run the recursive function
            add_children(item, mdl)

        # Restore expanded state
        self.set_expanded_items(expanded_items)

    def get_expanded_items(self):
        expanded_items = {}

        def _save_expanded_state(item):
            expanded_items[item.text(0)] = item.isExpanded()
            for j in range(item.childCount()):
                _save_expanded_state(item.child(j))

        for i in range(self.ui.tree.topLevelItemCount()):
            _save_expanded_state(self.ui.tree.topLevelItem(i))

        return expanded_items

    def set_expanded_items(self, expanded_items):
        def _expand_items(item):
            if item.text(0) in expanded_items:
                item.setExpanded(expanded_items[item.text(0)])
            for j in range(item.childCount()):
                _expand_items(item.child(j))

        for i in range(self.ui.tree.topLevelItemCount()):
            _expand_items(self.ui.tree.topLevelItem(i))

    def on_selection_changed(self):
        if self.config_widget is not None:
            self.ui.verticalLayout.removeWidget(self.config_widget)
            self.config_widget.deleteLater()
            self.config_widget = None

        if self.ui.tree.currentItem() is None:
            self.selected_module = None
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
        menu = QMenu()

        if is_rigged:
            if self.selected_module.parent is not None:
                parent_is_rigged, _, _ = self.selected_module.parent.get_info()
            else:
                parent_is_rigged = False

            if not parent_is_rigged:
                self.__destroy_rig_menu(menu)
        else:
            self.__rig_menu(menu)

            if is_connected:
                self.__disconnect_menu(menu)
            else:
                self.__connect_menu(menu)

            if not is_mirrored:
                if self.selected_module.mirrored_to is None:
                    self.__mirror_menu(menu)


        # Delete menu is for everything
        self.__delete_menu(menu)

        # Show context menu
        menu.exec_(self.ui.tree.mapToGlobal(position))

    def __connect_menu(self, menu):
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
                for i, pt in enumerate(option.guides):
                    action = QAction(f'{name} <{mdl_type}> {pt}', connect_menu)
                    connect_menu.addAction(action)

                    action.triggered.connect(partial(self.connect_module, option, i))
            else:
                action = QAction(f'{name} <{mdl_type}>', connect_menu)
                connect_menu.addAction(action)

                action.triggered.connect(partial(self.connect_module, option, -1))

        if len(conn_to) != 0:
            menu.addMenu(connect_menu)

    def __disconnect_menu(self, menu):
        disconnect_action = QAction('Disconnect', self)
        disconnect_action.triggered.connect(self.disconnect_item)
        menu.addAction(disconnect_action)

    def __edit_menu(self, menu):
        edit_action = QAction('Edit', self)
        edit_action.triggered.connect(self.edit_item)
        menu.addAction(edit_action)

    def __delete_menu(self, menu):
        # TODO: Add a confirmation dialog
        delete_action = QAction('Delete', self)
        delete_action.triggered.connect(self.delete_item)
        menu.addAction(delete_action)

    def __mirror_menu(self, menu):
        mirror_action = QAction('Mirror', self)
        mirror_action.triggered.connect(self.mirror_item)
        menu.addAction(mirror_action)

    def __rig_menu(self, menu):
        rig_action = QAction('Rig', self)
        rig_action.triggered.connect(self.recursive_rig)
        menu.addAction(rig_action)

    def __destroy_rig_menu(self, menu):
        destroy_rig_action = QAction('Destroy Rig', self)
        destroy_rig_action.triggered.connect(partial(self.recursive_rig, destroy=True))
        menu.addAction(destroy_rig_action)

    def __print_rig_pos(self, menu):
        print_rig_action = QAction('Print Rig Pos', self)
        print_rig_action.triggered.connect(self.selected_module.print_class)
        menu.addAction(print_rig_action)


    @run_update_tree
    def connect_module(self, module, index):
        print("CONNECTING MODULE", self.selected_module.name, module.name, index)
        with UndoStack(f"Connected {self.selected_module.name} to {module.name}"):
            self.selected_module.attach_index = index
            self.selected_module.metaNode.attach_index.set(index)
            self.selected_module.connect_guides(module)

    @run_update_tree
    def mirror_item(self):
        with UndoStack(f"Mirrored {self.selected_module.name}"):
            self.selected_module.mirror_guides()

    @run_update_tree
    def disconnect_item(self):
        with UndoStack(f"Disconnected {self.selected_module.name}"):
            self.selected_module.disconnect_guides()

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
            pm.showHidden(df.rig_guides_grp)
            return

        log.info(f"Rigging: {mdl_to_rig}")
        for module in mdl_to_rig:
            is_rigged, _, _ = module.get_info()
            if not is_rigged:
                module.create_joints()
                module.rig()

        # Hide guides grp
        pm.hide(df.rig_guides_grp)

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