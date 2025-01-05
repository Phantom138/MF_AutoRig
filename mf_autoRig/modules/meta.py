import pymel.core as pm

def create_metadata(name, moduleType, meta_attrs, can_mirror):
    metaNode = pm.createNode('network', name="META_" + name)

    attrs = meta_attrs

    # Config args
    for typ in attrs:
        for key in attrs[typ]:
            attr = attrs[typ][key]
            metaNode.addAttr(key, **attr)
            # Add extra attrs for double3
            if 'attributeType' in attr and attr['attributeType'] == 'double3':
                for axis in ['X', 'Y', 'Z']:
                    metaNode.addAttr(key + axis, **{'attributeType': 'double', 'p': key})

    metaNode.attr('name').set(name)
    metaNode.moduleType.set(moduleType)
    # # Create separator
    # metaNode.addAttr('info', at='compound', nc=len(info_args))
    #
    # # Custom args
    # for key in info_args:
    #     # Parent to info attr
    #     info_args[key]['p'] = 'info'
    #
    #     metaNode.addAttr(key, **info_args[key])


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

        # Set vector type variables
        elif isinstance(src, pm.dt.Vector):
            dest.set(src)

    # If it's a list of nodes connect each one to the destination
    if isinstance(nodes, list):
        for i, node in enumerate(nodes):
            connect(node, dst[i])
    else:
        connect(nodes, dst)



