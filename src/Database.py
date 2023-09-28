import mysql.connector
from mysql.connector import errorcode

class Database:
    def __init__(self, conn_info: dict, table_list: dict) -> None:
        self.ConnInfo = conn_info
        self.TableList = table_list
        self._sanity_check()

    def _sanity_check(self) -> bool:

        def _check_key(key_list: list, to_check_list: dict):
            for key in key_list:
                if key not in to_check_list:
                    return key
            return True

        conn_key_list = ['username', 'password', 'host', 'database']
        conn_check = _check_key(key_list=conn_key_list, to_check_list=self.ConnInfo)
        if conn_check != True:
            raise ValueError(f"database connection missing {conn_check}")
        table_key_list = ["Files"]
        table_check = _check_key(key_list=table_key_list, to_check_list=self.TableList)
        if table_check != True:
            raise ValueError(f"database connection missing {table_check}")
        return True

    def db_conn(self) -> mysql.connector.connection.MySQLConnection:
        try:
            self.cnx = mysql.connector.connect(user=self.ConnInfo['username'], password=self.ConnInfo['password'],
                                          host=self.ConnInfo['host'], database=self.ConnInfo['database'], use_pure=False)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
                self.cnx.close()
        return self.cnx

    def insert_file(self, file_list: list):
        file_list_len = len(file_list)
        query = f"INSERT INTO TABLE (FileName, FileUrl, Size) {self.TableList['Files']} VALUES "
        i = 0
        for file_metadata in file_list:
            query = query + f"({file_metadata['FileName']}, {file_metadata['FileUrl']}, {file_metadata['Size']})"
            if i == file_list_len: query = query + ";"
            else: query = query + ","
            i += 1

        self.db_conn()
        