import mysql.connector
from mysql.connector import errorcode
from pydantic import BaseModel
from azure.identity import DefaultAzureCredential
import pyodbc
import struct


class DatabaseConfig(BaseModel):
    username: str = ""
    user_password: str = ""
    credential: DefaultAzureCredential = None
    host: str
    database: str
    table_list: dict = {

    }
    token: str = ""


class Database:
    def __init__(self, config: DatabaseConfig) -> None:
        self.config = config
        self.conn = None

    def _get_token(self):
        # ref: https://learn.microsoft.com/en-us/azure/app-service/tutorial-connect-msi-azure-database?tabs=mysql%2Csystemassigned%2Cpython%2Cwindowsclient
        if self.config.credential != None:
            token = self.config.credential.get_token("https://database.windows.net/.default").token.encode("UTF-16-LE")
            self.config.token = struct.pack(f'<I{len(token)}s', len(token), token)
        else:
            raise ValueError("database credential is not provided")

    def db_conn(self) -> pyodbc.Connection:
        self._get_token()
        if not self.config.token:
            raise ValueError("database token is not provided")
        else:
            SQL_COPT_SS_ACCESS_TOKEN = 1256
            connString = f"Driver={{ODBC Driver 17 for SQL Server}};SERVER={self.config.host}.database.windows.net;DATABASE={self.config.database}"
            try:
                self.conn = pyodbc.connect(connstring=connString, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: self.config.token})
            except pyodbc.Error as err:
                raise err
        return self.conn

    def insert_file(self, file_list: list[dict]):
        self.db_conn()
        query = (f"INSERT INTO TABLE (FileName, FileUrl, Size) {self.TableList['Files']} VALUES (%s, %s, %s)")
        with self.conn.cursor() as cursor:
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
                    self.conn.commit()
                    return True
                except Exception as err:
                    return False
