from __future__ import absolute_import
try:
    from PySide2 import QtCore
except ImportError:
    from PySide import QtCore


class SingletonMetaclass(type):
    '''Basic Singleton metaclass'''
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            # print 'Init - CALL:', cls
            cls._instances[cls] = super(SingletonMetaclass, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class QtSingletonMetaclass(SingletonMetaclass, type(QtCore.QObject)):
    '''QObject-Compatible singleton metaclass'''
    pass
