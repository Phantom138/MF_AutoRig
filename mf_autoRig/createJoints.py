import pymel.core as pm
from PySide2.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout


default_pos = {
    # template: start pos, end pos
    'arm': [[19.18, 142.85, -0.82], [42.78, 95.32, 3.31]],
    'leg': [[9.67, 92.28, 2.10], [15.41, 10.46, -4.70]],
    'hand': [[0, 0, 0], [0, -15, 0]],
    'torso': [[0.09, 97.15, 0.0], [0.0, 128.61, 0.0]],
    'foot_ball': [16.84, 3.38, 4.09],
    'foot_end': [18.37, 1.2, 16.12],
    'hand_start': [43.59, 92.72, 7.61],
    'clavicle': [2.65, 143.59, 0.0]
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


def guides_grp():
    try:
        guides_grp = pm.PyNode('rig_guides_grp')
    except pm.MayaNodeError:
        guides_grp = pm.createNode('transform', name='rig_guides_grp')

    return guides_grp


def create_joint_chain(jnt_number, name, start_pos, end_pos, rot=None):
    if rot is None:
        rot = [0, 0, 0]

    # Create driven grp if not existent
    try:
        driven_grp = pm.PyNode('DONOTTOUCH_driven_guides_grp')
    except pm.MayaNodeError:
        driven_grp = pm.createNode('transform', name='DONOTTOUCH_driven_guides_grp')

    # Create plane
    plane = pm.polyPlane(name=f'tmp_{name}_Plane', w=2, h=26, sh=1, sw=1)[0]
    plane.v.set(0)
    pm.parent(plane, driven_grp)

    joints = []
    # Create joints and move them in position
    startJnt = pm.createNode('joint', name=f'{name}_start')
    endJnt = pm.createNode('joint', name=f'{name}_end')
    pm.move(startJnt, (-1, 0, 0))
    pm.move(endJnt, (1, 0, 0))

    pm.orientConstraint(startJnt, endJnt)

    # Group start and end jnt
    grp = pm.createNode('transform', name=f'{name}_grp')
    pm.matchTransform(grp, startJnt)
    pm.parent(startJnt, endJnt, grp)

    # Parent to rig grp
    pm.parent(grp, guides_grp())

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
        UVpin = pm.createNode('uvPin', name=f'{name}{i}_uvPin')
        planeShape.worldMesh.connect(UVpin.deformedGeometry)
        planeOrig.outMesh.connect(UVpin.originalGeometry)

        print(pm.listConnections(UVpin))

        # Create jnt and coords attributes
        jnt = pm.createNode('joint', name=f'{name}{i}')
        lock_and_hide(jnt)
        pm.parent(jnt, driven_grp)

        joints.append(jnt)
        default_value = 100/(jnt_number-1)*i

        for coord in ['uCoord', 'vCoord']:
            rv = pm.createNode('remapValue', name=f'{name}{i}_{coord}_RV')

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


def old(num):
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

def torso(num):
    start = 100
    end = 130
    step = (end-start)/(num-1)

    joints = []
    for i in range(num):
        jnt = pm.createNode('joint', name=f'torso{i}')
        joints.append(jnt)

        increment = step * i
        pm.move(jnt, (0, start + increment, 0))

    # Group joints
    grp = pm.createNode('transform', name='torso_grp')
    pm.matchTransform(grp, joints[0])
    pm.parent(joints, grp)
    pm.parent(grp, guides_grp())

    return joints

def foot():
    ball = pm.createNode('joint', name='foot')
    ball.translate.set(default_pos['foot_ball'])
    end = pm.createNode('joint', name='footEnd')
    end.translate.set(default_pos['foot_end'])

    pm.parent(ball, end, guides_grp())

def hand():
    finger_grps = []
    fingers_jnts = []
    # initialize constants
    startPos = default_pos['hand_start']

    fingers = ['thumb', 'index', 'middle', 'ring', 'pinky']
    zPos = startPos[2]
    zPos_cp = startPos[2]
    spacing = 1.5

    for index, name in enumerate(fingers):
        jnt_num = 5
        if index == 0:
            # Thumb has less joints
            jnt_num = 4
        else:
            # Offset fingers
            zPos -= spacing

        fingerPos = startPos[0], startPos[1], zPos
        # Do fingers
        print(fingerPos)
        yPos = fingerPos[1]
        offset = 4
        finger_jnts = []
        for i in range(jnt_num):
            jnt = pm.createNode('joint', name=f'{name}_{i}_jnt')
            finger_jnts.append(jnt)

            # Create more space for the knuckles
            if i == 1:
                yPos -= offset
            # Set jnt position
            pos = fingerPos[0], yPos, fingerPos[2]
            jnt.translate.set(pos)

            yPos -= offset
        fingers_jnts.append(finger_jnts)

        # Group fingers
        finger_grp = pm.createNode('transform', name=f'{name}_grp')
        finger_grps.append(finger_grp)

        pm.matchTransform(finger_grp, finger_jnts[0])
        pm.parent(finger_jnts, finger_grp)


        # Rotate Thumb
        if index == 0:
            pm.rotate(finger_grp,(-25,-30,0))

    hand_grp = pm.createNode('transform', name='hand_grp')
    pm.matchTransform(hand_grp, finger_grps[int(len(fingers)/2)])
    pm.parent(finger_grps, hand_grp)
    pm.parent(hand_grp, guides_grp())

    return fingers_jnts


def clavicle():
    for side in ['L', 'R']:
        jnt = pm.createNode('joint', name=f'{side}_clavicle')
        pos = [default_pos['clavicle'][0], default_pos['clavicle'][1], default_pos['clavicle'][2]]
        print(pos)
        # Flip for right side
        if side == 'R':
            pos[0] *= -1

        jnt.translate.set(pos)
        pm.parent(jnt, guides_grp())


def create_rig_guides():
    clavicle()
    arm()
    leg()
    hand()
    foot()
    torso(3)

create_rig_guides()