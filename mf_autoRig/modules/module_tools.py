import pymel.core as pm

from mf_autoRig.modules import Hand, Limb, Clavicle, Spine
from mf_autoRig.modules.Toon import BendyLimb


def createModule(metaNode):
    """
    Function to create corresponding class from metadata node
    """
    modules = {
        'Limb': Limb.Limb,
        'Arm': Limb.Arm,
        'Leg': Limb.Leg,
        'Hand': Hand.Hand,
        'Clavicle': Clavicle.Clavicle,
        'Spine': Spine.Spine,
        'BendyLimb': BendyLimb.BendyLimb
    }

    module = modules[metaNode.moduleType.get()]
    obj = module.create_from_meta(metaNode)

    return obj

def get_all_modules(module_types=None):
    metaNodes = pm.ls(regex='META_.*', type='network')

    if not metaNodes:
        pm.warning("No metadata nodes found")
        return None

    if module_types is not None:
        good_nodes = []
        for node in metaNodes:

            if node.moduleType.get() in module_types:
                good_nodes.append(node)

        return good_nodes

    return metaNodes

# node = pm.PyNode('META_L_hand')
# cls = createModule(node)
