import re
import os
import shutil
import time
import json

from win32gui import FindWindow, ShowWindow

from levels_name_data import DATA as LEVEL_NAMES_DATA
from global_var import gvar
from const import HE_DATA_PATH, HE_ARCHIVER_DATA, USERS_DAT, ARCHED_DAT_PATTERN, HE_ARCHIVER_GAME_DATA_PATH, GAME_DAT_PATTERN


def has_archiver_process():
    hwnd = FindWindow(None, "植物大战僵尸杂交版-存档管理工具")
    if hwnd:
        try:
            ShowWindow(hwnd, 5)
            return True
        except Exception as e:
            print(e)
            return False
    return False


def read_json(filename):
    with open(filename, 'r') as file:
        return json.load(file)


def write_json(_data):
    with open(HE_ARCHIVER_DATA, 'w') as file:
        json.dump(_data, file, indent=4)


def parse_hex_data(hex_data):
    data = bytes.fromhex(hex_data)
    _user_info = {}

    total_users = int.from_bytes(data[4:6], byteorder='little')
    offset = 6

    for _ in range(total_users):
        user = {}
        username_length = int.from_bytes(
            data[offset:offset + 2], byteorder='little')
        offset += 2

        username = data[offset:offset + username_length].decode('ascii')
        user['username'] = username
        offset += username_length

        user_id = int.from_bytes(data[offset:offset + 4], byteorder='little')
        user['id'] = user_id
        offset += 4

        save_file_number = int.from_bytes(
            data[offset:offset + 2], byteorder='little')
        user['save_file_number'] = save_file_number
        offset += 4

        _user_info[str(save_file_number)] = user

    return _user_info


def get_user_info():
    hex_data = ""  # 读取文件，先解析成十六进制进行保存
    if not os.path.isfile(USERS_DAT):
        return {}
    with open(USERS_DAT, 'rb') as dat:
        while a := dat.read(1):  # 可以取得每一个十六进制, read（1）表示每次读取一个字节长度的数值
            if ord(a) <= 15:
                # 前面不加“0x0”就会变成eg:7 而不是 07
                hex_data += ("0x0" + hex(ord(a))[2:])[2:]
            else:
                hex_data += (hex(ord(a)))[2:]  # 最终得到的就是十六进制的字符串表示，便于后续处理

    _user_info = parse_hex_data(hex_data)
    return _user_info


def match_value_from_data_name(data_name):
    match = re.search(ARCHED_DAT_PATTERN, data_name)
    if match:
        user_arch_id = match.group(1)
        game_id = match.group(2)
        date_time = f"{match.group(3)}-{match.group(4)}"
        return {"user_arch_id": user_arch_id, "game_id": game_id, "date_time": date_time, "int_time": 0}
    return {"user_arch_id": "", "game_id": "", "date_time": "", "int_time": 0}


def level_name_of(str_id: str):
    int_id = int(str_id)
    if int_id < 512 and int_id >= 256:
        return f"冒险模式 第{str(int_id - 255)}关"
    if str_id in LEVEL_NAMES_DATA.keys() and "name" in LEVEL_NAMES_DATA[str_id].keys():
        return LEVEL_NAMES_DATA[str_id]["name"]


def list_arched_game_data():
    game_data_dict = {}
    current_d = os.listdir(HE_ARCHIVER_GAME_DATA_PATH) if os.path.isdir(
        HE_ARCHIVER_GAME_DATA_PATH) else []
    user_info = get_user_info()
    for file in current_d:  # add a data_name which replaces the user_arch_id and game_id
        file_info_dict = match_value_from_data_name(file)
        user_name = file_info_dict["user_arch_id"]
        level_name = level_name_of(file_info_dict["game_id"])
        d_t = file_info_dict["date_time"]
        if user_name in user_info.keys():
            user_name = user_info[user_name]["username"]
        date_time_label = d_t[:4] + "-" + d_t[4:6] + "-" + d_t[6:8] + " " + d_t[9:11] + ":" + d_t[11:13] + ":" + d_t[13:]
        file_info_dict["user_name"] = user_name
        file_info_dict["level_name"] = level_name
        file_info_dict["save_time"] = date_time_label
        file_info_dict["int_time"] = int(d_t[:8] + d_t[9:])
        game_data_dict[file] = file_info_dict
    return game_data_dict
    # {filename: {"user_arch_id": str, "game_id": str, "date_time": str, "data_name": str, "int_time": int}}


def get_data_mtime(_data_path):
    return time.strftime('%Y%m%d-%H%M%S', time.localtime(os.stat(_data_path).st_mtime))


def current_data_path_of(arched_data_name):
    m_value = match_value_from_data_name(arched_data_name)
    game_data_filename = f"game{m_value['user_arch_id']}_{m_value['game_id']}.dat"
    game_data_filepath = os.path.join(HE_DATA_PATH, game_data_filename)
    if (os.path.isfile(game_data_filepath) and
            get_data_mtime(game_data_filepath) == m_value["date_time"]):
        return game_data_filepath
    return None


def archive_data(_user_arch_id: str, _scene_id: str, _data_path: str):
    global n_s
    if not os.path.isfile(_data_path):
        return
    arched_filename = f"{_user_arch_id}-{_scene_id}-{get_data_mtime(_data_path)}.dat"
    arched_data_path = os.path.join(
        HE_ARCHIVER_GAME_DATA_PATH, arched_filename)
    if not os.path.isdir(HE_ARCHIVER_GAME_DATA_PATH):
        os.makedirs(HE_ARCHIVER_GAME_DATA_PATH)
    if not os.path.isfile(arched_data_path):
        n_s = True
        try:
            shutil.copy2(_data_path, arched_data_path)
            print(arched_data_path + " --> Success")
        except Exception as e:
            print(e)


def scan_new_save():
    prev_files = set()
    exist_time_counters = {}
    while gvar.get("continue_scanning"):
        if os.path.isdir(HE_DATA_PATH):
            gvar.set("game_exist", True)
        else:
            time.sleep(1)
            continue
        cur_files = set(os.listdir(HE_DATA_PATH))
        new_files = cur_files - prev_files
        dec_files = prev_files - cur_files
        for n_file in new_files:
            exist_time_counters[n_file] = 1
        for p_file in prev_files - dec_files:
            exist_time_counters[p_file] += 1
        for d_file in dec_files:
            exist_time_counters[d_file] = 0
        process_new_save(new_files)

        if dec_files:
            cur_f = dec_files.pop()
            match = re.search(GAME_DAT_PATTERN, cur_f)
            if match:
                set_current_gaming(match)

        prev_files = cur_files if not gvar.get("rescan_savings") else set()
        gvar.set("rescan_savings", False)
        time.sleep(1)


def process_new_save(_new_files):
    global has_new_save, n_s
    n_s = False
    for file in _new_files:
        match = re.search(GAME_DAT_PATTERN, file)
        if match:
            file_path = os.path.join(HE_DATA_PATH, file)
            user_arch_id = match.group(1)
            game_id = match.group(2)
            archive_data(user_arch_id, game_id, file_path)
    has_new_save = n_s


def set_current_gaming(match):
    global current_gaming
    user_num = match.group(1)
    game_id = match.group(2)
    current_gaming = {"user_num": user_num, "game_id": game_id}
