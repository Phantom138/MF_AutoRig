import pymel.core as pm

from mf_autoRig.modules import Hand, Limb, Clavicle, Spine


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
        'Spine': Spine.Spine
    }

    module = modules[metaNode.moduleType.get()]
    obj = module.create_from_meta(metaNode)

    return obj

def get_all_modules():
    metaNodes = pm.ls(regex='META_.*', type='network')
    if not metaNodes:
        pm.warning("No metadata nodes found")
        return None

    return metaNodes

# node = pm.PyNode('META_L_hand')
# cls = createModule(node)
