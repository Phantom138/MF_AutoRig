import time
from maya import cmds
import pymel.core as pm
from mf_autoRig.modules import Limb, Hand, Clavicle, Spine, FKFoot, IKFoot, FKChain
# from unload_packages import unload_packages
# import mf_autoRig.UI.modifyWindow.modifyWindowUI as modifyWindow
# modifyWindow.showWindow()
# unload_packages(silent=True, packages=["mf_autoRig"])

default_pos = {
    # template: start pos, end pos
    'arm': [[1.773032097964995, 14.322893210773247, -0.09917052916917002], [3.1148938421900603, 11.69647354309644, -0.22577155288207962], [4.217464585541992, 9.666625709331072, 0.28031686998625727]],
    'leg': [[0.8487877898207787, 9.35869366991319, 0.05661994243791724], [1.2637507092887135, 5.0, -0.14445746998554232], [1.5278180216773998, 0.773339986281153, -0.5486720157348854]],
    'foot': [[14.41, 4.181, 2.51], [14.41, 1.382, 16.549]],
    'foot_loc': [[21.059,0,5.678], [7.2, 0, 4.226],[14.41, 0, -10.275]],
    'hand': [[0, 0, 0], [0, -15, 0]],
    'spine': [[0.0, 9.445656701806953, 0.0], [0.0, 13.617752617024404, 0.0]],
    'foot_ball': [16.84, 3.38, 4.09],
    'foot_end': [18.37, 1.2, 16.12],
    'hand_start': [43.59, 92.72, 7.61],
    'clavicle': [[0.4498149825047072, 14.346815201054653, 0.0], [1.773032097964995, 14.322893210773247, -0.09917052916917002]]
}

pos = {
    # template: start pos, end pos
    'clavicle': [(3.642359972000122, 138.716552734375, -1.464443445205686), (15.314141273498537, 138.29847717285156, -2.8424408435821515)],
    'arm': [[15.314141273498537, 138.29847717285156, -2.8424408435821515], [30.072890666376587, 115.56662078418057, -1.370172481936409], [41.858654022216754, 97.4138488769531, 12.150848388671871]],
    'leg': [(10.623377799987793, 96.98314666748047, 6.8833827526759706e-15), (12.171644062268411, 50.76010869862766, 0.012482166547694282), (13.629721641540527, 7.2296786308288645, -3.661197423934937)],
    'spine': [(0.0, 92.03780364990234, 0.0), (0.0, 108.32737657084999, 3.02757731005146), (0.0, 122.7728457088272, 1.7878774932105308), (0.0, 136.34156799316406, -1.464443445205686)],
    # 'foot': [[14.41, 4.181, 2.51], [14.41, 1.382, 16.549]],
    # 'foot_loc': [[21.059,0,5.678], [7.2, 0, 4.226],[14.41, 0, -10.275]],
    # 'hand': [[0, 0, 0], [0, -15, 0]],
    # 'foot_ball': [16.84, 3.38, 4.09],
    # 'foot_end': [18.37, 1.2, 16.12],
    'wrist_pos': (41.858654022216754, 97.4138488769531, 12.150848388671871),
    'hand': {
        'wrist': (41.858654022216754, 97.4138488769531, 12.150848388671871),
        'orient_guides_rot': [[43.59124406694018, -13.359304493363311, 4.914820049530678], [143.76591935161883, -128.7849250534684, -37.121668684680614], [156.73732521381604, -115.85873538946755, -57.13288235803591], [6.764895282698499, -69.71416365297786, 90.0], [0.0, -76.75383080225053, 90.0]],
        'guides': [[(41.116765324483175, 97.09430919137704, 14.28607787822605), (40.26142164374256, 94.1379203453278, 17.89700126843422), (39.981732368469245, 91.80722713470459, 20.279955625534047), (39.69228772955901, 88.7063357453228, 22.013819880834156)],
            [(42.67416046267897, 96.66980695242535, 14.048017940735303), (44.34198141098024, 91.2166728973389, 18.887983560562148), (44.896644115447984, 88.19577503204349, 20.638436079025258), (44.80530881881714, 85.74915981292727, 21.49814653396607), (44.66164356030855, 82.8040673160466, 22.549202958563207)],
            [(43.431037028889165, 96.12414943092578, 13.456088406056967), (45.22605180740358, 90.26529407501224, 17.23616552352905), (46.09932994842528, 87.20483303070067, 18.733942508697524), (45.55070447921753, 84.77151489257814, 19.43649220466614), (44.20023236659502, 81.77690371155268, 20.07722224677014)],
            [(43.68797571346544, 96.01813407875473, 12.783014458517608), (45.49515151977539, 89.75024127960205, 15.23952639102935), (46.26339864730836, 86.75470638275148, 16.35214567184446), (45.66140508651734, 84.88651561737062, 16.82543683052063), (44.65387584993593, 81.99070584756807, 17.571150345370086)],
            [(43.691477605555285, 96.17056938148912, 11.736813706259303), (45.34947490692138, 89.54770088195804, 13.317322134971615), (45.55180883407592, 87.38491821289064, 13.589964866638178), (45.220462799072266, 85.97926902770999, 13.94710099697112), (44.279551819711145, 83.70041500090309, 14.726852693090667)]]
             },
    'foot': {
        'guides': [[13.629721641540527, 7.229678630828857, -3.6611974239349365], [14.481945991516113, 1.121225118637085, 6.510270595550537], [14.691303253173828, 1.2859458923339844, 15.436973571777344]],
        'locators': [[20.68676479033753, 0.0, 5.0], [9.97200986019664, 0.0, 6.34463357263869], [13.837330829295325, 0.0, -8.660677518915602]]
    },
    'neck': [[3.151011819102351e-31, 141.91992040470987, -1.417937047779558], [3.1510118191023506e-31, 144.94525146484375, -1.417937047779558], [-1.2746704800627457e-30, 149.64504671096802, -0.22746194154023902]]
}



def test_body(positions=pos):
    L_arm = Limb.Limb('L_arm')
    L_leg = Limb.Limb('L_leg')
    spine = Spine.Spine('M_spine', num=4)
    M_neck = FKChain.FKChain('M_neck', num=3)
    L_clavicle = Clavicle.Clavicle('L_clavicle')
    L_hand = Hand.Hand('L_hand')
    L_foot = IKFoot.IKFoot('L_foot')

    L_arm.create_guides(pos=positions['arm'])
    L_leg.create_guides(pos=positions['leg'])
    spine.create_guides(pos=positions['spine'])
    L_clavicle.create_guides(pos=positions['clavicle'])
    L_hand.create_guides(pos = positions['hand'])
    L_foot.create_guides(pos=positions['foot'])
    M_neck.create_guides(pos=positions['neck'])

    L_leg.attach_index = 0
    L_leg.metaNode.attach_index.set(0)
    # L_leg.save_metadata() TODO: debug and see why this isn't working?
    L_arm.connect_guides(L_clavicle)
    L_clavicle.connect_guides(spine)
    L_leg.connect_guides(spine)
    L_hand.connect_guides(L_arm)
    L_foot.connect_guides(L_leg)
    M_neck.connect_guides(spine)

    ## Right side
    R_arm = L_arm.mirror_guides()
    R_leg = L_leg.mirror_guides()
    R_clavicle = L_clavicle.mirror_guides()
    R_hand = L_hand.mirror_guides()
    R_foot = L_foot.mirror_guides()

    R_arm.connect_guides(R_clavicle)
    R_clavicle.connect_guides(spine)
    R_leg.connect_guides(spine)
    R_hand.connect_guides(R_arm)
    R_foot.connect_guides(R_leg)


def test_hand():
    L_hand = Hand.Hand('L_hand', finger_num=3)
    L_hand.create_guides()
    # R_hand = Hand.Hand('R_hand')
    # R_hand.create_guides()
    R_hand = L_hand.mirror_guides()
    pm.move(pm.PyNode('L_hand_guide_grp'), [5, 0, 0])

    L_hand.create_joints()
    L_hand.rig()
    R_hand.create_joints()
    R_hand.rig()


def test_mirror():
    L_arm = Limb.Limb('L_arm')
    L_arm.create_guides()

    # L_hand = Hand.Hand('L_hand')
    # L_hand.create_guides()

    L_arm.mirror_guides()
    # L_hand.mirror_guides()

def test_config():
    L_arm = Limb.Limb('L_arm')
    L_arm.create_guides()
    R_arm = Limb.Limb('R_arm')
    R_arm.create_guides()

def test_ik_foot():
    L_foot = IKFoot.IKFoot('L_foot')
    L_leg = Limb.Limb('L_leg')
    L_leg.create_guides()
    L_leg.create_joints()


    L_foot.create_guides()
    L_foot.create_joints()
    L_foot.connect_guides(L_leg)

    L_foot.rig()
    L_leg.rig()


def main():
    cmds.file(new=True, f=True)

    time.sleep(2)

    test_body()

if __name__ == '__main__':
    main()





