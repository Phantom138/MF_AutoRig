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
    'arm': [[19.18, 142.85, -0.82], [42.78, 95.32, 3.31]],
    'leg': [[9.67, 92.28, 2.10], [15.41, 10.46, -4.70]],
    'foot': [[14.41, 4.181, 2.51], [14.41, 1.382, 16.549]],
    'foot_loc': [[21.059,0,5.678], [7.2, 0, 4.226],[14.41, 0, -10.275]],
    'hand': [[0, 0, 0], [0, -15, 0]],
    'torso': [[0.0, 97.15, 0.0], [0.0, 128.61, 0.0]],
    'foot_ball': [16.84, 3.38, 4.09],
    'foot_end': [18.37, 1.2, 16.12],
    'hand_start': [43.59, 92.72, 7.61],
    'clavicle': [[2.65, 143.59, 0.0], [19.18, 142.85, -0.82]]
}

def test_body():
    L_arm = Limb.Limb('L_arm')
    spine = Spine.Spine('M_spine', num=3)
    L_clavicle = Clavicle.Clavicle('L_clavicle')
    L_hand = Hand.Hand('L_hand')

    L_arm.create_guides(pos=default_pos['arm'])
    spine.create_guides(pos=default_pos['torso'])
    L_clavicle.create_guides(pos=default_pos['clavicle'])
    L_hand.create_guides(wrist_pos=default_pos['hand_start'])

    L_arm.connect_guides(L_clavicle)
    L_clavicle.connect_guides(spine)

    # L_arm.mirror_guides()
    # L_hand.mirror_guides()


def test_hand():
    L_hand = Hand.Hand('L_hand')
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

    test_mirror()

if __name__ == '__main__':
    main()





