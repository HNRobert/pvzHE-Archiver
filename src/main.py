import base64
import json
import os.path
from threading import Thread

from b64icon import b64_icon
from const import (HE_ARCHIVER_DATA, HE_ARCHIVER_DATA_PATH,
                   HE_ARCHIVER_GAME_DATA_PATH, HE_ARCHIVER_ICON)
from global_var import gvar
from mods import has_archiver_process, read_json, scan_new_save
from ui import mk_ui


def main():
    if has_archiver_process():
        return

    gvar.set("continue_scanning", True)
    gvar.set("has_new_save", False)

    if not os.path.isdir(HE_ARCHIVER_DATA_PATH):
        os.makedirs(HE_ARCHIVER_DATA_PATH)
    if not os.path.isdir(HE_ARCHIVER_GAME_DATA_PATH):
        os.makedirs(HE_ARCHIVER_GAME_DATA_PATH)
    if not os.path.isfile(HE_ARCHIVER_ICON):
        with open(HE_ARCHIVER_ICON, "wb") as f:
            f.write(base64.b64decode(b64_icon))
    if not os.path.isfile(HE_ARCHIVER_DATA):
        with open(HE_ARCHIVER_DATA, 'w') as f:
            json.dump({}, f, indent=4)

    gvar.set("note_data", read_json(HE_ARCHIVER_DATA))

    scanning_thread = Thread(target=scan_new_save, daemon=True)
    scanning_thread.start()

    mk_ui()


if __name__ == "__main__":
    main()
