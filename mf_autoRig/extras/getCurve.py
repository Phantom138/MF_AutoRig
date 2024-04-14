from maya import cmds
from mf_autoRig.utils import general as uf

def getCurve(curve, rounding_val = 2):
    # Degree
    degree = cmds.getAttr(curve+'.degree')

    # CVS
    cvs = cmds.getAttr(curve+'.cv[:]')
    print(cvs)
    new_cvs = []
    for cv in cvs:
        new_pts = ()
        for pt in cv:
            new_pt = round(pt, rounding_val)
            new_pts = new_pts + (new_pt,)
        new_cvs.append(new_pts)

    curveInfo = [degree, new_cvs]

    print(curveInfo)
    return curveInfo

# curve = uf.CtrlGrp(name='test',shape='joint_curve')
# cube = uf.CtrlGrp(name='test2',shape='cube')
sl = cmds.ls(sl=True)
getCurve(sl[0])