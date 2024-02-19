import abc
from abc import abstractmethod
import pymel.core as pm
import pymel.core.nodetypes as nt
import mf_autoRig.modules.meta as mdata
from mf_autoRig.utils.Side import Side

from pprint import pprint

class Module(abc.ABC):
    # TODO: add delete method that also cleans up the groups
    def __init__(self, name, args, meta):
        self.name = name
        self.meta = meta
        self.meta_args = args
        self.moduleType = self.__class__.__name__
        self.side = Side(name.split('_')[0])

        if meta:
            print(f"|||||||||||creating metadata for {name}")
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

    def save_metadata(self):
        """
        Do the appropriate connections to the metaNode, based on the meta_args
        Skip connections that already made to avoid warnings
        """
        for attribute in self.meta_args:
            src = getattr(self, attribute)
            if isinstance(src, list) and not src:
                # Skip if list is empty
                continue

            if src is not None:
                dst = self.metaNode.attr(attribute)
                #print(src, dst)
                mdata.add(src, dst)

    def connect_metadata(self, dest):
        # Connect meta nodes
        if self.meta:
            dest.metaNode.affects.connect(self.metaNode.affectedBy)

    def check_if_connected(self, dest):
        if self.meta and pm.isConnected(dest.metaNode.affects, self.metaNode.affectedBy):
            return True
        return False


    def __str__(self):
        return str(self.__dict__)

