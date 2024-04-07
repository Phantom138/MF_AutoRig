import abc
from abc import abstractmethod
import pymel.core as pm
import pymel.core.nodetypes as nt
import mf_autoRig.modules.meta as mdata
from mf_autoRig import log
from mf_autoRig.lib.get_curve_info import apply_curve_info, save_curve_info
from mf_autoRig.modules import module_tools
from mf_autoRig.utils.Side import Side
import mf_autoRig.lib.mirrorJoint as mirrorUtils

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
        'mirrored_to': {'attributeType': 'message'},
        'mirrored_from': {'attributeType': 'message'},
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


    @abstractmethod
    def reset(self):
        self.control_grp = None
        self.joints_grp = None
        self.mirrored_from = None
        self.mirrored_to = None
        self.curve_info = None


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
        # Reset the class so we start with clean values
        self.reset()

        # Get the attributes from the saved metadata
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

    # CONNECTION METHODS
    def connect_metadata(self, dest, index=0):
        # Connect meta nodes
        if self.meta:
            dest.metaNode.attach_pts[index].connect(self.metaNode.connected_to)
            log.info(f"Successfully connected {self.name} to {dest.name}")

    def check_if_connected(self, dest):
        if self.meta:
            if self.metaNode.connected_to.get() == dest.metaNode:
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

    def get_parent(self):
        """
        Get the parent module of the module
        Returns:
            Parent module if it exists, None otherwise
        """
        if self.meta:
            parent = self.metaNode.connected_to.get()
            if parent is None:
                return None
            else:
                return module_tools.createModule(parent)

    def get_children(self) -> list:
        """
        Get all children of the module
        Returns:
            List of children modules
            List is empty if there are no children
        """
        if self.meta:
            children = self.metaNode.attach_pts.get()
            if len(children) == 0:
                return []
            return [module_tools.createModule(child) for child in children]

    def get_info(self) -> tuple[bool, bool, bool]:
        """
        Utility method to get information about the module
        """
        self.update_from_meta()

        if self.all_ctrls is None or len(self.all_ctrls) == 0:
            # This means the module is not rigged
            is_rigged = False
        else:
            is_rigged = True

        if self.get_parent() is None:
            is_connected = False
        else:
            is_connected = True

        if self.mirrored_from is None:
            is_mirrored = False
        else:
            is_mirrored = True

        return is_rigged, is_connected, is_mirrored

    # EDIT METHODS
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
        if self.guides is not None:
            log.debug(f"Deleting {self.guides}")
            pm.delete(self.guides)

        if self.joints_grp is not None:
            log.debug(f"Deleting {self.joints_grp}")
            pm.delete(self.joints_grp)

        if self.control_grp is not None:
            log.debug(f"Deleting {self.control_grp}")
            pm.delete(self.control_grp)


        if not keep_meta_node:
            pm.delete(self.metaNode)

    def destroy_rig(self, disconnect=True):
        # Save curve info
        log.info(f"{self.name}: Destroying rig")
        self.curve_info = save_curve_info(self.all_ctrls)


        to_delete = [self.joints_grp, self.control_grp]
        for node in to_delete:
            log.debug(f"Deleting {node}")
            pm.delete(node)

        self.update_from_meta()

        if disconnect:
            # Disconnect
            self.metaNode.affectedBy.disconnect()

    def rebuild_rig(self):
        log.info(f"{self.name}: Rebuilding rig")

        if self.mirrored_from is not None:
            return

        self.create_joints()
        self.rig()

        if self.curve_info is not None:
            apply_curve_info(self.all_ctrls, self.curve_info)

        if self.mirrored_to is not None:
            mirrored_to = module_tools.createModule(self.mirrored_to)
            mirrored_to.delete()
            self.mirror()

    def mirror(self, rig=True):
        """
        Default mirror method, other modules might override this for custom behavior
        Mirrors on the YZ plane!
        Returns:
            New mirrored module, of the same type
        """

        # TODO: add possibility to mirror on different plane
        name = self.name.replace(f'{self.side.side}_', f'{self.side.opposite}_')
        mir_module = self.__class__(name)

        mir_module.joints = mirrorUtils.mirrorJoints(self.joints, (self.side.side, self.side.opposite))

        if rig:
            mir_module.rig()

        # Mirror Ctrls
        # Get ctrl info
        ctrl_info = save_curve_info(self.all_ctrls)

        mir_ctrl_info = {}
        # Mirror the positions across the YZ plane
        for key, value in ctrl_info.items():
            mir_key = key.replace(f'{self.side.side}_', f'{self.side.opposite}_')

            mir_ctrl_info[mir_key] = value

            for i, point in enumerate(value['cvs']):
                x, y, z = point
                # Multiply x and z value by -1 to mirror across YZ plane
                mir_ctrl_info[mir_key]['cvs'][i] = (x * -1, y, z * -1)

        pprint(mir_ctrl_info)

        apply_curve_info(mir_module.all_ctrls, mir_ctrl_info)

        # Do mirror connection for metadata
        self.metaNode.mirrored_to.connect(mir_module.metaNode.mirrored_from)

        return mir_module


    def __str__(self):
        return str(self.__dict__)

