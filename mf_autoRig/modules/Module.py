import pymel.core as pm
import pymel.core.nodetypes as nt


import mf_autoRig.modules.meta as mdata


def createModule(metaNode):
    """
    Function to create corresponding class from metadata node
    """
    name = metaNode.Name.get()
    moduleType = metaNode.moduleType.get()

    # Create corresponding class based on moduleType
    cls_object = modules_mapping[moduleType][0]
    if cls_object:
        cls_object = cls_object(name, meta=False)

    # Get attrs
    meta_args = modules_mapping[moduleType][1]
    attrs = list(meta_args.keys())

    for attr in attrs:
        value = getattr(metaNode, attr).get()
        if not value:
            pm.warning(f"Warning,{metaNode}.{attr} is empty!")
        setattr(cls_object, attr, value)

    print(f"Created {moduleType} from {metaNode}")
    return cls_object


class Module():
    def __init__(self, name, moduleType, args, meta=True):
        if meta == False:
            pass
        elif meta == True:
            self.metaModule = mdata.create_metadata(name, moduleType, args)
        elif isinstance(meta, nt.Network):
            # Create metadata from module
            self.create_from_meta(meta)

            pass
    def create_from_meta(self, metaNode):
        self.name = metaNode.Name.get()
        self.moduleType = metaNode.moduleType.get()
