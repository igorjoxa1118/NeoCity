#!/bin/python3

import subprocess
import libcalamares
from pathlib import Path

root_mount_point = libcalamares.globalstorage.value("rootMountPoint")

def run():
    """
    Installing base system!
    """

    try:
     subprocess.call(['rm', '/tmp/chroot_path.tmp'])
     with open('/tmp/chroot_path.tmp', 'w') as file:
      root_mount_point = libcalamares.globalstorage.value("rootMountPoint")
      file.write(root_mount_point)
      file.close()
    except:
     pass

    GET_PACSTRAP = "curl -s -Lo /tmp/pacstrap.sh https://raw.githubusercontent.com/virOS/virOS-sh/master/pacstrap.sh"
    PAC_STRAP = "sh /tmp/pacstrap.sh"

    try:
        subprocess.call(GET_PACSTRAP.split(' '))
        subprocess.call(PAC_STRAP.split(' '))
    except:
        pass
