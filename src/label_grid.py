# -*- coding: utf-8 -*-
"""
Created on Mon Jul  8 14:00:07 2019

@author: v.shkaberda
"""
import tkinter as tk

class LabelGrid(tk.Frame):
    """
    Creates a grid of cells with type determined by content.
    Columns width is a required parameter.
    Columns width can be provided as "headers.values" or as "grid_width".
    If headers are provided, grid_width will be ignored.
    """
    def __init__(self, master, headers=None,
                 content=[('Data is missing',)], grid_width=None,
                 *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.headers = headers
        self.content = content
        self.grid_width = list(headers.values()) if headers else grid_width
        self.content_size = (len(content), len(content[0]))
        self.im_unchecked = tk.PhotoImage(file='resources/unchecked.png')
        self.im_checked = tk.PhotoImage(file='resources/checked.png')
        assert len(self.grid_width) == self.content_size[1], ('Number of columns'
                  ' should be the same for headers, content and grid_width')
        if self.headers:
            self._create_headers()
        self.cells = []
        self._create_cells()

    def _create_headers(self):
        for j, (header, width) in enumerate(self.headers.items()):
            lb = tk.Label(self, text=header, font=('Calibri', 10, 'bold'),
                          relief='sunken', borderwidth=1, width=width)
            lb.grid(row=0, column=j, ipadx=5, sticky='nswe')

    def _create_cells(self):
        def __put_content_in_cell(row, column):
            content = self.content[row][column]
            content_type = type(content).__name__
            if content_type in ('float'):
                self.cells[row][column].insert(0, self._format_float_to_str(content))
            if content_type in ('int'):
                self.cells[row][column].insert(0, content)
                if column == 0:
                    self.cells[row][column].configure(state='readonly',
                                                       justify=tk.CENTER)
            elif content_type == 'str':
                self.cells[row][column].configure(text=content, anchor=tk.W)
            elif content_type == 'bool':
                img = self.im_checked if content else self.im_unchecked
                self.cells[row][column].create_image((32, 12), image=img,
                           tag=content)
                self.cells[row][column].bind("<Button-1>", self._click)

        for i in range(self.content_size[0]):
            self.cells.append(list())
            for j in range(self.content_size[1]):
                content = self.content[i][j]
                content_type = type(content).__name__
                if content_type in ('float', 'int'):
                    self.cells[i].append(tk.Entry(self))
                    if content_type == 'float':
                        self.cells[i][j].bind("<FocusIn>",
                                            self._on_focus_in_format_float)
                        self.cells[i][j].bind("<FocusOut>",
                                            self._on_focus_out_format_float)
                elif content_type == 'str':
                    self.cells[i].append(tk.Label(self, relief='sunken',
                                                   borderwidth=1))
                elif content_type == 'bool':
                    self.cells[i].append(tk.Canvas(self, height=20))
                __put_content_in_cell(i, j)
                self.cells[i][j].configure(width=self.grid_width[j])
                if self.headers:
                    self.cells[i][j].grid(row=i+1, column=j, sticky='we')
                else:
                    self.cells[i][j].grid(row=i+1, column=j, padx=2)

    def _click(self, event):
        """ Change canvas tag when click on it.
        """
        tags = event.widget.gettags(tk.ALL)
        if 'current' not in tags:
            return
        event.widget.delete(tk.ALL)
        if '1' in tags:
            event.widget.create_image((32, 12), image=self.im_unchecked, tag='0')
        else:
            event.widget.create_image((32, 12), image=self.im_checked, tag='1')

    def _format_float_to_str(self, float_var):
        """ Convert float into format with spaces as thousands separators.
        """
        return '{:,.2f}'.format(float_var).replace(',', ' ').replace('.', ',')

    def _format_str_to_num(self, str_var, num_type):
        """ Convert float formatted as str into num_type format.
            num_type - 'float' or 'int'.
        """
        float_var = float(str_var.replace(' ', '').replace(',', '.'))
        if num_type == 'float':
            return float_var
        if num_type == 'int':
            return int(float_var)

    def _on_focus_in_format_float(self, event):
        """ Convert str into float in binded entry when focus in.
        """
        try:
            entry = self._format_str_to_num(event.widget.get(), 'float')
        except ValueError:
            entry = 0
        finally:
            event.widget.delete(0, tk.END)
            event.widget.insert(0, entry)

    def _on_focus_out_format_float(self, event):
        """ Convert float into str in binded entry when focus out.
        """
        try:
            entry = float(event.widget.get().replace(',', '.'))
            entry = self._format_float_to_str(entry)
        except ValueError:
            entry = '0,00'
        finally:
            event.widget.delete(0, tk.END)
            event.widget.insert(0, entry)

    def get_values(self):
        """
        Return info about entries values and canvases tags for each grid row.
        Entries are converted into ints.
        Output: list of lists.
        """
        values = []
        for i in range(self.content_size[0]):
            values.append([])
            for j in range(self.content_size[1]):
                if self.cells[i][j].widgetName == 'entry':
                    val = self.cells[i][j].get()
                    values[i].append(self._format_str_to_num(val, 'int'))
                elif self.cells[i][j].widgetName == 'canvas':
                    values[i].append(int(self.cells[i][j].gettags(tk.ALL)[0]))
        return values


if __name__ == '__main__':
    root = tk.Tk()
    label_grid = LabelGrid(root,
                           headers={'One':10, 'Two, but long':20},
                           content=([3, True], ['my_str', False], [2, 12345.6])
                           )
    label_grid.pack()
    tk.mainloop()