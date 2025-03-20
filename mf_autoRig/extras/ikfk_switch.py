import pymel.core as pm


class UndoStack(object):
    def __init__(self, name="actionName"):
        self.name = name

    def __enter__(self):
        pm.undoInfo(openChunk=True, chunkName=self.name, infinity=True)

    def __exit__(self, *exc_info):
        pm.undoInfo(closeChunk=True)



def create_pole_vector(joints):
    A = pm.dt.Vector(pm.xform(joints[0], worldSpace=True, rotatePivot=True, q=True))
    B = pm.dt.Vector(pm.xform(joints[1], worldSpace=True, rotatePivot=True, q=True))
    C = pm.dt.Vector(pm.xform(joints[2], worldSpace=True, rotatePivot=True, q=True))
    AC = C - A
    AB = B - A

    # T = AB projected onto AC
    AC_n = AC.normal()
    dotP = AB * AC_n
    T = AC_n * dotP

    # Build TB vector
    TB = AB - T
    # Create pole length
    TB = TB.normal()
    pole_len = AB.length() * 1.3
    # Create pole position
    pole = TB * pole_len + T + A

    return pole


def switch_ik_fk(switch_ctrl):
    meta_lst = switch_ctrl.message.listConnections(t="network")

    if meta_lst:
        meta_node = meta_lst[0]
    else:
        raise ValueError(f'{switch_ctrl} is not part of any module')

    if meta_node.moduleType.get() != 'Limb':
        raise ValueError(f'{meta_node} of type {meta_node.moduleType.get()}is not a Limb')

    # Get switch_ctrl and see ik/fk value
    ikfk_attr = switch_ctrl.IkFkSwitch

    joints = meta_node.joints.get()
    fk_ctrls = meta_node.fk_ctrls.get()
    ik_ctrls = meta_node.ik_ctrls.get()

    # Get hand if it exists
    hand = None
    for child in meta_node.children.get():
        if child.moduleType.get() == 'Hand':
            hand = child.hand_ctrl.get()
            continue

    if ikfk_attr.get() == 0:
        # Set hand
        if hand != None:
            pm.select(cl=True)
            tmp = pm.createNode("transform")
            pm.matchTransform(tmp, hand)

        # In ik mode, switch_ctrl to fk
        for jnt, fk in zip(joints[:2], fk_ctrls):
            mtx = jnt.worldMatrix.get() * fk.parentInverseMatrix.get()
            pm.xform(fk, m=mtx)
            # Keyframes
            fk.r.setKey()

        ikfk_attr.set(1)
        if hand != None:
            pm.matchTransform(hand, tmp, rot=True)
            pm.delete(tmp)

        # Keyframe
        hand.r.setKey()

    else:
        # In fk mode, switch_ctrl to ik
        ik_ctrl = ik_ctrls[0]
        ik_mtx = joints[-1].worldMatrix.get() * ik_ctrl.parentInverseMatrix.get()

        # Set IK
        pm.xform(ik_ctrl, m=ik_mtx)

        # Set pole
        pole_ctrl = ik_ctrls[1]
        pole_parent_t = pole_ctrl.getParent(1).t.get()

        target_t = create_pole_vector(joints)
        res_t = target_t - pole_parent_t
        pole_ctrl.t.set(res_t)

        ikfk_attr.set(0)

        # Set keyframes
        pole_ctrl.t.setKey()
        ik_ctrl.t.setKey()
        ik_ctrl.r.setKey()

    # Key switch
    ikfk_attr.setKey(itt="auto", ott="step")

    # Set previous keyframe to step
    time = pm.currentTime(query=True)
    index = pm.keyframe(ikfk_attr, time=(time, time), iv=True, q=True)

    if index:
        index = index[0]
        pm.keyTangent(ikfk_attr, index=(index - 1, index - 1), itt="auto", ott="step")

class IkFkSwitch:
    def __init__(self, switch_ctrl):
        self.switch_ctrl = switch_ctrl
        self.ik_fk_attr = switch_ctrl.IkFkSwitch

        self.joints = switch_ctrl.joints.get()

        self.ik_joints = switch_ctrl.ik_joints.get()
        self.fk_joints = switch_ctrl.fk_joints.get()

        self.fk_ctrls = switch_ctrl.fk_ctrls.get()
        self.ik_ctrls = switch_ctrl.ik_ctrls.get()

        self.has_foot = switch_ctrl.has_foot.get()
        if self.has_foot:
            self.foot_joints = switch_ctrl.foot_joints.get()
            self.foot_fk_ctrls = switch_ctrl.foot_fk_ctrls.get()
            self.foot_offset = switch_ctrl.foot_offset.get()
        else:
            self.foot_joints = []
            self.fk_ctrls = []

    def ik_to_fk(self):
        for jnt, fk in zip(self.ik_joints[:2], self.fk_ctrls[:2]):
            mtx = jnt.worldMatrix.get() * fk.parentInverseMatrix.get()
            pm.xform(fk, m=mtx)
            
        if len(self.fk_ctrls) == 3:
            # Match end with ik_ctrl
            mtx = self.ik_ctrls[0].worldMatrix.get() * self.fk_ctrls[-1].parentInverseMatrix.get()
            pm.xform(self.fk_ctrls[-1], m=mtx)

        # If connected to foot
        if self.has_foot:
            for foot_jnt, fk_ctrl in zip(self.foot_joints, self.foot_fk_ctrls):
                mtx = foot_jnt.worldMatrix.get() * fk_ctrl.parentInverseMatrix.get()
                pm.xform(fk_ctrl, m=mtx)

    def fk_to_ik(self):
        # In fk mode, switch_ctrl to ik
        ik_ctrl = self.ik_ctrls[0]
        pole_ctrl = self.ik_ctrls[1]

        # Set IK
        if self.has_foot:
            tmp_loc = pm.spaceLocator()
            tmp_loc.r.set(self.foot_offset)
            
            res_mtx = tmp_loc.worldMatrix.get() * self.foot_fk_ctrls[0].worldMatrix.get()
            
            pm.xform(tmp_loc, m=res_mtx) # This is only for rotation
            ik_ctrl.r.set(tmp_loc.r.get())
            pm.delete(tmp_loc)

            pm.matchTransform(ik_ctrl, self.foot_fk_ctrls[0], position=True)
            
        else:
            ik_mtx = self.fk_joints[-1].worldMatrix.get() * ik_ctrl.parentInverseMatrix.get()
            pm.xform(ik_ctrl, m=ik_mtx)

        # Set pole
        target_t = create_pole_vector(self.fk_joints)
        tmp_loc = pm.spaceLocator()
        tmp_loc.t.set(target_t)

        pm.matchTransform(pole_ctrl, tmp_loc)
        pm.delete(tmp_loc)


    def switch(self, key=False):
        if self.ik_fk_attr.get() == 0:
            # In ik mode
            self.ik_to_fk()
            if key:
                self.fk_setKey()
        else:
            # in fk mode
            self.fk_to_ik()
            if key:
                self.ik_setKey()
    
    def ik_setKey(self):
        self.ik_ctrls[0].t.setKey()
        self.ik_ctrls[0].r.setKey()
        self.ik_ctrls[1].t.setKey() # pole vector

    def fk_setKey(self):
        for fk in self.fk_ctrls:
            fk.r.setKey()

        if self.has_foot:
            for ctrl in self.foot_fk_ctrls:
                ctrl.r.setKey()
    
    def select_ik(self):
        pm.select(self.ik_ctrls)

    def select_fk(self):
        pm.select(self.fk_ctrls)
        if self.has_foot:
            pm.select(self.foot_fk_ctrls,add=True)

    def bake_framerange(self):
        # Check that the switch value doesn't change in the fram range
        start = int(pm.playbackOptions(q=True, min=True))
        end = int(pm.playbackOptions(q=True, max=True))

        start_switch_value = self.ik_fk_attr.get(time=start)
        for i in range(start, end+1):
            val = self.ik_fk_attr.get(time=i)
            if val != start_switch_value:
                pm.error(f"Frame range has different switch values at frame {i}")
        
        for i in range(start, end+1):
            pm.currentTime(i, e=True)
            self.switch(key=True)

    def flip_switch_value(self):
        if self.ik_fk_attr.get() == 0:
            self.ik_fk_attr.set(1)
        else:
            self.ik_fk_attr.set(0)

# -------- Functions for creating switch ---------- #
def create_switch(switch_ctrl):
    meta_lst = switch_ctrl.message.listConnections(t="network")
    if meta_lst:
        meta_node = meta_lst[0]
    else:
        meta_node = None
        raise ValueError(f'{switch_ctrl} is not part of any module')

    if meta_node.moduleType.get() != 'Limb':
        raise ValueError(f'{meta_node} of type {meta_node.moduleType.get()}is not a Limb')

    # Get switch_ctrl and see ik/fk value
    data = {}
    data["joints"] = meta_node.joints.get()

    data["ik_joints"] = meta_node.ik_joints.get()
    data["fk_joints"] = meta_node.fk_joints.get()

    data["fk_ctrls"] = meta_node.fk_ctrls.get()
    data["ik_ctrls"] = meta_node.ik_ctrls.get()

    # Connected to foot?
    node = [a for a in meta_node.children.get() if a.moduleType.get() == 'IKFoot' ]

    data["has_foot"] = False
    data["foot_joints"] = []
    data["foot_fk_ctrls"] = []
    data["foot_offset"] = []

    if node:
        data["has_foot"] = True
        data["foot_fk_ctrls"] = node[0].fk_ctrls.get()
        data["foot_joints"] = node[0].joints.get()
        # calculate offset
        fk_parent_inv_mtx = data["foot_fk_ctrls"][0].parentInverseMatrix.get()
        ik_ctrl_parent_mtx = data["ik_ctrls"][0].parentMatrix.get()

        offset_mtx = fk_parent_inv_mtx * ik_ctrl_parent_mtx 
        tmp = pm.spaceLocator("temp_loc")
        pm.xform(tmp, m=offset_mtx)
        data["foot_offset"] = tmp.r.get()
        pm.delete(tmp)
        print(data["foot_offset"])
    _clear_node(switch_ctrl, data)
    _save_dict_to_node(switch_ctrl, data)

def _save_dict_to_node(node, data: dict):
    for key, item in data.items():
        if isinstance(item, list):
            if isinstance(item[0], pm.PyNode):
                node.addAttr(key, attributeType='message', m=True)

        elif isinstance(item, bool):
            node.addAttr(key, attributeType='bool')
        elif isinstance(item, pm.dt.Vector):
            node.addAttr(key, attributeType='double3')
            for axis in ['X', 'Y', 'Z']:
                node.addAttr(key + axis, attributeType= 'double', p=key)
        else:
            pm.error(f"Cannot writ {item}")
        _add(item, node.attr(key))

def _clear_node(node, data:dict):
    for key in data:
        try:
            node.deleteAttr(key)
        except:
            pass

def _add(nodes, dst):
    if not nodes:
        return

    def connect(src, dest):
        # If it's a pynode connect message attr
        if isinstance(src, pm.PyNode):
            if not pm.isConnected(src.message, dest):
                src.message.connect(dest)

        # If it's an int just set the value
        elif isinstance(src, (float, int, str)):
            dest.set(src)

        elif isinstance(src, bool):
            dest.set(src)

        # Set vector type variables
        elif isinstance(src, pm.dt.Vector):
            dest.set(src)

    # If it's a list of nodes connect each one to the destination
    if isinstance(nodes, list):
        for i, node in enumerate(nodes):
            connect(node, dst[i])
    else:
        connect(nodes, dst)
# ------------------------------------------------ #


# ---------------- UI Logic ---------------------- #
def switch_cmd(sw: IkFkSwitch):
    with UndoStack(f"Switching IKFK"):
        sw.switch()
        sw.flip_switch_value()

def ik_setKey_cmd(sw: IkFkSwitch):
    with UndoStack(f"Set IK"):
        sw.ik_setKey()
        sw.select_ik()

def fk_setKey_cmd(sw: IkFkSwitch):
    with UndoStack(f"Set FK"):
        sw.fk_setKey()
        sw.select_fk()

def bake_framerange_cmd(sw: IkFkSwitch):
    with UndoStack(f"Bake framerange"):
        sw.bake_framerange()
        sw.flip_switch_value()

def animUI():
    if pm.selected():
        node = pm.selected()[0]
    else:
        pm.warning("Nothing is selected")
        return
    
    sw = IkFkSwitch(node)
    window_name = node.name()

    win = pm.window(title=window_name, widthHeight=(200, 100))

    pm.columnLayout(adjustableColumn=True)

    pm.button(label="Switch current frame", command=lambda _: switch_cmd(sw), bgc=(0.3, 0.6, 1.0))
    pm.button(label="Key IK ctrls", command=lambda _: ik_setKey_cmd(sw))
    pm.button(label="Key FK ctrls", command=lambda _: fk_setKey_cmd(sw))
    pm.button(label="Mocap - Bake Framerange", command=lambda _: bake_framerange_cmd(sw), bgc=(1.0, 1.0, 0.3))

    pm.showWindow(win)
