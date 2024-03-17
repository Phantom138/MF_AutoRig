import os
import shutil
import winreg
import maya.cmds as cmds
import maya.mel as mel
import sys
import filecmp

def get_documents_path():
    key = winreg.HKEY_CURRENT_USER
    subkey = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
    value_name = "Personal"
    try:
        with winreg.OpenKey(key, subkey) as reg_key:
            value, _ = winreg.QueryValueEx(reg_key, value_name)
            return value
    except FileNotFoundError:
        print("Registry key not found.")
    except PermissionError:
        print("Permission denied to access the registry.")
    except Exception as e:
        print(f"An error occurred: {e}")

def onMayaDroppedPythonFile(*args):
    doc_path = get_documents_path()
    maya_version = cmds.about(version=True)

    shelf_name = "shelf_MF_Rigging_Tools.mel"
    shelf = shelf_name.replace(".mel", "")

    dest_shelf = os.path.join(doc_path, "maya", maya_version, "prefs", "shelves", shelf_name)

    try:
        source_dir = os.path.dirname(__file__)
    except:
        source_dir = "MF_AutoRig"
    source_shelf = os.path.normpath(os.path.join(source_dir, f"mf_autoRig/maya_shelf/{shelf_name}"))


    if os.path.isfile(dest_shelf) and filecmp.cmp(source_shelf, dest_shelf):
        # Shelf is already installed
        cmds.error("Shelf is already installed.")

        del sys.modules["drag_and_drop_install"]
        return

    shutil.copy(source_shelf, dest_shelf)
    mel.eval(f'loadNewShelf {shelf}')
    print("Shelf installed.")

    del sys.modules["drag_and_drop_install"]

