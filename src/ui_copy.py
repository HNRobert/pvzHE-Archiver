import time
import os
import tkinter as tk
import tkinter.font as tk_font
import tkinter.messagebox as tk_messagebox
from threading import Thread
from tkinter import Tk, ttk
import shutil

import mods
from const import HE_ARCHIVER_GAME_DATA_PATH, HE_DATA_PATH, HE_ARCHIVER_ICON
from global_var import gvar


def mk_ui():
    def save_note():
        _note_data: dict = gvar.get("note_data")
        for _t in arched_game_data.keys():
            c_note = savings_note_dict[_t].get()
            arched_game_data[_t]["note"] = c_note
            _note_data[_t] = c_note
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

    def extract_data(data_filename: str):
        arched_data_path = os.path.join(
            HE_ARCHIVER_GAME_DATA_PATH, data_filename)
        matched_values = mods.match_value_from_data_name(data_filename)
        _user_arch_id, _scene_id = matched_values["user_arch_id"], matched_values["game_id"]
        ori_data_path = os.path.join(
            HE_DATA_PATH, f"game{_user_arch_id}_{_scene_id}.dat")
        try:
            shutil.copy2(arched_data_path, ori_data_path)
            savings_extract_button_dict[data_filename].config(text="成功!")
            root.after(
                1000, lambda: savings_extract_button_dict[data_filename].config(text="提取"))
        except Exception as e:
            print(e)
            savings_extract_button_dict[data_filename].config(text="提取出错")
            root.after(
                1000, lambda: savings_extract_button_dict[data_filename].config(text="提取"))

    def refresh_game_data(rescan=False):
        nonlocal arched_game_data
        _note_data = gvar.get("note_data")
        if rescan:
            gvar.set("rescan_savings", True)
            refresh_button.config(text="刷新中...")
            root.after(1500, lambda: refresh_button.config(text="刷新成功!"))
            root.after(2500, lambda: refresh_button.config(text="刷新"))
        _arched_game_data = mods.list_arched_game_data()
        for _data in _arched_game_data.keys():
            # add note into the dict
            _arched_game_data[_data]["note"] = ""
            if _data in _note_data.keys():
                _arched_game_data[_data]["note"] = _note_data[_data]
        arched_game_data = _arched_game_data.copy()
        set_lines()

    def set_lines():
        # 清除所有旧控件
        for widget_dict in [savings_name_label_dict, savings_note_dict, savings_extract_button_dict,
                            savings_remove_button_dict]:
            for widget in widget_dict.values():
                widget.destroy()
            widget_dict.clear()
        # place the savings in the root
        for _saving in arched_game_data.keys():
            savings_name_label_dict[_saving] = ttk.Label(
                saving_frame, text=arched_game_data[_saving]["data_name"])
            savings_note_dict[_saving] = ttk.Entry(saving_frame)
            savings_note_dict[_saving].insert(
                0, arched_game_data[_saving]["note"])
            savings_extract_button_dict[_saving] = ttk.Button(
                saving_frame, text='提取', command=lambda _tar=_saving: extract_data(_tar))
            savings_remove_button_dict[_saving] = ttk.Button(
                saving_frame, text='删除', command=lambda _tar=_saving: remove_save(_tar))
        rearrange_lines()

    def rearrange_lines():
        nonlocal shown_game_data
        shown_game_data = arched_game_data.copy()
        shown_game_data = {k: v for k, v in sorted(shown_game_data.items(),
                                                   key=lambda item: item[1]["int_time"], reverse=True)}
        for _index, _saving in enumerate(shown_game_data.keys()):
            savings_name_label_dict[_saving].grid_forget()
            savings_note_dict[_saving].grid_forget()
            savings_extract_button_dict[_saving].grid_forget()
            savings_remove_button_dict[_saving].grid_forget()
            savings_name_label_dict[_saving].grid(
                row=_index + 1, column=0, padx=5, pady=2, sticky='NSEW')
            savings_note_dict[_saving].grid(
                row=_index + 1, column=1, padx=5, pady=2, sticky='NSEW')
            savings_extract_button_dict[_saving].grid(
                row=_index + 1, column=2, padx=4, pady=2, sticky='NSEW')
            savings_remove_button_dict[_saving].grid(
                row=_index + 1, column=3, padx=4, pady=2, sticky='NSEW')
        resize_root()

    def remove_line(_saving):
        # Delete the line and reset the button state
        savings_name_label_dict[_saving].destroy()
        savings_note_dict[_saving].destroy()
        savings_extract_button_dict[_saving].destroy()
        savings_remove_button_dict[_saving].destroy()
        rm_button_state_dict.pop(_saving)
        if _saving in rm_button_timer_dict:
            root.after_cancel(rm_button_timer_dict[_saving])
            rm_button_timer_dict.pop(_saving)
        savings_name_label_dict.pop(_saving)
        savings_extract_button_dict.pop(_saving)
        savings_remove_button_dict.pop(_saving)
        savings_note_dict.pop(_saving)
        saving_canvas.update_idletasks()
        saving_frame.update_idletasks()
        rearrange_lines()

    def remove_save(_saving):
        # Check if the button is in the "Sure?" state, if yes, delete the line and reset the button state
        if rm_button_state_dict.get(_saving, False):
            try:
                os.remove(os.path.join(HE_ARCHIVER_GAME_DATA_PATH, _saving))
                if game_data_filepath := mods.current_data_path_of(_saving):
                    os.remove(game_data_filepath)
                    pass
                arched_game_data.pop(_saving)
                shown_game_data.pop(_saving)
                remove_line(_saving)
            except Exception as e:
                print(e)
        else:
            # Set the button to "Sure?" state
            savings_remove_button_dict[_saving].config(text="确定?")
            rm_button_state_dict[_saving] = True

            # Set a timer, if no more action in 3 sec then reset
            if _saving in rm_button_timer_dict:
                root.after_cancel(rm_button_timer_dict[_saving])

            rm_button_timer_dict[_saving] = root.after(
                3000, reset_rm_button, _saving)

    def reset_rm_button(_saving):
        if _saving in savings_remove_button_dict:
            savings_remove_button_dict[_saving].config(text="删除")
            rm_button_state_dict[_saving] = False
            rm_button_timer_dict.pop(_saving, None)

    def resize_root():
        current_line_count = len(shown_game_data)
        root.rowconfigure(1, weight=1, minsize=31 *
                          int(bool(current_line_count)) - 5)
        root.minsize(width=800, height=140)
        root.geometry(
            f"{root.winfo_width()}x{min(max(24 * current_line_count + 190, root.winfo_height()), 600)}")
        for t_col in range(5):
            save_col_list[t_col].grid_configure(rowspan=current_line_count + 1)
        for f_col in range(5):
            save_final_row_sep[f_col].grid_configure(
                row=current_line_count + 1)

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

    savings_name_label_dict = {}
    savings_note_dict = {}
    savings_extract_button_dict = {}
    savings_remove_button_dict = {}

    rm_button_state_dict = {}
    rm_button_timer_dict = {}

    savings_notice_label = ttk.Label(root, text='存档栏:')
    savings_notice_label.grid(row=0, column=0, padx=10, pady=5, sticky='NSEW')

    saving_label_frame = tk.LabelFrame(root, relief=tk.GROOVE)
    saving_label_frame.grid(row=1, column=0, padx=11,
                            columnspan=2, sticky='NSEW')
    saving_label_frame.bind_all("<MouseWheel>", processwheel)
    saving_label_frame.columnconfigure(0, weight=1, minsize=200)
    saving_label_frame.rowconfigure(0, weight=1)

    saving_canvas = tk.Canvas(saving_label_frame)
    saving_canvas.config(highlightthickness=0)
    saving_canvas.grid(row=0, column=0, columnspan=1, sticky="NSEW")

    saving_frame = ttk.Frame(saving_canvas)
    saving_frame.columnconfigure(0, weight=1, minsize=200)

    saving_canvas_scrollbar = ttk.Scrollbar(
        saving_label_frame, orient=tk.VERTICAL)
    saving_canvas_scrollbar.grid(row=0, column=1, sticky="NSEW")
    saving_canvas_scrollbar.config(command=saving_canvas.yview)

    saving_canvas.config(yscrollcommand=saving_canvas_scrollbar.set)
    canvas_window = saving_canvas.create_window(
        (0, 0), window=saving_frame, anchor='nw')
    saving_canvas.bind("<Configure>", resize_canvas)

    save_col_list = []
    save_final_row_sep = []
    for col in range(5):
        save_col_list.append(ttk.Separator(saving_frame, orient="vertical"))
        save_col_list[-1].grid(row=0, rowspan=1, column=col, sticky='NSEW')
    for col in range(8):
        tar_first_row_sep = ttk.Separator(saving_frame, orient='horizontal')
        tar_first_row_sep.grid(row=col // 4, column=col %
                               4, padx=1, sticky='NSEW')
    for col in range(5):
        save_final_row_sep.append(ttk.Separator(
            saving_frame, orient="horizontal"))
        save_final_row_sep[-1].grid(row=0, column=col, padx=1, sticky='NSEW')

    savings_name_clabel = ttk.Label(saving_frame, text="存档用户名-关卡名称(代号)-日期-时间")
    savings_name_clabel.grid(row=0, column=0, pady=5)
    savings_note_clabel = ttk.Label(saving_frame, text="备注")
    savings_note_clabel.grid(row=0, column=1, pady=5)
    savings_arch_clabel = ttk.Label(saving_frame, text="提取")
    savings_arch_clabel.grid(row=0, column=2, pady=5)
    savings_del_clabel = ttk.Label(saving_frame, text="删除")
    savings_del_clabel.grid(row=0, column=3, pady=5)

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
    arched_game_data = {}
    shown_game_data = {}
    refresh_game_data()

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
