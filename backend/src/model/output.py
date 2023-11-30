from pydantic import BaseModel


class FileModelOut(BaseModel):
    BlobUrl: str
    FileName: str
    Success: bool
    
class OpenAISummarizeOut(BaseModel):
    content: str