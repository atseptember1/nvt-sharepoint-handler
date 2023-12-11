from pydantic import BaseModel
from common import CustomSkillContentRecordOut


class FileModelOut(BaseModel):
    BlobUrl: str
    FileName: str
    Success: bool
    
class OpenAISummarizeOut(BaseModel):
    content: str
    
class CustomSkillContentOut(BaseModel):
    values: list[CustomSkillContentRecordOut]
    
