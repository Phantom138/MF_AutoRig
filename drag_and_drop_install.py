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

def copyIcons(maya_path, source_path):
    icons = ["mf_colorPicker.png"]

    dest_icon_dir = os.path.join(maya_path, "prefs", "icons")

    for icon in icons:
        src_icon = os.path.join(source_path, icon)
        dest = shutil.copy(src_icon, dest_icon_dir)
        print(f"Icon {icon} copied to {dest}")

def addShelf(maya_path, source_path, forceInstall=False):
    shelf_name = "shelf_MF_Rigging_Tools.mel"
    shelf = shelf_name.replace(".mel", "")

    dest_shelf = os.path.join(maya_path, "prefs", "shelves", shelf_name)
    source_shelf = os.path.join(source_path, shelf_name)

    # If shelf already existing, don't install
    # Unless the force install is on, which will delete the shelf and install it again
    if os.path.isfile(dest_shelf):
        # Shelf is already installed
        cmds.warning("Shelf is already installed.")

        if forceInstall is False:
            del sys.modules["drag_and_drop_install"]
            return
        # Force delete shelf
        f = open(os.path.join(source_path, "force_deleteShelfTab.mel"), "r")
        script = f.read()
        mel.eval(script)
        mel.eval(f'force_deleteShelfTab {shelf.replace("shelf_", "")}')

    shutil.copy(source_shelf, dest_shelf)
    mel.eval(f'loadNewShelf {shelf}')
    print("Shelf installed.")

def add_directory_to_user_setup(maya_path, source_dir):
    # HACK: Add path to sys path just so restarting maya is not required
    # It is best to restart maya!!
    sys.path.append(source_dir)

    scripts_path = os.path.join(maya_path, "scripts")
    userSetup = os.path.join(scripts_path, "userSetup.py")

    append_path = f"sys.path.append('{source_dir}')"

    # Creates userSetup.py if it doesn't exist
    if not os.path.isfile(userSetup):
        f = open(userSetup, "w")
        f.close()

    # Read the file
    f = open(userSetup, "r")
    content = f.read()
    f.close()

    # Check if the path is already in the file
    if append_path not in content:
        # Switch to append mode
        f = open(userSetup, "a")

        f.write("\nimport sys\n")
        f.write(append_path)
        f.close()

        print(f"Added {source_dir} to userSetup.py")
    else:
        cmds.warning(f"{source_dir} is already in userSetup.py")

def onMayaDroppedPythonFile(*args):
    doc_path = get_documents_path()
    maya_version = cmds.about(version=True)

    # Get the source directory
    try:
        source_dir = os.path.dirname(__file__)
    except:
        source_dir = "MF_AutoRig"

    # Get maya path and source path for icon and shelf
    source_path = os.path.normpath(os.path.join(source_dir, f"mf_autoRig/maya_shelf/"))
    maya_path = os.path.join(doc_path, "maya", maya_version)

    copyIcons(maya_path, source_path)
    addShelf(maya_path, source_path, forceInstall=True)
    add_directory_to_user_setup(maya_path, source_dir)

    del sys.modules["drag_and_drop_install"]

