import os
from azure.identity import DefaultAzureCredential
from azure.storage.blob import ContainerClient, BlobClient
from pydantic import BaseModel


class BlobConfig(BaseModel):
    sa_name: str
    container_name: str
    credential: DefaultAzureCredential


class BlobHandler:
    def __init__(self, config: BlobConfig) -> None:
        self.config = config

    def _init_container_client(self) -> None:
        try:
            self._container_client = ContainerClient(account_url=f'https://{self.config.sa_name}.blob.core.windows.net/',
                                                     container_name=self.config.container_name,
                                                     credential=self.config.credential)
        except Exception as err:
            raise (err)

    def _init_blob_client(self, file_name) -> None:
        if hasattr(self, '_container_client'):
            try:
                self._blob_client = self._container_client.get_blob_client(file_name)
            except Exception as err:
                raise (err)

    def upload_blob(self, file_path: str) -> dict[str, any]:
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
            raise (err)
        return res
