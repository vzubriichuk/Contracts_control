from _version import upd_path
from tkinter import Tk, messagebox
from win32com.client import Dispatch
import getpass, os, zipfile, zlib

SOURCE = zlib.decompress(upd_path).decode()
TARGET = os.path.join('C:\\Users', getpass.getuser(), 'AppData\\Local')
DESKTOP = os.path.join('C:\\Users', getpass.getuser(), 'Desktop')
WDIR = os.path.join(TARGET, 'Contracts')
TARGETFILE = os.path.join(WDIR, 'contracts_checker.exe')
ICONFILE = os.path.join(WDIR, 'resources\\paper.ico')

print(TARGETFILE)

class SuccessMsg(Tk):
    """ Raise an error when user doesn't have permission to work with app.
    """
    def __init__(self):
        super().__init__()
        self.withdraw()  # Do not show main window
        messagebox.showinfo(
            'Учёт договоров аренды',
            'Установка завершена.\n'
            'На рабочем столе создан ярлык для запуска.'
        )
        self.destroy()

def create_shortcut(path, target='', wDir='', icon=''):
    shell = Dispatch('WScript.Shell')
    shortcut = shell.CreateShortCut(path)
    shortcut.Targetpath = target
    shortcut.WorkingDirectory = wDir
    shortcut.Description = 'Учёт договоров аренды'
    if icon:
        shortcut.IconLocation = icon
    shortcut.save()

def main():
    print('Выполняется начальная установка и создание ярлыков...')
    # extract actual version of app
    with zipfile.ZipFile(os.path.join(SOURCE, 'Contracts.zip'), 'r') as zip_ref:
        zip_ref.extractall(TARGET)
    create_shortcut(os.path.join(DESKTOP, 'Учёт договоров аренды.lnk'),
                    TARGETFILE,
                    WDIR,
                    ICONFILE)
    SuccessMsg()

if __name__ == '__main__':
    main()