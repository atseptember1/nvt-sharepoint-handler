from pydantic import BaseModel

from common import BlobProperties


class ListUserSiteApiIn(BaseModel):
    userId: str


class StorageDeleteApiIn(BaseModel):
    Files: list[str]


class BlobPropertiesApiIn(BaseModel):
    Value: list[BlobProperties]
