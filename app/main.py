from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base, FileContent
from .schemas import FileCreate, FileNamesRequest
from .crud import create_file, get_files, get_files_by_names

DATABASE_URL = "postgresql://user:password@db:5432/sber_bot_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        file_content = await file.read()
        file_db = FileCreate(name=file.filename, content=file_content.decode("utf-8"))
        db_file = create_file(db, file_db)
        db.commit()
        return JSONResponse(status_code=200, content={"message": "File uploaded successfully", "file_id": db_file.id})
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/files/")
async def get_all_files(db: Session = Depends(get_db)):
    try:
        files = get_files(db)
        files_data = [{"id": file.id, "name": file.name, "content": file.content} for file in files]
        return JSONResponse(status_code=200, content={"files": files_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/get_files_by_names/")
async def get_files_by_names(file_names: FileNamesRequest, db: Session = Depends(get_db)):
    try:
        files = get_files_by_names(db, file_names.names)
        if not files:
            raise HTTPException(status_code=404, detail="Files not found")

        files_content = [{"name": file.name, "content": file.content} for file in files]
        return JSONResponse(status_code=200, content={"files": files_content})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))