from pydantic import BaseModel


class BlobPropertiesApiOut(BaseModel):
    Value: any

    class Config:
        arbitrary_types_allowed = True
