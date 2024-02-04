class Side:
    def __init__(self, side: str):
        self.side = side

        left = ['L', 'l', 'Left', 'left']
        right = ['R', 'r', 'Right', 'right']
        mid = ['M', 'm', 'Middle', 'middle']

        if side in left:
            self.opposite = right[left.index(side)]
        elif side in right:
            self.opposite = left[right.index(side)]
        elif side in mid:
            pass
        else:
            raise ValueError(f'Side not named properly -> {side}')

    def __str__(self):
        return self.side

    def __eq__(self, other):
        return self.side == other