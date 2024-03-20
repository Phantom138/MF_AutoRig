import pymel.core as pm
from mf_autoRig.lib.useful_functions import CtrlGrp


# Small script to create clusters for every point in a curve and then parent controllers to them
def rig_curve(curve):
    cvs_num = curve.numCVs()

    print("CV number:", cvs_num)
    clusters = []
    for i in range(cvs_num):
        cluster = pm.cluster(curve.cv[i], name=f'{curve.name()}_{i+1:02}_cluster')[1]
        clusters.append(cluster)

    ctrls = []
    for i, cluster in enumerate(clusters):
        ctrl = CtrlGrp(name=f"{curve.name()}_{i+1:02}", shape='circle', scale=0.1)
        pm.matchTransform(ctrl.grp, cluster)
        pm.pointConstraint(ctrl.ctrl, cluster)
        ctrls.append(ctrl.grp)

    # Clean-up
    pm.group(clusters, name=f'{curve.name()}_Clusters_Grp')
    pm.group(ctrls, name=f'{curve.name()}_Control_Grp')


sl = pm.selected()[0]
rig_curve(sl)
