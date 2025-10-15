from fastapi import APIRouter,File, UploadFile, Request, Form, HTTPException, Query
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse
from pathlib import Path
from scripts.path_control import PM
from scripts.unique_string_generate import unique_name
from scripts.logger import logger


router = APIRouter(tags=["Files"])

@router.post("/upload/")
async def upload_file(
    request: Request,  # 添加 request 参数
    file: UploadFile = File(None),
    text: str = Form(None)
):
    form_data = await request.form()
    only_upload = form_data.get('only_upload') is not None
    if only_upload:
        file_to_path = PM.get_env("STORAGE_DIR_PATH")  # 不需要处理文件夹
    else:
        file_to_path = PM.get_env("UPLOAD_DIR_PATH") # 文件需要处理

    client_ip = request.client.host  # 获取客户端 IP

    file_to_path = Path(file_to_path)
    
    if file:
        dst = file_to_path / f"{unique_name() + Path(file.filename).suffix}"
        with dst.open("wb") as buffer:
            while chunk := await file.read(1024 * 1024):
                buffer.write(chunk)
        logger.info(f"File uploaded successfully from {client_ip}: {dst.name}")
        return RedirectResponse(url="/", status_code=303)

    elif text:
        filename = unique_name() + '.txt'
        dst = file_to_path / filename
        dst.write_text(text, encoding= PM.get_env("ENCODING"))
        logger.info(f"Text uploaded successfully from {client_ip}: {filename}")
        return RedirectResponse(url="/", status_code=303)

    logger.error(f"Upload failed from {client_ip}: No file or text provided.")
    return HTMLResponse(content="<h1>上传失败：未提供文件或文本</h1>", status_code=400)

@router.get("/download/{file_name}", response_class=FileResponse)
async def download_file(file_name: str, request: Request):
    file_path = Path(PM.get_env("UPLOAD_DIR_PATH")) / Path(file_name).name

    if not file_path.is_file():
        logger.error(f"Download failed from {request.client.host}: File not found - {file_name}")
        raise HTTPException(404, "文件不存在")
    logger.info(f"File downloaded successfully from {request.client.host}: {file_name}")
    return FileResponse(path=file_path, filename=file_path.name, media_type="application/octet-stream")
