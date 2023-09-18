import os
from azure.identity import DefaultAzureCredential
from azure.storage.blob import ContainerClient, BlobClient


class BlobHandler:
    def __init__(self, storage_account_name: str, container_name: str) -> None:
        self.storage_account_name = storage_account_name
        self.container_name = container_name

    def _init_credential(self) -> None:
        try:
            # credential automatically get from environment or use MSI with DefaultAzureCredential function
            self._token = DefaultAzureCredential()
        except Exception as err:
            raise(err)

    def _init_container_client(self) -> None:
        self._init_credential() # get the blob client credential
        try:
            self._container_client = ContainerClient(account_url=f'https://{self.storage_account_name}.blob.core.windows.net/',
                                                        container_name=self.container_name,
                                                        credential=self._token)
        except Exception as err:
            raise(err)
        
    def _init_blob_client(self, file_name) -> None:
        if hasattr(self, '_container_client'):
            try:
                self._blob_client = self._container_client.get_blob_client(file_name)
            except Exception as err:
                raise(err)

    def upload_blob(self, file_path: str) -> BlobClient.url:
        if not os.path.exists(file_path):
            print(f'file path not found: {file_path}')
        if not hasattr(self, '_container_client'):
            self._init_container_client()
        if not self._container_client.exists():
            self._container_client.create_container()

        file_name = os.path.split(file_path)[1]
        self._init_blob_client(file_name)
        if self._blob_client.exists():
            self._blob_client.delete_blob()

        try:
            with open(file=file_path, mode='rb') as data:
                self._container_client.upload_blob(name=file_name, data=data)
                if self._blob_client.exists():
                    return self._blob_client.url
        except Exception as err:
            raise(err)
