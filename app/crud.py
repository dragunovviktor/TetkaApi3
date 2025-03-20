from sqlalchemy.orm import Session
from .models import FileContent
from .schemas import FileCreate

def create_file(db: Session, file: FileCreate):
    db_file = FileContent(name=file.name, content=file.content)
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def get_files(db: Session):
    return db.query(FileContent).all()

def get_files_by_names(db: Session, names: list):
    return db.query(FileContent).filter(FileContent.name.in_(names)).all()