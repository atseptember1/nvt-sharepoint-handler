import os

from azure.storage.blob import ContainerClient
from azure.core.exceptions import HttpResponseError

from src.AzureAuthentication import AzureAuthenticate
from src.model.common import (
    BlobHandlerUploadBlob,
    BlobProperties
)
from src.model.config import StorageConfig
from src.model.output import BlobPropertiesApiOut


class StorageHandler(AzureAuthenticate):
    """
    A class that provides functionalities to interact with Azure Blob Storage.

    Inherits from AzureAuthenticate class.

    Args:
        config (StorageConfig): A StorageConfig object containing the storage name and container name.

    Attributes:
        config (StorageConfig): A StorageConfig object containing the storage name and container name.
        _container_client (ContainerClient): The container client for interacting with the Azure Blob Storage container.
        _blob_client (BlobClient): The blob client for interacting with a specific blob in the container.
    """

    def __init__(self, config: StorageConfig) -> None:
        """
        Initializes a StorageHandler object.

        Args:
            config (StorageConfig): A StorageConfig object containing the storage name and container name.
        """
        super().__init__()
        self.config = config
        self._container_client = None
        self._blob_client = None
        self._init_container_client()

    def _init_container_client(self) -> None:
        """
        Initializes the container client using the storage name and container name from the config.
        """
        try:
            self._container_client = ContainerClient(account_url=f'https://{self.config.StorageName}.blob.core.windows.net/',
                                                     container_name=self.config.ContainerName,
                                                     credential=self.credential)
        except Exception as err:
            raise err

    def _init_blob_client(self, file_name: str) -> None:
        """
        Initializes the blob client for a specific file name.

        Args:
            file_name (str): The name of the file/blob.
        """
        if not hasattr(self, '_container_client'):
            self._init_container_client()
        try:
            self._blob_client = self._container_client.get_blob_client(file_name)
        except Exception as err:
            raise err

    def upload_blob(self, file_path: str) -> BlobHandlerUploadBlob:
        """
        Uploads a file as a blob to the container.

        Args:
            file_path (str): The path of the file to be uploaded.

        Returns:
            BlobHandlerUploadBlob: A BlobHandlerUploadBlob object with the upload status and blob URL.
        """
        res = {
            "status": False,
            "BlobUrl": None
        }
        if not os.path.exists(file_path):
            print(f'file path not found: {file_path}')
        if not hasattr(self, '_container_client'):
            self._init_container_client()
        if not self._container_client.exists():
            self._container_client.create_container()

        file_name = os.path.split(file_path)[1]
        self._init_blob_client(file_name)
        try:
            with open(file=file_path, mode='rb') as data:
                self._container_client.upload_blob(name=file_name, data=data, overwrite=True)
                if self._blob_client.exists():
                    res["status"] = True
                    res["BlobUrl"] = self._blob_client.url
        except Exception as err:
            raise err

        res = BlobHandlerUploadBlob(
            Status=res["status"],
            BlobUrl=res["BlobUrl"]
        )
        return res

    def list_blobs(self) -> BlobPropertiesApiOut:
        """
        Lists all blobs in the container.

        Returns:
            BlobPropertiesApiOut: A BlobPropertiesApiOut object 
            with a list of BlobProperties objects containing the blob name and URL.
        """
        blobs = self._container_client.list_blobs()
        result: list[BlobProperties] = []
        for b in blobs:
            self._init_blob_client(b.name)
            result.append(BlobProperties(Name=b.name, BlobUrl=self._blob_client.url))
        parsed_result = BlobPropertiesApiOut(Value=result)
        return parsed_result

    def delete_blob(self, blob_name: str) -> bool:
        """
        Deletes a blob from the container.

        Args:
            blob_name (str): The name of the blob to be deleted.

        Returns:
            bool: True if the delete operation is successful, False otherwise.
        """
        try:
            self._container_client.delete_blob(blob_name)
            return True
        except HttpResponseError as err:
            raise err
