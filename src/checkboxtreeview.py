# -*- coding: utf-8 -*-
"""
Created on Wed Aug  7 11:44:46 2019

@author: v.shkaberda
"""
import tkinter as tk
from tkinter import ttk

class CheckboxTreeview(ttk.Treeview):
    """
    `ttk.Treeview` widget with checkboxes.
    The checkboxes are done via the image attribute of the item,
    so to keep the checkbox, you cannot add an image to the item.
    """
    def __init__(self, master=None, **kw):
        ttk.Treeview.__init__(self, master, **kw)
        # checkboxes are implemented with images. Image source:
        # https://commons.wikimedia.org/wiki/File:Checkbox_States.svg?uselang=en
        # License CC BY-SA 3.0  (https://creativecommons.org/licenses/by-sa/3.0)
        self.im_checked = tk.PhotoImage(file='resources/checked.png')
        self.im_unchecked = tk.PhotoImage(file='resources/unchecked.png')
        self.tag_configure('unchecked', image=self.im_unchecked)
        self.tag_configure('checked', image=self.im_checked)
        # check / uncheck boxes on click
        self.bind('<Button-1>', self._box_click, True)

    def _box_click(self, event):
        """Check or uncheck box when clicked."""
        x, y, widget = event.x, event.y, event.widget
        elem = widget.identify("element", x, y)
        if "image" in elem:
            item = self.identify_row(y)
            self._toggle_state(item)

    def _check_item(self, item, tags):
        """ Internal function that changes state of the item to "checked"."""
        new_tags = [t for t in tags if t != 'unchecked'] + ['checked']
        self.item(item, tags=tuple(new_tags))

    def _uncheck_item(self, item, tags):
        """ Internal function that changes state of the item to "unchecked"."""
        new_tags = [t for t in tags if t != 'checked'] + ['unchecked']
        self.item(item, tags=tuple(new_tags))

    def _toggle_state(self, item):
        """
        Check current state of the item and toggle state (checked/unchecked).
        """
        tags = self.item(item, 'tags')
        if 'checked' in tags:
            self._uncheck_item(item, tags)
        elif 'unchecked' in tags:
            self._check_item(item, tags)

    def check_item(self, item):
        """ Check item if it's unchecked. """
        tags = self.item(item, 'tags')
        if 'unchecked' in tags:
            self._check_item(item, tags)

    def uncheck_item(self, item):
        """ Uncheck item if it's checked. """
        tags = self.item(item, 'tags')
        if 'checked' in tags:
            self._uncheck_item(item, tags)


if __name__ == '__main__':
    root = tk.Tk()
    tree = CheckboxTreeview(root)
    tree.pack()
    tree.insert("", "end", "1", text="1", tag =('unchecked',))
    tree.insert("", "end", "2", text="2", tag =('checked',))
    root.mainloop()