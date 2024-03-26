import abc
from abc import abstractmethod
import pymel.core as pm
import pymel.core.nodetypes as nt
import mf_autoRig.modules.meta as mdata
from mf_autoRig import log
from mf_autoRig.lib.get_curve_info import apply_curve_info, save_curve_info
from mf_autoRig.modules import module_tools
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
        self.control_grp = None
        self.joints_grp = None

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

    @abstractmethod
    def create_guides(self):
        pass

    @abstractmethod
    def create_joints(self):
        pass

    @abstractmethod
    def rig(self):
        pass

    # METADATA METHODS
    @classmethod
    def create_from_meta(cls, metaNode):
        """
        Creates a Module instance from existing metadata node.

        Args:
            metaNode (pymel.core.nt.Network): The metadata node to create the module from.

        Returns:
            Module: An instance of the Module class.
        """

        name = metaNode.Name.get()
        general_obj = cls(name, meta=False)

        general_obj.moduleType = metaNode.moduleType.get()

        general_obj.metaNode = metaNode
        general_obj.meta = True

        general_obj.update_from_meta()

        return general_obj

    def update_from_meta(self):
        for attribute in self.meta_args:
            data = self.metaNode.attr(attribute).get()

            # If list is empty, set to None
            if isinstance(data, list) and not data:
                data = None

            setattr(self, attribute, data)

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
                mdata.add(src, dst)
                log.debug(f"{self.name} - Metadata connected {src} to {dst}")

    def connect_metadata(self, dest):
        # Connect meta nodes
        if self.meta:
            dest.metaNode.affects.connect(self.metaNode.affectedBy)

    def check_if_connected(self, dest):
        if self.meta and pm.isConnected(dest.metaNode.affects, self.metaNode.affectedBy):
            return True
        return False

    def get_connections(self, direction='up'):
        connections = []

        if direction == 'up':
            attr = self.metaNode.affectedBy
        elif direction == 'down':
            attr = self.metaNode.affects
        else:
            log.error(f"Invalid direction: {direction}")
            return None

        inputs = attr.get()

        while inputs:
            module = module_tools.createModule(inputs[0])
            connections.append(module)

            if direction == 'up':
                inputs = module.metaNode.affectedBy.get()
            if direction == 'down':
                inputs = module.metaNode.affects.get()

        if not connections:
            return [self]

        return connections

        # Get all affects connections
        # for each of them get all affects connections

    # EDIT METHODS
    def edit(self):
        # TODO: Make sure all controls are zeroed out!!
        self.edit_mode = True
        # Save edited curves
        self.curves_info = save_curve_info(self.all_ctrls)

        # Create guides where joints are
        edit_locators = []
        for jnt in self.joints:
            loc = pm.spaceLocator(name='temp_loc')
            trs = pm.xform(jnt, worldSpace=True, query=True, matrix=True)
            pm.xform(loc, worldSpace=True, matrix=trs)
            # pm.matchTransform(loc, jnt)
            edit_locators.append(loc)

        for i in range(len(edit_locators) - 1, 0, -1):
            pm.parent(edit_locators[i], edit_locators[i - 1])

        # Destroy rig
        self.delete(keep_meta_node=True)

        # Recreates class
        self.__init__(self.name, meta=self.metaNode)

        # Create guides
        self.guides = edit_locators

        connections = self.get_connections()
        for c in connections:
            module = module_tools.createModule(c)
            module.edit()

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

        connections = self.get_connections()
        for con in connections:
            con.apply_edit()


    def delete(self, keep_meta_node=False):
        """
        Delete Module
        """
        # Disconnect metaNode from everything
        if self.meta:
            all_connections = self.metaNode.listConnections(d=False, source=True, plugs=True, connections=True)
            conn = [tup[0] for tup in all_connections]
            for c in conn:
                c.disconnect()

        # Delete stuff
        try:
            log.debug(f"Deleting {self.joints_grp}")
            pm.delete(self.joints_grp)
        except:
            pass

        try:
            log.debug(f"Deleting {self.control_grp}")
            pm.delete(self.control_grp)
        except:
            pass

        if not keep_meta_node:
            pm.delete(self.metaNode)

    def destroy_rig(self):
        # guides = self.guides
        # metaNode = self.metaNode
        # name = self.name

        to_delete = [self.joints_grp, self.control_grp]
        for node in to_delete:
            log.debug(f"Deleting {node}")
            pm.delete(node)

        self.update_from_meta()

        # Disconnect
        self.metaNode.affectedBy.disconnect()

    def rebuild_rig(self):
        self.create_joints()
        self.rig()


    def __str__(self):
        return str(self.__dict__)

