from pydantic import BaseModel
from typing import List

class FileCreate(BaseModel):
    name: str
    content: str

class FileNamesRequest(BaseModel):
    names: List[str]