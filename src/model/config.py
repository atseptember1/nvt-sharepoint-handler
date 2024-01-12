from pydantic import BaseModel


class StorageConfig(BaseModel):
    StorageName: str
    StorageConnStr: str = None
    ContainerName: str


class SharepointHelperConfig(BaseModel):
    ClientId: str
    ClientSecret: str
    TenantId: str


class SearchConfig(BaseModel):
    Endpoint: str
    IndexName: str
    AoaiEndpoint: str
    AoaiKey: str
    AoaiEmbedDeployment: str


class SharepointSearchConfig(SearchConfig):
    SharepointClientId: str
    SharepointClientSecret: str
    SharepointTenantId: str
    SharepointDomain: str


class StorageSearchConfig(SearchConfig):
    StorageName: str
    StorageConnStr: str = None
    ContainerName: str
