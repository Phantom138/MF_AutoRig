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
        self.ik_fk_attr = self.switch_ctrl.IkFkSwitch

        meta_lst = switch_ctrl.message.listConnections(t="network")
        if meta_lst:
            self.meta_node = meta_lst[0]
        else:
            self.meta_node = None
            raise ValueError(f'{switch_ctrl} is not part of any module')

        if self.meta_node.moduleType.get() != 'Limb':
            raise ValueError(f'{self.meta_node} of type {self.meta_node.moduleType.get()}is not a Limb')

        # Get switch_ctrl and see ik/fk value

        self.joints = self.meta_node.joints.get()

        self.ik_joints = self.meta_node.ik_joints.get()
        self.fk_joints = self.meta_node.fk_joints.get()

        self.fk_ctrls = self.meta_node.fk_ctrls.get()
        self.ik_ctrls = self.meta_node.ik_ctrls.get()

        # Connected to foot?
        node = [a for a in self.meta_node.children.get() if a.moduleType.get() == 'IKFoot' ]
        if node:
            self.foot = node[0]
        else:
            self.foot = None

    def ik_to_fk(self):
        for jnt, fk in zip(self.ik_joints[:2], self.fk_ctrls[:2]):
            mtx = jnt.worldMatrix.get() * fk.parentInverseMatrix.get()
            pm.xform(fk, m=mtx)
            # Keyframes
            # fk.r.setKey()

        if len(self.fk_ctrls) == 3:
            # Match end with ik_ctrl
            mtx = self.ik_ctrls[0].worldMatrix.get() * self.fk_ctrls[-1].parentInverseMatrix.get()
            pm.xform(self.fk_ctrls[-1], m=mtx)

        # If connected to foot
        if self.foot is not None:
            for foot_jnt, fk_ctrl in zip(self.foot.joints.get(), self.foot.fk_ctrls.get()):
                mtx = foot_jnt.worldMatrix.get() * fk_ctrl.parentInverseMatrix.get()
                pm.xform(fk_ctrl, m=mtx)
        # test

    def fk_to_ik(self):
        # In fk mode, switch_ctrl to ik
        ik_ctrl = self.ik_ctrls[0]
        pole_ctrl = self.ik_ctrls[1]

        # Set IK
        if self.foot is not None:
            # Match rotation for ik ctrl
            match_to = self.foot.fk_ctrls.get()[0]
        else:
            match_to = self.fk_joints[-1]

        ik_mtx = match_to.worldMatrix.get() * ik_ctrl.parentInverseMatrix.get()
        pm.xform(ik_ctrl, m=ik_mtx)

        # Set pole
        pole_parent_t = pole_ctrl.getParent(1).t.get()

        target_t = create_pole_vector(self.fk_joints)
        res_t = target_t - pole_parent_t
        pole_ctrl.t.set(res_t)



        # ikfk_attr.set(0)
        #
        # # Set keyframes
        # pole_ctrl.t.setKey()
        # ik_ctrl.t.setKey()
        # ik_ctrl.r.setKey()
        pass

    def switch(self):
        if self.ik_fk_attr.get() == 0:
            # In ik mode
            self.ik_to_fk()
        else:
            # in fk mode
            self.fk_to_ik()

def main():
    if pm.selected():
        node = pm.selected()[0]
    else:
        pm.warning("Nothing is selected")

    with UndoStack(f"Switching {node} IKFK"):
        sw = IkFkSwitch(node)
        sw.switch()