import pymel.core as pm



def createModule(metaNode):
    """
    Function to create corresponding class from metadata node
    """
    from mf_autoRig.modules import Hand, Limb, Clavicle, Spine, IKFoot
    from mf_autoRig.modules import FKFoot

    from mf_autoRig.modules.Toon import BendyLimb

    modules = {
        'Limb': Limb.Limb,
        'Hand': Hand.Hand,
        'FKFoot': FKFoot.FKFoot,
        'Clavicle': Clavicle.Clavicle,
        'Spine': Spine.Spine,
        'BendyLimb': BendyLimb.BendyLimb
    }

    module = modules[metaNode.moduleType.get()]
    obj = module.create_from_meta(metaNode)

    return obj

def get_all_modules(module_types=None, create=False):
    metaNodes = pm.ls(regex='META_.*', type='network')

    if not metaNodes:
        pm.warning("No metadata nodes found")
        return None

    if module_types is not None:
        nodes = []
        for node in metaNodes:
            if node.moduleType.get() in module_types:
                nodes.append(node)
    else:
        nodes = metaNodes

    if create:
        return [createModule(node) for node in nodes]

    return nodes



def get_connections(metaNode):
    def get_con(metaNodes, conns):
        """
        This exits when there is no connections to the metaNode
        """
        if not isinstance(metaNodes, list):
            metaNodes = [metaNodes]

        # if not len(metaNodes) == 0:
        #     connections.append(metaNodes)

        for node in metaNodes:
            conn = node.affects.get()
            conns.append(node)

            get_con(conn, conns)

    connections = []
    get_con(metaNode, connections)

    modules = []
    for conn in connections:
        module = createModule(conn)
        modules.append(module)

    return modules


