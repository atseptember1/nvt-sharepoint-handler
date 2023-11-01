import os
from datetime import datetime
from fastapi import UploadFile
from SearchServiceHandler import SearchService
from OpenAIHandler import OpenAI
from LocalFileAndFolderOps import (
    write_to_file,
    get_size
)
from DocumentProcess import split_document
from BlobStorage import BlobHandler
from main import FileModel
from DatabaseHandler import Database
from pydantic import BaseModel


class FileManagement:
    def __init__(self, search_endpoint: str, search_key: str, search_index_name: str,
                 openai_endpoint: str, openai_key: str, openai_chat_deployment: str, openai_chat_model: str, openai_embed_deployment: str, openai_embed_model: str,
                 blob_sa_name: str, blob_container_name: str,
                 db_conn_info: dict, db_table_list: list) -> None:
        """
        Initializes the FileManagement class with the necessary parameters.

        Args:
            search_endpoint (str): The endpoint for the search service.
            search_key (str): The key for the search service.
            search_index_name (str): The name of the search index.
            openai_endpoint (str): The endpoint for the OpenAI service.
            openai_key (str): The key for the OpenAI service.
            openai_chat_deployment (str): The deployment for the OpenAI chat model.
            openai_chat_model (str): The model for the OpenAI chat model.
            openai_embed_deployment (str): The deployment for the OpenAI embed model.
            openai_embed_model (str): The model for the OpenAI embed model.
            blob_sa_name (str): The name of the blob storage account.
            blob_container_name (str): The name of the blob container.
            db_conn_info (dict): The connection information for the database.
            db_table_list (list): The list of tables in the database.
        """
        self.SearchService = SearchService(search_svc_endpoint=search_endpoint, search_svc_key=search_key, search_index_name=search_index_name)
        self.Openai = OpenAI(endpoint=openai_endpoint, key=openai_key, chat_deployment=openai_chat_deployment, chat_model=openai_chat_model,
                             embed_deployment=openai_embed_deployment, embed_model=openai_embed_model)
        self.BlobHandler = BlobHandler(storage_account_name=blob_sa_name, container_name=blob_container_name)
        self.Database = Database(conn_info=db_conn_info, table_list=db_table_list)
        self.UploadState: dict = {
            "FileList": None,
            "FileState": []
        }
        self.UploadPending: list[dict] = []
        self.UploadFailed: list[dict] = []

    def _create_sections(self, file_name: str, doc: list[str]) -> list[dict]:
        """
        Creates sections from the file content.

        Args:
            file_name (str): The name of the file.
            doc (list[str]): The content of the file.

        Returns:
            list[dict]: A list of sections containing the paragraph content, questions, and summary.
        """
        counter = 1
        section_list = []
        for paragraph in doc:
            questions = self.Openai.generate_question(paragrpah=paragraph)
            summary = self.Openai.summarize_text(paragrpah=paragraph)
            sections = {
                "id": f"{file_name}-{counter}".replace(".", "_").replace(" ", "_").replace(":", "_").replace("/", "_").replace(",", "_").replace("&", "_"),
                "content": paragraph,
                "contentVector": self.Openai.embedding_word(texts=paragraph),
                "questions": questions,
                "questionsVector": self.Openai.embedding_word(questions),
                "summary": summary,
                "summaryVector": self.Openai.embedding(texts=summary),
                "sourcefile": os.path.basename(file_name),
            }
            section_list.append(sections)
            counter += 1
        return section_list

    def upload_file(self, file: FileModel, file_io: UploadFile) -> dict:
        """
        Uploads a file and its content.

        Args:
            file (FileModel): An instance of the FileModel class representing the file to be uploaded.
            file_io (UploadFile): An instance of the UploadFile class representing the file content.

        Returns:
            dict: A dictionary containing the metadata for the uploaded file, including the blob URL, file name, size, and success status.
        """
        metadata = {
                "BlobUrl": "",
                "FileName": file.FileName,
                "Size": file.Size,
                "Success": False
        }
        file_path = write_to_file(file_name=file.FileName, file_bytes=file_io)
        data = split_document(path=file_path)
        sections = self._create_sections(file_name=file.FileName, doc=data)
        if not self.SearchService.index_sections(sections=sections):
            self.UploadFailed.append(metadata)
            print(SystemError("Search indexing failed"))
        else:
            blob_res = BlobHandler.upload_blob(file_path=file_path)
            if blob_res["status"]:
                metadata["BlobUrl"] = blob_res["BlobUrl"]
                metadata["Success"] = True
                self.UploadPending.append(metadata)
        self.UploadState["FileState"].append(metadata)
        return metadata
    
    def _check_cur_uploadlist(self, file_list: list):
        """
        Checks if the current upload list matches the provided file list.

        Args:
            file_list (list): The list of files.

        Returns:
            bool: True if the current upload list matches the provided file list, False otherwise.
        """
        if not self.UploadState["FileList"]: self.UploadState["FileList"] = file_list
        elif self.UploadState["FileList"] != file_list: return False
        return True
    
    def batch_upload(self, file: FileModel, file_io: UploadFile):
        """
        Performs batch upload of files.

        Args:
            file (FileModel): An instance of the FileModel class representing the file to be uploaded.
            file_io (UploadFile): An instance of the UploadFile class representing the file content.
        """
        if self._check_cur_uploadlist(file.FileList):
            file_list_len = len(file.FileList)
            self.upload_file(file=file, file_io=file_io)
            if file.FileList.index(file.FileName) - 1 == file_list_len:
                self.Database.insert_file(self.UploadPending)
        else:
            if len(self.UploadPending) != 0:
                self.Database.insert_file(self.UploadPending)
            else:
                self.UploadState["FileList"] = file.FileList
                self.upload_file(file=file, file_io=file_io)

