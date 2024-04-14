import pymel.core as pm
import maya.cmds as cmds
from mf_autoRig import log

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




