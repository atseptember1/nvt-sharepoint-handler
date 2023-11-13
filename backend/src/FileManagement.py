import os
from datetime import datetime
from fastapi import UploadFile
from pydantic import BaseModel
from pathlib import Path

from SearchServiceHandler import SearchService, SearchServiceConfig
from OpenAIHandler import OpenAI, OpenAIConfig
from LocalFileAndFolderOps import write_to_file
from DocumentProcess import split_document
from BlobStorage import BlobHandler, BlobConfig
# from main import FileModel, FileModelOut


class FileModel(BaseModel):
    FileName: str

class FileModelOut(BaseModel):
    BlobUrl: str
    FileName: str
    Success: bool

class FileManagementConfig(BaseModel):
    search_config: SearchServiceConfig
    openai_config: OpenAIConfig
    blob_config: BlobConfig

    class Config:
        arbitrary_types_allowed = True


class FileHandler:
    def __init__(self, config: FileManagementConfig):
        self.SearchService = SearchService(config=config.search_config)
        self.Openai = OpenAI(config=config.openai_config)
        self.BlobHandler = BlobHandler(config=config.blob_config)

    def _create_sections(self, file_name: str, doc: list[str]) -> list[dict]:
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

    def upload_file(self, file: FileModel, file_io: UploadFile) -> FileModelOut:
        metadata = FileModelOut(
            BlobUrl = "",
            FileName = file.FileName,
            Success = False
        )
            
        file_path = write_to_file(file_name=file.FileName, file_bytes=file_io)
        data = split_document(path=file_path)
        sections = self._create_sections(file_name=file.FileName, doc=data)
        if not self.SearchService.index_sections(sections=sections):
            print(SystemError("Search indexing failed"))
        else:
            blob_res = BlobHandler.upload_blob(file_path=file_path)
            if blob_res["status"]:
                metadata.BlobUrl = blob_res["BlobUrl"]
                metadata.Success = True
        return metadata
