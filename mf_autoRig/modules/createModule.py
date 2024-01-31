import pymel.core as pm

from mf_autoRig.modules import Hand
from mf_autoRig.modules import Limb
from mf_autoRig.modules import Torso


# modules_mapping = {
#     'Limb': Limb.Limb,
#     'Arm': [Limb.Arm, Limb.meta_args],
#     'Leg': [Limb.Leg, Limb.meta_args],
#     'Hand': [Hand.Hand, Hand.meta_args],
#     'Clavicle': [Torso.Clavicle, Torso.clavicle_meta_args],
#     'Spine': [Torso.Spine, Torso.spine_meta_args],
# }
#
# def createModule(metaNode):
#     """
#     Function to create corresponding class from metadata node
#     """
#     name = metaNode.Name.get()
#     moduleType = metaNode.moduleType.get()
#
#     # Create corresponding class based on moduleType
#     cls_object = modules_mapping[moduleType][0]
#     if cls_object:
#         cls_object = cls_object(name, meta=False)
#
#     # Get attrs
#     meta_args = modules_mapping[moduleType][1]
#     attrs = list(meta_args.keys())
#
#     for attr in attrs:
#         value = getattr(metaNode, attr).get()
#         if not value:
#             pm.warning(f"Warning,{metaNode}.{attr} is empty!")
#         setattr(cls_object, attr, value)
#
#     print(f"Created {moduleType} from {metaNode}")
#     return cls_object

def get_all_modules():
    metaNodes = pm.ls(regex='META_.*', type='network')
    if not metaNodes:
        pm.warning("No metadata nodes found")
        return None

    return metaNodes

# node = pm.PyNode('META_L_hand')
# cls = createModule(node)
