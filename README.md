# Payments_control
Application is a client part of project that helps to organize and control payments. It consists of several logical parts that allows to automatically update application.

<hr>

### payments_first_run.py

Provides initial installation of the application and creates a shortcut on desktop that refers to <i>payments_checker</i>.

### payments_checker.py

Checks and installs updates and executes <i>Payments</i> afterwards.

### Payments.py

Core of the application that establishes connection with database, checks permissions and creates an instance of <i>PaymentApp</i>.

### tkPayments.py

Contains GUI and provides the functionality.

### Auxiliary modules

`checkboxtreeview.py`, `label_grid.py`, `multiselect.py`, `splash_screen.py`, `tkHyperlinkManager.py` -  provide additional widgets or frames with additional functionality for Tkinter.
`db_connect_sql.py` - module to work with database.
`log_error.py` - writes info about error into the file <i>log.txt</i> to the same directory where the main program is.
`singleinstance.py` - creates Mutex to prevent launch multiple copies of application.
`xl.py` - module to work with Excel.

## Usage

End user is supposed to be working with executables created from `py` scripts. Current manual expects that [Pyinstaller](https://www.pyinstaller.org) is used for creating executables. Beforehand `upd_path` should be specified in `_version.py`.

Three scripts need to be turned into executables: `payments_first_run.py`, `payments_checker.py` and `Payments.py`. The first two can be created with the next commands: `pyinstaller --console --onefile payments_first_run.py` and `pyinstaller --noconsole payments_checker.py`. Since the GUI uses additional resources there is `spec` file containing required data links and hidden imports. To create <i>Payments</i> executable one should use next script: `pyinstaller --noconsole Payments.spec`. After creating executables <i>payments_checker.exe</i> and <i>payments_checker.exe.manifest</i> need to be transfered into <i>payments</i> directory where <i>payments.exe</i> is.

<i>payments_first_run.exe</i> and zipped <i>payments</i> directory (it should be named <i>payments.zip</i> explicitly) should be copied into <i>upd_path</i>. After executing <i>payments_first_run.exe</i> application will be installed on user's PC and shortcut on desktop will be created.

#### Application update

After changes have been made into current scripts `version_info` should be updated in `_version.py`. New subdirectory has to be created in the path <i>upd_path</i> with the same name as `version_info`, e.g. if the new `version_info = (1, 0, 3)` the subdirectory name has to be "1.0.3". All added/modified files created by <i>Pyinstaller</i> should be copied into created directory. Generally, all files can be copied into subdirectory but that will drastically slow down update process because `payments_checker.exe` will copy all files found in subdirectory.
When `payments_checker.exe` is runned by end user it loops through every subdirectory in path <i>upd_path</i> whose names are higher than current version of application und copies new files into working directory.
It is recommended to keep up zipped <i>payments</i> being archive of the last stable version, in order to new users running <i>payments_first_run.exe</i> receive the actual version of application.

#### Work with application

The instructions about work with application should be added to <i>./src/resources</i> as <i>README.pdf</i>.

<hr>

## Requirements

* OS Windows

* Python version `3.6` or higher

* [pyodbc](https://github.com/mkleehammer/pyodbc)

* pythoncom (part of [pywin32](https://github.com/mhammond/pywin32); when have a problem installing pywin32, check [pypiwin32](https://stackoverflow.com/questions/49307303/installing-the-pypiwin32-module) and [postinstall](https://www.reddit.com/r/Python/comments/57h1pf/pywin32_not_installing_properly/))

* win32com (also part of pywin32)

* [tkcalendar](https://github.com/j4321/tkcalendar) version `1.5.0`, `1.6.1` or higher (GNU General Public License v3.0)

* [xlsxwriter](https://pypi.org/project/XlsxWriter/) (BSD License)