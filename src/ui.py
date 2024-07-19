import os
import shutil
import time
import tkinter as tk
import tkinter.filedialog as tk_filedialog
import tkinter.font as tk_font
import tkinter.messagebox as tk_messagebox
import winreg
from threading import Thread
from tkinter import Tk, ttk
from typing import List

import mods
from ComBoPicker import Combopicker
from const import HE_ARCHIVER_GAME_DATA_PATH, HE_ARCHIVER_ICON, HE_DATA_PATH
from global_var import gvar
from widgetable import WidColData, WidgetTable, WidRowData

WIN_SHELL_KEY = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders')
DESKTOP_PATH = winreg.QueryValueEx(WIN_SHELL_KEY, "Desktop")[0]
FILTER_KEYS = ["用户名", "关卡名称", "保存时间", "备注"]

TIME_FILTER_DICT = {
    "<1分钟": 60, 
    "<1小时": 3600, 
    "<12小时": 3600*12, 
    "<1天": 3600*24,
    "<1周": 3600*24*7, 
    "<1月": 3600*24*31, 
    "<1年": 3600*24*365, 
    "不限": float('inf')
    }

NOTE_FILTER_DICT = {
    "有备注": True, 
    "无备注": False, 
    "不限": None
    }

SORT_BASIS_DICT = {
    "用户名": ["user_name", lambda x: x],
    "关卡名称": ["level_name", lambda x: x],
    "保存时间": ["save_time", lambda x: x],
    "备注内容": ["note", lambda x: x],
    "备注长度": ["note", lambda x: len(x)]
    }

SORT_REVERSE_DICT = {
    "正序": False,
    "倒序": True
}


def mk_ui():
    def read_column_input(column_data: WidColData):
        return saving_data_table.get_column_input(column_data)

    def save_note():
        """
        _note_data: dict = gvar.get("note_data")
        for _t in arched_game_data.keys():
            c_note = savings_note_dict[_t].get()
            arched_game_data[_t]["note"] = c_note
            _note_data[_t] = c_note
        """
        _note_data = read_column_input(save_note_col)
        gvar.set("note_data", _note_data)
        mods.write_json(_note_data)
        save_btn.config(text="成功!")
        root.after(1000, lambda: save_btn.config(text="保存备注"))

    def checking_new_save():
        while gvar.get("continue_scanning"):
            if gvar.get("has_new_save"):
                refresh_game_data()
                gvar.set("has_new_save", False)
            time.sleep(1)

    # Here, data_filename is exactly the id of the row
    def extract_data(data_filename: str):
        arched_data_path = os.path.join(
            HE_ARCHIVER_GAME_DATA_PATH, data_filename)
        matched_values = mods.match_value_from_data_name(data_filename)
        _user_arch_id, _scene_id = matched_values["user_arch_id"], matched_values["game_id"]
        ori_data_path = os.path.join(
            HE_DATA_PATH, f"game{_user_arch_id}_{_scene_id}.dat")
        shutil.copy2(arched_data_path, ori_data_path)
        print(arched_data_path, "Successfully extracted")

    def refresh_game_data(rescan=False):
        _note_data = gvar.get("note_data")
        if rescan:
            gvar.set("rescan_savings", True)
            refresh_button.config(text="刷新成功!")
            root.after(1500, lambda: refresh_button.config(text="刷新"))
        _arched_game_data = mods.list_arched_game_data()
        _save_rows_data: List[WidRowData] = []
        savings_filter_user_box.update_values([])
        savings_filter_user_box.entry_var.set("")
        savings_filter_level_box.update_values([])
        savings_filter_level_box.entry_var.set("")
        for _data in _arched_game_data.keys():
            # add note into the dict
            _arched_game_data[_data]["note"] = ""
            if _data in _note_data.keys():
                _arched_game_data[_data]["note"] = _note_data[_data]
            _save_rows_data.append(WidRowData(
                id=_data, cols_data=save_columns_data, data_storage=_arched_game_data[_data]))
            # save_rows_data[-1].wid_value_info
            savings_filter_user_box.append_value(_arched_game_data[_data]["user_name"])
            savings_filter_level_box.append_value(_arched_game_data[_data]["level_name"])

        saving_data_table.update_rows_data(_save_rows_data)

    def set_filter_key():
        key_filter = {
            "user_name": savings_filter_user_box.get().split('|'),
            "level_name": savings_filter_level_box.get().split('|')
        }
        comp_filter = {
            "time_limit": time_limit_var.get(),
            "note":  note_state_var.get()
        }

        def filter_func(data: WidRowData):
            for item in key_filter.items():
                if item[1] == [""]:
                    return False
                if data.data_storage[item[0]] not in item[1]:
                    return False
            if time.time() - data.data_storage["abs_int_time"] > comp_filter["time_limit"]:
                return False
            target_note_state = NOTE_FILTER_DICT[comp_filter["note"]]
            if not (target_note_state is None) and \
                bool(len(data.data_storage["note"])) != target_note_state:
                return False
            return True
        
        saving_data_table.set_filter_algo(filter_func)

    def set_sort_key():
        _reverse = SORT_REVERSE_DICT[savings_reverse_box.get()]
        _sort_basis =  SORT_BASIS_DICT[savings_sort_box.get()][0]
        _sort_func = SORT_BASIS_DICT[savings_sort_box.get()][1]
        def sort_key(data: WidRowData):
            return _sort_func(data.data_storage[_sort_basis])
        saving_data_table.set_sort_method(sort_key, _reverse)

    def resize_root():
        current_line_count = len(saving_data_table.rows_data)
        root.rowconfigure(2, weight=1, minsize=31 *
                          int(bool(current_line_count)) - 5)
        root.minsize(width=800, height=140)
        root.geometry(
            f"{root.winfo_width()}x{min(max(24 * current_line_count + 190, root.winfo_height()), 600)}")

    def toggle_del_selection_mode():
        nonlocal select_mode
        if saving_data_table.select_mode:
            items = saving_data_table.get_selected_rows()
            succ_rm_savings = []
            fail_rm_savings = []
            print(items)
            reply = False
            if items:
                reply = tk_messagebox.askyesnocancel(title="pvzHE Archiver", message=f"你确定要删除这「{len(items)}」个存档?")
            
            if reply is None:
                return
            
            delete_button.config(text="删除...")
            select_mode = ""

            if reply is False:
                saving_data_table.quit_select_mode()
                return
            
            for item in items:
                if del_item := mods.remove_saving(item):
                    succ_rm_savings.append(del_item)
                else:
                    fail_rm_savings.append(item)
            saving_data_table.delete_selected_rows(succ_rm_savings)
            saving_data_table.quit_select_mode()
            if fail_rm_savings:
                tk_messagebox.showwarning(
                    title="删除失败", message=f"删除以下存档时出错:\n{fail_rm_savings}")
        else:
            delete_button.config(text="确定删除")
            saving_data_table.enter_select_mode()
            select_mode = "d"
    
    def import_data():
        zjs_file = tk_filedialog.askopenfilename(
            filetypes=(("pvzHE save file", "*.zjs"), ))

        imported = mods.zip2file(zjs_file, HE_ARCHIVER_GAME_DATA_PATH)
        print(imported)
        refresh_game_data()
        tk_messagebox.showinfo(title="pvzHE Archiver", message=f"成功导入「{len(imported)}」个存档!")
        refresh_button.config(text="导入成功!")
        root.after(1500, lambda: refresh_button.config(text="刷新"))


    def select_export():
        nonlocal select_mode
        if select_mode == "d":
            tk_messagebox.showwarning(title="pvzHE Archiver", message="请先退出删除模式!")
        elif select_mode == "e":
            return
        else:
            select_mode = "e"
            delete_button.grid_forget()
            refresh_button.grid_forget()
            cancel_export_button.grid(row=3, column=0, padx=10,
                               ipadx=5, pady=5, sticky='NSEW')
            export_button.grid(row=3, column=1, columnspan=2, padx=10, ipadx=5,
                                pady=5, sticky='NSEW')
            saving_data_table.enter_select_mode()
    
    def export_selected_data():
        data_paths = [os.path.join(HE_ARCHIVER_GAME_DATA_PATH, id) for id in saving_data_table.get_selected_rows()]
        if data_paths and (zip_name := tk_filedialog.asksaveasfilename(
                defaultextension=".zjs", 
                filetypes=(("pvzHE save file", "*.zjs"), ), 
                initialdir=DESKTOP_PATH)):
            mods.file2zip(zip_name, data_paths)
            refresh_button.config(text="导出成功!")
            root.after(1500, lambda: refresh_button.config(text="刷新"))
        exit_export_mode()

    def exit_export_mode():
        nonlocal select_mode
        cancel_export_button.grid_forget()
        export_button.grid_forget()
        delete_button.grid(row=3, column=0, padx=10,
                           ipadx=5, pady=5, sticky='NSEW')
        refresh_button.grid(row=3, column=1, columnspan=2, padx=10, ipadx=5,
                            pady=5, sticky='NSEW')
        select_mode = ""
        saving_data_table.quit_select_mode()

    def exit_program():
        gvar.set("continue_scanning", False)
        root.quit()
        root.destroy()

    root = Tk()
    root.title('植物大战僵尸杂交版-存档管理工具')
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

    select_mode = ""

    heading_frame = ttk.Frame(root)
    heading_frame.grid(row=0, rowspan=1, column=0, columnspan=3, sticky='NSEW')
    heading_frame.columnconfigure(1, weight=1)
    heading_frame.columnconfigure(4, weight=1)

    select_all_text = tk.StringVar()
    select_all_text.set("全选")

    savings_filter_user_label = ttk.Label(heading_frame, text='筛选用户:')
    savings_filter_user_label.grid(
        row=0, column=0, padx=10, pady=5, sticky='NSEW')
    savings_filter_user_box = Combopicker(
        heading_frame, frameheight=190, allname_textvariable=select_all_text)
    savings_filter_user_box.grid(row=0, column=1, pady=5, sticky='NSEW')
    savings_filter_user_box.bind("<<CheckButtonSelected>>",
                                 lambda event: set_filter_key())
    heading_blank_label = ttk.Label(heading_frame, text='   ')
    heading_blank_label.grid(row=0, column=2, padx=5, rowspan=1, pady=5, sticky='NSEW')
    savings_filter_level_label = ttk.Label(heading_frame, text='筛选关卡:')
    savings_filter_level_label.grid(row=0, column=3, pady=5, sticky='NSEW')
    savings_filter_level_box = Combopicker(
        heading_frame, frameheight=190, allname_textvariable=select_all_text)
    savings_filter_level_box.grid(
        row=0, column=4, padx=12, pady=5, sticky='NSEW')
    savings_filter_level_box.bind("<<CheckButtonSelected>>",
                                  lambda event: set_filter_key())

    savings_sort_label = ttk.Label(heading_frame, text="排序依据:")
    savings_sort_label.grid(row=1, column=0, padx=10, pady=5, sticky='NSEW')
    savings_sort_box = ttk.Combobox(heading_frame, values=list(SORT_BASIS_DICT.keys()), state="readonly")
    savings_sort_box.grid(row=1, column=1, columnspan=1, pady=5, sticky='NSEW')
    savings_sort_box.bind("<<ComboboxSelected>>", lambda event: set_sort_key())
    savings_sort_box.current(2) # default value
    savings_reverse_label = ttk.Label(heading_frame, text="排列顺序:")
    savings_reverse_label.grid(row=1, column=3, pady=5, sticky='NSEW')
    savings_reverse_box = ttk.Combobox(heading_frame, values=list(SORT_REVERSE_DICT.keys()), state="readonly")
    savings_reverse_box.grid(row=1, column=4, padx=12, pady=5, sticky='NSEW')
    savings_reverse_box.bind("<<ComboboxSelected>>", lambda event: set_sort_key())
    savings_reverse_box.current(1)

    save_username_col = WidColData(1, title="用户名", widget_type=ttk.Label, data_key="user_name",
                                   stretchable=False, min_width=30)
    save_level_col = WidColData(2, title="关卡名称", widget_type=ttk.Label, data_key="level_name",
                                stretchable=False, min_width=50)
    save_time_col = WidColData(3, title="保存时间", widget_type=ttk.Label, data_key="save_time",
                               stretchable=False, min_width=50)
    save_note_col = WidColData(4, title="备注", widget_type=ttk.Entry, data_key="note",
                               stretchable=True, min_width=100)
    save_extract_col = WidColData(5, title="提取", wid_text="提取", active_text="成功!",
                                  error_active_text="提取出错", active_time=1000,
                                  widget_type=ttk.Button,
                                  command=extract_data, stretchable=False, min_width=100)
    save_columns_data = [save_username_col, save_level_col,
                         save_time_col, save_note_col, save_extract_col]

    save_rows_data = []

    saving_data_table = WidgetTable(
        root, save_columns_data, save_rows_data, sort_key=lambda col: col.data_storage["int_time"], sort_reverse=True)
    saving_data_table.grid(row=2, column=0, padx=11,
                           columnspan=3, sticky='NSEW')

    delete_button = ttk.Button(
        root, text="选择删除...", command=lambda: toggle_del_selection_mode())
    delete_button.grid(row=3, column=0, padx=10,
                       ipadx=5, pady=5, sticky='NSEW')

    refresh_button = ttk.Button(
        root, text='刷新', command=lambda: refresh_game_data(True))
    refresh_button.grid(row=3, column=1, columnspan=2, padx=10, ipadx=5,
                        pady=5, sticky='NSEW')

    cancel_export_button = ttk.Button(
        root, text="取消", command=exit_export_mode)
    export_button = ttk.Button(
        root, text="导出", command=export_selected_data)

    close_btn = ttk.Button(root, text='退出', command=exit_program)
    close_btn.grid(row=4, column=0, padx=10, ipadx=5, pady=5, sticky='NSEW')
    save_btn = ttk.Button(root, text='保存备注', command=save_note)
    save_btn.grid(row=4, column=1, columnspan=2, padx=10, ipadx=25, pady=5,
                  sticky='NSEW')
    root.bind_all('<Return>', lambda event: save_note())
    root.bind_all('<Control-s>', lambda event: save_note())
    root.grid_columnconfigure(1, weight=1, minsize=200)

    if not gvar.get("game_exist"):
        tk_messagebox.showwarning(title="提示", message="没有找到植物大战僵尸杂交版的游戏存档")
    refresh_game_data()
    resize_root()

    check_new_save_thread = Thread(target=checking_new_save, daemon=True)
    check_new_save_thread.start()

    about_text = """版本: v1.0.0 beta2
更新时间：2024年7月19日 17:30
作者：Robert He
网址：https://github.com/HNRobert/pvzHE-Archiver

本软件适用于植物大战僵尸杂交版的
【游戏自动存档+存档管理】，
功能列表:
1.在退出游戏返回主菜单时保存游戏进度。
2.自动在无尽模式进入下一个关卡时自动保存。
3.在历史任意关卡的任何时间节点重新切入。
4.便于系统化管理归档的备注功能。
5.存档筛选与排序功能。
6.批量导入与导出存档功能。"""

    main_menu = tk.Menu(root)

    file_menu = tk.Menu(main_menu, tearoff=False)
    file_menu.add_command(label="导入存档", command=import_data)
    file_menu.add_command(label="导出存档", command=lambda: select_export())
    file_menu.add_separator()
    file_menu.add_command(label="刷新", command=lambda: refresh_game_data(True))
    file_menu.add_command(label="保存备注", command=save_note)
    file_menu.add_separator()
    file_menu.add_command(label="退出", command=exit_program)

    adv_filter_menu = tk.Menu(main_menu, tearoff=False)

    time_limit_menu = tk.Menu(adv_filter_menu, tearoff=False)
    time_limit_var = tk.DoubleVar()
    time_limit_var.set(float("inf"))
    for _time_limit in TIME_FILTER_DICT.items():
        time_limit_menu.add_radiobutton(
            label=_time_limit[0], variable=time_limit_var, value=_time_limit[1], command=lambda: set_filter_key())
    adv_filter_menu.add_cascade(label="保存时间", menu=time_limit_menu)

    note_filter_menu = tk.Menu(adv_filter_menu, tearoff=False)
    note_state_var = tk.StringVar()
    note_state_var.set("不限")
    for _note_filter in NOTE_FILTER_DICT.keys():
        note_filter_menu.add_radiobutton(
            label=_note_filter, variable=note_state_var, value=_note_filter, command=lambda: set_filter_key())
    adv_filter_menu.add_cascade(label="备注状态", menu=note_filter_menu)

    help_menu = tk.Menu(main_menu, tearoff=False)
    help_menu.add_command(label="关于",
                          command=lambda: tk_messagebox.showinfo(title="关于pvzHE-Archiver", message=about_text))
    
    main_menu.add_cascade(label="文件", menu=file_menu)
    main_menu.add_cascade(label="高级筛选", menu=adv_filter_menu)
    main_menu.add_cascade(label="帮助", menu=help_menu)

    root.config(menu=main_menu)
    root.mainloop()


if __name__ == "__main__":
    import main
    main.main()
