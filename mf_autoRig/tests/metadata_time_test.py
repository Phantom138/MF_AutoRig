from unload_packages import unload_packages
unload_packages(silent=True, packages=["mf_autoRig"])
from mf_autoRig.modules.Body import Body
import mf_autoRig.lib.defaults as df
import maya.cmds as cmds

from datetime import datetime
import time

def test_func(meta):
    test = Body(meta=meta)
    test.create_guides(df.default_pos)
    test.create_joints()
    test.rig()

if __name__ == '__main__':
    cmds.file(new=True, f=True)
    # Start time
    time.sleep(3)
    start = datetime.now()

    test_func(True)

    # End time
    run_time = datetime.now() - start
    print(f'Running Body with metadata took {run_time}')

    cmds.file(new=True, f=True)

    # Start time
    time.sleep(7)
    start = datetime.now()

    test_func(False)

    # End time
    run_time = datetime.now() - start
    print(f'Running Body without metadata took {run_time}')