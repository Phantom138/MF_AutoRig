import abc
from abc import abstractmethod
import pymel.core as pm
import pymel.core.nodetypes as nt
import mf_autoRig.modules.meta as mdata
from mf_autoRig import log
from mf_autoRig.lib.get_curve_info import apply_curve_info, save_curve_info
from mf_autoRig.utils.Side import Side

from pprint import pprint

class Module(abc.ABC):
    # TODO: add delete method that also cleans up the groups
    """
    Abstract base class for creating rigging modules.

    Attributes:
        name (str): The name of the module.
        meta (bool): Flag indicating whether the module has associated metadata.
        meta_args (list): List of attributes to be stored in metadata.
        moduleType (str): The type of the module.
        side (Side): The side of the module (e.g., Left, Right, Center).
        metaNode (pymel.core.PyNode): Metadata node associated with the module if meta is True.

    Methods:
        create_from_meta(cls, metaNode):
            Creates a Module instance from existing metadata node.

        create_guides(self):
            Abstract method to create guide objects for the rigging module.

        create_joints(self):
            Abstract method to create joints for the rigging module.

        rig(self):
            Abstract method to perform the rigging process for the module.

        save_metadata(self):
            Saves attribute values to the associated metadata node.

        connect_metadata(self, dest):
            Connects the metadata node to another destination metadata node.

        check_if_connected(self, dest):
            Checks if the metadata node is connected to the destination metadata node.

        __str__(self):
            Returns a string representation of the Module instance.
    """

    df_meta_args = {
        'joints_grp': {'attributeType': 'message'},
        'control_grp': {'attributeType': 'message'},
    }

    def __init__(self, name, args, meta):
        self.name = name
        self.meta = meta
        self.meta_args = args

        # Add default args to meta_args
        self.meta_args.update(self.df_meta_args)

        self.moduleType = self.__class__.__name__
        self.side = Side(name.split('_')[0])

        if meta is True:
            log.debug(f"Creating metadata for {name}")
            self.metaNode = mdata.create_metadata(name, self.moduleType, args)
        if isinstance(meta, pm.nt.Network):
            # Using existing metadata node
            self.metaNode = meta
            # TODO: Validate metadata

    @classmethod
    def create_from_meta(cls, metaNode):
        """
        Creates a Module instance from existing metadata node.

        Args:
            metaNode (pymel.core.PyNode): The metadata node to create the module from.

        Returns:
            Module: An instance of the Module class.
        """

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

    def edit(self):
        # TODO: Make sure all controls are zeroed out!!
        self.edit_mode = True
        # Save edited curves
        self.curves_info = save_curve_info(self.all_ctrls)

        # Create guides where joints are
        edit_locators = []
        for jnt in self.joints:
            loc = pm.spaceLocator(name='temp_loc')
            pm.matchTransform(loc, jnt)
            edit_locators.append(loc)

        for i in range(len(edit_locators) - 1, 0, -1):
            pm.parent(edit_locators[i], edit_locators[i - 1])

        # Destroy rig
        self.delete(keep_meta_node=True)

        # Recreates class
        self.__init__(self.name, meta=self.metaNode)

        # Create guides
        self.guides = edit_locators

    def apply_edit(self):
        if self.edit_mode is False:
            log.warning(f"{self.name} not in edit mode!")
            return

        self.create_joints()
        self.rig()
        apply_curve_info(self.all_ctrls, self.curves_info)
        # Delete guides
        pm.delete(self.guides)
        self.guides = []


    def delete(self, keep_meta_node=False):
        """
        Delete Module
        """
        if keep_meta_node:
            # HACK: Create empty transform and connect it to metaNode so that when deleting the module,
            #       the metaNode is not deleted
            tmp = pm.createNode('transform', name=f'{self.name}_TEMP_NODE')
            self.metaNode.addAttr('TEMP_NODE', at='message')
            tmp.message.connect(self.metaNode.TEMP_NODE)

        # Delete stuff
        log.debug(f"Deleting {self.joints_grp}")
        pm.delete(self.joints_grp)

        log.debug(f"Deleting {self.control_grp}")
        pm.delete(self.control_grp)

        try:
            pm.delete(self.guides)
        except:
            pass

        if keep_meta_node:
            # Disconnect tmp from metaNode
            tmp.message.disconnect(self.metaNode.TEMP_NODE)
            pm.delete(tmp)
            self.metaNode.deleteAttr('TEMP_NODE')
        else:
            pm.delete(self.metaNode)

    def __str__(self):
        return str(self.__dict__)

