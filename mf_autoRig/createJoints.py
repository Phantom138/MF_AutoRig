import pymel.core as pm

default_pos = {
    ## template: start pos, end pos, rotation
    'arm': [[19.18483528988024, 142.85023108538144, -0.8201141132490157], [42.781092559775665, 95.32996316043445, 3.310636503344389]],
    'leg': [[9.673175630202605, 92.28047381987574, 2.104993454402031], [15.410806600295157, 10.46731563884532, -4.704663039138234]],
    'hand': [[0, 0, 0], [0, -15, 0]],
    'torso': [[0.0971650962367665, 97.15586313733928, 0.0], [0.0, 128.61501168394008, 0.0]]
}

def lock_and_hide(obj, translate=True, rotation=True, scale=True):
    if translate:
        for trs in ['tx', 'ty', 'tz']:
            obj.attr(trs).lock()
            obj.attr(trs).setKeyable(0)
    if rotation:
        for trs in ['rx', 'ry', 'rz']:
            obj.attr(trs).lock()
            obj.attr(trs).setKeyable(0)
    if scale:
        for trs in ['sx', 'sy', 'sz']:
            obj.attr(trs).lock()
            obj.attr(trs).setKeyable(0)


def create_joint_chain(jnt_number, name, start_pos, end_pos, rot=[0,0,0],):
    joints = []
    # Create plane
    plane = pm.polyPlane(name=f'tmp_{name}_Plane', w=2, h=26, sh=1, sw=1)[0]
    plane.v.set(0)

    # Create joints and move them in position
    startJnt = pm.createNode('joint', name=f'startJoint')
    endJnt = pm.createNode('joint', name=f'endJoint')
    pm.move(startJnt, (-1, 0, 0))
    pm.move(endJnt, (1, 0, 0))

    pm.orientConstraint(startJnt, endJnt)

    lock_and_hide(startJnt, translate=False, rotation=False)
    lock_and_hide(endJnt, translate=False)


    joints.append(startJnt)

    # Skin plane to jnts
    influencers = [startJnt, endJnt]
    skn_cluster = pm.skinCluster(influencers, plane, name=f'tmp_{name}_skinCluster', toSelectedBones=True, bindMethod=0, skinMethod=0, normalizeWeights=1)
    pm.skinPercent(skn_cluster, plane.vtx[0], transformValue=[(startJnt, 1), (endJnt, 0)])
    pm.skinPercent(skn_cluster, plane.vtx[2], transformValue=[(startJnt, 1), (endJnt, 0)])

    pm.skinPercent(skn_cluster, plane.vtx[1], transformValue=[(startJnt, 0), (endJnt, 1)])
    pm.skinPercent(skn_cluster, plane.vtx[3], transformValue=[(startJnt, 0), (endJnt, 1)])

    planeShape = pm.listRelatives(plane)[0]
    planeOrig = pm.listRelatives(plane)[1]

    # Create middle joints and connect to uv pin
    for i in range(1, jnt_number-1):
        # Create uv pin and connect to plane
        UVpin = pm.createNode('uvPin', name=f'joint{i}_uvPin')
        planeShape.worldMesh.connect(UVpin.deformedGeometry)
        planeOrig.outMesh.connect(UVpin.originalGeometry)

        print(pm.listConnections(UVpin))

        # Create jnt and coords attributes
        jnt = pm.createNode('joint', name=f'joint{i}')
        lock_and_hide(jnt)

        joints.append(jnt)
        coords = ['uCoord', 'vCoord']
        default_value = 100/(jnt_number-1)*i
        print(default_value)
        for coord in coords:
            rv = pm.createNode('remapValue', name=f'joint{i}_{coord}_RV')

            # Set min and max
            rv.inputMax.set(100)
            rv.outputMax.set(1)

            # Connect to coords
            if coord == 'uCoord':
                pm.addAttr(jnt, ln=coord, at='float', max=100, min=0, dv=default_value, k=True)
                jnt.uCoord.connect(rv.inputValue)
                rv.outValue.connect(UVpin.coordinate[0].coordinateU)
            elif coord == 'vCoord':
                pm.addAttr(jnt, ln=coord, at='float', max=100, min=0, dv=50, k=True)
                jnt.vCoord.connect(rv.inputValue)
                rv.outValue.connect(UVpin.coordinate[0].coordinateV)

        # Connect matrix from uv pin to jnt
        pick_mtx = pm.createNode('pickMatrix')
        pick_mtx.useScale.set(0)
        pick_mtx.useShear.set(0)

        UVpin.outputMatrix[0].connect(pick_mtx.inputMatrix)
        pick_mtx.outputMatrix.connect(jnt.offsetParentMatrix)

    startJnt.translate.set(start_pos)
    startJnt.rx.set(rot[0])
    startJnt.ry.set(rot[1])
    startJnt.rx.set(rot[2])
    endJnt.translate.set(end_pos)


    joints.append(endJnt)
    return joints

def arm():
    joints = create_joint_chain(3, 'arm', default_pos['arm'][0], default_pos['arm'][1])

def leg():
    joints = create_joint_chain(3, 'leg', default_pos['leg'][0], default_pos['leg'][1])

def hand(num):
    grps = []
    for i in range(num):
        increment = 2 * i
        pos = [[x, y, z-increment] for x,y,z in default_pos['hand']]
        if i==0:
            finger_jnts = create_joint_chain(4, 'hand', pos[0], pos[1], rot=[0, -90, 0])
        else:
            finger_jnts = create_joint_chain(5, 'hand',pos[0], pos[1], rot=[0,-90,0])

        grp = pm.createNode('transform', name=f'finger{i}')
        pm.matchTransform(grp, finger_jnts[0])
        pm.parent(finger_jnts[0], finger_jnts[-1], grp)

        grps.append(grp)
        #pm.xform(grp, objectSpace=True, pivots=[0, 0, 0])
    hand_grp = pm.group(grps)
    hand_grp.translate.set([44.27851160849259, 91.96554955207914, 0.41670216892921275])

def torso():
    create_joint_chain(3, 'torso', default_pos['torso'][0], default_pos['torso'][1])


torso()
