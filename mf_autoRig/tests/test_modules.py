import time
from maya import cmds
import pymel.core as pm
from mf_autoRig.modules import Limb, Hand, Clavicle, Spine, FKFoot
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

def test_body():
    L_arm = Limb.Limb('L_arm')
    L_leg = Limb.Limb('L_leg')
    spine = Spine.Spine('M_spine', num=4)
    L_clavicle = Clavicle.Clavicle('L_clavicle')
    # L_hand = Hand.Hand('L_hand')
    L_arm.create_guides(pos=default_pos['arm'])
    L_leg.create_guides(pos=default_pos['leg'])
    spine.create_guides(pos=default_pos['spine'])
    L_clavicle.create_guides(pos=default_pos['clavicle'])
    # L_hand.create_guides(wrist_pos=default_pos['hand_start'])

    print(L_arm)
    print(L_clavicle)
    L_leg.attach_index = 1
    L_leg.save_metadata()
    L_arm.connect_guides(L_clavicle)
    L_clavicle.connect_guides(spine)
    L_leg.connect_guides(spine)


    L_leg.mirror_guides()
    # L_hand.mirror_guides()


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

def main():
    cmds.file(new=True, f=True)

    time.sleep(2)

    test_hand()

if __name__ == '__main__':
    main()





