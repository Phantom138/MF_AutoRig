import pymel.core as pm
import pymel.core.datatypes as dt
from typing import Union

class VectorNodes:
    def __init__(self, attribute):
        self.attr = attribute

    def __add__(self, other):
        """
        Method that adds by creating a plusMinusAverage node

        Returns:
            VectorNodes: A new VectorNodes object with the output of the plusMinusAverage node.
        """
        plus_minus = pm.createNode('plusMinusAverage')

        self.attr.connect(plus_minus.input3D[0])
        other.attr.connect(plus_minus.input3D[1])

        return VectorNodes(plus_minus.output3D)

    def __sub__(self, other):
        """
        Method that subtracts by creating a plusMinusAverage node

        Returns:
            VectorNodes: A new VectorNodes object with the output of the plusMinusAverage node.
        """
        plus_minus = pm.createNode('plusMinusAverage')
        plus_minus.operation.set(2)

        self.attr.connect(plus_minus.input3D[0])
        other.attr.connect(plus_minus.input3D[1])

        return VectorNodes(plus_minus.output3D)

    def __mul__(self, other: Union['VectorNodes', tuple]):
        """
        Method that multiplies by creating a multiplyDivide node

        Returns:
            VectorNodes: A new VectorNodes object with the output of the multiplyDivide node.
        """
        multDivide = pm.createNode('multiplyDivide')
        self.attr.connect(multDivide.input1)

        if isinstance(other, tuple):
            multDivide.input2.set(other)
            return VectorNodes(multDivide.output)

        elif isinstance(other.attr, pm.Attribute):
            other.attr.connect(multDivide.input2)

        return VectorNodes(multDivide.output)

    def norm(self):
        """
        Method that normalizes the vector
        """
        norm = pm.createNode('vectorProduct')
        norm.operation.set(0) #Set operation mode to no operation
        norm.normalizeOutput.set(1)

        self.attr.connect(norm.input1)

        return VectorNodes(norm.output)
    @staticmethod
    def dotProduct(one, other):
        dot = pm.createNode('vectorProduct')
        dot.operation.set(1)

        one.attr.connect(dot.input1)
        other.attr.connect(dot.input2)

        return VectorNodes(dot.output)

# A_loc = pm.spaceLocator(name="A")
# A_loc.translate.set(0,10,0)
# B_loc = pm.spaceLocator(name="B")
# B_loc.translate.set(9,0,1)
# #
# A = VectorNodes(A_loc.translate)
# B = VectorNodes(B_loc.translate)
# AB = A + B
# AC = AB + B.norm()
#
# AB * (5,5,5)
# AB * AC

