from sqlalchemy import Column, Integer, String, Text
from .database import Base

class FileContent(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    content = Column(Text)