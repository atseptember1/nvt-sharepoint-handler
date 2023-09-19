import mysql.connector
from mysql.connector import errorcode


class Database:
    def __init__(self, conn_info: dict) -> None:
        self.conn_info = conn_info
        self._sanity_check()

    def _sanity_check(self):
        conn_key_list = ['username', 'password', 'host', 'database']
        for key in conn_key_list:
            if key not in self.conn_info:
                raise KeyError(f'key not in conn_info: {key}')

    def db_conn(self) -> mysql.connector.connection:
        try:
            self.cnx = mysql.connector.connect(user=self.conn_info['username'], password=self.conn_info['password'],
                                          host=self.conn_info['host'], database=self.conn_info['database'], use_pure=False)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
                self.cnx.close()
        return self.cnx
    
    # def query_file_mgmt(self, )