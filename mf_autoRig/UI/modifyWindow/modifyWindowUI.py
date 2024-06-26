from PySide2 import QtGui
from PySide2.QtGui import QFont
from PySide2.QtWidgets import QMenu, QAction, QTreeWidgetItem, QStyledItemDelegate
from PySide2.QtCore import Qt
from functools import partial


from mf_autoRig.UI.modifyWindow.editWidget import EditWidget
from mf_autoRig.UI.utils.UI_Template import delete_workspace_control, UITemplate
import mf_autoRig.modules.module_tools as module_tools
import pymel.core as pm


import pathlib
WORK_PATH = pathlib.Path(__file__).parent.resolve()



class ModifyWindow(UITemplate):
    def __init__(self, title):
        ui_path = f'{WORK_PATH}\modifyWindow.ui'
        super().__init__(widget_title=title, ui_path=ui_path)

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
        # Store expanded state
        expanded_items = self.get_expanded_items()

        self.ui.tree.clear()

        self.modules = module_tools.get_all_modules(create=True)

        if self.modules is None:
            return

        self.modules_ref = {module.name: module for module in self.modules}

        # Get root modules (the ones with no parents)
        root_modules = [module for module in self.modules if module.get_parent() is None]

        def validate(item, module):
            # Mirrored modules are grey
            if module.mirrored_from is not None:
                color = QtGui.QColor("#737373")
                item.setForeground(0, QtGui.QBrush(color))
                item.setForeground(1, QtGui.QBrush(color))

            # If module doesn't have guides, show red
            elif module.guides is None or len(module.guides) < 2:
                item.setForeground(0, QtGui.QBrush(Qt.red))
                item.setForeground(1, QtGui.QBrush(Qt.red))
                item.setToolTip(0, "Warning: No guides found, delete or recreate module")

            elif module.all_ctrls is not None and len(module.all_ctrls) != 0:
                color = QtGui.QColor("#00deff")
                item.setForeground(0, QtGui.QBrush(color))
                item.setForeground(1, QtGui.QBrush(color))
                item.setToolTip(0, "Module is rigged")

            else:
                item.setToolTip(0, "Module is not rigged, rig it to connect to other modules")

        for mdl in root_modules:
            item = QTreeWidgetItem([mdl.name, mdl.moduleType])
            self.ui.tree.addTopLevelItem(item)
            validate(item, mdl)

            # add children recursively
            def add_children(parent_item, parent_mdl):
                for child in parent_mdl.get_children():
                    child_item = QTreeWidgetItem([child.name, child.moduleType])
                    parent_item.addChild(child_item)
                    # Validate item
                    validate(child_item, child)

                    add_children(child_item, child)

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
        if self.ui.tree.currentItem() is None:
            return
        key = self.ui.tree.currentItem().text(0)
        self.selected_module = self.modules_ref[key]

        if self.selected_module.joints_grp is not None:
            pm.select(self.selected_module.joints_grp)
            # pm.viewFit()

    def context_menu(self, position):
        if self.ui.tree.currentItem() is None:
            return

        # Create context menu
        self.menu = QMenu()

        if self.selected_module.all_ctrls is None or len(self.selected_module.all_ctrls) == 0:
            # This means the module is not rigged
            rig_action = QAction('Rig', self)
            rig_action.triggered.connect(self.rig_item)
            self.menu.addAction(rig_action)

        else:
            # This means the module is rigged, so we can show connect menu and mirror menu
            # Connect menu

            # If module isn't connected to anything, show all connectable modules
            if self.selected_module.get_parent() is None:
                connect_menu = QMenu('Connect to', self)
                try:
                    conn_to = self.selected_module.connectable_to
                except AttributeError:
                    conn_to = []

                conn_options = module_tools.get_all_modules(module_types=conn_to, create=True)


                for option in conn_options:
                    name = option.name
                    type = option.moduleType

                    if type == 'Spine' and self.selected_module.moduleType == 'Limb':
                        # HACKY way to do the Limb to Spine connection
                        action1 = QAction(f'{name} <{type}> Chest', connect_menu)
                        connect_menu.addAction(action1)

                        action1.triggered.connect(partial(self.selected_module.connect, option, 'Chest'))

                        action2 = QAction(f'{name} <{type}> Hip', connect_menu)
                        connect_menu.addAction(action2)

                        action2.triggered.connect(partial(self.selected_module.connect, option, 'Hip'))

                    else:
                        action = QAction(f'{name} <{type}>', connect_menu)
                        connect_menu.addAction(action)

                        action.triggered.connect(partial(self.connect_module, option))


                self.menu.addMenu(connect_menu)

            # Module is connected to something, show disconnect option
            else:
                disconnect_action = QAction('Disconnect', self)
                disconnect_action.triggered.connect(self.disconnect_item)
                self.menu.addAction(disconnect_action)

            # If it is rigged, enable mirror menu
            if self.selected_module.mirrored_from is None:
                mirror_action = QAction('Mirror', self)
                mirror_action.triggered.connect(self.mirror_item)
                self.menu.addAction(mirror_action)



        # Create actions
        edit_action = QAction('Edit', self)
        delete_action = QAction('Delete', self)

        # Connect actions to functions
        edit_action.triggered.connect(self.edit_item)
        delete_action.triggered.connect(self.delete_item)

        # Add actions to menu
        self.menu.addAction(edit_action)
        self.menu.addAction(delete_action)

        # Show context menu
        self.menu.exec_(self.ui.tree.mapToGlobal(position))

    def connect_module(self, module):
        self.selected_module.connect(module)
        self.update_tree()

    def mirror_item(self):
        self.selected_module.mirror()
        self.update_tree()
        print('Mirror item')

    def disconnect_item(self):
        self.selected_module.destroy_rig()
        self.selected_module.create_joints()
        self.selected_module.rig()
        self.update_tree()

    def edit_item(self):
        self.edit_widget = EditWidget(self.selected_module, self.update_tree, parent=self)
        mouse_pos = QtGui.QCursor.pos()
        self.edit_widget.setGeometry(mouse_pos.x(), mouse_pos.y(), self.edit_widget.width(), self.edit_widget.height() )
        self.edit_widget.show()

    def rig_item(self):
        self.selected_module.create_joints()
        self.selected_module.rig()
        self.update_tree()

    def delete_item(self):
        self.selected_module.delete()
        self.update_tree()
        print('Delete item')

def showWindow():
    title = 'Modify Modules'

    delete_workspace_control(title)

    ui = ModifyWindow(title)
    ui.show(dockable=True)

if __name__ == "__main__":
    showWindow()