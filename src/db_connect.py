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
        access = self.__cursor.fetchone()
        # check AccessType
        if access and (access[0] == 1):
            return True
        else:
            return None

    @monitor_network_state
    def create_request(self, userID, mvz, start_date, finish_date,
                       sum_extra_total,
                       sumtotal, nds, square, contragent, okpo,
                       num_main_contract,
                       num_add_contract, date_main_contract_start,
                       date_add_contract, text, filename,
                       date_main_contract_end,
                       price_meter, type_business,mvz_choice_list):
        """ Executes procedure that creates new request.
        """
        query = '''
        exec contracts.create_contract @UserID = ?,
                                    @MVZ = ?,
                                    @DateStart = ?,
                                    @DateFinish = ?,
                                    @SumExtraNoTax = ?,
                                    @SumNoTax = ?,
                                    @Tax = ?,
                                    @Square = ?,
                                    @Contragent = ?,
                                    @OKPO = ?,
                                    @NumMain = ?,
                                    @NumAdditional = ?,
                                    @DateMain = ?,
                                    @DateAdditional = ?,
                                    @Description = ?,
                                    @Filename = ?,
                                    @DateMainEnd = ?,
                                    @PriceSquareMeter = ?,
                                    @TypeBusiness = ?,
                                    @ObjectIDLIst = ?
            '''
        # print(userID, mvz, start_date, finish_date,
        #       sum_extra_total, sumtotal, nds, square,
        #       contragent, okpo, num_main_contract,
        #       num_add_contract, date_main_contract_start,
        #       date_add_contract, text, filename,
        #       date_main_contract_end, price_meter, type_business,mvz_choice_list)
        try:
            self.__cursor.execute(query, userID, mvz, start_date, finish_date,
                                  sum_extra_total, sumtotal, nds, square,
                                  contragent, okpo, num_main_contract,
                                  num_add_contract, date_main_contract_start,
                                  date_add_contract, text, filename,
                                  date_main_contract_end, price_meter,
                                  type_business,mvz_choice_list)
            request_allowed = self.__cursor.fetchone()[0]
            self.__db.commit()
            return request_allowed
        except pyodbc.ProgrammingError:
            return

    @monitor_network_state
    def update_request(self, userID, id, mvz, start_date, finish_date,
                       sum_extra_total,
                       sumtotal, nds, square, contragent, okpo,
                       num_main_contract,
                       num_add_contract, date_main_contract_start,
                       date_add_contract, text, filename,
                       date_main_contract_end,
                       price_meter, type_business, mvz_choice_list):
        """ Executes procedure that creates new request.
        """
        query = '''
            exec contracts.update_contract @UserID = ?,
                                        @ID = ?,
                                        @MVZ = ?,
                                        @DateStart = ?,
                                        @DateFinish = ?,
                                        @SumExtraNoTax = ?,
                                        @SumNoTax = ?,
                                        @Tax = ?,
                                        @Square = ?,
                                        @Contragent = ?,
                                        @OKPO = ?,
                                        @NumMain = ?,
                                        @NumAdditional = ?,
                                        @DateMain = ?,
                                        @DateAdditional = ?,
                                        @Description = ?,
                                        @Filename = ?,
                                        @DateMainEnd = ?,
                                        @PriceSquareMeter = ?,
                                        @TypeBusiness = ?,
                                        @ObjectIDLIst = ?
                '''
        try:
            self.__cursor.execute(query, userID, id, mvz, start_date, finish_date,
                                  sum_extra_total, sumtotal, nds, square,
                                  contragent, okpo, num_main_contract,
                                  num_add_contract, date_main_contract_start,
                                  date_add_contract, text, filename,
                                  date_main_contract_end, price_meter,
                                  type_business, mvz_choice_list)
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
        select UserID, ShortUserName, AccessType, isSuperUser
        from contracts.People
        where UserLogin = ?
        '''
        self.__cursor.execute(query, UserLogin)
        return self.__cursor.fetchone()

    @monitor_network_state
    def get_additional_objects(self, ContractID):
        """ Returns information about additionals MVZ for object's contract.
        """
        query = '''
             exec contracts.get_additional_objects @ContractID = ?
             '''

        self.__cursor.execute(query, ContractID)
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
    def get_type_business(self):
        """ Returns list of available MVZ for current user.
        """
        query = '''
        exec contracts.get_type_business
        '''
        self.__cursor.execute(query)
        return self.__cursor.fetchall()

    @monitor_network_state
    def get_contracts_list(self, mvz=None, statusID=None, type_businessID=None):
        """ Get list contracts with filters.
        """
        query = '''
           exec contracts.get_contracts_list @MVZ = ?,
                                             @StatusID = ?,
                                             @TypeBusinessID = ?
           '''
        self.__cursor.execute(query, mvz, statusID, type_businessID)
        contracts = self.__cursor.fetchall()
        self.__db.commit()
        return contracts

    @monitor_network_state
    def get_current_contract(self, contractID):
        """ Returns contract info from DB.
        """
        query = "exec contracts.get_current_contract @contractID = ?"
        self.__cursor.execute(query, contractID)
        return self.__cursor.fetchone()


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
    def delete_contract(self, deleteID):
        """ Set status of contract to "delete".
        """
        query = "exec contracts.delete_contract @contractID = ?"
        self.__cursor.execute(query, deleteID)
        self.__db.commit()


if __name__ == '__main__':
    with DBConnect(server='s-kv-center-s59', db='LogisticFinance',
                   uid='XXX', pwd='XXX') as sql:
        query = '''
                exec payment.get_MVZ @UserID = 20,
                                     @AccessType = 1,
                                     @isSuperUser = 0
                '''
        print(sql.raw_query(query))
    print('Connected successfully.')
    input('Press Enter to exit...')
