import os
from datetime import datetime
from fastapi import UploadFile
from SearchServiceHandler import SearchService
from OpenAIHandler import Openai
from LocalFileAndFolderOps import (
    write_to_file,
    get_size
)
from DocumentProcess import split_document
from BlobStorage import BlobHandler
from main import FileModel


class FileManagement:
    def __init__(self, search_endpoint: str, search_key: str, search_index_name: str,
                 openai_endpoint: str, openai_key: str, openai_chat_deployment: str, openai_chat_model: str, openai_embed_deployment: str, openai_embed_model: str,
                 blob_sa_name: str, blob_container_name: str) -> None:
        self.SearchService = SearchService(search_svc_endpoint=search_endpoint, search_svc_key=search_key, search_index_name=search_index_name)
        self.Openai = Openai(endpoint=openai_endpoint, key=openai_key, chat_deployment=openai_chat_deployment, chat_model=openai_chat_model,
                             embed_deployment=openai_embed_deployment, embed_model=openai_embed_model)
        self.BlobHandler = BlobHandler(storage_account_name=blob_sa_name, container_name=blob_container_name)
        self.UploadState: dict[list] = {
            "FileList": None,
            "FileState": []
        }

    def _create_sections(self, file_name: str, doc: list[str]) -> list[dict]:
        counter = 1
        section_list = []
        for paragraph in doc:
            questions = self.Openai.generate_question(paragrpah=paragraph)
            summary = self.Openai.summarize_text(paragrpah=paragraph)
            sections = {
                "id": f"{file_name}-{counter}".replace(".", "_").replace(" ", "_").replace(":", "_").replace("/", "_").replace(",", "_").replace("&", "_"),
                "content": paragraph,
                "contentVector": self.Openai.embedding(texts=paragraph),
                "questions": questions,
                "questionsVector": self.Openai.embedding(questions),
                "summary": summary,
                "summaryVector": self.Openai.embedding(texts=summary),
                "sourcefile": os.path.basename(file_name)
            }
            section_list.append(sections)
            counter += 1
        return section_list

    def upload_file(self, file: FileModel, file_io: UploadFile) -> dict:
        metadata = {
                "BlobUrl": "",
                "FileName": file.FileName,
                "Size": file.Size,
                "UploadDate": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "Success": False
        }

        file_path = write_to_file(file_name=file.FileName, file_bytes=file_io)
        data = split_document(path=file_path)
        sections = self._create_sections(file_name=file.FileName, doc=data)
        if not self.SearchService.index_sections(sections=sections):
            print(SystemError("Search indexing failed"))
        else:
            blob_res = BlobHandler.upload_blob(file_path=file_path)
            if blob_res["status"]:
                metadata["BlobUrl"] = blob_res["BlobUrl"]
                metadata["Success"] = True
        return metadata
    
    def _check_cur_uploadlist(self, file_list: list):
        if not self.UploadState["FileList"]: self.UploadState["FileList"] = file_list
        else:
            if self.UploadState["FileList"] != file_list: return False
        return True
    
    def 