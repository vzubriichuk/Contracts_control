# -*- coding: utf-8 -*-

from _version import __version__
from checkboxtreeview import CheckboxTreeview
from calendar import month_name
from datetime import date, datetime
from decimal import Decimal
from label_grid import LabelGrid
from multiselect import MultiselectMenu
from tkcalendar import DateEntry
from tkinter import ttk, messagebox
from tkinter.filedialog import askopenfile
from shutil import copy2
from pathlib import Path
from tkinter import filedialog as fd
import tkinter.font as tkFont
from tkHyperlinkManager import HyperlinkManager
from math import floor
from xl import export_to_excel
import datetime as dt
import locale
import os, zlib
import tkinter as tk
import ast

# example of subsription and default recipient
EMAIL_TO = b'\xd0\xa4\xd0\xbe\xd0\xb7\xd0\xb7\xd0\xb8|\
\xd0\x9b\xd0\xbe\xd0\xb3\xd0\xb8\xd1\x81\xd1\x82\xd0\xb8\xd0\xba\xd0\xb0|\
\xd0\x90\xd0\xbd\xd0\xb0\xd0\xbb\xd0\xb8\xd1\x82\xd0\xb8\xd0\xba\xd0\xb8'.decode()
# example of path to independent report
REPORT_PATH = zlib.decompress(b'x\x9c\x8b\x89I\xcb\xaf\xaa\xaa\xd4\xcbI\xcc\
\x8bq\xc9O.\xcdM\xcd+)\x8e\xf1\xc8\xcfI\xc9\xccK\x8fqI-H,*\x81\x88\xf9\xe4\
\xa7g\x16\x97df\'\xc6\xb8e\xe6\xc5\\Xpa\xc3\xc5\xc6\x0b\xfb/6\\\xd8za\x0b\x10\
\xef\x06\xe2\xbd\x17v\\\xd8\x1a\x7fa;P\xaa\t(\x01$c.L\xb9\xb0\xef\xc2~\x85\x0b\
\xfb\x80"\xed\x17\xb6\x02\xc9n\x00\x9b\x8c?\xef').decode()

UPLOAD_PATH = zlib.decompress(b"x\x9c\x8b\x89I\xcb\xaf\xaa\xaa\xd4\xcbI\xcc"
                              b"\x8bq\xc9O.\xcdM\xcd+)\x8e\xf1\xc8\xcfI\xc9"
                              b"\xccK\x8fqI-H,*\x81\x88\xf9\xe4\xa7g\x16"
                              b"\x97df'\xc6\xb8e\xe6\xc5\\\x98x\xb1\xef\xc2"
                              b"\x96\x0b\xdb.l\xbd\xd8\x14\x13Z\x90\x93\x9f"
                              b"\x98\x02\x00\xa3\x8c!\xb1").decode()


class PaymentsError(Exception):
    """Base class for exceptions in this module."""
    pass


class IncorrectFloatError(PaymentsError):
    """ Exception raised if sum is not converted to float.

    Attributes:
        expression - input expression in which the error occurred;
        message - explanation of the error.
    """

    def __init__(self, expression, message='Введена некорректная сумма'):
        self.expression = expression
        self.message = message
        super().__init__(self.expression, self.message)


class MonthFilterError(PaymentsError):
    """ Exception raised if month don't chosen in filter.

    Attributes:
        expression - input expression in which the error occurred;
        message - explanation of the error.
    """

    def __init__(self, expression, message='Не выбран месяц'):
        self.expression = expression
        self.message = message
        super().__init__(self.expression, self.message)


class AccessError(tk.Tk):
    """ Raise an error when user doesn't have permission to work with app.
    """

    def __init__(self):
        super().__init__()
        self.withdraw()  # Do not show main window
        messagebox.showerror(
            'Ошибка доступа',
            'Нет прав для работы с приложением.\n'
            'Для получения прав обратитесь на рассылку ' + EMAIL_TO
        )
        self.destroy()


class LoginError(tk.Tk):
    """ Raise an error when user doesn't have permission to work with db.
    """

    def __init__(self):
        super().__init__()
        self.withdraw()  # Do not show main window
        messagebox.showerror(
            'Ошибка подключения',
            'Нет прав для работы с сервером.\n'
            'Обратитесь на рассылку ' + EMAIL_TO
        )
        self.destroy()


class NetworkError(tk.Tk):
    """ Raise a message about network error.
    """

    def __init__(self):
        super().__init__()
        self.withdraw()  # Do not show main window
        messagebox.showerror(
            'Ошибка cети',
            'Возникла общая ошибка сети.\nПерезапустите приложение'
        )
        self.destroy()


class RestartRequiredAfterUpdateError(tk.Tk):
    """ Raise a message about restart needed after update.
    """

    def __init__(self):
        super().__init__()
        self.withdraw()  # Do not show main window
        messagebox.showinfo(
            'Необходима перезагрузка',
            'Выполнено критическое обновление.\nПерезапустите приложение'
        )
        self.destroy()


class UnexpectedError(tk.Tk):
    """ Raise a message when an unexpected exception occurs.
    """

    def __init__(self, *args):
        super().__init__()
        self.withdraw()  # Do not show main window
        messagebox.showinfo(
            'Непредвиденное исключение',
            'Возникло непредвиденное исключение\n' + '\n'.join(map(str, args))
        )
        self.destroy()


class StringSumVar(tk.StringVar):
    """ Contains function that returns var formatted in a such way, that
        it can be converted into a float without an error.
    """

    def get_float_form(self, *args, **kwargs):
        return super().get(*args, **kwargs).replace(' ', '').replace(',', '.')


class PaymentApp(tk.Tk):
    def __init__(self, **kwargs):
        super().__init__()
        self.title('Учёт договоров аренды')
        self.iconbitmap('resources/paper.ico')
        # store the state of PreviewForm
        self.state_PreviewForm = 'normal'
        # geometry_storage {Framename:(width, height)}
        self._geometry = {'PreviewForm': (1200, 550),
                          'CreateForm': (850, 440),
                          'UpdateForm': (850, 440)}
        # Virtual event for creating request
        self.event_add("<<create>>", "<Control-S>", "<Control-s>",
                       "<Control-Ucircumflex>", "<Control-ucircumflex>",
                       "<Control-twosuperior>", "<Control-threesuperior>",
                       "<KeyPress-F5>")
        self.bind_all("<Key>", self._onKeyRelease, '+')
        self.bind("<<create>>", self._create_request)
        self.active_frame = None
        # handle the window close event
        self.protocol("WM_DELETE_WINDOW", self._quit)
        # hide until all frames have been created
        self.withdraw()
        # To import months names in cyrillic
        locale.setlocale(locale.LC_ALL, 'RU')
        # Customize header style (used in PreviewForm)
        style = ttk.Style()
        try:
            style.element_create("HeaderStyle.Treeheading.border", "from",
                                 "default")
            style.layout("HeaderStyle.Treeview.Heading", [
                ("HeaderStyle.Treeheading.cell", {'sticky': 'nswe'}),
                ("HeaderStyle.Treeheading.border",
                 {'sticky': 'nswe', 'children': [
                     ("HeaderStyle.Treeheading.padding",
                      {'sticky': 'nswe', 'children': [
                          ("HeaderStyle.Treeheading.image",
                           {'side': 'right', 'sticky': ''}),
                          ("HeaderStyle.Treeheading.text", {'sticky': 'we'})
                      ]})
                 ]}),
            ])
            style.configure("HeaderStyle.Treeview.Heading",
                            background="#eaeaea", foreground="black",
                            relief='groove', font=('Arial', 8))
            style.map("HeaderStyle.Treeview.Heading",
                      relief=[('active', 'sunken'), ('pressed', 'flat')])

            style.map('ButtonGreen.TButton')
            style.configure('ButtonGreen.TButton', foreground='green')

            style.map('ButtonRed.TButton')
            style.configure('ButtonRed.TButton', foreground='red')

            style.configure("TMenubutton", background='white')
        except tk.TclError:
            # if during debug previous tk wasn't destroyed
            # and style remains modified
            pass

        # the container is where we'll stack a bunch of frames
        # the one we want to be visible will be raised above others
        container = tk.Frame(self)
        container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self._frames = {}
        for F in (PreviewForm, CreateForm, UpdateForm):
            frame_name = F.__name__
            frame = F(parent=container, controller=self, **kwargs)
            self._frames[frame_name] = frame
            # put all of them in the same location
            frame.grid(row=0, column=0, sticky='nsew')

        self._show_frame('PreviewForm')
        # restore after withdraw
        self.deiconify()

    def _center_window(self, w, h):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        start_x = int((screen_width / 2) - (w / 2))
        start_y = int((screen_height / 2) - (h * 0.55))

        self.geometry('{}x{}+{}+{}'.format(w, h, start_x, start_y))

    def _fill_CreateForm(self, Объект, **kwargs):
        """ Control function to transfer data from Preview- to CreateForm. """
        # print(kwargs)
        num_main_contract_heading = kwargs['№ договора']
        date_main_contract_heading = kwargs['Дата договора (начало)']
        date_main_contract_heading_end = kwargs['Дата договора (конец)']
        contragent_heading = kwargs['Арендодатель']
        type_business = kwargs['Бизнес']
        okpo = kwargs['ЕГРПОУ']
        frame = self._frames['CreateForm']
        frame._fill_from_PreviewForm(Объект, num_main_contract_heading,
                                     date_main_contract_heading,
                                     date_main_contract_heading_end,
                                     contragent_heading, type_business, okpo)

    def _fill_UpdateForm(self, Объект, **kwargs):
        """ Control function to transfer data from Preview- to CreateForm. """
        id = kwargs['ID']

        num_main_contract = kwargs['№ договора']
        date_main_contract_start = kwargs['Дата договора (начало)']
        date_main_contract_end = kwargs['Дата договора (конец)']
        add_contract_num = kwargs['№ доп.согл.']
        date_add_contract = kwargs['Дата доп.согл.']
        date_add_contract_start = kwargs['Дата с']
        date_add_contract_end = kwargs['Дата по']
        square = kwargs['Площадь']
        price1m2 = kwargs['Цена за 1м²']
        cost = kwargs['Сумма без НДС']
        contragent = kwargs['Арендодатель']
        business = kwargs['Бизнес']
        okpo = kwargs['ЕГРПОУ']
        description = kwargs['Описание']
        cost_extra = kwargs['Сумма экспл. без НДС']
        filename = kwargs['Имя файла']
        frame = self._frames['UpdateForm']
        frame._fill_from_UpdateForm(Объект, id, num_main_contract,
                                    date_main_contract_start,
                                    date_main_contract_end, date_add_contract,
                                    date_add_contract_end,
                                    add_contract_num, date_add_contract_start,
                                    square,
                                    price1m2, cost_extra, cost, contragent,
                                    business, okpo, description, filename)

    def _onKeyRelease(*args):
        event = args[1]
        # check if Ctrl pressed
        if not (event.state == 12 or event.state == 14):
            return
        if event.keycode == 88 and event.keysym.lower() != 'x':
            event.widget.event_generate("<<Cut>>")
        elif event.keycode == 86 and event.keysym.lower() != 'v':
            event.widget.event_generate("<<Paste>>")
        elif event.keycode == 67 and event.keysym.lower() != 'c':
            event.widget.event_generate("<<Copy>>")

    def _show_frame(self, frame_name):
        """ Show a frame for the given frame name. """
        if frame_name == 'CreateForm' or frame_name == 'UpdateForm':
            # since we have only two forms, when we activating CreateForm
            # we know by exception that PreviewForm is active
            self.state_PreviewForm = self.state()
            self.state('normal')
            self.resizable(width=False, height=False)
        else:
            self.state(self.state_PreviewForm)
            self.resizable(width=True, height=True)
        frame = self._frames[frame_name]
        frame.tkraise()
        self._center_window(*(self._geometry[frame_name]))
        # Make sure active_frame changes in case of network error
        try:
            if frame_name in ('PreviewForm'):
                frame._resize_columns()
                frame._refresh()
                # Clear form in CreateFrom by autofill form
                self._frames['CreateForm']._clear()
                self._frames['UpdateForm']._clear()
        finally:
            self.active_frame = frame_name

    def _create_request(self, event):
        """
        Creates request when hotkey is pressed if active_frame is CreateForm.
        """
        if self.active_frame == 'CreateForm':
            self._frames[self.active_frame]._create_request()

    def _quit(self):
        if self.active_frame != 'PreviewForm':
            self._show_frame('PreviewForm')
        elif messagebox.askokcancel("Выход", "Выйти из приложения?"):
            self.destroy()


class PaymentFrame(tk.Frame):
    def __init__(self, parent, controller, connection, user_info, mvz):
        super().__init__(parent)
        self.parent = parent
        self.controller = controller
        self.conn = connection
        self.mvz = {}
        if isinstance(self, PreviewForm):
            self.mvz['Все'] = (None, ('Все',))
        for mvzSAP, mvzname, id in mvz:
            try:
                self.mvz[mvzname][1].append(id)
            except KeyError:
                self.mvz[mvzname] = [mvzSAP, id]
        self.user_info = user_info
        # Often used info
        self.userID = user_info.UserID

    def _add_user_label(self, parent):
        """ Adds user name in top right corner. """
        user_label = tk.Label(parent, text='Пользователь: ' +
                                           self.user_info.ShortUserName + '  Версия ' + __version__,
                              font=('Arial', 8))
        user_label.pack(side=tk.RIGHT, anchor=tk.NE)

    def _format_float(self, sum_float):
        return '{:,.2f}'.format(sum_float).replace(',', ' ').replace('.', ',')

    def _format_float_decimal(self, sum_float):
        return '{:,.6f}'.format(sum_float).replace(',', ' ').replace('.', ',')

    def _on_focus_in_format_sum(self, event):
        """ Convert str into float in binded to entry variable when focus in.
        """
        varname = str(event.widget.cget("textvariable"))
        sum_entry = event.widget.get().replace(' ', '')
        event.widget.setvar(varname, sum_entry)
        self._multiply_cost_square()

    def _on_focus_out_format_sum(self, event):
        """ Convert float into str in binded to entry variable when focus out.
        """
        if not event.widget.get().replace(',', '.'):
            return
        sum_entry = float(event.widget.get().replace(',', '.'))
        varname = str(event.widget.cget("textvariable"))
        event.widget.setvar(varname, self._format_float(sum_entry))
        self._multiply_cost_square()

    def _on_focus_out_format_sum_decimal(self, event):
        """ Convert float into str in binded to entry variable when focus out.
        """
        if not event.widget.get().replace(',', '.'):
            return
        sum_entry = float(event.widget.get().replace(',', '.'))
        varname = str(event.widget.cget("textvariable"))
        event.widget.setvar(varname, self._format_float_decimal(sum_entry))
        self._multiply_cost_square()

    def _validate_sum(self, sum_entry):
        """ Validation of entries that contains sum. """
        sum_entry = sum_entry.replace(',', '.').replace(' ', '')
        try:
            if not sum_entry or 0 <= float(sum_entry) < 10 ** 9:
                return True
        except (TypeError, ValueError):
            return False
        return False

    def get_mvzSAP(self, mvz):
        return self.mvz[mvz][0]

    def get_mvzID(self, mvz):
        return self.mvz[mvz][1]
    #
    # def _multiply_cost_square(self):
    #     pass


class CreateForm(PaymentFrame):
    def __init__(self, parent, controller, connection, user_info, mvz,
                 type_business, **kwargs):
        super().__init__(parent, controller, connection, user_info, mvz)
        self.upload_filename = str()
        # print(self.mvz)
        # Top Frame with description and user name
        top = tk.Frame(self, name='top_cf', padx=5)
        self.main_label = tk.Label(top,
                                   text='Форма внесения дополнительного '
                                        'соглашения к основому договору',
                                   padx=10, font=('Arial', 8, 'bold'))
        self.type_businessID, self.type_business = zip(*type_business)
        self.mvz_choice_list = []
        self._add_user_label(top)
        self._top_pack()

        # First Fill Frame with (MVZ, business)
        row1_cf = tk.Frame(self, name='row1_cf', padx=15)

        self.mvz_label = tk.Label(row1_cf, text='Объект', padx=7)
        self.mvz_current = tk.StringVar()
        self.mvz_box = ttk.OptionMenu(row1_cf, self.mvz_current, '',
                                      *self.mvz.keys(),
                                      command=self._restraint_by_mvz)
        self.mvz_box.config(width=40)
        # self.mvz_sap_label = tk.Label(row1_cf, text='SAPmvz', padx=10)
        # self.mvz_sap = tk.Label(row1_cf, padx=10, bg='lightgray', width=11)

        self.menubutton = tk.Menubutton(row1_cf, text="Выбрать адреса договора",
                                        indicatoron=True, borderwidth=1,
                                        relief="raised")
        self.menu_choice_mvz = tk.Menu(self.menubutton, tearoff=False)
        self.menubutton.configure(menu=self.menu_choice_mvz)

        self.choices = {}
        for choice in self.mvz.keys():
            self.choices[choice] = tk.IntVar(value=0)
            self.menu_choice_mvz.add_checkbutton(label=choice,
                                                 variable=self.choices[choice],
                                                 onvalue=1, offvalue=0,
                                                 command=self._mvz_choice_list)

        self.square = StringSumVar()
        self.square.set('0,00')
        self.square_label = tk.Label(row1_cf, text='Площадь, м²')
        vcmd = (self.register(self._validate_sum))
        self.square_entry = tk.Entry(row1_cf, name='square_entry', width=18,
                                     textvariable=self.square, validate='all',
                                     validatecommand=(vcmd, '%P')
                                     )
        self.square_entry.bind("<FocusIn>", self._on_focus_in_format_sum)
        self.square_entry.bind("<FocusOut>", self._on_focus_out_format_sum)

        self._row1_pack()

        # Second Fill Frame
        row2_cf = tk.Frame(self, name='row2_cf', padx=15)
        self.type_business_label = tk.Label(row2_cf, text='Тип бизнеса', padx=7)
        self.type_business_box = ttk.Combobox(row2_cf, width=20,
                                              state='readonly')
        self.type_business_box['values'] = self.type_business
        self.type_business_box.configure(state="normal")
        self.date_main_label_start = tk.Label(row2_cf, text='Договор с:',
                                              padx=12)
        self.date_main_start = tk.StringVar()
        self.date_main_contract_start = DateEntry(row2_cf, width=16,
                                                  state='readonly',
                                                  textvariable=self.date_main_start,
                                                  font=('Arial', 9),
                                                  selectmode='day',
                                                  borderwidth=2,
                                                  locale='ru_RU')
        self.square_cost = StringSumVar()
        self.square_cost.set('0,00')
        self.square_cost_label = tk.Label(row2_cf, text='Цена за 1м², грн')
        vcmd = (self.register(self._validate_sum))
        self.square_cost_entry = tk.Entry(row2_cf, name='square_cost_entry',
                                          width=18,
                                          textvariable=self.square_cost,
                                          validate='all',
                                          validatecommand=(vcmd, '%P')
                                          )
        self.square_cost_entry.bind("<FocusIn>", self._on_focus_in_format_sum)
        # Change format price to max decimal format
        self.square_cost_entry.bind("<FocusOut>",
                                    self._on_focus_out_format_sum_decimal)

        self._row2_pack()

        # Third Fill Frame
        row3_cf = tk.Frame(self, name='row3_cf', padx=15)

        self.num_main_contract = tk.Label(row3_cf, text='№ договора', padx=0)
        self.num_main_contract_entry = tk.Entry(row3_cf, width=23)
        self.date_main_label_end = tk.Label(row3_cf, text='Договор по:', padx=7)
        self.date_main_end = tk.StringVar()
        self.date_main_contract_end = DateEntry(row3_cf, width=16,
                                                state='readonly',
                                                textvariable=self.date_main_end,
                                                font=('Arial', 9),
                                                selectmode='day', borderwidth=2,
                                                locale='ru_RU')
        self.sum_extra_label = tk.Label(row3_cf,
                                        text='Сумма экспл. без НДС, грн',
                                        padx=3)
        self.sum_extra_total = StringSumVar()
        self.sum_extra_total.set('0,00')
        vcmd = (self.register(self._validate_sum))
        self.sum_extra_entry = tk.Entry(row3_cf, name='sum_extra_entry',
                                        width=18,
                                        textvariable=self.sum_extra_total,
                                        validate='all',
                                        validatecommand=(vcmd, '%P')
                                        )
        self.sum_extra_entry.bind("<FocusIn>", self._on_focus_in_format_sum)
        self.sum_extra_entry.bind("<FocusOut>", self._on_focus_out_format_sum)

        self._row3_pack()

        # Fourth Fill Frame
        row4_cf = tk.Frame(self, name='row4_cf', padx=15)

        self.num_add_contract = tk.Label(row4_cf, text='№ доп.дог.  ', padx=0)
        self.num_add_contract_entry = tk.Entry(row4_cf, width=23)
        self.date_add_label = tk.Label(row4_cf, text='Дата доп.', padx=7)
        self.date_add = tk.StringVar()
        self.date_add_contract = DateEntry(row4_cf, width=16, state='readonly',
                                           textvariable=self.date_add,
                                           font=('Arial', 9),
                                           selectmode='day', borderwidth=2,
                                           locale='ru_RU')
        self.sum_label = tk.Label(row4_cf, text='Сумма всего без НДС, грн',
                                  padx=3)
        self.sumtotal = tk.StringVar(row4_cf, value='0.00')
        vcmd = (self.register(self._validate_sum))
        # self.sum_entry = tk.Entry(row4_cf, textvariable=self.sumtotal, width=18)
        self.sum_entry = tk.Entry(row4_cf, name='sum_entry',
                                  width=18,
                                  textvariable=self.sumtotal,
                                  validate='all',
                                  validatecommand=(vcmd, '%P')
                                  )
        self.sum_entry.config(background='lightgrey')
        # self.sum_entry.config(state='disabled')

        self.sum_entry.bind("<FocusIn>", self._on_focus_in_format_sum)
        self.sum_entry.bind("<FocusOut>", self._on_focus_out_format_sum)

        self._row4_pack()

        # Fifth Fill Frame
        row5_cf = tk.Frame(self, name='row5_cf', padx=15)
        self.contragent_label = tk.Label(row5_cf, text='Арендодатель')
        self.contragent_entry = tk.Entry(row5_cf, width=23)
        self.date_start_label = tk.Label(row5_cf, text='Период с:', padx=17)
        self.date_start = tk.StringVar()
        self.date_start_entry = DateEntry(row5_cf, width=16, state='readonly',
                                          textvariable=self.date_start,
                                          font=('Arial', 9),
                                          selectmode='day', borderwidth=2,
                                          locale='ru_RU')
        self.nds_label = tk.Label(row5_cf, text='Ставка НДС', padx=0)
        self.nds = tk.IntVar()
        self.nds.set(20)
        self.nds20 = ttk.Radiobutton(row5_cf, text="20 %", variable=self.nds,
                                     value=20)
        self.nds0 = ttk.Radiobutton(row5_cf, text="0 %", variable=self.nds,
                                    value=0)

        self._row5_pack()

        # Six Fill Frame
        row6_cf = tk.Frame(self, name='row6_cf', padx=15)

        self.okpo_label = tk.Label(row6_cf, text='ЕГРПОУ           ')
        self.okpo_entry = tk.Entry(row6_cf, width=23)
        self.date_finish_label = tk.Label(row6_cf, text='Период по:', padx=16)
        self.date_finish = tk.StringVar()
        self.date_finish_entry = DateEntry(row6_cf, width=16, state='readonly',
                                           textvariable=self.date_finish,
                                           font=('Arial', 9),
                                           selectmode='day', borderwidth=2,
                                           locale='ru_RU')
        self.file_label = tk.Label(row6_cf, text='Файл не выбран')
        bt_upload = ttk.Button(row6_cf, text="Выбрать файл", width=20,
                               command=self._file_opener,
                               style='ButtonGreen.TButton')
        bt_upload.pack(side=tk.RIGHT, padx=15, pady=0)

        # Text Frame
        text_cf = ttk.LabelFrame(self, text=' Комментарий к договору ',
                                 name='text_cf')

        self.customFont = tkFont.Font(family="Arial", size=10)
        self.desc_text = tk.Text(text_cf,
                                 font=self.customFont)  # input and output box
        self.desc_text.configure(width=115)
        self.desc_text.pack(in_=text_cf, expand=True)

        self._row6_pack()

        # Bottom Frame with buttons
        bottom_cf = tk.Frame(self, name='bottom_cf')

        bt3 = ttk.Button(bottom_cf, text="Назад", width=10,
                         # command=self._deselect_checked_mvz)
                         # command=self.button_back(controller))
                         command=lambda: controller._show_frame('PreviewForm'))
        bt3.pack(side=tk.RIGHT, padx=15, pady=10)

        bt2 = ttk.Button(bottom_cf, text="Очистить", width=10,
                         command=self._clear, style='ButtonRed.TButton')
        bt2.pack(side=tk.RIGHT, padx=15, pady=10)

        bt1 = ttk.Button(bottom_cf, text="Создать", width=10,
                         command=self._create_request,
                         style='ButtonGreen.TButton')
        bt1.pack(side=tk.RIGHT, padx=15, pady=10)

        # Pack frames
        top.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        bottom_cf.pack(side=tk.BOTTOM, fill=tk.X)
        row1_cf.pack(side=tk.TOP, fill=tk.X, pady=5)
        row2_cf.pack(side=tk.TOP, fill=tk.X, pady=5)
        row3_cf.pack(side=tk.TOP, fill=tk.X, pady=5)
        row4_cf.pack(side=tk.TOP, fill=tk.X, pady=5)
        row5_cf.pack(side=tk.TOP, fill=tk.X, pady=5)
        row6_cf.pack(side=tk.TOP, fill=tk.X, pady=5)
        text_cf.pack(side=tk.TOP, fill=tk.X, expand=True, padx=15, pady=15)

    def _mvz_choice_list(self):
        self.mvz_choice_list = []
        for name, var in self.choices.items():
            if var.get() == 1:
                self.mvz_choice_list.append(self.get_mvzID(name))

    # Deselect checked row in menu (destroy and create menubutton again)
    def _deselect_checked_mvz(self):
        self.mvz_choice_list.clear()
        self.menu_choice_mvz.destroy()
        self.menu_choice_mvz = tk.Menu(self.menubutton, tearoff=False)
        self.menubutton.configure(menu=self.menu_choice_mvz)
        for choice in self.mvz.keys():
            self.choices[choice] = tk.IntVar(value=0)
            self.menu_choice_mvz.add_checkbutton(label=choice,
                                                 variable=self.choices[choice],
                                                 onvalue=1, offvalue=0,
                                                 command=self._mvz_choice_list)
            # print(self.mvz_choice_list)

    def _file_opener(self):
        filename = fd.askopenfilename()
        if filename:
            copy2(filename, UPLOAD_PATH)
            path = Path(filename)
            self.upload_filename = path.name
            self.file_label.config(text='Файл добавлен')

    def _remove_upload_file(self):
        os.remove(UPLOAD_PATH + '\\' + self.upload_filename)
        self.file_label.config(text='Файл не выбран')

    def _multiply_cost_square(self):
        square_get = float(self.square.get_float_form()
                           if self.square_entry.get() else 0)
        square_cost_get = float(self.square_cost.get_float_form()
                                if self.square_cost_entry.get() else 0)
        total_square_cost = square_get * square_cost_get
        if total_square_cost:
            self.sum_entry.delete(0, tk.END)
            self.sum_entry.insert(0, total_square_cost)

    def _clear(self):
        self.type_business_box.configure(state="readonly")
        self.num_main_contract_entry.configure(state="normal")
        self.date_main_contract_start.configure(state="normal")
        self.date_main_contract_end.configure(state="normal")
        self.contragent_entry.configure(state="normal")
        self.num_main_contract_entry.delete(0, tk.END)
        self.contragent_entry.delete(0, tk.END)
        self.square.set('0,00')
        self.square_cost_entry.delete(0, tk.END)
        self.square_cost_entry.insert(0, '0,00')
        self.num_main_contract_entry.delete(0, tk.END)
        self.num_add_contract_entry.delete(0, tk.END)
        self.okpo_entry.delete(0, tk.END)
        self.sum_extra_total.set('0,00')
        self.sumtotal.set('0,00')
        self.nds.set(20)
        self.desc_text.delete("1.0", tk.END)
        self.date_start_entry.set_date(datetime.now())
        self.date_finish_entry.set_date(datetime.now())
        self.date_add_contract.set_date(datetime.now())
        self.date_main_contract_start.set_date(datetime.now())
        self.date_main_contract_end.set_date(datetime.now())
        self._deselect_checked_mvz()

    def _fill_from_PreviewForm(self, mvz, num_main_contract_entry,
                               date_main_contract_start, date_main_contract_end
                               , contragent, type_business, okpo):
        """ When button "Добавить из договора" from PreviewForm is activated,
        fill some fields taken from choosed in PreviewForm request.
        """
        self.mvz_current.set(mvz)
        self.type_business_box.set(type_business)
        self.type_business_box.configure(state="readonly")
        self.num_main_contract_entry.delete(0, tk.END)
        self.num_main_contract_entry.insert(0, num_main_contract_entry)
        self.num_main_contract_entry.configure(state="readonly")
        self.date_main_contract_start.set_date(
            self._convert_str_date(date_main_contract_start))
        self.date_main_contract_start.configure(state="readonly")
        self.date_main_contract_end.set_date(
            self._convert_str_date(date_main_contract_end))
        self.date_main_contract_end.configure(state="readonly")
        self.mvz_sap = self.get_mvzSAP(self.mvz_current.get())
        self.contragent_entry.delete(0, tk.END)
        self.contragent_entry.insert(0, contragent)
        self.contragent_entry.configure(state="readonly")
        self.okpo_entry.insert(0, okpo)
        self.square_cost.set('0,00')

    def _convert_date(self, date, output=None):
        """ Take date and convert it into output format.
            If output is None datetime object is returned.

            date: str in format '%d[./]%m[./]%y' or '%d[./]%m[./]%Y'.
            output: str or None, output format.
        """
        date = date.replace('/', '.')
        try:
            dat = datetime.strptime(date, '%d.%m.%y')
        except ValueError:
            dat = datetime.strptime(date, '%d.%m.%Y')
        if output:
            return dat.strftime(output)
        return dat

    def _create_request(self):
        messagetitle = 'Добавление договора'
        sumtotal = self.sum_entry.get()
        sum_extra_total = float(self.sum_extra_total.get_float_form()
                                if self.sum_extra_entry.get() else 0)
        square = float(self.square.get_float_form()
                       if self.square_entry.get() else 0)
        price_meter = float(self.square_cost.get_float_form()
                            if self.square_cost_entry.get() else 0)
        is_validated = self._validate_request_creation(messagetitle, sumtotal)
        if not is_validated:
            return

        request = {'mvz': self.mvz_sap,  # self.mvz_sap.cget('text') or None,
                   # 'office': self.office_box.get(),
                   # 'categoryID': self.categories[self.category_box.get()],
                   'start_date': self._convert_date(
                       self.date_start_entry.get()),
                   'finish_date': self._convert_date(
                       self.date_finish_entry.get()),
                   'sum_extra_total': sum_extra_total,
                   'sumtotal': sumtotal,
                   'nds': self.nds.get(),
                   'square': square,
                   'contragent': self.contragent_entry.get().strip().replace(
                       '\n', '') or None,
                   'okpo': self.okpo_entry.get(),
                   'num_main_contract': self.num_main_contract_entry.get(),
                   'num_add_contract': self.num_add_contract_entry.get(),
                   'date_main_contract_start': self._convert_date(
                       self.date_main_contract_start.get()),
                   'date_add_contract': self._convert_date(
                       self.date_add_contract.get()),
                   'text': self.desc_text.get("1.0", tk.END).strip(),
                   'filename': self.upload_filename,
                   'date_main_contract_end': self._convert_date(
                       self.date_main_contract_end.get()),
                   'price_meter': price_meter,
                   'type_business': self.type_business_box.get(),
                   'mvz_choice_list': ','.join(map(str, self.mvz_choice_list))

                   }
        created_success = self.conn.create_request(userID=self.userID,
                                                   **request)
        if created_success == 1:
            messagebox.showinfo(
                messagetitle, 'Договор добавлен'
            )
            self._clear()
            self.controller._show_frame('PreviewForm')
        else:
            self._remove_upload_file()
            messagebox.showerror(
                messagetitle, 'Произошла ошибка при добавлении договора'
            )

            # МВЗ, Договор, Арендодатель, ЕГРПОУ, Описание

    def _convert_str_date(self, date):
        """ Take str and convert it into date format.
            date: str in format '%d[./]%m[./]%y' or '%d[./]%m[./]%Y'.
        """
        date_time_str = date
        date_time_obj = dt.datetime.strptime(date_time_str, '%Y-%m-%d')
        return date_time_obj.date()

    def _restraint_by_mvz(self, event):
        """ Shows mvz_sap that corresponds to chosen MVZ and restraint offices.
            If 1 office is available, choose it, otherwise make box active.
        """
        # tcl language has no notion of None or a null value, so use '' instead
        self.mvz_sap = self.get_mvzSAP(self.mvz_current.get()) or ''

    def _row1_pack(self):
        self.mvz_label.pack(side=tk.LEFT)
        self.mvz_box.pack(side=tk.LEFT, padx=10)
        # self.mvz_sap_label.pack(side=tk.LEFT)
        # self.mvz_sap.pack(side=tk.LEFT)
        self.menubutton.pack(side=tk.LEFT, padx=10)
        self.square_entry.pack(side=tk.RIGHT, padx=10)
        self.square_label.pack(side=tk.RIGHT, padx=10)

    def _row2_pack(self):
        self.type_business_label.pack(side=tk.LEFT)
        self.type_business_box.pack(side=tk.LEFT, padx=17)
        self.date_main_label_start.pack(side=tk.LEFT)
        self.date_main_contract_start.pack(side=tk.LEFT, padx=0)
        self.square_cost_entry.pack(side=tk.RIGHT, padx=10)
        self.square_cost_label.pack(side=tk.RIGHT, padx=10)

    def _row3_pack(self):
        self.num_main_contract.pack(side=tk.LEFT, padx=7)
        self.num_main_contract_entry.pack(side=tk.LEFT, padx=19)
        self.date_main_label_end.pack(side=tk.LEFT)
        self.date_main_contract_end.pack(side=tk.LEFT, padx=0)
        self.sum_extra_entry.pack(side=tk.RIGHT, padx=11)
        self.sum_extra_label.pack(side=tk.RIGHT, padx=0)

    def _row4_pack(self):
        self.num_add_contract.pack(side=tk.LEFT, padx=7)
        self.num_add_contract_entry.pack(side=tk.LEFT, padx=19)
        self.date_add_label.pack(side=tk.LEFT)
        self.date_add_contract.pack(side=tk.LEFT, padx=18)
        self.sum_entry.pack(side=tk.RIGHT, padx=11)
        self.sum_label.pack(side=tk.RIGHT, padx=0)

    def _row5_pack(self):
        self.contragent_label.pack(side=tk.LEFT, padx=7)
        self.contragent_entry.pack(side=tk.LEFT, padx=7)
        self.date_start_label.pack(side=tk.LEFT)
        self.date_start_entry.pack(side=tk.LEFT, padx=6)
        self.nds0.pack(side=tk.RIGHT, padx=7)
        self.nds20.pack(side=tk.RIGHT, padx=8)
        self.nds_label.pack(side=tk.RIGHT)

    def _row6_pack(self):
        self.okpo_label.pack(side=tk.LEFT, padx=7)
        self.okpo_entry.pack(side=tk.LEFT, padx=7)
        self.date_finish_label.pack(side=tk.LEFT)
        self.date_finish_entry.pack(side=tk.LEFT, padx=0)
        self.file_label.pack(side=tk.RIGHT, padx=0)

    def _top_pack(self):
        self.main_label.pack(side=tk.TOP, expand=False, anchor=tk.NW)

    def _validate_request_creation(self, messagetitle, sumtotal):
        """ Check if all fields are filled properly. """
        if not self.mvz_current.get():
            messagebox.showerror(
                messagetitle, 'Не выбран объект'
            )
            return False

        if not self.mvz_choice_list:
            messagebox.showerror(
                messagetitle, 'Не выбраны адреса к договору'
            )
            return False
        if not self.type_business_box.get():
            messagebox.showerror(
                messagetitle, 'Не выбран тип бизнеса'
            )
            return False
        if not self.num_main_contract_entry.get():
            messagebox.showerror(
                messagetitle, 'Не указан номер основного договора'
            )
            return False
        if not self.num_add_contract_entry.get():
            messagebox.showerror(
                messagetitle, 'Не указан номер дополнительного соглашения'
            )
            return False
        if not self.contragent_entry.get():
            messagebox.showerror(
                messagetitle, 'Не указан арендодатель'
            )
            return False
        if ast.literal_eval(self.square_entry.get()[0]) == 0:
            messagebox.showerror(
                messagetitle, 'Не указана площадь аренды'
            )
            return False
        if ast.literal_eval(self.square_cost_entry.get()[0]) == 0:
            messagebox.showerror(
                messagetitle, 'Не указана стоимость за 1 кв.м.'
            )
            return False
        return True


class UpdateForm(PaymentFrame):
    def __init__(self, parent, controller, connection, user_info, mvz,
                 type_business, **kwargs):
        super().__init__(parent, controller, connection, user_info, mvz)
        self.upload_filename = str()
        # print(self.mvz)
        # Top Frame with description and user name
        top = tk.Frame(self, name='top_cf', padx=5)
        self.main_label = tk.Label(top,
                                   text='Форма редактирования данных по договору',
                                   padx=10, font=('Arial', 8, 'bold'))
        self.type_businessID, self.type_business = zip(*type_business)
        self.mvz_choice_list = []
        self._add_user_label(top)
        self._top_pack()

        # First Fill Frame with (MVZ, business)
        row1_cf = tk.Frame(self, name='row1_cf', padx=15)

        self.mvz_label = tk.Label(row1_cf, text='Объект', padx=7)
        self.mvz_current = tk.StringVar()
        self.mvz_box = ttk.OptionMenu(row1_cf, self.mvz_current, '',
                                      *self.mvz.keys(),
                                      command=self._restraint_by_mvz)
        self.mvz_box.config(width=40)
        # self.mvz_sap_label = tk.Label(row1_cf, text='SAPmvz', padx=10)
        # self.mvz_sap = tk.Label(row1_cf, padx=10, bg='lightgray', width=11)

        self.menubutton = tk.Menubutton(row1_cf, text="Выбрать адреса договора",
                                        indicatoron=True, borderwidth=1,
                                        relief="raised")
        self.menu_choice_mvz = tk.Menu(self.menubutton, tearoff=False)
        self.menubutton.configure(menu=self.menu_choice_mvz)

        self.choices = {}
        for choice in self.mvz.keys():
            self.choices[choice] = tk.IntVar(value=0)
            self.menu_choice_mvz.add_checkbutton(label=choice,
                                                 variable=self.choices[choice],
                                                 onvalue=1, offvalue=0,
                                                 command=self._mvz_choice_list)

        self.square = StringSumVar()
        self.square.set('0,00')
        self.square_label = tk.Label(row1_cf, text='Площадь, м²')
        vcmd = (self.register(self._validate_sum))
        self.square_entry = tk.Entry(row1_cf, name='square_entry', width=18,
                                     textvariable=self.square, validate='all',
                                     validatecommand=(vcmd, '%P')
                                     )
        self.square_entry.bind("<FocusIn>", self._on_focus_in_format_sum)
        self.square_entry.bind("<FocusOut>", self._on_focus_out_format_sum)

        self._row1_pack()

        # Second Fill Frame
        row2_cf = tk.Frame(self, name='row2_cf', padx=15)
        self.type_business_label = tk.Label(row2_cf, text='Тип бизнеса', padx=7)
        self.type_business_box = ttk.Combobox(row2_cf, width=20,
                                              state='readonly')
        self.type_business_box['values'] = self.type_business
        self.type_business_box.configure(state="normal")
        self.date_main_label_start = tk.Label(row2_cf, text='Договор с:',
                                              padx=12)
        self.date_main_start = tk.StringVar()
        self.date_main_contract_start = DateEntry(row2_cf, width=16,
                                                  state='readonly',
                                                  textvariable=self.date_main_start,
                                                  font=('Arial', 9),
                                                  selectmode='day',
                                                  borderwidth=2,
                                                  locale='ru_RU')
        self.square_cost = StringSumVar()
        self.square_cost.set('0,00')
        self.square_cost_label = tk.Label(row2_cf, text='Цена за 1м², грн')
        vcmd = (self.register(self._validate_sum))
        self.square_cost_entry = tk.Entry(row2_cf, name='square_cost_entry',
                                          width=18,
                                          textvariable=self.square_cost,
                                          validate='all',
                                          validatecommand=(vcmd, '%P')
                                          )
        self.square_cost_entry.bind("<FocusIn>", self._on_focus_in_format_sum)
        # Change format price to max decimal format
        self.square_cost_entry.bind("<FocusOut>",
                                    self._on_focus_out_format_sum_decimal)

        self._row2_pack()

        # Third Fill Frame
        row3_cf = tk.Frame(self, name='row3_cf', padx=15)

        self.num_main_contract = tk.Label(row3_cf, text='№ договора', padx=0)
        self.num_main_contract_entry = tk.Entry(row3_cf, width=23)
        self.date_main_label_end = tk.Label(row3_cf, text='Договор по:', padx=7)
        self.date_main_end = tk.StringVar()
        self.date_main_contract_end = DateEntry(row3_cf, width=16,
                                                state='readonly',
                                                textvariable=self.date_main_end,
                                                font=('Arial', 9),
                                                selectmode='day', borderwidth=2,
                                                locale='ru_RU')
        self.sum_extra_label = tk.Label(row3_cf,
                                        text='Сумма экспл. без НДС, грн',
                                        padx=3)
        self.sum_extra_total = StringSumVar()
        self.sum_extra_total.set('0,00')
        vcmd = (self.register(self._validate_sum))
        self.sum_extra_entry = tk.Entry(row3_cf, name='sum_extra_entry',
                                        width=18,
                                        textvariable=self.sum_extra_total,
                                        validate='all',
                                        validatecommand=(vcmd, '%P')
                                        )
        self.sum_extra_entry.bind("<FocusIn>", self._on_focus_in_format_sum)
        self.sum_extra_entry.bind("<FocusOut>", self._on_focus_out_format_sum)

        self._row3_pack()

        # Fourth Fill Frame
        row4_cf = tk.Frame(self, name='row4_cf', padx=15)

        self.num_add_contract = tk.Label(row4_cf, text='№ доп.дог.  ', padx=0)
        self.num_add_contract_entry = tk.Entry(row4_cf, width=23)
        self.date_add_label = tk.Label(row4_cf, text='Дата доп.', padx=7)
        self.date_add = tk.StringVar()
        self.date_add_contract = DateEntry(row4_cf, width=16, state='readonly',
                                           textvariable=self.date_add,
                                           font=('Arial', 9),
                                           selectmode='day', borderwidth=2,
                                           locale='ru_RU')
        self.sum_label = tk.Label(row4_cf, text='Сумма всего без НДС, грн',
                                  padx=3)
        self.sumtotal = tk.StringVar(row4_cf, value='0.00')
        vcmd = (self.register(self._validate_sum))
        # self.sum_entry = tk.Entry(row4_cf, textvariable=self.sumtotal, width=18)
        self.sum_entry = tk.Entry(row4_cf, name='sum_entry',
                                  width=18,
                                  textvariable=self.sumtotal,
                                  validate='all',
                                  validatecommand=(vcmd, '%P')
                                  )
        self.sum_entry.config(background='lightgrey')
        # self.sum_entry.config(state='disabled')

        self.sum_entry.bind("<FocusIn>", self._on_focus_in_format_sum)
        self.sum_entry.bind("<FocusOut>", self._on_focus_out_format_sum)

        self._row4_pack()

        # Fifth Fill Frame
        row5_cf = tk.Frame(self, name='row5_cf', padx=15)
        self.contragent_label = tk.Label(row5_cf, text='Арендодатель')
        self.contragent_entry = tk.Entry(row5_cf, width=23)
        self.date_start_label = tk.Label(row5_cf, text='Период с:', padx=17)
        self.date_start = tk.StringVar()
        self.date_start_entry = DateEntry(row5_cf, width=16, state='readonly',
                                          textvariable=self.date_start,
                                          font=('Arial', 9),
                                          selectmode='day', borderwidth=2,
                                          locale='ru_RU')
        self.nds_label = tk.Label(row5_cf, text='Ставка НДС', padx=0)
        self.nds = tk.IntVar()
        self.nds.set(20)
        self.nds20 = ttk.Radiobutton(row5_cf, text="20 %", variable=self.nds,
                                     value=20)
        self.nds0 = ttk.Radiobutton(row5_cf, text="0 %", variable=self.nds,
                                    value=0)

        self._row5_pack()

        # Six Fill Frame
        row6_cf = tk.Frame(self, name='row6_cf', padx=15)

        self.okpo_label = tk.Label(row6_cf, text='ЕГРПОУ           ')
        self.okpo_entry = tk.Entry(row6_cf, width=23)
        self.date_finish_label = tk.Label(row6_cf, text='Период по:', padx=16)
        self.date_finish = tk.StringVar()
        self.date_finish_entry = DateEntry(row6_cf, width=16, state='readonly',
                                           textvariable=self.date_finish,
                                           font=('Arial', 9),
                                           selectmode='day', borderwidth=2,
                                           locale='ru_RU')
        self.file_label = tk.Label(row6_cf, text='Файл не выбран')
        bt_upload = ttk.Button(row6_cf, text="Выбрать файл", width=20,
                               command=self._file_opener,
                               style='ButtonGreen.TButton')
        bt_upload.pack(side=tk.RIGHT, padx=15, pady=0)

        # Text Frame
        text_cf = ttk.LabelFrame(self, text=' Комментарий к договору ',
                                 name='text_cf')

        self.customFont = tkFont.Font(family="Arial", size=10)
        self.desc_text = tk.Text(text_cf,
                                 font=self.customFont)  # input and output box
        self.desc_text.configure(width=115)
        self.desc_text.pack(in_=text_cf, expand=True)

        self._row6_pack()

        # Bottom Frame with buttons
        bottom_cf = tk.Frame(self, name='bottom_cf')

        bt3 = ttk.Button(bottom_cf, text="Назад", width=10,
                         # command=self._deselect_checked_mvz)
                         # command=self.button_back(controller))
                         command=lambda: controller._show_frame('PreviewForm'))
        bt3.pack(side=tk.RIGHT, padx=15, pady=10)

        bt1 = ttk.Button(bottom_cf, text="Обновить", width=10,
                         command=self._update_request,
                         style='ButtonGreen.TButton')
        bt1.pack(side=tk.RIGHT, padx=15, pady=10)

        # Pack frames
        top.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        bottom_cf.pack(side=tk.BOTTOM, fill=tk.X)
        row1_cf.pack(side=tk.TOP, fill=tk.X, pady=5)
        row2_cf.pack(side=tk.TOP, fill=tk.X, pady=5)
        row3_cf.pack(side=tk.TOP, fill=tk.X, pady=5)
        row4_cf.pack(side=tk.TOP, fill=tk.X, pady=5)
        row5_cf.pack(side=tk.TOP, fill=tk.X, pady=5)
        row6_cf.pack(side=tk.TOP, fill=tk.X, pady=5)
        text_cf.pack(side=tk.TOP, fill=tk.X, expand=True, padx=15, pady=15)

    def _mvz_choice_list(self):
        self.mvz_choice_list = []
        for name, var in self.choices.items():
            if var.get() == 1:
                self.mvz_choice_list.append(self.get_mvzID(name))

    # Deselect checked row in menu (destroy and create menubutton again)
    def _deselect_checked_mvz(self):
        self.mvz_choice_list.clear()
        self.menu_choice_mvz.destroy()
        self.menu_choice_mvz = tk.Menu(self.menubutton, tearoff=False)
        self.menubutton.configure(menu=self.menu_choice_mvz)
        for choice in self.mvz.keys():
            self.choices[choice] = tk.IntVar(value=0)
            self.menu_choice_mvz.add_checkbutton(label=choice,
                                                 variable=self.choices[choice],
                                                 onvalue=1, offvalue=0,
                                                 command=self._mvz_choice_list)

    def _file_opener(self):
        filename = fd.askopenfilename()
        if filename:
            copy2(filename, UPLOAD_PATH)
            path = Path(filename)
            self.upload_filename = path.name
            self.file_label.config(text='Файл добавлен')

    def _remove_upload_file(self):
        os.remove(UPLOAD_PATH + '\\' + self.upload_filename)
        self.file_label.config(text='Файл не выбран')

    def _multiply_cost_square(self):
        square_get = float(self.square.get_float_form()
                           if self.square_entry.get() else 0)
        square_cost_get = float(self.square_cost.get_float_form()
                                if self.square_cost_entry.get() else 0)
        total_square_cost = square_get * square_cost_get
        if total_square_cost:
            self.sum_entry.delete(0, tk.END)
            self.sum_entry.insert(0, total_square_cost)

    def _clear(self):
        self.type_business_box.configure(state="readonly")
        self.num_main_contract_entry.configure(state="normal")
        self.date_main_contract_start.configure(state="normal")
        self.date_main_contract_end.configure(state="normal")
        self.contragent_entry.configure(state="normal")
        self.num_main_contract_entry.delete(0, tk.END)
        self.contragent_entry.delete(0, tk.END)
        self.square.set('0,00')
        self.square_cost_entry.delete(0, tk.END)
        self.square_cost_entry.insert(0, '0,00')
        self.num_main_contract_entry.delete(0, tk.END)
        self.num_add_contract_entry.delete(0, tk.END)
        self.okpo_entry.delete(0, tk.END)
        self.sum_extra_total.set('0,00')
        self.sumtotal.set('0,00')
        self.nds.set(20)
        self.desc_text.delete("1.0", tk.END)
        self.date_start_entry.set_date(datetime.now())
        self.date_finish_entry.set_date(datetime.now())
        self.date_add_contract.set_date(datetime.now())
        self.date_main_contract_start.set_date(datetime.now())
        self.date_main_contract_end.set_date(datetime.now())
        self.file_label.config(text='Файл не выбран')
        self._deselect_checked_mvz()

    def _fill_from_UpdateForm(self, mvz, id, num_main_contract,
                              date_main_contract_start,
                              date_main_contract_end, date_add_contract,
                              date_add_contract_end,
                              add_contract_num, date_add_contract_start, square,
                              price1m2, cost_extra, cost, contragent,
                              business, okpo, description, filename):
        """ When button "Редактировать" from PreviewForm is activated,
        fill some fields taken from choosed in PreviewForm request.
        """
        self.contract_id = id
        self.mvz_current.set(mvz)
        self.type_business_box.set(business)
        self.num_main_contract_entry.delete(0, tk.END)
        self.num_main_contract_entry.insert(0, num_main_contract)
        self.num_add_contract_entry.insert(0, add_contract_num)
        self.date_add_contract.set_date(
            self._convert_str_date(date_add_contract))
        self.date_start_entry.set_date(
            self._convert_str_date(date_add_contract_start))
        self.date_finish_entry.set_date(
            self._convert_str_date(date_add_contract_end))
        self.date_main_contract_start.set_date(
            self._convert_str_date(date_main_contract_start))
        self.date_main_contract_end.set_date(
            self._convert_str_date(date_main_contract_end))

        self.mvz_sap = self.get_mvzSAP(self.mvz_current.get())
        self.contragent_entry.delete(0, tk.END)
        self.contragent_entry.insert(0, contragent)
        self.okpo_entry.insert(0, okpo)
        self.square_cost.set(price1m2)
        self.square.set(square)
        self.sum_extra_entry.insert(0, cost)
        self.sum_entry.insert(0, cost_extra)
        self.desc_text.insert("1.0", description)
        self.fill_filename = filename
        if filename:
            self.file_label.config(text='Файл добавлен')
        self._multiply_cost_square()

    def _convert_date(self, date, output=None):
        """ Take date and convert it into output format.
            If output is None datetime object is returned.

            date: str in format '%d[./]%m[./]%y' or '%d[./]%m[./]%Y'.
            output: str or None, output format.
        """
        date = date.replace('/', '.')
        try:
            dat = datetime.strptime(date, '%d.%m.%y')
        except ValueError:
            dat = datetime.strptime(date, '%d.%m.%Y')
        if output:
            return dat.strftime(output)
        return dat

    def _update_request(self):
        messagetitle = 'Обновление договора'
        sumtotal = self.sum_entry.get()
        sum_extra_total = float(self.sum_extra_total.get_float_form()
                                if self.sum_extra_entry.get() else 0)
        square = float(self.square.get_float_form()
                       if self.square_entry.get() else 0)
        price_meter = float(self.square_cost.get_float_form()
                            if self.square_cost_entry.get() else 0)
        is_validated = self._validate_request_creation(messagetitle, sumtotal)
        if not is_validated:
            return

        update_request = {'id': self.contract_id,
                          'mvz': self.mvz_sap,
                          # self.mvz_sap.cget('text') or None,
                          'start_date': self._convert_date(
                              self.date_start_entry.get()),
                          'finish_date': self._convert_date(
                              self.date_finish_entry.get()),
                          'sum_extra_total': sum_extra_total,
                          'sumtotal': sumtotal,
                          'nds': self.nds.get(),
                          'square': square,
                          'contragent': self.contragent_entry.get().strip().replace(
                              '\n', '') or None,
                          'okpo': self.okpo_entry.get(),
                          'num_main_contract': self.num_main_contract_entry.get(),
                          'num_add_contract': self.num_add_contract_entry.get(),
                          'date_main_contract_start': self._convert_date(
                              self.date_main_contract_start.get()),
                          'date_add_contract': self._convert_date(
                              self.date_add_contract.get()),
                          'text': self.desc_text.get("1.0", tk.END).strip(),
                          'filename': self.fill_filename if self.fill_filename else self.upload_filename,
                          'date_main_contract_end': self._convert_date(
                              self.date_main_contract_end.get()),
                          'price_meter': price_meter,
                          'type_business': self.type_business_box.get(),
                          'mvz_choice_list': ','.join(
                              map(str, self.mvz_choice_list))

                          }
        update_success = self.conn.update_request(userID=self.userID,
                                                  **update_request)
        if update_success == 1:
            messagebox.showinfo(
                messagetitle, 'Договор обновлен'
            )
            self._clear()
            self.controller._show_frame('PreviewForm')
        else:
            # self._remove_upload_file()
            messagebox.showerror(
                messagetitle, 'Произошла ошибка при обновлении договора'
            )

            # МВЗ, Договор, Арендодатель, ЕГРПОУ, Описание

    def _convert_str_date(self, date):
        """ Take str and convert it into date format.
            date: str in format '%d[./]%m[./]%y' or '%d[./]%m[./]%Y'.
        """
        date_time_str = date
        date_time_obj = dt.datetime.strptime(date_time_str, '%Y-%m-%d')
        return date_time_obj.date()

    def _restraint_by_mvz(self, event):
        """ Shows mvz_sap that corresponds to chosen MVZ and restraint offices.
            If 1 office is available, choose it, otherwise make box active.
        """
        # tcl language has no notion of None or a null value, so use '' instead
        self.mvz_sap = self.get_mvzSAP(self.mvz_current.get()) or ''

    def _row1_pack(self):
        self.mvz_label.pack(side=tk.LEFT)
        self.mvz_box.pack(side=tk.LEFT, padx=10)
        # self.mvz_sap_label.pack(side=tk.LEFT)
        # self.mvz_sap.pack(side=tk.LEFT)
        self.menubutton.pack(side=tk.LEFT, padx=10)
        self.square_entry.pack(side=tk.RIGHT, padx=10)
        self.square_label.pack(side=tk.RIGHT, padx=10)

    def _row2_pack(self):
        self.type_business_label.pack(side=tk.LEFT)
        self.type_business_box.pack(side=tk.LEFT, padx=17)
        self.date_main_label_start.pack(side=tk.LEFT)
        self.date_main_contract_start.pack(side=tk.LEFT, padx=0)
        self.square_cost_entry.pack(side=tk.RIGHT, padx=10)
        self.square_cost_label.pack(side=tk.RIGHT, padx=10)

    def _row3_pack(self):
        self.num_main_contract.pack(side=tk.LEFT, padx=7)
        self.num_main_contract_entry.pack(side=tk.LEFT, padx=19)
        self.date_main_label_end.pack(side=tk.LEFT)
        self.date_main_contract_end.pack(side=tk.LEFT, padx=0)
        self.sum_extra_entry.pack(side=tk.RIGHT, padx=11)
        self.sum_extra_label.pack(side=tk.RIGHT, padx=0)

    def _row4_pack(self):
        self.num_add_contract.pack(side=tk.LEFT, padx=7)
        self.num_add_contract_entry.pack(side=tk.LEFT, padx=19)
        self.date_add_label.pack(side=tk.LEFT)
        self.date_add_contract.pack(side=tk.LEFT, padx=18)
        self.sum_entry.pack(side=tk.RIGHT, padx=11)
        self.sum_label.pack(side=tk.RIGHT, padx=0)

    def _row5_pack(self):
        self.contragent_label.pack(side=tk.LEFT, padx=7)
        self.contragent_entry.pack(side=tk.LEFT, padx=7)
        self.date_start_label.pack(side=tk.LEFT)
        self.date_start_entry.pack(side=tk.LEFT, padx=6)
        self.nds0.pack(side=tk.RIGHT, padx=7)
        self.nds20.pack(side=tk.RIGHT, padx=8)
        self.nds_label.pack(side=tk.RIGHT)

    def _row6_pack(self):
        self.okpo_label.pack(side=tk.LEFT, padx=7)
        self.okpo_entry.pack(side=tk.LEFT, padx=7)
        self.date_finish_label.pack(side=tk.LEFT)
        self.date_finish_entry.pack(side=tk.LEFT, padx=0)
        self.file_label.pack(side=tk.RIGHT, padx=0)

    def _top_pack(self):
        self.main_label.pack(side=tk.TOP, expand=False, anchor=tk.NW)

    def _validate_request_creation(self, messagetitle, sumtotal):
        """ Check if all fields are filled properly. """
        if not self.mvz_current.get():
            messagebox.showerror(
                messagetitle, 'Не выбран объект'
            )
            return False

        if not self.mvz_choice_list:
            messagebox.showerror(
                messagetitle, 'Не выбраны адреса к договору'
            )
            return False
        if not self.type_business_box.get():
            messagebox.showerror(
                messagetitle, 'Не выбран тип бизнеса'
            )
            return False
        if not self.num_main_contract_entry.get():
            messagebox.showerror(
                messagetitle, 'Не указан номер основного договора'
            )
            return False
        if not self.num_add_contract_entry.get():
            messagebox.showerror(
                messagetitle, 'Не указан номер дополнительного соглашения'
            )
            return False
        if not self.contragent_entry.get():
            messagebox.showerror(
                messagetitle, 'Не указан арендодатель'
            )
            return False
        if ast.literal_eval(self.square_entry.get()[0]) == 0:
            messagebox.showerror(
                messagetitle, 'Не указана площадь аренды'
            )
            return False
        if ast.literal_eval(self.square_cost_entry.get()[0]) == 0:
            messagebox.showerror(
                messagetitle, 'Не указана стоимость за 1 кв.м.'
            )
            return False
        return True


class PreviewForm(PaymentFrame):
    def __init__(self, parent, controller, connection, user_info,
                 mvz, type_business, status_list, **kwargs):
        super().__init__(parent, controller, connection, user_info, mvz)

        self.statusID, self.status_list = zip(*[(None, 'Все'), ] + status_list)
        self.type_businessID, self.type_business = zip(
            *[(None, 'Все'), ] + type_business)
        # print(self.statusID, self.status_list)

        # List of functions to get payments
        # determines what payments will be shown when refreshing
        self.contracts_load_list = [self._get_all_contracts]
        self.get_contracts = self._get_all_contracts
        # Parameters for sorting
        self.rows = None  # store all rows for sorting and redrawing
        self.sort_reversed_index = None  # reverse sorting for the last sorted column
        self.month = list(month_name)
        self.month_default = self.month[datetime.now().month]

        # Top Frame with description and user name
        top = tk.Frame(self, name='top_cf', padx=5)

        main_label = tk.Label(top, text='Просмотр договоров',
                              padx=5, font=('Calibri', 10, 'bold'))
        main_label.pack(side=tk.LEFT, expand=False, anchor=tk.NW)

        self._add_copyright(top)
        self._add_user_label(top)

        top.pack(side=tk.TOP, fill=tk.X, expand=False)

        # Filters
        filterframe = ttk.LabelFrame(self, text=' Фильтры ', name='filterframe')

        # First Filter Frame with (MVZ, office)
        row1_cf = tk.Frame(filterframe, name='row1_cf', padx=15, pady=5)

        self.mvz_label = tk.Label(row1_cf, text='Объект', padx=10)
        self.mvz_box = ttk.Combobox(row1_cf, width=45, state='readonly')
        self.mvz_box['values'] = list(self.mvz)

        self.type_business_label = tk.Label(row1_cf, text='Тип бизнеса',
                                            padx=20)
        self.type_business_box = ttk.Combobox(row1_cf, width=15,
                                              state='readonly')
        self.type_business_box['values'] = self.type_business

        self.status_label = tk.Label(row1_cf, text='Статус договора', padx=20)
        self.status_box = ttk.Combobox(row1_cf, width=10, state='readonly')
        self.status_box['values'] = self.status_list

        self.bt3_1 = ttk.Button(row1_cf, text="Применить фильтр", width=20,
                                command=self._use_filter_and_refresh)
        self.bt3_2 = ttk.Button(row1_cf, text="Очистить фильтр", width=20,
                                command=self._clear_filters)

        # Pack row1_cf
        self._row1_pack()
        row1_cf.pack(side=tk.TOP, fill=tk.X)

        # Second Fill Frame with (Plan date, Sum, Tax)
        row2_cf = tk.Frame(filterframe, name='row2_cf', padx=15)

        self.date_label = tk.Label(row2_cf, text='Дата', padx=10)
        self.date_type = ttk.Combobox(row2_cf, width=12, state='readonly')
        self.date_type['values'] = ['плановая', 'создания']
        self.date_label_m = tk.Label(row2_cf, text=':  месяц', padx=10)
        self.date_entry_m = MultiselectMenu(row2_cf, self.month_default,
                                            self.month, width=15)
        self.date_label_y = tk.Label(row2_cf, text='год', padx=20)
        self.year = tk.IntVar()
        self.date_entry_y = tk.Spinbox(row2_cf, width=7, from_=2019, to=2059,
                                       font=('Arial', 9),
                                       textvariable=self.year)

        # Pack row2_cf
        self._row2_pack()
        row2_cf.pack(side=tk.TOP, fill=tk.X)
        filterframe.pack(side=tk.TOP, fill=tk.X, expand=False, padx=10, pady=5)

        # Third Fill Frame (checkbox + button to apply filter)
        row3_cf = tk.Frame(filterframe, name='row3_cf', padx=15)

        # Pack row3_cf
        self._row3_pack()
        row3_cf.pack(side=tk.TOP, fill=tk.X, pady=10)

        # Set all filters to default
        self._clear_filters()

        # Text Frame
        preview_cf = ttk.LabelFrame(self, text=' Список договоров ',
                                    name='preview_cf')

        # column name and width
        self.headings = {'№ п/п': 40, 'ID': 0, 'InitiatorID': 0,
                         'Кем создано': 80, 'Дата внесения': 90, 'SAPmvz': 70,
                         'Объект': 0, 'Бизнес': 0, 'Арендодатель': 130,
                         'ЕГРПОУ': 0,
                         '№ договора': 80
            , 'Дата договора (начало)': 0, 'Дата договора (конец)': 0
            , '№ доп.согл.': 80, 'Дата доп.согл.': 80
            , 'Дата с': 80, 'Дата по': 90, 'Площадь': 50, 'Цена за 1м²': 70
            , 'Сумма экспл. без НДС': 0, 'Сумма без НДС': 85
            , 'Сумма с НДС': 85, 'Файл': 40, 'Имя файла': 0, 'Статус': 80
            , 'Описание': 12
                         }

        self.table = ttk.Treeview(preview_cf, show='headings',
                                  selectmode='browse',
                                  style='HeaderStyle.Treeview'
                                  )

        self._init_table(preview_cf)
        self.table.pack(expand=tk.YES, fill=tk.BOTH)

        # asserts for headings used through script as indices
        head = self.table["columns"]
        msg = 'Heading order must be reviewed. Wrong heading: '
        assert head[1] == 'ID', '{}ID'.format(msg)
        assert head[-2] == 'Статус', '{}Статус'.format(msg)
        assert head[-5] == 'Сумма с НДС', '{}Сумма с НДС'.format(msg)

        # Bottom Frame with buttons
        bottom_cf = tk.Frame(self, name='bottom_cf')
        # Show create buttons only for users with rights
        # to create (1) or approve + create (2)
        if self.user_info.AccessType in (1, 2):
            bt1 = ttk.Button(bottom_cf, text="Добавить", width=25,
                             command=lambda: controller._show_frame(
                                 'CreateForm'))
            bt1.pack(side=tk.LEFT, padx=10, pady=10)

            bt2 = ttk.Button(bottom_cf, text="Добавить доп.согл. из договора",
                             width=30,
                             command=self._create_from_current)
            bt2.pack(side=tk.LEFT, padx=10, pady=10)

            if self.userID in (2, 6, 1):
                bt3 = ttk.Button(bottom_cf, text="Редактировать",
                                 width=20,
                                 command=self._edit_current_contract)
                bt3.pack(side=tk.LEFT, padx=10, pady=10)

        bt6 = ttk.Button(bottom_cf, text="Выход", width=10,
                         command=controller._quit)
        bt6.pack(side=tk.RIGHT, padx=10, pady=10)

        bt5 = ttk.Button(bottom_cf, text="Подробно", width=10,
                         command=self._show_detail)
        bt5.pack(side=tk.RIGHT, padx=10, pady=10)

        bt4 = ttk.Button(bottom_cf, text="Экспорт в Excel", width=15,
                         command=self._export_to_excel)
        bt4.pack(side=tk.RIGHT, padx=10, pady=10)

        # Pack frames
        bottom_cf.pack(side=tk.BOTTOM, fill=tk.X, expand=False)
        preview_cf.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)

    def _add_copyright(self, parent):
        """ Adds user name in the top right corner. """
        copyright_label = tk.Label(parent, text="О программе",
                                   font=('Arial', 8, 'underline'),
                                   cursor="hand2")
        copyright_label.bind("<Button-1>", self._show_about)
        copyright_label.pack(side=tk.RIGHT, anchor=tk.N)

    def _center_popup_window(self, newlevel, w, h, static_geometry=True):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        start_x = int((screen_width / 2) - (w / 2))
        start_y = int((screen_height / 2) - (h * 0.7))

        if static_geometry == True:
            newlevel.geometry('{}x{}+{}+{}'.format(w, h, start_x, start_y))
        else:
            newlevel.geometry('+{}+{}'.format(start_x, start_y))

    def _change_preview_state(self, new_state):
        """ Change payments state that determines which payments will be shown.
        """
        if new_state == 'Show payments according to filters':
            self.get_contractss = self._get_all_contracts
        elif new_state == 'Show payments for approval':
            self.get_contracts = self._get_payments_for_approval

    def _clear_filters(self):
        # self.initiator_box.set('Все')
        self.mvz_box.set('Все')
        self.type_business_box.set('Все')
        self.status_box.set('Все')
        self.date_type.set('плановая')
        self.date_entry_m.set_default_option()
        self.year.set(datetime.now().year)

    def _create_from_current(self):
        """ Raises CreateForm with partially filled labels/entries. """
        curRow = self.table.focus()

        if curRow:
            # extract info to be putted in CreateForm
            to_fill = dict(zip(self.table["columns"],
                               self.table.item(curRow).get('values')))
            # print(to_fill)
            self.controller._fill_CreateForm(**to_fill)
            self.controller._show_frame('CreateForm')

    def _edit_current_contract(self):
        """ Raises UpdateForm with partially filled labels/entries. """
        curRow = self.table.focus()

        if curRow:
            # extract info to be putted in CreateForm
            to_fill = dict(zip(self.table["columns"],
                               self.table.item(curRow).get('values')))
            # print(to_fill)
            # current_contract_info = self.conn.get_current_contract(to_fill.get('ID'))
            objects = self.conn.get_additional_objects(to_fill.get('ID'))
            self.controller._fill_UpdateForm(**to_fill)
            self.controller._show_frame('UpdateForm')

    def _delete_current(self):
        """ Raises CreateForm with partially filled labels/entries. """
        curRow = self.table.focus()

        if curRow:
            # extract info to be putted in CreateForm
            to_fill = dict(zip(self.table["columns"],
                               self.table.item(curRow).get('values')))

    def _export_to_excel(self):
        if not self.rows:
            return
        headings = {k: v for k, v in self.headings.items() if k != '№ п/п'}
        isExported = export_to_excel(headings, self.rows)
        if isExported:
            messagebox.showinfo(
                'Экспорт в Excel',
                'Данные экспортированы на рабочий стол'
            )
        else:
            messagebox.showerror(
                'Экспорт в Excel',
                'При экспорте произошла непредвиденная ошибка'
            )

    def _get_all_contracts(self):
        """ Extract information from filters and get payments list. """
        filters = {
            'mvz': self.get_mvzSAP(self.mvz_box.get()),
            'statusID': (self.statusID[self.status_box.current()]),
            'type_businessID': (
                self.type_businessID[self.type_business_box.current()])
        }
        # if not filters['date_m']:
        #     raise MonthFilterError(filters['date_m'])
        self.rows = self.conn.get_contracts_list(**filters)

    def _init_table(self, parent):
        """ Creates treeview. """
        if isinstance(self.headings, dict):
            self.table["columns"] = tuple(self.headings.keys())
            self.table["displaycolumns"] = tuple(k for k in self.headings.keys()
                                                 if k not in (
                                                     'ID', 'НДС', 'Описание',
                                                     'Бизнес', 'Объект',
                                                     'InitiatorID',
                                                     'Инициатор', 'Кем создано'
                                                     , '№ заявки',
                                                     'Дата договора (начало)',
                                                     'Дата договора (конец)'
                                                     , 'ЕГРПОУ'
                                                     , 'Сумма экспл. без НДС'
                                                     # , 'Цена за 1 кв.м.'
                                                     , 'Имя файла'))
            for head, width in self.headings.items():
                self.table.heading(head, text=head, anchor=tk.CENTER)
                self.table.column(head, width=width, anchor=tk.CENTER)

        else:
            self.table["columns"] = self.headings
            self.table["displaycolumns"] = self.headings
            for head in self.headings:
                self.table.heading(head, text=head, anchor=tk.CENTER)
                self.table.column(head, width=50 * len(head), anchor=tk.CENTER)

        for tag, bg in zip(self.status_list[1:3],
                           ('#e0e0d1', '#9ae59a')):
            self.table.tag_configure(tag, background=bg)

        self.table.bind('<Double-1>', self._show_detail)
        self.table.bind('<Button-1>', self._sort, True)

        scrolltable = tk.Scrollbar(parent, command=self.table.yview)
        self.table.configure(yscrollcommand=scrolltable.set)
        scrolltable.pack(side=tk.RIGHT, fill=tk.Y)

    def _open_report(self):
        """ Open independent report. """
        os.startfile(os.path.join(REPORT_PATH, 'Договора аренды.xlsb'))

    def _raise_Toplevel(self, frame, title, width, height,
                        static_geometry=True, options=()):
        """ Create and raise new frame with limits.
        Input:
        frame - class, Frame class to be drawn in Toplevel;
        title - str, window title;
        width - int, width parameter to center window;
        height - int, height parameter to center window;
        static_geometry - bool, if True - width and height will determine size
            of window, otherwise size will be determined dynamically;
        options - tuple, arguments that will be sent to frame.
        """
        newlevel = tk.Toplevel(self.parent)
        # newlevel.transient(self)  # disable minimize/maximize buttons
        newlevel.title(title)
        newlevel.bind('<Escape>', lambda e, w=newlevel: w.destroy())
        frame(newlevel, *options)
        newlevel.resizable(width=False, height=False)
        self._center_popup_window(newlevel, width, height, static_geometry)
        newlevel.focus()
        newlevel.grab_set()

    def _refresh(self):
        """ Refresh information about payments. """
        try:
            self.get_contracts()
        except MonthFilterError as e:
            messagebox.showerror(self.controller.title(), e.message)
            return
        self._show_rows(self.rows)

    def _resize_columns(self):
        """ Resize columns in treeview. """
        self.table.column('#0', width=36)
        for head, width in self.headings.items():
            self.table.column(head, width=width)

    def _row1_pack(self):
        self.mvz_label.pack(side=tk.LEFT)
        self.mvz_box.pack(side=tk.LEFT, padx=5, pady=5)
        self.type_business_label.pack(side=tk.LEFT)
        self.type_business_box.pack(side=tk.LEFT, padx=5, pady=5)
        self.status_label.pack(side=tk.LEFT)
        self.status_box.pack(side=tk.LEFT, padx=5, pady=5)

        self.bt3_2.pack(side=tk.RIGHT, padx=10)
        self.bt3_1.pack(side=tk.RIGHT, padx=10)

    def _row2_pack(self):
        pass

    def _row3_pack(self):
        pass

    def _show_about(self, event=None):
        """ Raise frame with info about app. """
        self._raise_Toplevel(frame=AboutFrame,
                             title='Учёт договоров аренды ',
                             width=400, height=150)

    def _show_detail(self, event=None):
        """ Show details when double-clicked on row. """
        show_detail = (not event or (self.table.identify_row(event.y) and
                                     int(self.table.identify_column(event.x)[
                                         1:]) > 0
                                     )
                       )
        if show_detail:
            curRow = self.table.focus()
            if curRow:
                newlevel = tk.Toplevel(self.parent)
                newlevel.withdraw()
                # newlevel.transient(self.parent)  # disable minimize/maximize buttons
                newlevel.title('Информация по договору')
                newlevel.iconbitmap('resources/clipboard.ico')
                newlevel.bind('<Escape>', lambda e, w=newlevel: w.destroy())
                DetailedPreview(newlevel, self, self.conn, self.userID,
                                self.headings,
                                self.table.item(curRow).get('values'),
                                self.table.item(curRow).get('tags'))
                newlevel.resizable(width=False, height=False)
                # width is set implicitly in DetailedPreview._newRow
                # based on columnWidths values
                self._center_popup_window(newlevel, 500, 400,
                                          static_geometry=False)
                newlevel.deiconify()
                newlevel.focus()
                newlevel.grab_set()
        else:
            # if double click on header - redirect to sorting rows
            self._sort(event)

    def _sort(self, event):
        if self.table.identify_region(event.x,
                                      event.y) == 'heading' and self.rows:
            # determine index of displayed column
            disp_col = int(self.table.identify_column(event.x)[1:]) - 1
            if disp_col < 1:  # ignore sort by '№ п/п' and checkboxes
                return
            # determine index of this column in self.rows
            # substract 1 because of added '№ п/п' which don't exist in data
            sort_col = self.table["columns"].index(
                self.table["displaycolumns"][disp_col]) - 1
            self.rows.sort(key=lambda x: x[sort_col],
                           reverse=self.sort_reversed_index == sort_col)
            # store index of last sorted column if sort wasn't reversed
            self.sort_reversed_index = None if self.sort_reversed_index == sort_col else sort_col
            self._show_rows(self.rows)

    def _show_rows(self, rows):
        """ Refresh table with new rows. """
        self.table.delete(*self.table.get_children())

        if not rows:
            return
        for i, row in enumerate(rows):
            self.table.insert('', tk.END,
                              values=(i + 1,) + tuple(
                                  map(lambda val: self._format_float(val)
                                  if isinstance(val, Decimal) else val, row)),
                              tags=(row[-2], 'unchecked'))

    def _toggle_all_rows(self, event=None):
        if self.all_rows_checked.get():
            for item in self.table.get_children():
                self.table.check_item(item)
        else:
            for item in self.table.get_children():
                self.table.uncheck_item(item)

    def _use_filter_and_refresh(self):
        """ Change state to filter usage. """
        self._change_preview_state('Show payments according to filters')
        self._refresh()


class DetailedPreview(tk.Frame):
    """ Class that creates Frame with information about chosen request. """

    def __init__(self, parent, parentform, conn, userID, head, info, tags):
        super().__init__(parent)
        self.parent = parent
        self.parentform = parentform
        self.conn = conn
        # self.approveclass_bool = isinstance(self, ApproveConfirmation)
        self.contractID, self.initiatorID = info[1:3]
        self.userID = userID
        self.rowtags = tags
        self.filename_preview = str()
        # Top Frame with description and user name
        self.top = tk.Frame(self, name='top_cf', padx=5, pady=5)

        # Create a frame on the canvas to contain the buttons.
        self.table_frame = tk.Frame(self.top)

        # Add info to table_frame
        fonts = (('Arial', 9, 'bold'), ('Arial', 10))
        # filelink = str()
        for row in zip(range(len(head)), zip(head, info)):
            if row[1][0] not in ('№ п/п', 'ID', 'InitiatorID', 'Дата создания',
                                 'ID Утверждающего', 'Утверждающий', 'Статус',
                                 'Файл'):
                if row[1][0] == 'Имя файла' and (row[1][1] != 'None'
                                                 or row[1][1] is not None):
                    self.filename_preview = row[1][1]
                self._newRow(self.table_frame, fonts, *row)

        self.appr_label = tk.Label(self.top, text='Адреса по договору',
                                   padx=10, pady=5, font=('Arial', 10, 'bold'))

        # Top Frame with list mvz
        self.appr_cf = tk.Frame(self, name='appr_cf', padx=5)

        # Add list of all mvz for current contract
        fonts = (('Arial', 10), ('Arial', 10))
        approvals = self.conn.get_additional_objects(self.contractID)
        for rowNumber, row in enumerate(approvals):
            self._newRow(self.appr_cf, fonts, rowNumber + 1, row)

        self._add_buttons()
        self._pack_frames()

    def _open_file(self):
        pathToFile = UPLOAD_PATH + "\\" + self.filename_preview
        return os.startfile(pathToFile)

    def _add_buttons(self):
        # Bottom Frame with buttons
        self.bottom = tk.Frame(self, name='bottom')
        if self.filename_preview:
            bt1 = ttk.Button(self.bottom, text="Просмотреть файл", width=20,
                             command=self._open_file,
                             style='ButtonGreen.TButton')
            bt1.pack(side=tk.LEFT, padx=15, pady=10)

        bt2 = ttk.Button(self.bottom, text="Закрыть", width=10,
                         command=self.parent.destroy)
        bt2.pack(side=tk.RIGHT, padx=15, pady=10)

        # show delete button for users
        if self.userID in (2, 6, 1):
            bt3 = ttk.Button(self.bottom, text="Удалить договор", width=18,
                             command=self._delete)
            bt3.pack(side=tk.RIGHT, padx=15, pady=10)

    def _delete(self):
        mboxname = 'Удаление договора'
        confirmed = messagebox.askyesno(title=mboxname,
                                        message='Вы уверены, что хотите удалить '
                                                'этот договор?')
        if confirmed:
            self.conn.delete_contract(self.contractID)
            messagebox.showinfo(mboxname, 'Договор удален')
            self.parentform._refresh()
            self.parent.destroy()

    def _newRow(self, frame, fonts, rowNumber, info):
        """ Adds a new line to the table. """

        numberOfLines = []  # List to store number of lines needed
        columnWidths = [23, 50]  # Width of the different columns in the table

        # Find the length and the number of lines of each element and column
        for index, item in enumerate(info):
            # minimum 1 line + number of new lines + lines that too long
            numberOfLines.append(1 + str(item).count('\n') +
                                 sum(floor(len(s) / columnWidths[index]) for s
                                     in str(item).split('\n'))
                                 )

        # Find the maximum number of lines needed
        lineNumber = max(numberOfLines)

        # Define labels (columns) for row
        def form_column(rowNumber, lineNumber, col_num, cell, fonts):
            col = tk.Text(frame, bg='white', padx=3)
            col.insert(1.0, cell)
            col.grid(row=rowNumber, column=col_num + 1, sticky='news')
            col.configure(width=columnWidths[col_num],
                          height=min(9, lineNumber),
                          font=fonts[col_num], state="disabled")
            if lineNumber > 9 and col_num == 1:
                scrollbar = tk.Scrollbar(frame, command=col.yview)
                scrollbar.grid(row=rowNumber, column=col_num + 2, sticky='nsew')
                col['yscrollcommand'] = scrollbar.set

        for col_num, cell in enumerate(info):
            form_column(rowNumber, lineNumber, col_num, cell, fonts)

    def _pack_frames(self):
        self.top.pack(side=tk.TOP, fill=tk.X, expand=False)
        self.bottom.pack(side=tk.BOTTOM, fill=tk.X, expand=False)
        self.appr_cf.pack(side=tk.TOP, fill=tk.X)
        self.table_frame.pack()
        self.appr_label.pack(side=tk.LEFT, expand=False)
        self.pack()


class AboutFrame(tk.Frame):
    """ Creates a frame with copyright and info about app. """

    def __init__(self, parent):
        super().__init__(parent)

        self.top = ttk.LabelFrame(self, name='top_af')

        logo = tk.PhotoImage(file='resources/paper.png')
        self.logo_label = tk.Label(self.top, image=logo)
        self.logo_label.image = logo  # keep a reference to avoid gc!

        self.copyright_text = tk.Text(self.top, bg='#f1f1f1',
                                      font=('Arial', 8), relief=tk.FLAT)
        hyperlink = HyperlinkManager(self.copyright_text)

        def link_instruction():
            path = 'resources\\README.pdf'
            os.startfile(path)

        self.copyright_text.insert(tk.INSERT,
                                   'Платформа для учёта договоров аренды \n'
                                   '(версия ' + __version__ + ')\n')
        self.copyright_text.insert(tk.INSERT, "\n")

        def link_license():
            path = 'resources\\LICENSE.txt'
            os.startfile(path)

        self.copyright_text.insert(tk.INSERT,
                                   'Copyright © 2020 Департамент аналитики\n'
                                   'Офис контролинга логистики\n')
        self.copyright_text.insert(tk.INSERT, 'MIT License',
                                   hyperlink.add(link_license))

        self.bt = ttk.Button(self, text="Закрыть", width=10,
                             command=parent.destroy)
        self.pack_all()

    def pack_all(self):
        self.bt.pack(side=tk.BOTTOM, pady=5)
        self.top.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10)
        self.logo_label.pack(side=tk.LEFT, padx=10)
        self.copyright_text.pack(side=tk.LEFT, padx=10)
        self.pack(fill=tk.BOTH, expand=True)


if __name__ == '__main__':
    from db_connect import DBConnect
    from collections import namedtuple

    UserInfo = namedtuple('UserInfo', ['UserID', 'ShortUserName',
                                       'AccessType', 'isSuperUser', 'GroupID',
                                       'PayConditionsID'])

    with DBConnect(server='s-kv-center-s59', db='AnalyticReports') as sql:
        try:
            app = PaymentApp(connection=sql,
                             user_info=UserInfo(24, 'TestName', 2, 1, 1, 2),
                             mvz=[('20511RC191', '20511RC191', 'Офис'),
                                  ('40900A2595', '40900A2595', 'Офис')],
                             status_list=[(1, 'На согл.'), (2, 'Отозв.')]
                             )
            app.mainloop()
        except Exception as e:
            print(e)
            raise
    input('Press Enter...')
