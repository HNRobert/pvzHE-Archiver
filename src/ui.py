import time
import os
import tkinter as tk
import tkinter.font as tk_font
import tkinter.messagebox as tk_messagebox
from threading import Thread
from tkinter import Tk, ttk
import shutil
from typing import List

import mods
from const import HE_ARCHIVER_GAME_DATA_PATH, HE_DATA_PATH, HE_ARCHIVER_ICON
from global_var import gvar
from widgetable import WidColData, WidRowData, WidgetTable


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

    def extract_data(data_filename: str):  # Here, data_filename is exactly the id of the row
        arched_data_path = os.path.join(
            HE_ARCHIVER_GAME_DATA_PATH, data_filename)
        matched_values = mods.match_value_from_data_name(data_filename)
        _user_arch_id, _scene_id = matched_values["user_arch_id"], matched_values["game_id"]
        ori_data_path = os.path.join(
            HE_DATA_PATH, f"game{_user_arch_id}_{_scene_id}.dat")
        shutil.copy2(arched_data_path, ori_data_path)
        print(arched_data_path, "Success")

    def refresh_game_data(rescan=False):
        _note_data = gvar.get("note_data")
        if rescan:
            gvar.set("rescan_savings", True)
            refresh_button.config(text="刷新中...")
            root.after(1500, lambda: refresh_button.config(text="刷新成功!"))
            root.after(2500, lambda: refresh_button.config(text="刷新"))
        _arched_game_data = mods.list_arched_game_data()
        _save_rows_data: List[WidRowData] = []
        for _data in _arched_game_data.keys():
            # add note into the dict
            _arched_game_data[_data]["note"] = ""
            if _data in _note_data.keys():
                _arched_game_data[_data]["note"] = _note_data[_data]
            _save_rows_data.append(WidRowData(
                id=_data, cols_data=save_columns_data, data_storage=_arched_game_data[_data]))
            # save_rows_data[-1].wid_value_info
        saving_data_table.update_rows_data(_save_rows_data)


    def resize_root():
        current_line_count = len(saving_data_table.rows_data)
        root.rowconfigure(1, weight=1, minsize=31 *
                          int(bool(current_line_count)) - 5)
        root.minsize(width=800, height=140)
        root.geometry(
            f"{root.winfo_width()}x{min(max(24 * current_line_count + 190, root.winfo_height()), 600)}")

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

    savings_notice_label = ttk.Label(root, text='存档栏:')
    savings_notice_label.grid(row=0, column=0, padx=10, pady=5, sticky='NSEW')

    save_username_col = WidColData(0, title="用户名", widget_type=ttk.Label, data_key="user_name",
                                stretchable=False, min_width=30)
    save_level_col = WidColData(1, title="关卡名称", widget_type=ttk.Label, data_key="level_name",
                                stretchable=False, min_width=50)
    save_time_col = WidColData(2, title="保存时间", widget_type=ttk.Label, data_key="save_time",
                               stretchable=False, min_width=50)
    save_note_col = WidColData(3, title="备注", widget_type=ttk.Entry, data_key="note",
                               stretchable=True, min_width=100)
    save_extract_col = WidColData(4, title="提取", wid_text="提取", active_text="成功!", 
                                  error_active_text="提取出错", active_time=1000, 
                                  widget_type=ttk.Button, 
                                  command=extract_data, stretchable=False, min_width=100)
    save_columns_data = [save_username_col, save_level_col,
                         save_time_col, save_note_col, save_extract_col]

    save_rows_data = []

    saving_data_table = WidgetTable(root, save_columns_data, save_rows_data)
    saving_data_table.grid(row=1, column=0, padx=11,
                            columnspan=2, sticky='NSEW')

    refresh_button = ttk.Button(
        root, text='刷新', command=lambda: refresh_game_data(True))
    refresh_button.grid(row=2, column=0, columnspan=3, padx=10, ipadx=5,
                        pady=5, sticky='NSEW')
    close_btn = ttk.Button(root, text='退出', command=exit_program)
    close_btn.grid(row=3, column=0, padx=10, ipadx=5, pady=5, sticky='NSEW')
    save_btn = ttk.Button(root, text='保存备注', command=save_note)
    save_btn.grid(row=3, column=1, columnspan=2, padx=10, ipadx=25, pady=5,
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

    about_text = """版本: v0.0.2
更新时间：2024年6月10日 17:30
作者：Robert He
网址：https://github.com/HNRobert/pvzHE-Archiver

本软件适用于植物大战僵尸杂交版的
【游戏自动存档+存档管理】，
可以在退出游戏返回主菜单时保存游戏进度，
也可以自动在无尽模式进入下一个关卡时自动保存，
并在历史任意关卡的任何时间节点重新切入。
还有备注功能便于管理归档。

当前软件为测试版，
后续将继续更新，加入筛选排序等功能"""

    main_menu = tk.Menu(root)
    help_menu = tk.Menu(main_menu, tearoff=False)
    help_menu.add_command(label="关于",
                          command=lambda: tk_messagebox.showinfo(title="关于pvzHE-Archiver", message=about_text))
    main_menu.add_cascade(label="帮助", menu=help_menu)
    root.config(menu=main_menu)
    root.mainloop()

if __name__ == "__main__":
    import main
    main.main()