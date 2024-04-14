import re

import pathlib

from PySide2.QtWidgets import QStyleFactory

from mf_autoRig.UI.utils.UI_Template import UITemplate, delete_workspace_control
import pymel.core as pm
from mf_autoRig.utils.useful_functions import *

WORK_PATH = pathlib.Path(__file__).parent.resolve()

class ToolsWindow(UITemplate):
    def __init__(self, title):
        ui_path = f'{WORK_PATH}/toolsWindow.ui'

        super().__init__(widget_title=title, ui_path=ui_path)
        # self.ui.groupBox.setStyle(QStyleFactory.create("plastique"))
        # self.ui.groupBox_2.setStyle(QStyleFactory.create("plastique"))


        self.connect_widgets()

    def connect_widgets(self):
        self.ui.ctrl_scale_1.clicked.connect(lambda: self.scale_ctrl(0.25))
        self.ui.ctrl_scale_2.clicked.connect(lambda: self.scale_ctrl(0.5))
        self.ui.ctrl_scale_3.clicked.connect(lambda: self.scale_ctrl(1.25))
        self.ui.ctrl_scale_4.clicked.connect(lambda: self.scale_ctrl(1.5))

        self.ui.ctrl_replace.clicked.connect(self.replace_ctrl)
        self.ui.ctrl_mirror.clicked.connect(self.mirror_ctrl_shape)

        self.ui.create_IK.clicked.connect(self.create_ik)
        self.ui.create_FK.clicked.connect(self.create_fk)
        self.ui.create_IKFK.clicked.connect(self.create_ikfk)

    @staticmethod
    def scale_ctrl(increment):
        # TODO: use xform transform instead of set cvs, so that you can undo
        selection = pm.selected()
        for sl in selection:
            if sl.getShape().type() == 'nurbsCurve':
                cvs = sl.getCVs()
                cvs = [cv * increment for cv in cvs]
                sl.setCVs(cvs)
                sl.updateCurve()

    @staticmethod
    def create_fk():
        selection = pm.selected()
        for sl in selection:
            if not isinstance(sl, pm.nt.Joint):
                pm.error("Selection contains non-joint objects")
                return

        create_fk_ctrls(selection)

    @staticmethod
    def create_ik():
        selection = pm.selected()
        for sl in selection:
            if not isinstance(sl, pm.nt.Joint):
                pm.error("Selection contains non-joint objects")
                return

        create_ik(selection, create_new=False)

    @staticmethod
    def create_ikfk():
        selection = pm.selected()
        for sl in selection:
            if not isinstance(sl, pm.nt.Joint):
                pm.error("Selection contains non-joint objects")
                return

        joints = selection
        # FK
        fk_joints = create_fk_jnts(joints)
        fk_ctrls = create_fk_ctrls(fk_joints)

        # IK
        ik_joints, ik_ctrls, ik_ctrl_grp, ikHandle = create_ik(joints)

        ikfk_const = constraint_ikfk(joints, fk_joints, ik_joints)
        ikfk_switch(ik_ctrl_grp, fk_ctrls, ikfk_const, joints[-1])

    @staticmethod
    def replace_ctrl():
        sl = pm.selected()
        if len(sl) != 2:
            pm.error("Select two objects")

        replace_ctrl(sl[0], sl[1])

    @staticmethod
    def mirror_ctrl_shape():
        sl = pm.selected()
        if len(sl) != 2:
            pm.error("Select two objects")

        control_shape_mirror(sl[0], sl[1])


def showWindow():
    title = 'Tools Window'
    delete_workspace_control(title)

    ui = ToolsWindow(title)
    ui.show(dockable=True)