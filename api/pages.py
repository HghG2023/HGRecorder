from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import FileResponse, RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from scripts.path_control import PM
from scripts.logger import logger
from api.auth import verify_auth
from scripts.DBprocessor import ProcessDB
from app.bbcLearning import BbcLearning
from pathlib import Path

router = APIRouter(tags=["Pages"])
templates = Jinja2Templates(directory=str(PM.get_env("TEMPLATES_PATH")))
db = ProcessDB()

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if request.cookies.get(PM.get_env("COOKIE_NAME")) != "true":
        return RedirectResponse("/login")
    files = [f.name for f in Path(PM.get_env("UPLOAD_DIR_PATH")).iterdir() if f.is_file()]
    return templates.TemplateResponse("index.html", {"request": request, "files": files})

@router.get("/daily/", response_class=HTMLResponse)
async def daily(request: Request):
    events = db.search_events_undo()
    return templates.TemplateResponse("daily.html", {"request": request, "events": events})

@router.get("/learn/", response_class=HTMLResponse)
async def learn(request: Request):
    article = BbcLearning().doing
    if not article:
        raise HTTPException(404, "文章不存在")
    # 修正路径
    for k in ['path_audio', 'path_pdf']:
        if k in article:
            article[k] = article[k].replace("\\", "/")
            if not article[k].startswith("userdata/"):
                article[k] = "userdata/" + article[k]
    return templates.TemplateResponse("learn.html", {"request": request, "article": article})

@router.get("/detail/{event_id}", response_class=HTMLResponse)
async def event_detail(request: Request, event_id: int):
    event = db.read_event(event_id)
    if not event:
        raise HTTPException(404, "事件不存在")
    return templates.TemplateResponse("detail.html", {"request": request, "event": event})



@router.get("/userdata/{file_path:path}")
async def get_userdata_file(file_path: str):
    USERDATA_DIR = Path(PM.get_env("USERDATA_DIR_PATH"))

    # 修正：在文件路径前添加 "userdata/" 前缀
    corrected_path = "userdata" / Path(file_path)
    full_path = USERDATA_DIR / corrected_path

    # 安全检查
    try:
        full_path.resolve().relative_to(USERDATA_DIR.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="访问被拒绝")
    
    # 检查文件是否存在
    if not full_path.exists() or not full_path.is_file():
        # # 列出可能的文件位置
        # if USERDATA_DIR.exists():
        #     print(f"USERDATA_DIR 下的 userdata 目录: {list((USERDATA_DIR / 'userdata').glob('**/*')) if (USERDATA_DIR / 'userdata').exists() else '不存在'}")
        raise HTTPException(status_code=404, detail=f"文件不存在: {full_path}")
    
    # 根据文件类型设置响应
    if file_path.endswith('.pdf'):
        return FileResponse(full_path, media_type='application/pdf')
    elif file_path.endswith('.mp3'):
        return FileResponse(full_path, media_type='audio/mpeg')
    else:
        return FileResponse(full_path)
