from collections import namedtuple
from db_connect import DBConnect
from log_error import writelog
from pyodbc import Error as SQLError
from time import sleep
from singleinstance import Singleinstance
import os, sys
import tkContracts as tkp
import getpass
import pwd

UPDATER_VERSION = '0.9.20a'


class RestartRequiredError(Exception):
    """ Exception raised if restart is required.

    Attributes:
        expression - input expression in which the error occurred;
        message - explanation of the error.
    """

    def __init__(self, expression,
                 message='Необходима перезагрузка приложения'):
        self.expression = expression
        self.message = message
        super().__init__(self.expression, self.message)


def apply_update():
    from _version import upd_path
    from shutil import copy2
    from zlib import decompress

    upd_path = decompress(upd_path).decode()
    print(upd_path)
    for file in ('contracts_checker.exe', 'contracts_checker.exe.manifest'):
        copy2(os.path.join(upd_path, file), '.')
    with open('contracts_checker.inf', 'w') as f:
        f.write(UPDATER_VERSION)
    raise RestartRequiredError(UPDATER_VERSION,
                               'Выполнено критическое обновление.\nПерезапустите приложение')


def check_meta_update():
    """ Check update for updater itself (contracts_checker).
    """
    # determine pid of contracts_checker and terminate it
    from win32com.client import GetObject
    from signal import SIGTERM
    WMI = GetObject('winmgmts:')
    processes = WMI.InstancesOf('Win32_Process')
    try:
        pid = next(p.Properties_('ProcessID').Value for p in processes
                   if p.Properties_('Name').Value == 'contracts_checker.exe')
        os.kill(pid, SIGTERM)
    except (StopIteration, PermissionError):
        pass
    # version comparing
    try:
        with open('contracts_checker.inf', 'r') as f:
            version_info = f.readline()
    except FileNotFoundError:
        from _version import __version__ as version_info
    if version_info == UPDATER_VERSION:
        return
    # add time to properly close contracts_checker
    sleep(3)
    apply_update()


def main():
    check_meta_update()
    # Check connection to db and permission to work with app
    # If debug mode then 1 else 0
    db_info = pwd.access_return(1)
    conn = DBConnect(server=db_info.get('Server'),
                     db=db_info.get('DB'),
                     uid=db_info.get('UID'),
                     pwd=db_info.get('PWD'))
    try:
        with conn as sql:
            UserLogin = getpass.getuser()
            # UserLogin = 'v.zubriichuk'
            access_permitted = sql.access_check(UserLogin)
            if not access_permitted:
                tkp.AccessError()
                sys.exit()

            UserInfo = namedtuple('UserInfo',
                                  ['UserID', 'ShortUserName', 'AccessType']
                                  )

            # load references
            user_info = UserInfo(*sql.get_user_info(UserLogin))
            # print(user_info)
            # Restriction: users in approvals_for_first_stage
            # should have different names to be distinguished
            refs = {'connection': sql,
                    'user_info': user_info,
                    'mvz': sql.get_objects(),
                    # 'pay_conditions': sql.get_pay_conditions(),
                    # 'allowed_initiators':
                    #     sql.get_allowed_initiators(user_info.UserID,
                    #                                user_info.AccessType,
                    #                                user_info.isSuperUser),
                    # 'approvals_for_first_stage':
                    #     sql.get_approvals_for_first_stage(),
                    'status_list': sql.get_status_list()
                    }
            for k, v in refs.items():
                assert v is not None, 'refs[' + k + '] value is None'
            # Run app
            app = tkp.PaymentApp(**refs)
            app.mainloop()

    except SQLError as e:
        # login failed
        if e.args[0] in ('28000', '42000'):
            # writelog(e)
            tkp.LoginError()
        else:
            raise


if __name__ == '__main__':
    try:
        fname = os.path.basename(__file__)
        myapp = Singleinstance(fname)
        if myapp.aleradyrunning():
            sys.exit()
        main()
    except RestartRequiredError as e:
        tkp.RestartRequiredAfterUpdateError()
    except Exception as e:
        writelog(e)
    finally:
        sys.exit()



