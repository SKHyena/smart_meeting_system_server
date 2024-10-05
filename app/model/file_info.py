from pydantic import BaseModel


class FileInfo(BaseModel):    
    file_name: str
