import abc
from abc import abstractmethod
import pymel.core as pm
import pymel.core.nodetypes as nt
import mf_autoRig.modules.meta as mdata

from pprint import pprint

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


class Module(abc.ABC):
    def __init__(self, name, args, meta=True):
        self.name = name
        self.meta = meta
        self.moduleType = self.__class__.__name__

        if meta:
            self.metaNode = mdata.create_metadata(name, self.moduleType, args)

    @classmethod
    @abstractmethod
    def create_from_meta(cls, metaNode):
        name = metaNode.Name.get()
        general_obj = cls(name, meta=False)

        general_obj.metaNode = metaNode
        general_obj.meta = True
        # Get attributes
        for attribute in general_obj.meta_args:
            setattr(general_obj, attribute, general_obj.metaNode.attr(attribute).get())

        general_obj.moduleType = metaNode.moduleType.get()

        return general_obj

    @abstractmethod
    def create_guides(self):
        pass

    @abstractmethod
    def create_joints(self):
        pass

    @abstractmethod
    def rig(self):
        pass

    def __str__(self):
        return str(self.__dict__)

