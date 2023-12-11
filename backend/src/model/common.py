from pydantic import BaseModel


class CustomSkillContentDataIn(BaseModel):
    text: str

class CustomSkillContentRecordIn(BaseModel):
    recordId: str
    data: CustomSkillContentDataIn
    
class CustomSkillContentDataOut(BaseModel):
    questions: str
    
class CustomSkillContentRecordOut(BaseModel):
    recordId: str
    data: CustomSkillContentDataOut
    
class GraphConfig(BaseModel):
    tenant_id: str
    client_id: str
    
class SharepointToken(BaseModel):
    token_type: str
    expires_in: int
    ext_expires_in: int
    access_token: str
    
# class SharepointUserGroupMemberShip(BaseModel):
#     displayName: str
#     id: str

class SharepointSite(BaseModel):
    displayName: str
    name: str
    webUrl: str
    id: str
    companyId: str
    siteId1: str
    siteId2: str

class SharepointSiteList(BaseModel):
    value: list[SharepointSite]
    
class AzureADGroup(BaseModel):
    displayName: str
    id: str
    proxyAddresses: list[str]
    
class AzureADGroupList(BaseModel):
    value: list[AzureADGroup]
    
class IndexerProp(BaseModel):
    name: str
    DataSourceName: str
    SkillSetName: str
    IndexName: str
    
class IndexerList(BaseModel):
    value: list[IndexerProp]