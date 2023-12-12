import pymel.core as pm

def create_joint_chain(jnt_number):
    plane = pm.polyPlane(name='testPlane', w=2, h=26, sh=1, sw=1)[0]
    startJnt = pm.createNode('joint', name=f'joint{1}')
    endJnt = pm.createNode('joint', name=f'joint{jnt_number}')
    pm.move(startJnt, (-1, 0, 0))
    pm.move(endJnt, (1, 0, 0))

    # Skin plane to jnts
    influencers = [startJnt, endJnt]
    skn_cluster = pm.skinCluster(influencers, plane, name='plane_skinCluster_tmp', toSelectedBones=True, bindMethod=0, skinMethod=0, normalizeWeights=1)
    pm.skinPercent(skn_cluster, plane.vtx[0], transformValue=[(startJnt, 1), (endJnt, 0)])
    pm.skinPercent(skn_cluster, plane.vtx[2], transformValue=[(startJnt, 1), (endJnt, 0)])

    pm.skinPercent(skn_cluster, plane.vtx[1], transformValue=[(startJnt, 0), (endJnt, 1)])
    pm.skinPercent(skn_cluster, plane.vtx[3], transformValue=[(startJnt, 0), (endJnt, 1)])

    for i in range(jnt_number):
        print(i)
        #jnt = pm.createNode('joint', name=f'joint{i}')
        #pm.move(jnt, (1, 0, 0))

create_joint_chain(3)