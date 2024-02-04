import pymel.core as pm

def create_metadata(name, moduleType, info_args):
    # Default args
    metaNode = pm.createNode('network', name="META_" + name)
    metaNode.addAttr('Name', type='string')
    metaNode.Name.set(name)

    metaNode.addAttr('moduleType', type='string')
    metaNode.moduleType.set(moduleType)

    # Create separator
    metaNode.addAttr('info', at='compound', nc=len(info_args))

    # Custom args
    for key in info_args:
        # Parent to info attr
        info_args[key]['p'] = 'info'

        metaNode.addAttr(key, **info_args[key])


    return metaNode

def add(nodes, dst):
    if nodes:
        if isinstance(nodes, list):
            for i, node in enumerate(nodes):
                # Check if it isn't already connected
                if not pm.isConnected(node.message, dst[i]):
                    node.message.connect(dst[i])
        else:
            if not pm.isConnected(nodes.message, dst):
                nodes.message.connect(dst)



