from fastapi import FastAPI, Request, File, UploadFile, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .models import Base, FileContent
from .schemas import FileCreate, FileNamesRequest
from .crud import create_file, get_files, get_files_by_names
from .database import engine, SessionLocal
from fastapi import Path
import os
import chardet


Base.metadata.create_all(bind=engine)

app = FastAPI()


app.mount("/static", StaticFiles(directory="app/static"), name="static")


templates = Jinja2Templates(directory="app/templates")


UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})



@app.get("/files/{filename}")
async def get_file_by_name(filename: str = Path(..., description="Имя файла"), db: Session = Depends(get_db)):
    try:
        # Ищем файл в базе данных по имени
        file = db.query(FileContent).filter(FileContent.name == filename).first()
        if not file:
            raise HTTPException(status_code=404, detail="File not found")


        return JSONResponse(
            status_code=200,
            content={
                "id": file.id,
                "name": file.name,
                "content": file.content.decode("utf-8") if isinstance(file.content, bytes) else file.content
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload")
async def upload_files(request: Request, files: list[UploadFile] = File(...), db: Session = Depends(get_db)):
    for file in files:
        try:
            file_content = await file.read()

            # Определяем кодировку файла
            encoding = chardet.detect(file_content)['encoding']
            if not encoding:
                encoding = 'utf-8'


            try:
                decoded_content = file_content.decode(encoding)
            except UnicodeDecodeError:
                decoded_content = file_content.decode('utf-8', errors='replace')  # Заменяем некорректные символы


            file_path = os.path.join(UPLOAD_DIR, file.filename)
            with open(file_path, "wb") as f:
                f.write(file_content)

            # Сохраняем информацию о файле в базу данных
            file_db = FileCreate(name=file.filename, content=decoded_content)
            db_file = create_file(db, file_db)
            db.commit()
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to process file {file.filename}: {str(e)}")

    return RedirectResponse(url="/success", status_code=303)
# Роут для отображения страницы успеха
@app.get("/success", response_class=HTMLResponse)
async def success_page(request: Request):
    return templates.TemplateResponse("success.html", {"request": request})

# Роут для загрузки файла через API
@app.post("/uploadfile/")
async def create_upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        file_content = await file.read()

        # Сохраняем файл на сервере в папку uploads
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Сохраняем информацию о файле в базу данных
        file_db = FileCreate(name=file.filename, content=file_content.decode("utf-8"))
        db_file = create_file(db, file_db)
        db.commit()

        return JSONResponse(status_code=200, content={"message": "File uploaded successfully", "file_id": db_file.id})
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# Роут для получения всех файлов
@app.get("/files/")
async def get_all_files(db: Session = Depends(get_db)):
    try:
        files = get_files(db)
        files_data = [{"id": file.id, "name": file.name, "content": file.content} for file in files]
        return JSONResponse(status_code=200, content={"files": files_data})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Роут для получения файлов по именам
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