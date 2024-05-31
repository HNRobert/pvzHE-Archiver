import base64
import os.path
import re
import shutil
import time
import tkinter as tk
import tkinter.font as tk_font
import tkinter.messagebox as tk_messagebox
from threading import Thread
from tkinter import Tk, ttk

from win32gui import FindWindow, ShowWindow

from b64icon import b64_icon
from levels_name_data import DATA as LEVEL_NAMES_DATA

import json

HE_ARCHIVER_DATA_PATH = "C:\\ProgramData\\pvzHEArchiver"
HE_ARCHIVER_DATA = os.path.join(HE_ARCHIVER_DATA_PATH, "data.json")
HE_ARCHIVER_ICON = os.path.join(HE_ARCHIVER_DATA_PATH, "icon.ico")
HE_ARCHIVER_GAME_DATA_PATH = os.path.join(HE_ARCHIVER_DATA_PATH, "game_data")

HE_DATA_PATH = "C:\\ProgramData\\PopCap Games\\PlantsVsZombies\\pvzHE\\yourdata"
USERS_DAT = os.path.join(HE_DATA_PATH, "users.dat")


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


def write_note_data():
    with open(HE_ARCHIVER_DATA, 'w') as file:
        json.dump(note_data, file, indent=4)


def parse_hex_data(hex_data):
    data = bytes.fromhex(hex_data)
    _user_info = {}

    total_users = int.from_bytes(data[4:6], byteorder='little')
    offset = 6

    for _ in range(total_users):
        user = {}
        username_length = int.from_bytes(data[offset:offset + 2], byteorder='little')
        offset += 2

        username = data[offset:offset + username_length].decode('ascii')
        user['username'] = username
        offset += username_length

        user_id = int.from_bytes(data[offset:offset + 4], byteorder='little')
        user['id'] = user_id
        offset += 4

        save_file_number = int.from_bytes(data[offset:offset + 2], byteorder='little')
        user['save_file_number'] = save_file_number
        offset += 4

        _user_info[str(save_file_number)] = user

    return _user_info


def get_user_info():
    hex_data = ""  # 读取文件，先解析成十六进制进行保存
    with open(USERS_DAT, 'rb') as dat:
        while a := dat.read(1):  # 可以取得每一个十六进制, read（1）表示每次读取一个字节长度的数值
            if ord(a) <= 15:
                hex_data += ("0x0" + hex(ord(a))[2:])[2:]  # 前面不加“0x0”就会变成eg:7 而不是 07
            else:
                hex_data += (hex(ord(a)))[2:]  # 最终得到的就是十六进制的字符串表示，便于后续处理

    _user_info = parse_hex_data(hex_data)
    return _user_info


def match_value_from_data_name(data_name):
    pattern = r"(\d+)-(\d+)-(\d+)-(\d+)\.dat"
    match = re.search(pattern, data_name)
    if match:
        user_arch_id = match.group(1)
        game_id = match.group(2)
        date_time = f"{match.group(3)}-{match.group(4)}"
        return {"user_arch_id": user_arch_id, "game_id": game_id, "date_time": date_time}
    return {"user_arch_id": "", "game_id": "", "date_time": ""}


def list_arched_game_data():
    game_data_dict = {}
    current_d = os.listdir(HE_ARCHIVER_GAME_DATA_PATH)
    for file in current_d:  # add a data_name which replaces the user_num and game_id
        file_info_dict = match_value_from_data_name(file)
        user_name, level_name = file_info_dict["user_arch_id"], file_info_dict["game_id"]
        if file_info_dict["user_arch_id"] in user_info.keys():
            user_name = user_info[file_info_dict["user_arch_id"]]["username"]
        if file_info_dict["game_id"] in LEVEL_NAMES_DATA.keys():
            level_name = LEVEL_NAMES_DATA[file_info_dict["game_id"]]
        file_info_dict["data_name"] = f"{user_name}-{level_name}-{file_info_dict['date_time']}"
        game_data_dict[file] = file_info_dict
    return game_data_dict  # {filename: {"user_num": "", "game_id": "", "date_time": "", "data_name": ""}}


def archive_data(_user_arch_id: str, _scene_id: str, _data_path: str):
    if not os.path.isfile(_data_path):
        return
    data_mtime = time.strftime('%Y%m%d-%H%M%S', time.localtime(os.stat(_data_path).st_mtime))
    arched_filename = f"{_user_arch_id}-{_scene_id}-{data_mtime}.dat"
    arched_data_path = os.path.join(HE_ARCHIVER_GAME_DATA_PATH, arched_filename)
    if not os.path.isdir(HE_ARCHIVER_GAME_DATA_PATH):
        os.makedirs(HE_ARCHIVER_GAME_DATA_PATH)
    if not os.path.isfile(arched_data_path):
        shutil.copy2(_data_path, arched_data_path)


def scan_new_save():
    pattern = r"game(\d+)_(\d+)\.dat"
    prev_files = set()

    while continue_scanning:
        cur_files = set(os.listdir(HE_DATA_PATH))
        new_files = cur_files - prev_files
        dec_files = prev_files - cur_files
        if new_files:
            for file in new_files:
                match = re.search(pattern, file)
                if match:
                    file_path = os.path.join(HE_DATA_PATH, file)
                    print(file_path)
                    user_arch_id = match.group(1)
                    game_id = match.group(2)
                    archive_data(user_arch_id, game_id, file_path)

        if dec_files:
            cur_f = dec_files.pop()
            match = re.search(pattern, cur_f)
            if match:
                set_current_gaming(match)

        prev_files = cur_files
        time.sleep(1)


def set_current_gaming(match):
    global current_gaming
    user_num = match.group(1)
    game_id = match.group(2)
    current_gaming = {"user_num": user_num, "game_id": game_id}


def mk_ui():
    def save_data():
        global note_data
        for _t in current_game_data.keys():
            note_data[_t] = current_game_data[_t]["note"]
        write_note_data()
        save_btn.config(text="成功!")
        root.after(1000, lambda: save_btn.config(text="保存"))

    def extract_data(data_filename: str):
        arched_data_path = os.path.join(HE_ARCHIVER_GAME_DATA_PATH, data_filename)
        matched_values = match_value_from_data_name(data_filename)
        _user_arch_id, _scene_id = matched_values["user_arch_id"], matched_values["game_id"]
        ori_data_path = os.path.join(HE_DATA_PATH, f"game{_user_arch_id}_{_scene_id}.dat")
        try:
            shutil.copy2(arched_data_path, ori_data_path)
            savings_extract_button_dict[data_filename].config(text="成功!")
            root.after(1000, lambda: savings_extract_button_dict[data_filename].config(text="提取"))
        except Exception as e:
            print(e)
            savings_extract_button_dict[data_filename].config(text="提取出错")
            root.after(1000, lambda: savings_extract_button_dict[data_filename].config(text="提取"))

    def refresh_game_data():
        nonlocal current_game_data
        _arched_game_data = list_arched_game_data()
        for _data in _arched_game_data.keys():
            _arched_game_data[_data]["note"] = ""  # add note into the dict
            if _data in note_data.keys():
                _arched_game_data[_data]["note"] = note_data[_data]
        current_game_data = _arched_game_data
        place_lines()

    def place_lines():
        # place the savings in the root
        for _saving in current_game_data.keys():
            savings_name_label_dict[_saving] = ttk.Label(saving_frame, text=current_game_data[_saving]["data_name"])
            savings_note_dict[_saving] = ttk.Entry(saving_frame)
            savings_note_dict[_saving].insert(0, current_game_data[_saving]["note"])
            savings_extract_button_dict[_saving] = ttk.Button(
                saving_frame, text='提取', command=lambda _tar=_saving: extract_data(_tar))
            savings_remove_button_dict[_saving] = ttk.Button(
                saving_frame, text='删除', command=lambda _tar=_saving: remove_line(_tar))
        rearrange_lines()

    def rearrange_lines():
        for _index, _target in enumerate(savings_name_label_dict.keys()):
            savings_name_label_dict[_target].grid(
                row=_index + 1, column=0, padx=5, pady=2, sticky='NSEW')
            savings_note_dict[_target].grid(row=_index + 1, column=1, padx=5, pady=2, sticky='NSEW')
            savings_remove_button_dict[_target].grid(row=_index + 1, column=2, padx=4, pady=2, sticky='NSEW')
        resize_root()

    def remove_line(_saving):
        # Check if the button is in the "Sure?" state, if yes, delete the line and reset the button state
        if rm_button_state_dict.get(_saving, False):
            # Delete the line and reset the button state
            savings_extract_button_dict[_saving].destroy()
            savings_remove_button_dict[_saving].destroy()
            savings_note_dict[_saving].destroy()
            rm_button_state_dict.pop(_saving, None)
            if _saving in rm_button_timer_dict:
                root.after_cancel(rm_button_timer_dict[_saving])
                rm_button_timer_dict.pop(_saving)
            savings_remove_button_dict.pop(_saving, None)
            savings_extract_button_dict.pop(_saving, None)
            savings_note_dict.pop(_saving, None)
            savings_name_label_dict.pop(_saving, None)
            rearrange_lines()
        else:
            # Set the button to "Sure?" state
            savings_remove_button_dict[_saving].config(text="确定?")
            rm_button_state_dict[_saving] = True

            # Set a timer, if no more action in 3 sec then reset
            if _saving in rm_button_timer_dict:
                root.after_cancel(rm_button_timer_dict[_saving])

            rm_button_timer_dict[_saving] = root.after(3000, reset_button, _saving)

    def reset_button(_target):
        if _target in savings_remove_button_dict:
            savings_remove_button_dict[_target].config(text="删除")
            rm_button_state_dict[_target] = False
            rm_button_timer_dict.pop(_target, None)

    def resize_root():
        current_line_count = len(current_game_data)
        root.rowconfigure(1, weight=1, minsize=31 * int(bool(current_line_count)) - 5)
        root.minsize(width=800, height=140)
        root.geometry(
            f"{root.winfo_width()}x{min(max(24 * current_line_count + 190, root.winfo_height()), 600)}")
        for t_col in range(4):
            save_col_list[t_col].grid_configure(rowspan=current_line_count + 1)
        for f_col in range(3):
            save_final_row_sep[f_col].grid_configure(row=current_line_count + 1)

    def resize_canvas(event):
        # Update canvas' scroll region to match the actual size
        canvas_width = event.width
        saving_canvas.itemconfig(canvas_window, width=canvas_width)
        saving_canvas.config(scrollregion=saving_canvas.bbox("all"))

    def processwheel(event):
        a = int(-event.delta)
        if a > 0:
            saving_canvas.yview_scroll(1, tk.UNITS)
        else:
            saving_canvas.yview_scroll(-1, tk.UNITS)

    def exit_program():
        global continue_scanning
        continue_scanning = False
        root.quit()
        root.destroy()

    root = Tk()
    root.title('植物大战僵尸杂交版 存档管理工具')
    root.iconbitmap(HE_ARCHIVER_ICON)
    root.geometry("600x100")
    root.protocol('WM_DELETE_WINDOW', exit_program)
    """
    root.attributes('-topmost', True)
    root.attributes('-topmost', False)
    root.update_idletasks()
    """
    tkfont = tk_font.nametofont("TkDefaultFont")
    tkfont.config(family='Microsoft YaHei UI')
    root.option_add("*Font", tkfont)

    savings_name_label_dict = {}
    savings_note_dict = {}
    savings_extract_button_dict = {}
    savings_remove_button_dict = {}

    rm_button_state_dict = {}
    rm_button_timer_dict = {}

    savings_notice_label = ttk.Label(root, text='存档栏:')
    savings_notice_label.grid(row=0, column=0, padx=10, pady=5, sticky='NSEW')

    saving_label_frame = tk.LabelFrame(root, relief=tk.GROOVE)
    saving_label_frame.grid(row=1, column=0, padx=11, columnspan=2, sticky='NSEW')
    saving_label_frame.bind_all("<MouseWheel>", processwheel)
    saving_label_frame.columnconfigure(0, weight=1, minsize=200)
    saving_label_frame.rowconfigure(0, weight=1)

    saving_canvas = tk.Canvas(saving_label_frame)
    saving_canvas.config(highlightthickness=0)
    saving_canvas.grid(row=0, column=0, columnspan=1, sticky="NSEW")

    saving_frame = ttk.Frame(saving_canvas)
    saving_frame.columnconfigure(0, weight=1, minsize=200)

    saving_canvas_scrollbar = ttk.Scrollbar(saving_label_frame, orient=tk.VERTICAL)
    saving_canvas_scrollbar.grid(row=0, column=1, sticky="NSEW")
    saving_canvas_scrollbar.config(command=saving_canvas.yview)

    saving_canvas.config(yscrollcommand=saving_canvas_scrollbar.set)
    canvas_window = saving_canvas.create_window((0, 0), window=saving_frame, anchor='nw')
    saving_canvas.bind("<Configure>", resize_canvas)

    save_col_list = []
    save_final_row_sep = []
    for col in range(4):
        save_col_list.append(ttk.Separator(saving_frame, orient="vertical"))
        save_col_list[-1].grid(row=0, rowspan=1, column=col, sticky='NSEW')
    for col in range(6):
        tar_first_row_sep = ttk.Separator(saving_frame, orient='horizontal')
        tar_first_row_sep.grid(row=col // 3, column=col % 3, padx=1, sticky='NSEW')
    for col in range(3):
        save_final_row_sep.append(ttk.Separator(saving_frame, orient="horizontal"))
        save_final_row_sep[-1].grid(row=0, column=col, padx=1, sticky='NSEW')

    savings_name_label = ttk.Label(saving_frame, text="存档用户名-关卡名称(代号)-日期-时间")
    savings_name_label.grid(row=0, column=0, pady=5)
    savings_arg_label = ttk.Label(saving_frame, text="备注")
    savings_arg_label.grid(row=0, column=1, pady=5)
    savings_del_label = ttk.Label(saving_frame, text="删除")
    savings_del_label.grid(row=0, column=2, pady=5)

    refresh_button = ttk.Button(root, text='Refresh', command=refresh_game_data())
    refresh_button.grid(row=2, column=0, columnspan=3, padx=10, ipadx=5,
                        pady=5, sticky='NSEW')
    close_btn = ttk.Button(root, text='Exit', command=exit_program)
    close_btn.grid(row=3, column=0, padx=10, ipadx=5, pady=5, sticky='NSEW')
    save_btn = ttk.Button(root, text='Save & Apply', command=save_data)
    save_btn.grid(row=3, column=1, columnspan=2, padx=10, ipadx=25, pady=5,
                  sticky='NSEW')
    root.bind_all('<Return>', lambda event: save_data())
    root.bind_all('<Control-s>', lambda event: save_data())
    root.grid_columnconfigure(1, weight=1, minsize=200)

    current_game_data = {}
    refresh_game_data()

    about_text = """作者：Robert He
更新时间：2024年6月1日

本软件适用于植物大战僵尸杂交版的
【游戏存档时间轴管理】，
可以自动在无尽模式进入下一个关卡时保存游戏进度，
并在历史任意关卡的任何时间节点重新切入。

当前软件为测试版，后续将继续更新"""

    main_menu = tk.Menu(root)
    help_menu = tk.Menu(main_menu, tearoff=False)
    help_menu.add_command(label="关于",
                          command=lambda: tk_messagebox.showinfo(title="关于pvzHE-Archiver", message=about_text))
    main_menu.add_cascade(label="帮助", menu=help_menu)
    root.config(menu=main_menu)
    root.mainloop()


def main():
    global continue_scanning, user_info, note_data
    if has_archiver_process():
        return

    continue_scanning = True
    user_info = get_user_info()

    if not os.path.isdir(HE_ARCHIVER_DATA_PATH):
        os.makedirs(HE_ARCHIVER_DATA_PATH)
    if not os.path.isfile(HE_ARCHIVER_ICON):
        with open(HE_ARCHIVER_ICON, "wb") as f:
            f.write(base64.b64decode(b64_icon))
    if not os.path.isfile(HE_ARCHIVER_DATA):
        with open(HE_ARCHIVER_DATA, 'w') as f:
            json.dump({}, f, indent=4)

    note_data = read_json(HE_ARCHIVER_DATA)

    scanning_thread = Thread(target=scan_new_save, daemon=True)
    scanning_thread.start()

    mk_ui()


if __name__ == "__main__":
    main()
