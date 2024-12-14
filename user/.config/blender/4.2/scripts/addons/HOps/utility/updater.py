import re
import requests

import bpy

from .. utility import addon

update_url = 'https://api.github.com/repos/teamcsharp/HardOps-updater/tags'

version_regex = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+")
def check_for_update(current_version):
    if not addon.preference().check_update: return

    # TODO: this should be stored in transient storage, like window_manager, so
    # that we don't need to clear it here
    addon.preference().needs_update = ""

    try:
        response = requests.get(update_url, timeout=6)
        if response.status_code == 200:
            resp_json = response.json()
            versions = list()
            for tag in resp_json:
                name = tag['name']
                if version_regex.match(name):
                    versions.append(name)
            latest_version_str = sorted(versions, reverse=True)[0]

            current_version_str = '.'.join(map(str, list(current_version)))
            if str(current_version_str) != str(latest_version_str):
                needs_update = f"HardOps {latest_version_str} available!"
                print(needs_update)
                addon.preference().needs_update = needs_update
        else:
            raise Exception

    except:
        addon.preference().needs_update = 'Connection Failed'
