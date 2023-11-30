import os
from datetime import datetime
from fastapi import UploadFile
from pydantic import BaseModel
from pathlib import Path
from SearchServiceHandler import SearchService
from OpenAIHandler import OpenAI
from LocalFileAndFolderOps import write_to_file
from DocumentProcess import split_document
from BlobStorage import BlobHandler


class FileModelOut(BaseModel):
    BlobUrl: str
    FileName: str
    Success: bool


class FileManagementConfig(BaseModel):
    search_config: any
    openai_config: any
    blob_config: any

    class Config:
        arbitrary_types_allowed = True


#test
class FileHandler:
    def __init__(self, config: FileManagementConfig):
        self.SearchService = SearchService(config=config.search_config)
        self.Openai = OpenAI(config=config.openai_config)
        self.BlobHandler = BlobHandler(config=config.blob_config)

    def upload_file(self, file_io: UploadFile) -> FileModelOut:
        # TODO: parse the file name to URL-safe version of Base64, can only contain letters, digits, underscore (_), dash (-), or equal sign (=).
        metadata = FileModelOut(
            BlobUrl="",
            FileName=file_io.filename,
            Success=False
        )

        file_path = write_to_file(
            file_name=file_io.filename, file_bytes=file_io)
        data = split_document(path=file_path)
        sections = self.SearchService.create_sections(file_name=file_io.filename, doc=data, openai=self.Openai)
        if not self.SearchService.index_sections(sections=sections):
            print(SystemError("Search indexing failed"))
        else:
            blob_res = self.BlobHandler.upload_blob(file_path=file_path)
            if blob_res["status"]:
                metadata.BlobUrl = blob_res["BlobUrl"]
                metadata.Success = True
        return metadata
