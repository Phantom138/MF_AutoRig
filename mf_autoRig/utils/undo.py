import pymel.core as pm

class UndoStack(object):
    def __init__(self, name="actionName"):
        self.name = name

    def __enter__(self):
        pm.undoInfo(openChunk=True, chunkName=self.name, infinity=True)

    def __exit__(self, *exc_info):
        pm.undoInfo(closeChunk=True)
