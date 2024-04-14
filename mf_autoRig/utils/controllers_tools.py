import pymel.core as pm
import maya.cmds as cmds
import mf_autoRig.utils.defaults as df
from mf_autoRig import log


class CtrlGrp:
    def __init__(self, name, shape, scale=df.CTRL_SCALE, axis=(0, 1, 0)):
        # Create empty grp
        self.grp = pm.createNode('transform', name=name + df.ctrl_sff + df.grp_sff)

        if shape == 'circle':
            self.ctrl = pm.circle(nr=axis, c=(0, 0, 0), radius=scale, name=name + df.ctrl_sff,
                                  constructionHistory=False)[0]
        elif shape == 'arc':
            self.ctrl = pm.circle(nr=axis, c=(0, 0, 0), radius=scale, sw=180, d=3, ut=0, tol=0.01, s=8, ch=0,
                                  name=name + df.ctrl_sff)[0]
        else:
            points = [(x * scale, y * scale, z * scale) for x, y, z in df.CTRL_SHAPES[shape][1]]
            self.ctrl = pm.curve(degree=df.CTRL_SHAPES[shape][0],
                                 point=points,
                                 name=name + df.ctrl_sff)
        # Parent ctrl and grp
        pm.parent(self.ctrl, self.grp)


def save_curve_info(curves):
    curve_info ={}
    for curve in curves:
        crv_name = curve.name()
        if crv_name.endswith('_pole_ctrl'):
            continue

        deg = cmds.getAttr(f'{crv_name}.degree')
        form = cmds.getAttr(f'{crv_name}.form')
        cvs = cmds.getAttr(f'{crv_name}.cv[*]')

        curve_info[crv_name] = {
            'degree': deg,
            'form': form,
            'cvs': cvs
        }

    return curve_info

def apply_curve_info(curves, curve_info):
    for curve in curves:
        crv_name = curve.name()
        try:
            curve_info[crv_name]
        except KeyError:
            log.warning(f'{curve} not found in curve_info')
            continue

        cvs = curve_info[crv_name]['cvs']
        deg = curve_info[crv_name]['degree']
        form = curve_info[crv_name]['form']
        log.debug(f"Applying curve info for {crv_name}")
        pm.curve(curve, r=True, point=cvs, degree=deg, per=False)

        if form == 2:
            pm.closeCurve(curve, preserveShape=False, replaceOriginal=True)

def control_shape_mirror(src, dst):
    targetCvList = pm.ls(f'{src.name()}.cv[:]', flatten=True)
    destCvList = pm.ls(f'{dst.name()}.cv[:]', flatten=True)

    if len(targetCvList) != len(destCvList):
        pm.error('ctrls not matching')

    for tar, des in zip(targetCvList, destCvList):  # zip target and destination list to match data
        pos = pm.xform(tar, query=True, translation=True, worldSpace=True)
        pos = [pos[0] * -1.0, pos[1], pos[2]]  # flip x value of position
        pm.xform(des, translation=pos, worldSpace=True)

def replace_ctrl(src, dst):
    src_shape = src.getShape()
    dst_shape = dst.getShape()

    if src_shape.type() != 'nurbsCurve' or dst_shape.type() != 'nurbsCurve':
        pm.error("Non-curve objects")
        return

    import mf_autoRig.utils.controllers_tools as curve_info

    deg = cmds.getAttr(f'{src}.degree')
    form = cmds.getAttr(f'{src}.form')
    cvs = cmds.getAttr(f'{src}.cv[*]')


    pm.curve(dst, r=True, point=cvs, degree=deg, per=False)

    if form == 2:
        pm.closeCurve(dst, preserveShape=False, replaceOriginal=True)



