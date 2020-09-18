# -*- coding: utf-8 -*-
"""
Created on Fri Jul  5 12:24:40 2019

@author: v.shkaberda
"""
from decimal import Decimal
from log_error import writelog
from pathlib import Path
from os import path
import time
import xlsxwriter

def export_to_excel(headers, rows):
    try:
        # Create a new Excel file and add a worksheet
        time_txt = time.strftime("%d-%m-%Y %H.%M.%S", time.localtime())
        wbpath = path.join(Path.home(), 'Desktop',
                              'Заявки на платежи ({}).xlsx'.format(time_txt))
        wb = xlsxwriter.Workbook(wbpath)
        ws = wb.add_worksheet()
        # default format
        wb.formats[0].set_font('Tahoma')
        wb.formats[0].set_font_size(8.5)
        ws.set_default_row(15.5)
        # Customizing style
        format_settings = {'align':'center',
                           'valign':'vcenter',
                           'bold':True,
                           'border':1,
                           'border_color':'FF000000',
                           'font':'Tahoma',
                           'font_size':8.5,
                           'pattern':1, # solid
                           'fg_color':"D3D3D3"
                           }
        header_format = wb.add_format(format_settings)
        datetime_format = wb.add_format({'font':'Tahoma', 'font_size':8.5})
        datetime_format.set_num_format('dd/mm/yyyy hh:mm')
        for col, width in enumerate(headers.values()):
            if col == 5:
                ws.set_column(col, col, width / 5, datetime_format)
            else:
                ws.set_column(col, col, width / 5)
        # Headers
        ws.write_row(0, 0, headers.keys(), header_format)
        # Rows
        for row, data in enumerate(rows):
            ws.write_row(row+1, 0, data)
        # Adjust additional properties
        ws.autofilter(0, 0, row+1, col)
        ws.freeze_panes(1, 0)
        wb.close()
        return 1
    except Exception as e:
        writelog(e)
        print(e)


if __name__ == '__main__':
    export_to_excel(headers={'abc':50, 'def':30}, rows=((2, 42), ('a', 'b')))