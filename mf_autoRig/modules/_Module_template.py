from mf_autoRig.modules.Module import Module
import pymel.core as pm
from mf_autoRig import utils
from mf_autoRig.utils import defaults as df

class _Template(Module):
    meta_args = {
        'creation_attrs': {
            **Module.meta_args['creation_attrs']
            # Here you add other creation attrs
        },

        'module_attrs': {
            **Module.meta_args['module_attrs'],
            # Here you add other module attrs
        },

        'config_attrs': {
            **Module.meta_args['config_attrs'],
            # Here you add other config attrs
            # Eg 'auto_clavicle': {'attributeType': 'bool'}
        },
        'info_attrs': {
            **Module.meta_args['info_attrs'],
            # Here you add other info attrs
            # eg. 'guides': {'attributeType': 'message', 'm': True},
            # eg. 'joints': {'attributeType': 'message', 'm': True},
            # eg. 'clavicle_ctrl': {'attributeType': 'message'},
        }
    }

    connectable_to = ['Spine'] # List of modules this module can connect to

    def __init__(self, name, meta=True):
        super().__init__(name, self.meta_args, meta)

        '''
        Here you define the attributes of the module

        self.auto_clavicle = False

        self.clavicle_ctrl = None
        self.joints = []
        self.guides = []

        self.control_grp = None
        self.joints_grp = None
        '''

        self.reset()

    def reset(self):
        super().reset()
        '''
        TODO: this might be deleted in the future. The usability of the function is in question
        Here you define the defaults of the attributes of the module
        
        self.auto_clavicle = False

        self.clavicle_ctrl = None
        self.joints = []
        self.guides = []

        '''

    def create_guides(self, pos=None):
        """
        Create guides usually takes a pos argument, which is a list/dict of xyz values
        """

        if pos is None:
            pos = [(0,0,0), (5,0,0)]

        # Create guide grp
        self.guide_grp = pm.createNode('transform', name=f'{self.name}_guide_grp')

        # Create guides
        self.guides = utils.create_guide_chain(self.name, 2, pos, parent=self.guide_grp)

        '''
        All guides are parented under the guide_grp. 
        You should be able to delete the guide_grp and all guides should be deleted
        '''

        # Save guides
        if self.meta:
            self.save_metadata()
    def create_joints(self):
        """
        Create joints from starting guides
        """

        self.joints = utils.create_joints_from_guides(self.name, self.guides,
                                                      aimVector=self.jnt_orient_main,
                                                      upVector=self.jnt_orient_secondary)

        pm.parent(self.joints[0], utils.get_group(df.joints_grp))

        #Save joints
        if self.meta:
            self.save_metadata()
