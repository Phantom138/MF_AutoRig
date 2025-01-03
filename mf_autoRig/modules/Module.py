import abc
from abc import abstractmethod
import pymel.core as pm
import pymel.core.nodetypes as nt
import mf_autoRig.modules.meta as mdata
from mf_autoRig import log
from mf_autoRig.utils.controllers_tools import apply_curve_info, save_curve_info
from mf_autoRig.utt.Side import Side
import mf_autoRig.utils as utils
from mf_autoRig.modules import module_tools
from mf_autoRig.utils import defaults as df
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
        'creation_attr':{
            'name': {'type': 'string'},
            'moduleType': {'type': 'string'},
        },

        'module_attrs': {
            'mirrored_to': {'attributeType': 'message'},
            'mirrored_from': {'attributeType': 'message'},
            'children': {'attributeType': 'message', 'm': True, 'w': False},
            'parent': {'attributeType': 'message', 'r': False},
        },

        # Stuff related to the rig config
        'config_attrs': {
            'attach_index': {'attributeType': 'long'},
            'jnt_orient_main': {'attributeType': 'double3'},
            'jnt_orient_secondary': {'attributeType': 'double3'},
        },

        # Attributes for keeping track of nodes created by the rig
        'info_attrs':{
            'joints_grp': {'attributeType': 'message'},
            'control_grp': {'attributeType': 'message'},
        }

    }

    # Class level dictionary that keeps track of all instances
    instances = {}

    def __init__(self, name, args, meta):
        self.name = name
        self.moduleType = self.__class__.__name__
        self.side = Side(name.split('_')[0])

        # If it is a middle module, you cannot mirror it
        if self.side.opposite is None:
            can_mirror = False
        else:
            can_mirror = True

        # Add default args to meta_args
        self.meta_args = self.df_meta_args.copy()
        for key in self.meta_args:
            if key in args:
                self.meta_args[key].update(args[key])

        print(f"Meta args: {self.meta_args}")
        self.meta = meta
        if isinstance(meta, pm.nt.Network):
            # Using existing metadata node
            self.metaNode = meta

        elif meta is True:
            log.debug(f"Creating metadata for {name}")
            self.metaNode = mdata.create_metadata(name, self.moduleType, self.meta_args,True)

        # Parent - child
        self.parent = None
        self.children = []

        # Save instance
        self.instances[self.metaNode.name()] = self


    @abstractmethod
    def reset(self):
        self.guides = []

        self.guide_grp = None
        self.control_grp = None
        self.joints_grp = None

        self.mirrored_from = None
        self.mirrored_to = None

        self.jnt_orient_main = (0,1,0)
        self.jnt_orient_secondary = (0,0,1)

        self.curve_info = []
        self.all_ctrls = []

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

        name = pm.getAttr(metaNode + '.name')
        general_obj = cls(name, meta=metaNode)

        general_obj.moduleType = metaNode.moduleType.get()

        general_obj.metaNode = metaNode
        general_obj.meta = True
        general_obj.update_from_meta()

        return general_obj

    def update_from_meta(self):
        # Reset the class so we start with clean values
        self.reset()

        # Get the attributes from the saved metadata
        for typ in self.meta_args:
            for attribute in self.meta_args[typ]:
                data = self.metaNode.attr(attribute).get()

                # If it's a metadata node, create the corresponding class
                if isinstance(data, pm.nt.Network) and data.name().startswith(df.meta_prf):
                    data_class = module_tools.createModule(data)
                    setattr(self, attribute, data_class)
                    continue

                # If it's a list of metadata nodes, create the corresponding classes
                if isinstance(data, list) and len(data) != 0:
                    is_meta_list = all(isinstance(d, pm.nt.Network) and d.name().startswith(df.meta_prf) for d in data)
                    if is_meta_list:
                        # Means we have a list of network nodes
                        result = [module_tools.createModule(d) for d in data]
                        setattr(self, attribute, result)
                        continue

                setattr(self, attribute, data)

    def save_metadata(self):
        """
        Do the appropriate connections to the metaNode, based on the meta_args
        Skip connections that already made to avoid warnings
        """
        for typ in self.meta_args:
            for attribute in self.meta_args[typ]:
                src = getattr(self, attribute)
                if isinstance(src, list) and not src:
                    # Skip if list is empty
                    continue

                if src is None:
                    continue

                dst = self.metaNode.attr(attribute)
                mdata.add(src, dst)
                log.debug(f"{self.name} - Metadata connected {src} to {dst}")

    # CONNECTION METHODS
    def connect_metadata(self, dest, index=0):
        # Connect meta nodes
        if self.meta:
            # Connect children one by one
            length = len(dest.children)
            dest.metaNode.children[length].connect(self.metaNode.parent)
            log.info(f"Successfully connected {self.name} to {dest.name}")

        self.parent = dest
        dest.children.append(self)

    def check_if_connected(self, dest):
        if self.meta:
            if self.metaNode.parent.get() == dest.metaNode:
                return True
        return False

    def connect_children(self):
        print(f"Connecting parent {self.__dict__}")
        print(f"Connecting children {self.children}")
        for child in self.children:
            child.connect(self)

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

    def get_all_children(self):
        all_children = []
        def children(parent_mdl):
            for child in parent_mdl.get_children():
                all_children.append(child)
                children(child)

        children(self)
        return all_children

    def get_parent(self):
        """
        Get the parent module of the module
        Returns:
            Parent module if it exists, None otherwise
        """
        return self.parent

    def get_children(self) -> list:
        """
        Get all children of the module
        Returns:
            List of children modules
            List is empty if there are no children
        """
        return self.children

    def get_info(self):
        """
        Utility method to get information about the module
        """
        # self.update_from_meta()

        if len(self.all_ctrls) == 0:
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
        if len(self.guides) != 0:
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

    def destroy_rig(self):
        # Save curve info
        log.info(f"{self.name}: Destroying rig")
        #self.curve_info = save_curve_info(self.all_ctrls)


        to_delete = [self.joints_grp, self.control_grp]
        for node in to_delete:
            log.debug(f"Deleting {node}")
            pm.delete(node)

        self.update_from_meta()

        if self.mirrored_to is not None:
            mirrored_to = module_tools.createModule(self.mirrored_to)
            mirrored_to.destroy_rig()

    def rebuild_rig(self):
        log.info(f"{self.name}: Rebuilding rig")

        # If module is mirrored
        if self.mirrored_from is not None:
            return

        self.create_joints()
        self.rig()

        if self.curve_info is not None:
            apply_curve_info(self.all_ctrls, self.curve_info)

        if self.mirrored_to is not None:
            mirrored_to = module_tools.createModule(self.mirrored_to)
            mirrored_to.update_mirrored(destroy=False)

    def mirror_guides(self):
        name = self.name.replace(f'{self.side.side}_', f'{self.side.opposite}_')
        mir_module = self.__class__(name)
        mir_module.create_guides()

        # Change orient
        if self.jnt_orient_main == (0,1,0):
            mir_module.jnt_orient_main = (0,-1,0)
        if self.jnt_orient_secondary == (0,0,1):
            mir_module.jnt_orient_secondary = (0,0,-1)

        identity_mtx = [1, 0, 0, 0,
                        0, 1, 0, 0,
                        0, 0, 1, 0,
                        0, 0, 0, 1]

        utils.mirror_guides_transforms([self.guide_grp], [mir_module.guide_grp])

        # Get guide hierarchy
        keep = ['joint', 'transform']
        guide_hierarchy = []
        for h in (self.guide_grp.getChildren(ad=True)):
            if h.type() in keep and not h.endswith('_clusterHandle'):
                guide_hierarchy.append(h)

        # Get mir hierarchy
        mir_hierarchy = []
        for h in mir_module.guide_grp.getChildren(ad=True):
            if h.type() in keep and not h.endswith('_clusterHandle'):
                mir_hierarchy.append(h)

        for guide, mir_guide in zip(guide_hierarchy, mir_hierarchy):
            pm.xform(mir_guide, m=identity_mtx)
            utils.lock_and_hide(mir_guide)
            guide.xformMatrix.connect(mir_guide.offsetParentMatrix)

        mir_module.save_metadata()
        return  mir_module

    def mirror(self):
        """
        Default mirror method
        """
        name = self.name.replace(f'{self.side.side}_', f'{self.side.opposite}_')
        mir_module = self.__class__(name)

        # Do mirror connection for metadata
        self.metaNode.mirrored_to.connect(mir_module.metaNode.mirrored_from)

        mir_module.update_mirrored(source=self)

    def mirror_ctrls(self, source):
        # Mirror Ctrls
        # Get ctrl info
        ctrl_info = save_curve_info(source.all_ctrls)

        mir_ctrl_info = {}
        # Mirror the positions across the YZ plane
        for key, value in ctrl_info.items():
            mir_key = key.replace(f'{source.side.side}_', f'{self.side.side}_')

            mir_ctrl_info[mir_key] = value

            for i, point in enumerate(value['cvs']):
                x, y, z = point
                # Multiply x and z value by -1 to mirror across YZ plane
                mir_ctrl_info[mir_key]['cvs'][i] = (x * -1, y, z * -1)

        apply_curve_info(self.all_ctrls, mir_ctrl_info)


    def update_mirrored(self, destroy=False, source=None):
        """
        Update the mirrored module. This assumes it has already been destroyed, or started from scratch
        """
        if source is None:
            # Try and get the source from the metadata
            if self.mirrored_from is None:
                pm.warning(f"{self.name} has no mirrored source")
                return
            else:
                source = module_tools.createModule(self.mirrored_from)
        elif not isinstance(source, self.__class__):
            raise ValueError(f"Source must be of same type ({self.__class__})")

        if destroy:
            self.destroy_rig()

        self.joints = utils.mirrorJoints(source.joints, (self.side.opposite, self.side.side))

        self.rig()

        self.mirror_ctrls(source)

    def __str__(self):
        return str(self.__dict__)

