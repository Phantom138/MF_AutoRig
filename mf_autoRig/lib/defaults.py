tool_prf = 'autoMF_'
grp_sff = '_grp'
ctrl_sff = '_ctrl'
jnt_sff = '_jnt'
end_sff = '_end'
skin_sff = '_skin'
ik_sff = '_ik'
fk_sff = '_fk'
pole_sff = '_pole'
attr_sff = '_attr'
loc_sff = '_loc'
control_grp = '_Control_Grp'
ikfkSwitch_name = 'IkFkSwitch'
root = 'Root_Ctrl'
joints_grp = 'Joints_Grp'
ikHandle_grp = 'ikHandle_grp'
rig_guides_grp = 'rig_guides_grp'
driven_grp = 'DO_NOT_TOUCH_driven_guides_grp'


# CTRL Shapes structure: Degree, Points, Knots
CTRL_SHAPES = {
    'cube': [1, [(1, 1, 1), (1, 1, -1), (-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, -1, 1), (1, -1, -1), (1, 1, -1),
                 (-1, 1, -1),
                 (-1, -1, -1), (1, -1, -1),
                 (-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, -1, 1), (1, -1, 1)],[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]],
    'square': [1, [(-1.0, 0.0, -1.0), (1.0, 0.0, -1.0), (1.0, 0.0, 1.0), (-1.0, 0.0, 1.0), (-1.0, 0.0, -1.0)]],
    'joint_curve': [1, [(0.0, 1.0, 0.0), (0.0, 0.93, 0.39), (0.0, 0.71, 0.71), (0.0, 0.39, 0.93), (0.0, 0.0, 1.0), (0.0, -0.39, 0.93), (0.0, -0.71, 0.71), (0.0, -0.93, 0.39), (0.0, -1.0, 0.0), (0.0, -0.93, -0.39), (0.0, -0.71, -0.71), (0.0, -0.39, -0.93), (0.0, 0.0, -1.0), (0.0, 0.39, -0.93), (0.0, 0.71, -0.71), (0.0, 0.93, -0.39), (0.0, 1.0, 0.0), (0.39, 0.93, 0.0), (0.71, 0.71, 0.0), (0.93, 0.39, 0.0), (1.0, 0.0, 0.0), (0.93, -0.39, 0.0), (0.71, -0.71, 0.0), (0.39, -0.93, 0.0), (0.0, -1.0, 0.0), (-0.39, -0.93, 0.0), (-0.71, -0.71, 0.0), (-0.93, -0.39, 0.0), (-1.0, 0.0, 0.0), (-0.93, 0.39, 0.0), (-0.71, 0.71, 0.0), (-0.39, 0.93, 0.0), (0.0, 1.0, 0.0), (0.0, 0.93, -0.39), (0.0, 0.71, -0.71), (0.0, 0.39, -0.93), (0.0, 0.0, -1.0), (-0.39, 0.0, -0.93), (-0.71, 0.0, -0.71), (-0.93, 0.0, -0.39), (-1.0, 0.0, 0.0), (-0.93, 0.0, 0.39), (-0.71, 0.0, 0.71), (-0.39, 0.0, 0.93), (0.0, 0.0, 1.0), (0.39, 0.0, 0.93), (0.71, 0.0, 0.71), (0.93, 0.0, 0.39), (1.0, 0.0, 0.0), (0.93, 0.0, -0.39), (0.71, 0.0, -0.71), (0.39, 0.0, -0.93), (0.0, 0.0, -1.0)]],
    'arrow': [1, [(0.0, 0.0, 0.0), (-1.0, 0.0, -0.33), (-1.0, 0.0, 0.33), (0.0, 0.0, 0.0), (-1.0, 0.33, 0.0), (-1.0, 0.0, 0.0), (-1.0, -0.33, 0.0), (0.0, 0.0, 0.0)]],
    'star': [3, [(0.06, 0.0, -0.9), (0.0, 0.0, -1.22), (-0.06, 0.0, -0.9), (-0.09, 0.0, -0.81), (-0.16, 0.0, -0.61), (-0.23, 0.0, -0.48), (-0.33, 0.0, -0.33), (-0.48, 0.0, -0.23), (-0.62, 0.0, -0.16), (-0.8, 0.0, -0.09), (-0.91, 0.0, -0.06), (-1.19, 0.0, 0.0), (-0.91, 0.0, 0.06), (-0.8, 0.0, 0.09), (-0.62, 0.0, 0.16), (-0.48, 0.0, 0.23), (-0.33, 0.0, 0.33), (-0.23, 0.0, 0.48), (-0.16, 0.0, 0.62), (-0.09, 0.0, 0.8), (-0.06, 0.0, 0.91), (0.0, 0.0, 1.19), (0.06, 0.0, 0.91), (0.09, 0.0, 0.8), (0.16, 0.0, 0.62), (0.23, 0.0, 0.48), (0.33, 0.0, 0.33), (0.48, 0.0, 0.23), (0.62, 0.0, 0.16), (0.8, 0.0, 0.09), (0.91, 0.0, 0.06), (1.19, 0.0, 0.0), (0.91, 0.0, -0.06), (0.8, 0.0, -0.09), (0.62, 0.0, -0.16), (0.48, 0.0, -0.23), (0.33, 0.0, -0.33), (0.23, 0.0, -0.48), (0.16, 0.0, -0.61), (0.1, 0.0, -0.77), (0.06, 0.0, -0.9), (0.06, 0.0, -0.9), (0.06, 0.0, -0.9), (0.06, 0.0, -0.9)]]
}

CTRL_SCALE = 1

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
    'clavicle': [2.65, 143.59, 0.0]
}


def mirror_default_pos():
    mirrored_pos = {}
    for key, value in default_pos.items():
        if isinstance(value[0], list):
            mirrored_pos[key] = [[pos[0]*(-1)] + pos[1:] for pos in value]
        else:
            mirrored_pos[key] = [value[0]*(-1)] + value[1:]

    #mirrored_pos = {key: [[-pos[0]] + pos[1:] for pos in value] for key, value in default_pos.items()}
    return mirrored_pos

mirrored_pos = mirror_default_pos()
