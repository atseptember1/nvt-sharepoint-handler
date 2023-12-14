from pydantic import BaseModel
from azure.identity import DefaultAzureCredential
from common import CustomSkillContentRecordIn


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
    key: str = None
    chat_deployment: str
    chat_model: str
    embed_deployment: str = None
    embed_model: str = None
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

class CognitveSearchConfig(BaseModel):
    endpoint: str
    index_name: str
    sharepoint_appid: str
    sharepoint_appsec: str
    sharepoint_apptenantid: str
    sharepoint_domain: str
    aoai_endpoint: str
    aoai_key: str
    aoai_embed_deployment: str

# CustomSkill input based from SplitSkill of Azure AI Search
class CustomSkillContentIn(BaseModel):
    values: list[CustomSkillContentRecordIn]
    
class SharepointHelperConfig(BaseModel):
    client_id: str
    client_secret: str
    tenant_id: str
    
class ListUserSiteIn(BaseModel):
    userId: str