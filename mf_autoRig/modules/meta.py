import pymel.core as pm

def create_metadata(name, moduleType, info_args, can_mirror):
    metaNode = pm.createNode('network', name="META_" + name)
    # Connection attributes
    metaNode.addAttr('connected_to', at='message', r=False)
    metaNode.addAttr('attach_pts', at='message', m=True, w=False)

    # Mirror attributes
    if can_mirror:
        metaNode.addAttr('mirrored_to', at='message')
        metaNode.addAttr('mirrored_from', at='message')

    # Default args
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
    if not nodes:
        return

    def connect(src, dest):
        # If it's a pynode connect message attr
        if isinstance(src, pm.PyNode):
            if not pm.isConnected(src.message, dest):
                src.message.connect(dest)

        # If it's an int just set the value
        elif isinstance(src, (float, int, str)):
            dest.set(src)

        elif isinstance(src, bool):
            dest.set(src)

    # If it's a list of nodes connect each one to the destination
    if isinstance(nodes, list):
        for i, node in enumerate(nodes):
            connect(node, dst[i])
    else:
        connect(nodes, dst)



