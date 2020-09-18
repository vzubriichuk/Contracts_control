# -*- coding: utf-8 -*-
"""
Created on Tue Jul  9 15:44:08 2019

@author: v.shkaberda
"""
from tkinter import ttk
import tkinter as tk

class MultiselectMenu(tk.Frame):
    """
        Class that provides multiselection from options.
        "Default_option" is an option name from "options".
        "Options" should be an iterable.
        "Width" - int, configures width of menubutton.
    """
    def __init__(self, parent, default_option, options, width,
                 *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.default_option = default_option
        self.options = options

        self.menubutton = ttk.Menubutton(self, text=default_option)
        menu = tk.Menu(self.menubutton, tearoff=False)
        self.menubutton.configure(menu=menu, width=width)
        self.menubutton.pack(padx=10, pady=10)

        self.choices = {}
        for choice in self.options:
            if not choice:
                choice = 'Выбрать все'
            self.choices[choice] = tk.IntVar(value=1 if choice == self.default_option
                                                   else 0)
            if choice == 'Выбрать все':
                menu.add_checkbutton(label=choice, variable=self.choices[choice],
                                     onvalue=1, offvalue=0,
                                     command=self._select_all_options)
            else:
                menu.add_checkbutton(label=choice, variable=self.choices[choice],
                                     onvalue=1, offvalue=0,
                                     command=self._select_single_option)

    def _change_menubutton_text(self, all_selected=None, selected_one=None):
        if all_selected == 1:
            self.menubutton.configure(text='(все)')
        elif all_selected == 0:
            self.menubutton.configure(text='(не выбрано)')
        elif selected_one:
            self.menubutton.configure(text=selected_one)
        elif self.menubutton.cget('text') != '(несколько элементов)':
            self.menubutton.configure(text='(несколько элементов)')

    def _select_all_options(self):
        all_selected = self.choices['Выбрать все'].get()
        for k in self.choices:
            if k != 'Выбрать все':
                self.choices[k].set(1 if all_selected else 0)
        self._change_menubutton_text(all_selected)

    def _select_single_option(self):
        selected_count = sum(map(tk.IntVar.get, self.choices.values()))
        if selected_count != 12:
            if not selected_count:
                self._change_menubutton_text(all_selected=0)
            elif selected_count == 1:
                self._change_menubutton_text(selected_one=next(opt for opt, val
                                        in self.choices.items() if val.get()))
            else:
                self._change_menubutton_text()
            return
        all_selected = self.choices['Выбрать все'].get()
        self.choices['Выбрать все'].set(0 if all_selected else 1)
        if self.choices['Выбрать все'].get() == 1:
            self._change_menubutton_text(all_selected=1)
        else:
            self._change_menubutton_text()

    def get_selected(self):
        """ Return string of selected options optimized for sql query:
            Nothing selected — returns '';
            One selected — returns 'Index';
            Multiple selected — returns 'Index1, Index2, ...'.
        """
        options_selected = []
        for idx, selected in enumerate(self.choices.values()):
            if selected.get():
                options_selected.append(idx)
        return ', '.join(map(str, options_selected))

    def set_default_option(self):
        """ Deselect selected options if any and set option provided as default
        """
        for choice in self.choices:
            self.choices[choice].set(1 if choice == self.default_option else 0)
        self._change_menubutton_text(selected_one=self.default_option)


if __name__ == "__main__":
    from calendar import month_name
    root = tk.Tk()
    options = list(month_name)
    MultiselectMenu(root, options[1], options,
                    width=15).pack(fill="both", expand=True)
    root.mainloop()