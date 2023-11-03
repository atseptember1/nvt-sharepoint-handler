import os
from datetime import datetime
from fastapi import UploadFile
from pydantic import BaseModel
from pathlib import Path

from SearchServiceHandler import SearchService, SearchServiceConfig
from OpenAIHandler import OpenAI, OpenAIConfig
from LocalFileAndFolderOps import write_to_file, get_size
from DocumentProcess import split_document
from BlobStorage import BlobHandler, BlobConfig
from main import FileModel
from DatabaseHandler import Database





class FileManagement:
    def __init__(self, search_config: SearchServiceConfig, openai_config: OpenAIConfig,
                 blob_config: BlobConfig,
                 db_conn_info: dict, db_table_list: list) -> None
        self.SearchService = SearchService(config=search_config)
        self.Openai = OpenAI(config=openai_config)
        self.BlobHandler = BlobHandler(blob)
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
        section_list = [
            {
                "id": f"{file_name}-{counter}".replace(".", "_").replace(" ", "_").replace(":", "_").replace("/", "_").replace(",", "_").replace("&", "_"),
                "content": paragraph,
                "contentVector": self.Openai.embedding_word(texts=paragraph),
                "questions": self.Openai.generate_question(paragrpah=paragraph),
                "questionsVector": self.Openai.embedding_word(self.Openai.generate_question(paragrpah=paragraph)),
                "summary": self.Openai.summarize_text(paragrpah=paragraph),
                "summaryVector": self.Openai.embedding(texts=self.Openai.summarize_text(paragrpah=paragraph)),
                "sourcefile": Path(file_name).name,
            }
            for counter, paragraph in enumerate(doc, start=1)
        ]
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

