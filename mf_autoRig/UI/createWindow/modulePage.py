import pathlib
from functools import partial

try:
    from PySide2 import QtWidgets, QtGui, QtCore
except ImportError:
    from PySide6 import QtWidgets, QtGui, QtCore

from mf_autoRig.UI.utils.loadUI import loadUi
from mf_autoRig.utils.undo import UndoStack
import pymel.core as pm
from pymel.core import dt


class CustomLineEdit(QtWidgets.QLineEdit):
    def __init__(self, parent=None):
        QtWidgets.QLineEdit.__init__(self, parent)
        self.setMaximumWidth(50)

class Vector3Input(QtWidgets.QWidget):
    vectorChanged = QtCore.Signal()
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setSpacing(1)

        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.x_axis = CustomLineEdit()
        self.y_axis = CustomLineEdit()
        self.z_axis = CustomLineEdit()

        for input_field in (self.x_axis, self.y_axis, self.z_axis):
            input_field.setValidator(QtGui.QDoubleValidator())
            input_field.editingFinished.connect(self.emit_vector_changed)
            self.main_layout.addWidget(input_field)

        self.main_layout.addStretch()
        self.setLayout(self.main_layout)

    def setValue(self, value):
        if isinstance(value, dt.Vector):
            x,y,z = value.get()
        elif isinstance(value, (list, tuple)):
            x,y,z = value
        else:
            x,y,z = (0,0,0)
            raise ValueError(f"Value {value} not recognized")

        self.x_axis.setText(str(x))
        self.y_axis.setText(str(y))
        self.z_axis.setText(str(z))

    def emit_vector_changed(self):
        self.vectorChanged.emit()

    def value(self):
        return dt.Vector([float(self.x_axis.text()), float(self.y_axis.text()), float(self.z_axis.text())])

class FormFromDict:
    def __init__(self, module_dict, module=None):
        self.module = module
        self.form_layout = QtWidgets.QFormLayout()

        self.form_layout.setContentsMargins(0, 0, 0, 0)

        for key, value in module_dict.items():
            self.add_field(key, value)

    def add_field(self, key, data):
        if key == 'moduleType':
            return

        # Get type
        if 'attributeType' in data:
            field_type = data['attributeType']
        elif 'type' in data:
            field_type = data['type']
        else:
            raise ValueError(f"Attribute {key} does not have an attributeType")

        # Use nice_name if existent
        if 'niceName' in data:
            label = data['niceName']
        else:
            label = key

        # Set value if existent
        if 'value' in data:
            field_value = data['value']
        else:
            field_value = None

        # Value is a dict of type: label: {'attributeType': 'type'}
        if field_type in ['int','float','long']:
            field = QtWidgets.QSpinBox()
            policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            field.setMaximumWidth(50)
            field.setMinimum(-1)
            field.setSizePolicy(policy)

            if field_value is not None:
                field.setValue(field_value)
            # print(field.value)
            print(key, field.value)
            field.editingFinished.connect(lambda: self.update_class(key, field.value))

        elif field_type == 'bool':
            field = QtWidgets.QCheckBox()
            if field_value is not None:
                field.setChecked(field_value)

            field.stateChanged.connect(lambda: self.update_class(key, field.isChecked))

        elif field_type == 'string':
            field = QtWidgets.QLineEdit()
            if field_value is not None:
                field.setText(field_value)

            field.editingFinished.connect(lambda: self.update_class(key, field.text))

        elif field_type == 'double3':
            field = Vector3Input()
            if field_value is not None:
                field.setValue(field_value)

            field.vectorChanged.connect(lambda: self.update_class(key, field.value))
        else:
            raise ValueError(f"Field type {field_type} not recognized")



        self.form_layout.addRow(label, field)

    def update_class(self, attr, value_function):

        if self.module is None:
            return
        value = value_function()
        setattr(self.module, attr, value)
        self.module.metaNode.attr(attr).set(value)

    def get_data(self):
        data = {}
        for i in range(self.form_layout.rowCount()):
            label = self.form_layout.itemAt(i, QtWidgets.QFormLayout.LabelRole).widget()
            field = self.form_layout.itemAt(i, QtWidgets.QFormLayout.FieldRole).widget()

            if isinstance(field, QtWidgets.QLineEdit):
                data[label.text()] = field.text()
            elif isinstance(field, QtWidgets.QSpinBox):
                data[label.text()] = field.value()
            elif isinstance(field, Vector3Input):
                data[label.text()] = field.value()
            elif isinstance(field, QtWidgets.QCheckBox):
                data[label.text()] = field.isChecked()
            else:
                raise ValueError(f"Field type {type(field)} not recognized")

        return data

def value_dict_from_class(instance, key):
    data = {}
    for attr in instance.meta_args[key]:
        attr_dict = {}
        meta_attr = instance.metaNode.attr(attr)
        attr_dict['niceName'] = pm.attributeName(meta_attr, n=True)
        attr_dict['type'] = meta_attr.type()
        attr_dict['value'] = meta_attr.get()
        data[attr] = attr_dict

    print(data)
    return data

class CreatePage(QtWidgets.QWidget):
    def __init__(self, base_module, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.module = base_module

        self.main_layout = QtWidgets.QVBoxLayout()
        # self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.form = FormFromDict(self.module.meta_args['creation_attrs'])

        self.create_button = QtWidgets.QPushButton("create")
        self.create_button.clicked.connect(self.create_module)

        self.main_layout.addLayout(self.form.form_layout)
        self.main_layout.addWidget(self.create_button)

        self.setLayout(self.main_layout)

    def create_module(self):
        args = self.form.get_data()
        print(args)
        with UndoStack(f"Create Module {args['name']}"):
            mdl = self.module(**args)
            mdl.create_guides()

class ConfigPage(QtWidgets.QWidget):
    def __init__(self, base_module, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.module = base_module

        self.main_layout = QtWidgets.QVBoxLayout()
        # self.main_layout.setContentsMargins(0, 0, 0, 0)
        attr_dict = value_dict_from_class(self.module, 'config_attrs')
        self.form = FormFromDict(attr_dict, module=self.module)

        self.create_button = QtWidgets.QPushButton("save")
        self.create_button.clicked.connect(self.save_config)

        self.label = QtWidgets.QLabel(f"Config for module: {self.module.name}")

        self.main_layout.addWidget(self.label)
        self.main_layout.addLayout(self.form.form_layout)
        self.main_layout.addWidget(self.create_button)

        self.setLayout(self.main_layout)

    def save_config(self):
        config = self.form.get_data()
        # print(args)
        for attr, value in config.items():
            setattr(self.module, attr, value)
            self.module.save_metadata()



