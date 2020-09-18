from functools import wraps
from tkContracts import NetworkError
import pyodbc


def monitor_network_state(method):
    """ Show error message in case of network error.
    """

    @wraps(method)
    def wrapper(self, *args, **kwargs):
        try:
            return method(self, *args, **kwargs)
        except pyodbc.Error as e:
            # Network error
            if e.args[0] in ('01000', '08S01', '08001'):
                NetworkError()

    return wrapper


class DBConnect(object):
    """ Provides connection to database and functions to work with server.
    """

    def __init__(self, *, server, db, uid, pwd):
        self._server = server
        self._db = db
        self._uid = uid
        self._pwd = pwd

    def __enter__(self):
        # Connection properties
        conn_str = (
            f'Driver={{SQL Server}};'
            f'Server={self._server};'
            )
        if self._db is not None:
            conn_str += f'Database={self._db};'
        if self._uid:
            conn_str += f'uid={self._uid};pwd={self._pwd}'
        else:
            conn_str += 'Trusted_Connection=yes;'
        self.__db = pyodbc.connect(conn_str)
        self.__cursor = self.__db.cursor()
        return self

    def __exit__(self, type, value, traceback):
        self.__db.close()

    @monitor_network_state
    def access_check(self, UserLogin):
        """ Check user permission.
            If access permitted returns True, otherwise None.
        """
        query = '''exec contracts.Access_Check @UserLogin = ?'''

        self.__cursor.execute(query, UserLogin)
        access = self.__cursor.fetchone()[0]
        # check AccessType
        if access and (access == 1):
            return True

    @monitor_network_state
    def alter_payment(self, userID, paymentID, date_planed, SumNoTax):
        """ Alter payment and log changes on server.
        """
        query = '''
        exec payment.alter_payment @UserID = ?,
                                   @PaymentID = ?,
                                   @date_planed = ?,
                                   @SumNoTax = ?
        '''

        try:
            self.__cursor.execute(query, userID, paymentID, date_planed,
                                  SumNoTax)
            self.__db.commit()
            return 1
        except pyodbc.ProgrammingError:
            return 0

    @monitor_network_state
    def create_request(self, userID, mvz, office, categoryID, contragent, csp,
                       plan_date, sumtotal, nds, text, approval, is_cashless,
                       payconditionsID, initiator_name, okpo):
        """ Executes procedure that creates new request.
        """
        query = '''
        exec payment.create_request @UserID = ?,
                                    @MVZ = ?,
                                    @Office = ?,
                                    @CategoryID = ?,
                                    @Contragent = ?,
                                    @date_planed = ?,
                                    @Description = ?,
                                    @SumNoTax = ?,
                                    @Tax = ?,
                                    @CSP = ?,
                                    @Approval = ?,
                                    @is_cashless = ?,
                                    @PayConditionsID = ?,
                                    @initiator_name = ?,
                                    @okpo = ?
            '''
        try:
            self.__cursor.execute(query, userID, mvz, office, categoryID,
                                  contragent, plan_date, text,
                                  sumtotal, nds, csp, approval, is_cashless,
                                  payconditionsID, initiator_name, okpo)
            request_allowed = self.__cursor.fetchone()[0]
            self.__db.commit()
            return request_allowed
        except pyodbc.ProgrammingError:
            return

    @monitor_network_state
    def get_user_info(self, UserLogin):
        """ Returns information about current user based on ORIGINAL_LOGIN().
        """
        query = '''
        select UserID, ShortUserName, AccessType
        from contracts.People
        where UserLogin = ?
        '''
        self.__cursor.execute(query, UserLogin)
        return self.__cursor.fetchone()

    @monitor_network_state
    def get_allowed_initiators(self, UserID, AccessType, isSuperUser):
        """ Determines list of persons that should be shown in filters.
        """
        query = '''
        exec payment.get_allowed_initiators @UserID = ?,
                                            @AccessType = ?,
                                            @isSuperUser = ?
        '''
        self.__cursor.execute(query, UserID, AccessType, isSuperUser)
        return [(None, 'Все'), ] + self.__cursor.fetchall()

    @monitor_network_state
    def get_approvals(self, paymentID):
        """ Returns all approvals of the request with id = paymentID.
        """
        query = "exec payment.get_approvals @paymentID = ?"
        self.__cursor.execute(query, paymentID)
        return self.__cursor.fetchall()

    @monitor_network_state
    def get_approvals_for_first_stage(self):
        """ Returns all approvals for first stage who can be chosen.
        """
        query = "exec payment.get_approvals_for_first_stage"
        self.__cursor.execute(query)
        return self.__cursor.fetchall()

    @monitor_network_state
    def get_info_to_alter_payment(self, paymentID):
        """ Returns info about request is intended to be altered.
        """
        query = "exec payment.get_info_to_alter_payment @PaymentID = ?"
        self.__cursor.execute(query, paymentID)
        return self.__cursor.fetchall()

    @monitor_network_state
    def get_limits_info(self):
        """ Returns info about limits for all users.
        """
        query = '''
        select UserID, UserName,
               cast(userCreateRequestLimit as float) as userCreateRequestLimit,
               resetCreateRequestLimit
        from payment.People
        where AccessType in (1, 2)
            or isSuperUser = 1
        order by UserName
            '''
        self.__cursor.execute(query)
        return self.__cursor.fetchall()

    @monitor_network_state
    def get_objects(self):
        """ Returns list of available MVZ for current user.
        """
        query = '''
        exec contracts.get_objects
        '''
        self.__cursor.execute(query)
        return self.__cursor.fetchall()


    @monitor_network_state
    def get_contracts_list(self, mvz=None, statusID=None):
        """ Get list contracts with filters.
        """
        query = '''
           exec contracts.get_contracts_list @MVZ = ?,
                                             @StatusID = ?
           '''
        self.__cursor.execute(query, mvz, statusID)
        return self.__cursor.fetchall()


    @monitor_network_state
    def get_status_list(self):
        """ Returns status list.
        """
        query = "exec contracts.get_status_list"
        self.__cursor.execute(query)
        return self.__cursor.fetchall()

    @monitor_network_state
    def raw_query(self, query):
        """ Takes the query and returns output from db.
        """
        self.__cursor.execute(query)
        return self.__cursor.fetchall()

    @monitor_network_state
    def update_confirmed(self, userID, paymentID, is_approved):
        """ Adds information to db if paymentID has been approved.
        """
        query = '''
        exec payment.approve_request @UserID = ?,
                                     @paymentID = ?,
                                     @is_approved = ?
        '''
        self.__cursor.execute(query, userID, paymentID, is_approved)
        self.__db.commit()

    @monitor_network_state
    def update_discarded(self, discardID):
        """ Set status of request to "discarded".
        """
        query = "exec payment.discard_request @paymentID = ?"
        self.__cursor.execute(query, discardID)
        self.__db.commit()

    @monitor_network_state
    def update_limits(self, limits):
        """ Update user limits.
        """
        query = '''
        UPDATE payment.People
        SET resetCreateRequestLimit = ?, userCreateRequestLimit = ?
        where UserID = ?
        '''
        limits = [tuple(reversed(info)) for info in limits]
        try:
            self.__cursor.executemany(query, limits)
            self.__db.commit()
            return 1
        except pyodbc.ProgrammingError:
            return 0


if __name__ == '__main__':
    with DBConnect(server='s-kv-center-s59', db='LogisticFinance',
                   uid='XXX', pwd='XXX') as sql:
        query = '''
                exec payment.get_MVZ @UserID = 20,
                                     @AccessType = 1,
                                     @isSuperUser = 0
                '''
        print(sql.raw_query(query))
        # assert sql.raw_query(query)[0][0] == 42, 'Server returns no output.'
    print('Connected successfully.')
    input('Press Enter to exit...')
