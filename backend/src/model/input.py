from pydantic import BaseModel
from azure.identity import DefaultAzureCredential


class BlobConfig(BaseModel):
    sa_name: str
    container_name: str
    credential: DefaultAzureCredential

    class Config:
        arbitrary_types_allowed = True

class FileManagementConfig(BaseModel):
    search_config: any
    openai_config: any
    blob_config: any

    class Config:
        arbitrary_types_allowed = True
        
class OpenAIConfig(BaseModel):
    endpoint: str
    key: str
    chat_deployment: str
    chat_model: str
    embed_deployment: str
    embed_model: str
    api_type: str = "azure"
    api_version: str = "2023-03-15-preview"
    
class SearchServiceConfig(BaseModel):
    endpoint: str
    credential: DefaultAzureCredential
    index_name: str

    class Config:
        arbitrary_types_allowed = True
        
class OpenaiSummarizeIn(BaseModel):
    paragraph: str
