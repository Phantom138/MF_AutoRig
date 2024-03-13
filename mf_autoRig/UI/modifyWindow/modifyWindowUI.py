from PySide2 import QtGui
from PySide2.QtGui import QFont
from PySide2.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QMenu, QAction
from PySide2.QtCore import Qt

from mf_autoRig.UI.modifyWindow.editWidget import EditWidget
from mf_autoRig.UI.utils.UI_Template import delete_workspace_control, UITemplate
import mf_autoRig.modules.createModule as crMod


import pathlib
WORK_PATH = pathlib.Path(__file__).parent.resolve()

class ModifyWindow(UITemplate):
    def __init__(self, title):
        ui_path = f'{WORK_PATH}\modifyWindow.ui'
        super().__init__(widget_title=title, ui_path=ui_path)

        # Populate list with sample data
        for i in range(30):
            self.ui.list_modules.addItem(f"Item {i}")

        font = QFont()
        font.setPointSize(7)
        self.ui.list_modules.setFont(font)
        self.ui.list_modules.setSpacing(2)

        # Enable context menu
        self.ui.list_modules.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.list_modules.customContextMenuRequested.connect(self.context_menu)

        self.ui.btn_updateLists.clicked.connect(self.updateList)
        self.updateList()

    def updateList(self):
        self.ui.list_modules.clear()

        self.modules = crMod.get_all_modules()
        if self.modules is not None:
            for module in self.modules:
                # Get base name for adding to item
                name = module.Name.get()
                moduleType = module.moduleType.get()

                # Add item to list
                item = f'{name} <{moduleType}>'
                self.ui.list_modules.addItem(item)


    def context_menu(self, position):
        # Create context menu
        menu = QMenu()

        # Create actions
        mirror_action = QAction('Mirror', self)
        edit_action = QAction('Edit', self)
        delete_action = QAction('Delete', self)

        # Connect actions to functions
        mirror_action.triggered.connect(self.mirror_item)
        edit_action.triggered.connect(self.edit_item)
        delete_action.triggered.connect(self.delete_item)

        # Add actions to menu
        menu.addAction(mirror_action)
        menu.addAction(edit_action)
        menu.addAction(delete_action)

        # Show context menu
        menu.exec_(self.ui.list_modules.mapToGlobal(position))

    def mirror_item(self):
        print('Mirror item')

    def edit_item(self):
        row = self.ui.list_modules.currentRow()

        self.edit_widget = EditWidget(self.modules[row], parent=self)
        mouse_pos = QtGui.QCursor.pos()
        self.edit_widget.setGeometry(mouse_pos.x(), mouse_pos.y(), self.edit_widget.width(), self.edit_widget.height() )
        self.edit_widget.show()

    def delete_item(self):
        print('Delete item')

def showWindow():
    title = 'Modify Modules'

    delete_workspace_control(title)

    ui = ModifyWindow(title)
    ui.show(dockable=True)

if __name__ == "__main__":
    showWindow()