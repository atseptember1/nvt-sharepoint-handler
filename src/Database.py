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
        return self.cnx

    def insert_file(self, file_list: list[dict]):
        query = (f"INSERT INTO TABLE (FileName, FileUrl, Size) {self.TableList['Files']} VALUES (%s, %s, %s)")
        self.db_conn()
        with self.cnx.cursor() as cursor:
            insert_values = []
            for file_metadata in file_list:
                if file_metadata["Success"]:
                    value = {
                        "FileName": file_metadata["FileName"],
                        "FileUrl": file_metadata["BlobUrl"],
                        "Size": file_metadata["Size"]
                    }
                    insert_values.append(value)
                try:
                    cursor.execute(query, insert_values, multi=True)
                    self.cnx.commit()
                    return True
                except Exception as err:
                    return False