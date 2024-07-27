import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

DATA_TYPE_REF: Dict[Type[tk.Widget], Type[tk.Variable]] = {
    ttk.Label: tk.StringVar,
    ttk.Entry: tk.StringVar,
    ttk.Checkbutton: tk.BooleanVar,
    ttk.Radiobutton: tk.IntVar,
}


class WidColData:
    def __init__(self,
                 id: int,
                 title: str = "",
                 wid_text: Optional[str] = None,
                 widget_type: Type[tk.Widget] = ttk.Label,
                 data_key: Optional[str] = None,
                 command: Callable[[Any], Any] = lambda x: None,
                 active_text: Optional[str] = None,
                 error_active_text: Optional[str] = None,
                 active_time: int = 1000, stretchable: bool = False, min_width: int = 0,
                 widget_padding: Optional[Tuple] = None,
                 **kwargs):
        """
        This function initializes various attributes for a column widget in a graphical user interface.

        :param id: The `id` parameter is used to uniquely identify the column. It is of type
        `int`
        :type id: int
        :param title: The `title` parameter is a string that represents the title of the column.
        :type title: str
        :param wid_text: The `wid_text` parameter is used to store the text that will be displayed in 
        the widget. If not provided, the text to display will follow the rows' settings
        :type wid_text: str
        :param widget_type: The `widget_type` parameter is used to specify the
        type of widget that will be created for the object. It has a default value of `ttk.Label`.
        :type widget_type: Type[tk.Widget]
        :param data_key: The `data_key` parameter is a string parameter that
        represents the key of the corresponding data in data_storage dict in WidRowData, which is used for store the inputted data from each widgets.
        :type data_key: str
        :param command: The `command` parameter is a callable to use for the widget placed.
        :type command: Callable[[Any], Any]
        :param active_text: The `active_text` parameter is used to specify the
        text that should be displayed when the widget is in an active state. If a value is provided for
        `active_text`, it will be used as the text to display.
        :type active_text: Optional[str]
        :param false_active_text: The `false_active_text` parameter is used to specify the text that
        should be displayed when the widget is in a error state. If a value is not provided for
        `error_active_text`, it defaults to the value of `wid_text`
        :type false_active_text: Optional[str]
        :param active_time: The `active_time` parameter represents the duration
        in milliseconds for which the widget should display the `active_text` before reverting to the
        original `wid_text` or `false_active_text` if provided, defaults to 1000
        :type active_time: int (optional)
        :param stretchable: The `stretchable` parameter you provided is a
        boolean flag that indicates whether the widget should be able to stretch horizontally to fill
        available space. If `stretchable` is set to `True`, the column can expand horizontally as
        needed. If set to `False, defaults to False
        :type stretchable: bool (optional)
        :param min_width: The `min_width` parameter is used to specify the
        minimum width of the column. This parameter allows you to set a minimum width for
        the widget to ensure it is displayed with at least the specified width, defaults to 0
        :type min_width: int (optional)
        """
        if id in [0] and not ("select_col" in kwargs.keys() and kwargs["select_col"]):
            raise ValueError("id can't be 0, because it's occupied")
        self.id = id
        self.title = title
        self.text = wid_text
        self.widget_type = widget_type
        self.data_key = data_key
        self.stretchable = stretchable
        self.min_width = min_width
        self.command = command
        self.active_text = active_text if not (
            active_text is None) else wid_text
        self.false_active_text = error_active_text if not (
            error_active_text is None) else wid_text
        self.active_time = active_time
        self.widget_padding = widget_padding


class WidRowData:
    def __init__(self, id: str, cols_data: List[WidColData], data_storage: Optional[dict] = None):
        self.id = id
        self.wid_variable_dict = {}
        self.wid_variable_dict[0] = tk.BooleanVar()
        self.wid_variable_dict[0].set(False)
        if data_storage is not None:
            self.data_storage = data_storage
            self.update(cols_data)
        else:
            self.data_storage = {}

    def update(self, cols_data: List[WidColData], new_data_storage: Optional[dict] = None):
        if new_data_storage is not None:
            self.data_storage = new_data_storage
        for col_data in cols_data:
            self.wid_variable_dict[col_data.id] = DATA_TYPE_REF.get(
                col_data.widget_type, tk.StringVar)()
            if col_data.data_key is not None and col_data.data_key in self.data_storage:
                self.wid_variable_dict[col_data.id].set(
                    self.data_storage[col_data.data_key])


class WidgetTable(tk.LabelFrame):
    def __init__(self, master, columns_data: List[WidColData], rows_data: List[WidRowData], add_sep: bool = True, filter_algo: Optional[Callable[[Any], Any]] = None, sort_key: Optional[Callable[[WidRowData], Any]] = None, sort_reverse: bool = False, **kw):
        self.select_mode = False

        self.master: tk.Tk = master
        self.column_num = len(columns_data)
        self.columns_data = columns_data
        self.runtime_columns_data: List[WidColData] = columns_data.copy()
        self.column_titles = [c_data.title for c_data in columns_data]
        self._column_label_var = {}
        self.add_sep = add_sep

        self.rows_data = rows_data
        self.shown_rows_data: List[WidRowData] = []

        self.column_widget_dicts = []

        self.filter_algo = filter_algo
        self.sort_algo = sort_key
        self.sort_reverse = sort_reverse

        tk.LabelFrame.__init__(self, master, **kw)
        self.bind_all("<MouseWheel>", self._processwheel)
        self.columnconfigure(0, weight=1, minsize=200)
        self.rowconfigure(0, weight=1)

        self.table_canvas = tk.Canvas(self)
        self.table_canvas.config(highlightthickness=0)
        self.table_canvas.grid(row=0, column=0, columnspan=1, sticky="NSEW")

        self.table_frame = ttk.Frame(self.table_canvas)
        self.table_frame.columnconfigure(0, weight=1, minsize=200)

        self.saving_canvas_scrollbar = ttk.Scrollbar(
            self, orient=tk.VERTICAL)
        self.saving_canvas_scrollbar.grid(row=0, column=1, sticky="NSEW")
        self.saving_canvas_scrollbar.config(command=self.table_canvas.yview)

        self.table_canvas.config(
            yscrollcommand=self.saving_canvas_scrollbar.set)
        self.canvas_window = self.table_canvas.create_window(
            (0, 0), window=self.table_frame, anchor='nw')
        self.table_canvas.bind("<Configure>", self._resize_canvas)

        self.title_col_sep_list = []
        self.first_row_sep_list = []
        self.final_row_sep_list = []

        self.refresh_columns()

        self._select_column_data = WidColData(
            id=0, wid_text="", widget_type=ttk.Checkbutton, select_col=True, widget_padding=(6, 0, 0, 0))

        """
        self.master.geometry(
            f"{self.table_frame.winfo_width()}x{self.table_frame.winfo_height()}")
        """

    def fixed_col(self, x): return x + \
        1 if x > 0 and not self.select_mode else x

    def fixed_span(
        self, x) -> int: return 2 if not self.select_mode and x == 0 else 1

    def enter_select_mode(self):
        if self.select_mode:
            raise Exception("Already in select mode")
        self.select_mode = True
        # print([data.id for data in rt_data])
        # self.runtime_columns_data = rt_data if not (
        #    rt_data is None) else self.runtime_columns_data
        self.runtime_columns_data = [
            self._select_column_data] + self.columns_data
        self.refresh_columns()
        self._set_rows()

    # it returns the ids of the selected rows
    def get_selected_rows_id(self) -> List[str]:
        if not self.select_mode:
            raise Exception("Not in select mode")
        return [res for res, val in self.get_column_input(self._select_column_data).items() if val]

    def quit_select_mode(self):
        self.select_mode = False
        for _row in self.rows_data:
            _row.wid_variable_dict[0].set(False)
        self.refresh_columns()
        """
        for c in self.saving_frame.winfo_children():
            print(c.info)
            print(c.grid_info())
            print()
        """

    def get_column_input(self, column_data: WidColData) -> Dict[str, Any]:
        """
        This function reads data from a specified column in the table based on the widget type of the
        column.

        :param column_data: `column_data` is an object that represents the data associated with a
        specific column in a table or grid. It contains information such as the widget type (e.g., Entry
        or Checkbutton) that is used to display and interact with the data in that column
        :type column_data: WidColData
        :return: The `read_from_column` method returns a dictionary where the keys are the `id`
        attribute of each `row_data` object in `self.rows_data`, and the values are obtained based on
        the widget type of the `column_data`.
        """
        return {
            row_data.id: row_data.wid_variable_dict[column_data.id].get() for row_data in self.rows_data
        }

    def set_filter_algo(self, filter_algo: Optional[Callable[[Any], Any]]):
        self.filter_algo = filter_algo
        self._rearrange_lines()

    def set_sort_method(self, key: Optional[Callable[[WidRowData], Any]], reverse: bool = False):
        self.sort_algo = key
        self.sort_reverse = reverse
        self._rearrange_lines()

    def refresh_columns(self, new_columns_data: Optional[List[WidColData]] = None):
        if not (new_columns_data is None):
            self.columns_data = new_columns_data
        if not self.select_mode:
            self.runtime_columns_data = self.columns_data.copy()
        self.column_titles = [
            c_data.title for c_data in self.runtime_columns_data]
        self.column_num = len(self.column_titles)
        self._clear_widgets()
        self.column_widget_dicts = [{} for _ in range(self.column_num+1)]

        # 清除现有的列标题
        for widget in self._column_label_var.values():
            widget.grid_remove()
            widget.destroy()
        self._column_label_var.clear()

        if self.add_sep:
            self._draw_seps()
        # 创建并布局新的列标题
        for i, c_label in enumerate(self.column_titles):
            self._column_label_var[i] = ttk.Label(
                self.table_frame, text=c_label)
            self._column_label_var[i].grid(row=0, column=self.fixed_col(
                i), columnspan=self.fixed_span(i), pady=5)

            # 设置列的拉伸属性和最小宽度
            self.table_frame.columnconfigure(self.fixed_col(i), weight=1 if self.runtime_columns_data[i].stretchable else 0,
                                             minsize=self.runtime_columns_data[i].min_width)

        self._set_rows()

    def _rm_seps(self):
        for sep in self.title_col_sep_list:
            sep.grid_remove()
            sep.destroy()
        self.title_col_sep_list.clear()
        for sep in self.first_row_sep_list:
            sep.grid_remove()
            sep.destroy()
        self.first_row_sep_list.clear()
        for sep in self.final_row_sep_list:
            sep.grid_remove()
            sep.destroy()
        self.final_row_sep_list.clear()

    def _draw_seps(self):
        self._rm_seps()
        for col in range(self.column_num + 1):
            self.title_col_sep_list.append(ttk.Separator(
                self.table_frame, orient="vertical"))
            self.title_col_sep_list[-1].grid(row=0, rowspan=1,
                                             column=self.fixed_col(col), sticky='NSEW')
        for col in range(2 * self.column_num):
            self.first_row_sep_list.append(ttk.Separator(
                self.table_frame, orient='horizontal'))
            self.first_row_sep_list[-1].grid(row=col // self.column_num, column=self.fixed_col(col %
                                             self.column_num), columnspan=self.fixed_span(col %
                                             self.column_num), padx=1, sticky='NSEW')
        for col in range(self.column_num):
            self.final_row_sep_list.append(ttk.Separator(
                self.table_frame, orient="horizontal"))
            self.final_row_sep_list[-1].grid(row=0,
                                             column=self.fixed_col(col), columnspan=self.fixed_span(col), padx=1, sticky='NSEW')

    def _adj_seps(self):
        current_row_count = len(self.shown_rows_data)
        for t_col in range(self.column_num + 1):
            self.title_col_sep_list[t_col].grid_configure(
                rowspan=current_row_count + 1)
        for f_col in range(self.column_num):
            self.final_row_sep_list[f_col].grid_configure(
                row=current_row_count + 1)

    def _remove_row(self, _row_data):
        # Delete the row and reset the button state
        for i in range(self.column_num):
            self.column_widget_dicts[i][_row_data.id].grid_remove()
            self.column_widget_dicts[i][_row_data.id].destroy()
            self.column_widget_dicts[i].pop(_row_data.id)
        if _row_data in self.rows_data:
            self.rows_data.remove(_row_data)

    def delete_rows(self, del_rows_id: Optional[List[str]]):
        if del_rows_id is None:
            return
        for row_id in del_rows_id:
            if row_data := next((r for r in self.rows_data if r.id == row_id), None):
                self._remove_row(row_data)
        self._rearrange_lines()

    def update_rows_data(self, new_rows_data: Optional[List[WidRowData]] = None):
        if not (new_rows_data is None):
            self.rows_data = new_rows_data
        self._set_rows()

    def _clear_widgets(self):
        # clear previous widgets
        for widget_dict in self.column_widget_dicts:
            for widget in widget_dict.values():
                widget.grid_remove()
                widget.destroy()
            widget_dict.clear()

    def _set_rows(self):
        self._clear_widgets()
        # place the savings in the root
        for _row_data in self.rows_data:
            for _col_idx, _col_data in enumerate(self.runtime_columns_data):
                self.column_widget_dicts[_col_idx][_row_data.id] = self._get_widget_at(
                    _col_data, _row_data)
        self._rearrange_lines()

    def _act_command(self, ori_command: Optional[Callable[[str], Any]], col_id: int, row_data: WidRowData):
        _col_idx = col_id - 1 if not self.select_mode else col_id
        try:
            if not (ori_command is None):
                ori_command(row_data.id)
        except Exception as e:
            print(e)
            self.column_widget_dicts[_col_idx][row_data.id].config(
                text=self.runtime_columns_data[_col_idx].false_active_text)
        else:
            self.column_widget_dicts[_col_idx][row_data.id].config(
                text=self.runtime_columns_data[_col_idx].active_text)
        finally:
            self.master.after(self.runtime_columns_data[_col_idx].active_time, lambda: self.column_widget_dicts[_col_idx][row_data.id].config(
                text=self.runtime_columns_data[_col_idx].text))

    def _get_wid_text(self, col_data: WidColData, row_data: WidRowData):
        if col_data.text is None:
            return row_data.wid_variable_dict[col_data.id]
        col_string_var = tk.StringVar()
        col_string_var.set(col_data.text)
        return col_string_var

    def _get_widget_at(self, col_data: WidColData, row_data: WidRowData):
        if col_data.widget_type == ttk.Label:
            return ttk.Label(self.table_frame, textvariable=self._get_wid_text(col_data, row_data), anchor="center")
        elif col_data.widget_type == ttk.Entry:
            ent = ttk.Entry(self.table_frame,
                            textvariable=row_data.wid_variable_dict[col_data.id])
            return ent
        elif col_data.widget_type == ttk.Button:
            return ttk.Button(self.table_frame, text=self._get_wid_text(col_data, row_data).get(),
                              command=lambda: self._act_command(
                                  col_data.command, col_data.id, row_data))
        elif col_data.widget_type == ttk.Checkbutton:
            return ttk.Checkbutton(self.table_frame, textvariable=self._get_wid_text(col_data, row_data),
                                   command=lambda id=row_data.id: col_data.command(
                                       id),
                                   variable=row_data.wid_variable_dict[col_data.id],
                                   padding=col_data.widget_padding)
        else:
            raise ValueError(
                f"Unsupported widget type: {col_data.widget_type}")

    def _rearrange_lines(self):
        # Copy the list to avoid modifying the original
        self.shown_rows_data = list(self.rows_data)
        if not (self.filter_algo is None):
            self.shown_rows_data = list(
                filter(self.filter_algo, self.shown_rows_data))
        if not (self.sort_algo is None):
            self.shown_rows_data.sort(
                key=self.sort_algo, reverse=self.sort_reverse)

        for widget_dict in self.column_widget_dicts:
            for widget in widget_dict.values():
                widget.grid_forget()

        for _row_idx, _row_data in enumerate(self.shown_rows_data):
            for _col_idx in range(self.column_num):
                self.column_widget_dicts[_col_idx][_row_data.id].grid(
                    row=_row_idx + 1, column=self.fixed_col(_col_idx), columnspan=self.fixed_span(_col_idx), padx=5, pady=2, sticky='NSEW')

        self._adj_seps()
        self.update_idletasks()
        self.table_canvas.update_idletasks()
        self.table_frame.update_idletasks()

    def _processwheel(self, event):
        if event.delta > 0:
            self.table_canvas.yview_scroll(-1, tk.UNITS)
        else:
            self.table_canvas.yview_scroll(1, tk.UNITS)

    def _resize_canvas(self, event):
        # Update canvas' scroll region to match the actual size
        canvas_width = event.width
        self.table_canvas.itemconfig(self.canvas_window, width=canvas_width)
        self.table_canvas.config(scrollregion=self.table_canvas.bbox("all"))


if __name__ == "__main__":
    import main
    main.main()
