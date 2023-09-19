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


class FileManagement:
    def __init__(self, search_endpoint: str, search_key: str, search_index_name: str,
                 openai_endpoint: str, openai_key: str, openai_chat_deployment: str, openai_chat_model: str, openai_embed_deployment: str, openai_embed_model: str,
                 blob_sa_name: str, blob_container_name: str) -> None:
        self.search_service = SearchService(search_svc_endpoint=search_endpoint, search_svc_key=search_key, search_index_name=search_index_name)
        self.openai = OpenAI(endpoint=openai_endpoint, key=openai_key, chat_deployment=openai_chat_deployment, chat_model=openai_chat_model,
                             embed_deployment=openai_embed_deployment, embed_model=openai_embed_model)
        self.BlobHandler = BlobHandler(storage_account_name=blob_sa_name, container_name=blob_container_name)

    def _create_sections(self, file_name: str, doc: list[str]) -> list[dict]:
        counter = 1
        section_list = []
        for paragraph in doc:
            questions = self.openai.generate_question(paragrpah=paragraph)
            summary = self.openai.summarize_text(paragrpah=paragraph)
            sections = {
                "id": f"{file_name}-{counter}".replace(".", "_").replace(" ", "_").replace(":", "_").replace("/", "_").replace(",", "_").replace("&", "_"),
                "content": paragraph,
                "contentVector": self.openai.embedding(texts=paragraph),
                "questions": questions,
                "questionsVector": self.openai.embedding(questions),
                "summary": summary,
                "summaryVector": self.openai.embedding(texts=summary),
                "sourcefile": os.path.basename(file_name)
            }
            section_list.append(sections)
            counter += 1
        return section_list

    def upload_file(self, file_name: str, file_io: UploadFile) -> bool:
        file_path = write_to_file(file_name=file_name, file_bytes=file_io)
        data = split_document(path=file_path)
        sections = self._create_sections(file_name=file_name, doc=data)
        if not self.search_service.index_sections(sections=sections):
            raise SystemError("Search indexing failed")
        blob_url = BlobHandler.upload_blob(file_path=file_path)
        
        # Check if file exist in the database, if not insert this metadata as new rows else modify exist data
        metadata_new = {
            "BlobUrl": blob_url,
            "FileName": os.path.splitext(p=file_path)[1],
            "Size": get_size(file_path=file_path, unit="mb"),
            "UploadDate": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "ModifedDate": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        metadata_exist = {
            "BlobUrl": blob_url,
            "FileName": os.path.splitext(p=file_path)[1],
            "Size": get_size(file_path=file_path, unit="mb"),
            "UploadDate": ,
            "ModifedDate": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        
