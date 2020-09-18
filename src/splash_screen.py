# -*- coding: utf-8 -*-
"""
Created on Tue Aug 20 17:56:36 2019

@author: v.shkaberda
"""
import tkinter as tk
from time import sleep


class SplashScreen(tk.Tk):
    ''' Class that inherits from tkinter.Tk and allows create background
        splash screen while running python script.
        func - function to be computed.

        Usage:
        root = SplashScreen(func)
        root.after(200, root.task) # give tkinter time to render the window
        root.mainloop()
    '''
    def __init__(self, func=None, exception_handlers=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.func = func or (lambda: sleep(7))  # simulate computation
        self.exception_handlers = exception_handlers
        self._center_window(400, 400)

    def _center_window(self, w, h):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        start_x = int((screen_width/2) - (w/2))
        start_y = int((screen_height/2) - (h/2))
        self.geometry('{}x{}+{}+{}'.format(w, h, start_x, start_y))

    def task(self):
        ''' The window will stay open until this function call ends.
        '''
        try:
            self.func()
        except StopIteration:
            if 'NetworkError' in self.exception_handlers:
                self.exception_handlers['NetworkError']()
        except Exception as e:
            if 'UnexpectedError' in self.exception_handlers:
                self.exception_handlers['UnexpectedError'](type(e), e.args)
        finally:
            self.destroy()


def main():
    root = SplashScreen()
    root.overrideredirect(True)

    label = tk.Label(root,
                     text='Выполняется поиск обновлений и запуск приложения.')
    label.pack(expand='yes')

    root.after(200, root.task)
    root.mainloop()

    print("Main loop is now over and we can do other stuff.")

if __name__ == '__main__':
    main()