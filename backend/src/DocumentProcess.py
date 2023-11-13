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
    """
    Load a PDF file using PyMuPDFLoader.

    Args:
        path (str): The file path of the PDF document.

    Returns:
        list[Document]: A list of Document objects extracted from the PDF.
    """
    loader = PyMuPDFLoader(file_path=path)
    return loader.load()


def _file_loader(path: str) -> list[Document]:
    """
    Load an unstructured file (e.g., .docx, .xlsx, .xls) using UnstructuredFileLoader.

    Args:
        path (str): The file path of the unstructured file.

    Returns:
        list[Document]: A list of Document objects extracted from the unstructured file.
    """
    loader = UnstructuredFileLoader(file_path=path, mode='single')
    return loader.load()


def _load_file(path: str) -> list[Document]:
    """
    Load a document file and extract the documents.

    Args:
        path (str): The file path of the document file.

    Returns:
        list[Document]: A list of Document objects extracted from the file.
    """
    data = []
    if os.path.exists(path=path):
        file_extension = os.path.splitext(path)[1].lower()
        for extension in DOCUMENT_LOADER_MAPPING:
            if file_extension == extension:
                loader_type = DOCUMENT_LOADER_MAPPING[extension]
            if loader_type == 'PymuPDFLoader':
                data = _pdf_loader(path=path)
            elif loader_type == 'UnstructuredFileLoader':
                data = _file_loader(path=path)
    return data
        

def _document_splitter(data: list[Document]) -> list[str]:
    """
    Split the content of the documents into chunks using TokenTextSplitter.

    Args:
        data (list[Document]): A list of Document objects.

    Returns:
        list[str]: A list of chunks of text extracted from the documents.
    """
    full_text = ''
    for page in data:
        full_text = full_text + page.page_content

    return TokenTextSplitter.from_tiktoken_encoder(encoding_name='cl100k_base', model_name='gpt-3.5-turbo',
                                                           chunk_size=2600, chunk_overlap=200).split_text(text=full_text)


def split_document(path: str) -> list[str]:
    """
    Split a document file into chunks of text.

    Args:
        path (str): The file path of the document file.

    Returns:
        list[str]: A list of chunks of text extracted from the document.
    """
    data = _load_file(path=path)
    return _document_splitter(data=data)
