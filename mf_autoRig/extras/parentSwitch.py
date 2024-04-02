import re
import pymel.core as pm
import pymel.core.datatypes as dt

def get_base_name(name):
    search = re.search('[A-Za-z]', name)
    return search.group(1)


def parent_switch_locators(object, drivers, hasGroup=True):
    # Get nice name for object
    object_match = re.search(r'^[a-zA-Z]_*[a-zA-Z]+\d*', object.name())
    object_name = object_match.group(0)

    # Create Locators
    locators = []
    enum_names = ''

    if hasGroup:
        grp = object.getParent(1)
    else:
        grp = object

    for driver in drivers:
        # Get nice name for drivers, to be used in enum
        # If it has a prefix, take only what is after
        if re.search(r'^[a-zA-Z]_', driver.name()):
            print(f'{driver.name()} starts with prefix')
            driver_match = re.search(r'^[a-zA-Z]_([a-zA-Z]+\d*)', driver.name())
            driver_name = driver_match.group(1)
        else:
            driver_match = re.search('^([a-zA-Z]+)_', driver.name())
            driver_name = driver_match.group(1)

        enum_names += driver_name+':'

        # Create locator and parent it in the right place
        loc = pm.spaceLocator(name=f'{object_name}_{driver_name}_space_loc')
        pm.matchTransform(loc, drivers[0])
        pm.parent(loc, driver)
        locators.append(loc)

    # Create enum attributes, enum_names = Root:World:...
    pm.addAttr(object, ln='parentSwitch', attributeType='enum', en=enum_names, k=True)

    # Create parent constraint
    print(locators)
    constraint = pm.parentConstraint(locators, grp, maintainOffset=True)
    weights = constraint.getWeightAliasList()

    for index, weight in enumerate(weights):
        # Get weight name for the condition
        weight_match = re.search(r'([a-zA-Z]+_[a-zA-Z]+)_space_loc', weight.name())
        weight_name = weight_match.group(1)

        # Create condition and connect it accordingly
        condition = pm.createNode('condition', name=weight_name+'_condition')

        object.parentSwitch.connect(condition.firstTerm)

        condition.secondTerm.set(index)
        condition.colorIfTrueR.set(1)
        condition.colorIfFalseR.set(0)
        condition.outColorR.connect(weight)


def parent_switch_matrix(obj, drivers, names=None):
    """
    Creates a parent switch using matrix multiplication, this is a much cleaner way of doing it, compared to the locator method.

    Originally from: https://www.chadvernon.com/blog/space-switching-offset-parent-matrix/
    This only works in maya 2020 or onwards

    @param obj: The object to be parent switched
    @param drivers: The objects that will drive the parent switching
    @param names: The names of the drivers, if not provided, it will use the drivers names
    """
    switch_name = 'spaceSwitch'

    # If it has switch attribute already, it attempts to connect to the existing switch and to the existing blend matrix
    if pm.hasAttr(obj, switch_name):
        pm.warning(f'{obj.name()} already has spaceSwitch attribute, trying to connect the drivers to it')

        # Get enum_names
        enum_names = pm.attributeQuery(switch_name, node=obj, listEnum=True)[0]
        offset = len(enum_names.split(':'))

        enum_names += ':' # Add a colon to separate the new names
        has_switch = True
    else:
        enum_names = ''
        offset = 0
        has_switch = False

    # Generate names for enum
    if names is None:
        # Get names from drivers
        for driver in drivers:
            enum_names += driver.name() + ':'
    else:
        # Length of names and drivers must be the same
        if len(names) != len(drivers):
            pm.error("Names and drivers must be the same length")

        for name in names:
            enum_names += name + ':'

    # Get or create blend and switch for connecting later
    if has_switch:
        # Try and get the blend matrix node
        inputs = obj.offsetParentMatrix.inputs(type='blendMatrix')
        if len(inputs) == 1:
            blend = inputs[0]
        else:
            pm.error(f'{obj.name()} has no offsetParentMatrix attribute, please remove the spaceSwitch attribute')
            return

        # Add new enum names
        switch = obj.attr(switch_name)
        pm.addAttr(switch, e=True, en=enum_names)

    else:
        # Create blend and switch
        blend = pm.createNode("blendMatrix", name=f'{obj.name()}_spaceSwitch_blend')

        # Connect blend to object
        blend.outputMatrix.connect(obj.offsetParentMatrix)

        # Add enum attribute for object
        pm.addAttr(obj, ln=switch_name, attributeType='enum', en=enum_names, k=True)
        switch = obj.attr(switch_name)

    # Do the switch
    for i, driver in enumerate(drivers):
        # Offset i
        index = i+offset

        mtx = _get_matrices(obj, driver)

        # Connect the result to blend
        mtx.matrixSum.connect(blend.target[index].targetMatrix)

        _connect_to_switch(switch, blend, index)

def _get_matrices(obj, driver):
    # Multiply matrices
    mult = pm.createNode("multMatrix")

    # Get the offset matrix
    offset = dt.Matrix(obj.worldMatrix[0].get())
    offset *= dt.Matrix(obj.matrix.get()).inverse()
    offset *= dt.Matrix(driver.worldInverseMatrix[0].get())

    mult.matrixIn[0].set(offset, type="matrix")
    driver.worldMatrix[0].connect(mult.matrixIn[1])

    parent = obj.getParent(1)
    if parent is not None:
        parent.worldInverseMatrix[0].connect(mult.matrixIn[2])

    return mult

def _connect_to_switch(switch, blend, index):
    # Connect blend to enum using condition nodes
    condition = pm.createNode('condition')

    switch.connect(condition.firstTerm)

    condition.secondTerm.set(index)
    condition.colorIfTrueR.set(1)
    condition.colorIfFalseR.set(0)
    condition.outColorR.connect(blend.target[index].weight)




child = pm.PyNode('L_arm03_ik_ctrl')
driverss = [pm.PyNode("M_spine02_ctrl")]

parent_switch_matrix(child, driverss)
