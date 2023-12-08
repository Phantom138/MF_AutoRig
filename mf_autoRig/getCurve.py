import math
from maya import cmds

def getCurve(curve):
    # Degree
    degree = cmds.getAttr(curve+'.degree')

    # CVS
    cvs = cmds.getAttr(curve+'.cv[:]')
    print(cvs)
    new_cvs = []
    for cv in cvs:
        new_pts = ()
        for pt in cv:
            new_pt = round(pt, 2)
            new_pts = new_pts + (new_pt,)
        new_cvs.append(new_pts)

    curveInfo = []
    curveInfo.append(degree)
    curveInfo.append(new_cvs)

    print(curveInfo)
    return curveInfo

