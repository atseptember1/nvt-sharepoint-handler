import os
from langchain.document_loaders import (
    PyMuPDFLoader,
    UnstructuredFileLoader
)
from langchain.schema import Document
from langchain.text_splitter import TokenTextSplitter

DOCUMENT_LOADER_MAPPING = {
    '.pdf': 'PymuPDFLoader',
    '.docx': 'UnstructuredFileLoader',
    '.xlsx': 'UnstructuredFileLoader',
    '.xls': 'UnstructuredFileLoader'
}


def _pdf_loader(path: str) -> list[Document]:
    loader = PyMuPDFLoader(path=path)
    return loader.load()


def _file_loader(path: str) -> list[Document]:
    loader = UnstructuredFileLoader(path=path, mode='single')
    return loader.load()


def _load_file(path: str) -> list[Document]:
    if os.path.exists(path=path):
        file_extension = os.path.splitext(path)[1].lower()
        for extension in DOCUMENT_LOADER_MAPPING:
            if file_extension == extension:
                loader_type = DOCUMENT_LOADER_MAPPING[extension]

            data = None
            if loader_type == 'PymuPDFLoader':
                data = _pdf_loader(path=path)
            elif loader_type == 'UnstructuredFileLoader':
                data = _file_loader(path=path)
            return data
        

def _document_splitter(data: list[Document]) -> list[str]:
    full_text = ''
    for page in data:
        full_text = full_text + page.page_content

    return TokenTextSplitter.from_tiktoken_encoder(encoding_name='cl100k_base', model_name='gpt-3.5-turbo',
                                                           chunk_size=2600, chunk_overlap=200)


def split_document(path: str) -> list[str]:
    data = _load_file(path=path)
    return _document_splitter(data=data)
